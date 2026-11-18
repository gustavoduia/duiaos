#!/usr/bin/env python3
"""DuiaOS — Ora, o navegador do DuiaOS (ADR 072).

Interface própria em QML sobre o motor Chromium do Qt WebEngine. Abas, barra de endereço com
sugestões, favoritos (com barra e pastas), histórico com busca, downloads, configurações, janela
privada, ferramentas do desenvolvedor, tela cheia, permissões por site e menus na Barra de Recursos.

Um processo só por pessoa (o perfil do Chromium não aceita dois processos): abrir o Ora de novo
entrega os endereços à janela que já existe, pelo soquete local duiaos-ora-<uid>.

Uso:
  main.py [ENDEREÇO...] [--nova-janela] [--privada]
  main.py --demonstracao [--pagina inicio|historico|favoritos|downloads|configuracoes|web] [--escuro]
          [--captura ARQUIVO]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
# Motor web do DuiaOS (pacote duiaos-motor-web, ADR 072): o Qt WebEngine recente vem antes do PySide6 do Debian,
# só neste processo (os programas que ele abre não herdam).
_MOTOR_WEB = Path(os.environ.get("DUIAOS_MOTOR_WEB", "/usr/lib/duiaos/motor-web"))
if (_MOTOR_WEB / "PySide6").is_dir():
    sys.path.insert(0, str(_MOTOR_WEB))
for _comum in (Path(os.environ.get("DUIAOS_SHELL", "/usr/share/duiaos/shell")) / "comum",
               PASTA.parents[1] / "shell" / "comum"):
    if (_comum / "interface.py").is_file():
        sys.path.insert(0, str(_comum))
        break
sys.path.insert(0, str(PASTA))

DEMONSTRACAO = "--demonstracao" in sys.argv
if DEMONSTRACAO:
    # Dados de mentira numa pasta temporária: a demonstração nunca toca nos dados da pessoa
    _TEMP = Path(tempfile.mkdtemp(prefix="ora-demo-"))
    os.environ["XDG_DATA_HOME"] = str(_TEMP / "dados")
    os.environ["XDG_CONFIG_HOME"] = str(_TEMP / "config")
    os.environ["XDG_CACHE_HOME"] = str(_TEMP / "cache")

import dados  # noqa: E402
import endereco  # noqa: E402

from PySide6.QtCore import (QObject, Property, QTimer, QUrl, Signal, Slot, QStandardPaths,  # noqa: E402
                            QCoreApplication, Qt)
from PySide6.QtNetwork import QLocalServer, QLocalSocket  # noqa: E402

VERSAO = "0.1"
NOME_SOQUETE = f"duiaos-ora-{os.getuid()}"
MENSAGENS = {"ora_inicio": "Ora aberto", "ora_janela": "Janela do Ora aberta", "ora_download": "Download no Ora",
             "ora_download_fim": "Download do Ora terminou", "ora_importar": "Favoritos importados no Ora",
             "ora_processo_parou": "Página do Ora parou", "ora_erro": "Erro no Ora"}


def registrar(nivel, evento, **campos):
    """Eventos no registro do sistema (duiaos_registro), quando existir. Endereços nunca são registrados."""
    try:
        import duiaos_registro
    except ImportError:
        return
    getattr(duiaos_registro, nivel)(evento, MENSAGENS.get(evento, evento), **campos)


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def enderecos_da_linha_de_comando():
    saida, pular = [], False
    for i, arg in enumerate(sys.argv[1:], 1):
        if pular:
            pular = False
            continue
        if arg in ("--pagina", "--captura"):
            pular = True
            continue
        if arg.startswith("-"):
            continue
        caminho = Path(arg)
        saida.append(caminho.resolve().as_uri() if caminho.exists() else arg)
    return saida


def entregar_a_janela_aberta(pedido):
    """Já há um Ora aberto? Entrega o pedido e devolve True (este processo então sai)."""
    soquete = QLocalSocket()
    soquete.connectToServer(NOME_SOQUETE)
    if not soquete.waitForConnected(400):
        return False
    soquete.write(json.dumps(pedido).encode() + b"\n")
    soquete.flush()
    soquete.waitForBytesWritten(1000)
    soquete.disconnectFromServer()
    return True


class Bloqueador:
    """Cabeçalhos de privacidade em cada requisição (Não rastrear / Global Privacy Control)."""

    @staticmethod
    def criar(configuracoes):
        from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

        class Interceptador(QWebEngineUrlRequestInterceptor):
            def interceptRequest(self, info):
                if configuracoes["nao_rastrear"]:
                    info.setHttpHeader(b"DNT", b"1")
                    info.setHttpHeader(b"Sec-GPC", b"1")

        return Interceptador()


class Ora(QObject):
    mudou = Signal()
    favoritosMudaram = Signal()
    downloadsMudaram = Signal()
    configuracoesMudaram = Signal()
    abrirPedido = Signal(str, str)           # endereço, id da janela que abre
    ultimaMudou = Signal()
    aviso = Signal(str)

    def __init__(self, motor, perfil, perfil_privado, config):
        super().__init__()
        self._motor = motor
        self.perfil = perfil
        self.perfil_privado = perfil_privado
        self.banco = dados.Banco()
        self.config = config
        self._downloads_ativos = {}          # id → (QQuickWebEngineDownloadRequest, dict)
        self._seq = 0
        self._sessoes = {}                   # id da janela → [{"url", "titulo"}]
        self._janelas = []
        self._ids = []                       # janelas abertas, na ordem em que ficaram ativas
        self._salvar_sessao = QTimer(self, singleShot=True, interval=1500, timeout=self._gravar_sessao)
        for p in (perfil, perfil_privado):
            p.downloadRequested.connect(self._download_pedido)
            p.presentNotification.connect(self._notificacao)

    # ------------------------------------------------------------ janelas
    def abrir_janela(self, privada=False, enderecos=None):
        self._motor.setInitialProperties({"privada": privada, "enderecosIniciais": list(enderecos or [])})
        self._motor.load(PASTA / "JanelaOra.qml")
        if self._motor.rootObjects():
            self._janelas.append(self._motor.rootObjects()[-1])
        registrar("info", "ora_janela", privada=privada)

    @Slot(bool, str)
    def novaJanela(self, privada, url):
        self.abrir_janela(privada, [url] if url else [])

    def pedido_externo(self, pedido):
        enderecos = [endereco.normalizar(e, self.config["buscador"]) for e in pedido.get("abrir", [])]
        if pedido.get("privada") or pedido.get("nova_janela") or not self._ids:
            self.abrir_janela(bool(pedido.get("privada")), enderecos)
            return
        for e in enderecos or [""]:
            self.abrirPedido.emit(e, self._ids[-1])

    @Slot(str)
    def janelaAtiva(self, id_janela):
        if id_janela in self._ids:
            self._ids.remove(id_janela)
        self._ids.append(id_janela)
        self.ultimaMudou.emit()

    @Slot(int, result=str)
    def nomePermissao(self, tipo):
        return {1: "usar o seu microfone", 2: "usar a sua câmera", 3: "usar a sua câmera e o seu microfone",
                4: "ver a sua tela", 5: "ver a sua tela e ouvir o som do computador", 6: "esconder o cursor do mouse",
                7: "mostrar notificações", 8: "saber a sua localização", 9: "ler e escrever na área de transferência",
                10: "ver as fontes instaladas"}.get(int(tipo), "usar um recurso do computador")

    @Slot(str, result=str)
    def caminhoPdf(self, titulo):
        pasta = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or Path.home())
        pasta.mkdir(parents=True, exist_ok=True)
        nome = "".join(c for c in (titulo or "Página") if c not in '/\\:*?"<>|').strip()[:80] or "Página"
        destino, n = pasta / f"{nome}.pdf", 2
        while destino.exists():
            destino, n = pasta / f"{nome} ({n}).pdf", n + 1
        return str(destino)

    # ------------------------------------------------------------ endereço
    @Slot(str, result=str)
    def normalizar(self, texto):
        return endereco.normalizar(texto, self.config["buscador"])

    @Slot(str, result=str)
    def paraMostrar(self, url):
        return endereco.para_mostrar(url)

    @Slot(str, result=str)
    def dominio(self, url):
        return endereco.dominio(url)

    @Slot(str, result="QVariantList")
    def sugestoes(self, texto):
        return self.banco.sugestoes(texto)

    # ------------------------------------------------------------ histórico
    @Slot(str, str)
    def visitou(self, url, titulo):
        self.banco.registrar_visita(url, titulo)

    @Slot(str, str)
    def atualizarTitulo(self, url, titulo):
        self.banco.atualizar_titulo(url, titulo)

    @Slot(str, result="QVariantList")
    def historico(self, busca):
        return self.banco.historico(busca)

    @Slot(int)
    def removerDoHistorico(self, id_item):
        self.banco.remover_do_historico(id_item)
        self.mudou.emit()

    @Slot(str)
    def apagarHistorico(self, periodo):
        """periodo: hora | dia | semana | tudo."""
        segundos = {"hora": 3600, "dia": 86400, "semana": 7 * 86400}.get(periodo)
        self.banco.apagar_historico(time.time() - segundos if segundos else 0)
        self.mudou.emit()
        self.aviso.emit("Histórico apagado.")

    @Slot(result="QVariantList")
    def maisVisitados(self):
        return self.banco.mais_visitados(8)

    @Slot()
    def limparDadosDeNavegacao(self):
        self.banco.apagar_historico(0)
        self.perfil.clearHttpCache()
        self.perfil.cookieStore().deleteAllCookies()
        self.mudou.emit()
        self.aviso.emit("Histórico, cookies e arquivos temporários apagados.")

    # ------------------------------------------------------------ favoritos
    @Slot(str, str, result=bool)
    def alternarFavorito(self, url, titulo):
        if self.banco.eh_favorito(url):
            self.banco.remover_favorito(url)
            marcado = False
        else:
            self.banco.adicionar_favorito(url, titulo)
            marcado = True
        self.favoritosMudaram.emit()
        return marcado

    @Slot(str, result=bool)
    def ehFavorito(self, url):
        return self.banco.eh_favorito(url)

    @Slot(str)
    def removerFavorito(self, url):
        self.banco.remover_favorito(url)
        self.favoritosMudaram.emit()

    @Slot(int, str, str)
    def editarFavorito(self, id_favorito, titulo, url):
        self.banco.renomear_favorito(id_favorito, titulo, url)
        self.favoritosMudaram.emit()

    @Slot(str, result="QVariantList")
    def favoritosDaPasta(self, pasta):
        return self.banco.favoritos(pasta)

    def _todos_favoritos(self):
        return self.banco.favoritos()

    @Slot(str, str, result=str)
    def importar(self, tipo, caminho):
        try:
            if tipo == "chrome":
                lista, rotulo = dados.ler_chrome(caminho), "Importados do Chrome"
            elif tipo == "firefox":
                lista, rotulo = dados.ler_firefox(caminho), "Importados do Firefox"
            else:
                lista, rotulo = dados.ler_html(caminho.replace("file://", "")), "Importados"
        except Exception as erro:  # noqa: BLE001 — arquivo de outro programa: qualquer formato inesperado
            registrar("aviso", "ora_erro", acao="importar", erro=type(erro).__name__)
            return "Não foi possível ler os favoritos desse navegador."
        n = self.banco.importar(lista, rotulo)
        registrar("info", "ora_importar", tipo=tipo, quantidade=n)
        self.favoritosMudaram.emit()
        return f"{n} favoritos importados para a pasta “{rotulo}”."

    @Slot(result=str)
    def exportarFavoritos(self):
        pasta = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or Path.home())
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / "Favoritos do Ora.html"
        dados.exportar_html(self.banco.favoritos(), destino)
        return f"Favoritos salvos em {destino}."

    # ------------------------------------------------------------ configurações
    @Slot(str, "QVariant")
    def definir(self, chave, valor):
        self.config.definir(chave, valor)
        if chave in ("bloquear_cookies_de_terceiros", "corretor_ortografico"):
            self._aplicar_perfil()
        self.configuracoesMudaram.emit()

    def _aplicar_perfil(self):
        idiomas = ["pt_BR"] if self.config["corretor_ortografico"] else []
        for p in (self.perfil, self.perfil_privado):
            p.setSpellCheckEnabled(bool(idiomas) and _tem_dicionarios())
            if idiomas:
                p.setSpellCheckLanguages(idiomas)

    @Slot(result=bool)
    def ehPadrao(self):
        if DEMONSTRACAO or not shutil.which("xdg-settings"):
            return False
        try:
            saida = subprocess.run(["xdg-settings", "get", "default-web-browser"], capture_output=True, text=True,
                                   timeout=3).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return False
        return saida == "duiaos-ora.desktop"

    @Slot()
    def tornarPadrao(self):
        if DEMONSTRACAO:
            return
        comandos = [["xdg-settings", "set", "default-web-browser", "duiaos-ora.desktop"]]
        comandos += [["xdg-mime", "default", "duiaos-ora.desktop", t] for t in
                     ("x-scheme-handler/http", "x-scheme-handler/https", "text/html", "application/xhtml+xml")]
        for comando in comandos:
            try:
                subprocess.run(comando, timeout=5, check=False)
            except (OSError, subprocess.SubprocessError):
                pass
        self.configuracoesMudaram.emit()
        self.aviso.emit("O Ora agora é o navegador padrão.")

    @Slot(result="QVariantList")
    def navegadoresParaImportar(self):
        return dados.navegadores_instalados()

    @Slot(result="QVariantList")
    def buscadores(self):
        return [{"id": k, "nome": v["nome"]} for k, v in endereco.BUSCADORES.items()]

    # ------------------------------------------------------------ sessão
    @Slot(str, "QVariantList")
    def guardarSessao(self, id_janela, abas):
        self._sessoes[id_janela] = [a for a in abas if a.get("url")]
        self._salvar_sessao.start()

    @Slot(str)
    def janelaFechada(self, id_janela):
        if id_janela in self._ids:
            self._ids.remove(id_janela)
        # A última janela normal fecha: a sessão dela é a que volta na próxima vez
        if len(self._sessoes) > 1:
            self._sessoes.pop(id_janela, None)
        self._gravar_sessao()

    def _gravar_sessao(self):
        if DEMONSTRACAO:
            return
        self.config.definir("sessao", [a for lista in self._sessoes.values() for a in lista][:60])

    def enderecos_iniciais(self):
        if self.config["ao_iniciar"] == "sessao":
            return [a["url"] for a in self.config["sessao"] if a.get("url")]
        if self.config["ao_iniciar"] == "pagina" and self.config["pagina_inicial"]:
            return [endereco.normalizar(self.config["pagina_inicial"], self.config["buscador"])]
        return []

    # ------------------------------------------------------------ downloads
    def _pasta_downloads(self):
        escolhida = self.config["pasta_downloads"]
        if escolhida and Path(escolhida).is_dir():
            return escolhida
        return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or str(Path.home())

    def _download_pedido(self, pedido):
        self._seq += 1
        ident = self._seq
        pedido.setDownloadDirectory(self._pasta_downloads())
        info = {"id": ident, "arquivo": pedido.downloadFileName(), "pasta": pedido.downloadDirectory(),
                "url": pedido.url().toString(), "recebido": 0, "total": pedido.totalBytes(), "estado": "andamento"}
        self._downloads_ativos[ident] = (pedido, info)

        def atualizar():
            info["recebido"] = pedido.receivedBytes()
            info["total"] = pedido.totalBytes()
            info["arquivo"] = pedido.downloadFileName()
            estado = pedido.state()
            from PySide6.QtWebEngineCore import QWebEngineDownloadRequest as R
            info["estado"] = {R.DownloadState.DownloadCompleted: "concluido", R.DownloadState.DownloadCancelled: "cancelado",
                              R.DownloadState.DownloadInterrupted: "interrompido"}.get(
                estado, "pausado" if pedido.isPaused() else "andamento")
            if pedido.isFinished() and not info.get("gravado"):
                info["gravado"] = True
                if pedido.profile() is not self.perfil_privado:
                    self.banco.registrar_download(info["url"], str(Path(info["pasta"]) / info["arquivo"]),
                                                  info["total"], info["estado"])
                registrar("info", "ora_download_fim", estado=info["estado"], tamanho=info["total"])
                if info["estado"] == "concluido":
                    self.aviso.emit(f"Download concluído: {info['arquivo']}")
            self.downloadsMudaram.emit()

        for sinal in (pedido.receivedBytesChanged, pedido.totalBytesChanged, pedido.stateChanged,
                      pedido.isPausedChanged, pedido.isFinishedChanged):
            sinal.connect(atualizar)
        pedido.accept()
        registrar("info", "ora_download", tamanho=info["total"])
        self.downloadsMudaram.emit()

    def _lista_downloads(self):
        ativos = [dict(info) for _, info in sorted(self._downloads_ativos.values(), key=lambda par: -par[1]["id"])]
        caminhos = {str(Path(a["pasta"]) / a["arquivo"]) for a in ativos}
        antigos = [{"id": -d["id"], "arquivo": Path(d["arquivo"]).name, "pasta": str(Path(d["arquivo"]).parent),
                    "url": d["url"], "recebido": d["tamanho"], "total": d["tamanho"], "estado": d["estado"]}
                   for d in self.banco.downloads() if d["arquivo"] not in caminhos]
        for item in ativos + antigos:
            item["existe"] = (Path(item["pasta"]) / item["arquivo"]).exists()
        return ativos + antigos

    @Slot(int, str)
    def acaoDownload(self, ident, acao):
        par = self._downloads_ativos.get(ident)
        if par and acao in ("pausar", "retomar", "cancelar"):
            pedido = par[0]
            {"pausar": pedido.pause, "retomar": pedido.resume, "cancelar": pedido.cancel}[acao]()
            return
        item = next((d for d in self._lista_downloads() if d["id"] == ident), None)
        if not item:
            return
        caminho = Path(item["pasta"]) / item["arquivo"]
        if acao == "abrir" and caminho.exists():
            _abrir_externo(str(caminho))
        elif acao == "pasta":
            _abrir_externo(str(caminho.parent))

    @Slot()
    def limparDownloads(self):
        self.banco.limpar_downloads()
        self._downloads_ativos = {k: v for k, v in self._downloads_ativos.items() if v[1]["estado"] == "andamento"}
        self.downloadsMudaram.emit()

    # ------------------------------------------------------------ notificações dos sites
    def _notificacao(self, notificacao):
        if DEMONSTRACAO or not shutil.which("notify-send"):
            return
        origem = endereco.dominio(notificacao.origin().toString())
        try:
            subprocess.Popen(["notify-send", "--app-name=Ora", "--icon=duiaos-ora",
                              notificacao.title() or origem, notificacao.message()],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            notificacao.show()
        except OSError:
            pass

    # ------------------------------------------------------------ para o QML
    favoritos = Property("QVariantList", _todos_favoritos, notify=favoritosMudaram)
    favoritosDaBarra = Property("QVariantList", lambda self: self.banco.favoritos(""), notify=favoritosMudaram)
    pastasDeFavoritos = Property("QVariantList", lambda self: self.banco.pastas(), notify=favoritosMudaram)
    downloads = Property("QVariantList", _lista_downloads, notify=downloadsMudaram)
    downloadsEmAndamento = Property(int, lambda self: sum(1 for _, i in self._downloads_ativos.values()
                                                            if i["estado"] == "andamento"), notify=downloadsMudaram)
    configuracoes = Property("QVariantMap", lambda self: dict(self.config.valores), notify=configuracoesMudaram)
    ultimaJanela = Property(str, lambda self: self._ids[-1] if self._ids else "", notify=ultimaMudou)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)
    versao = Property(str, lambda self: VERSAO, constant=True)

    @Property(str, constant=True)
    def versaoChromium(self):
        from PySide6.QtWebEngineCore import qWebEngineChromiumVersion
        return qWebEngineChromiumVersion()

    @Property(str, constant=True)
    def versaoMotor(self):
        from PySide6.QtWebEngineCore import qWebEngineVersion
        return qWebEngineVersion()


def _tem_dicionarios():
    pasta = os.environ.get("QTWEBENGINE_DICTIONARIES_PATH", "")
    return bool(pasta) and any(Path(pasta).glob("*.bdic"))


def _abrir_externo(caminho):
    if DEMONSTRACAO:
        return
    try:
        subprocess.Popen(["xdg-open", caminho], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def criar_perfis(config):
    from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
    perfil = QQuickWebEngineProfile("padrao")
    perfil.setPersistentStoragePath(str(dados.PASTA_DADOS / "perfis"))
    perfil.setCachePath(str(Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "duiaos" / "ora"))
    perfil.setPersistentCookiesPolicy(QQuickWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
    privado = QQuickWebEngineProfile()          # sem nome: nada vai para o disco
    for p in (perfil, privado):
        p.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en-US;q=0.7,en;q=0.6")
    return perfil, privado


def preparar_demonstracao(banco):
    agora = time.time()
    for url, titulo, pasta in (("https://duiaos.com.br/", "DuiaOS", ""), ("https://www.wikipedia.org/", "Wikipédia", ""),
                               ("https://www.youtube.com/", "YouTube", ""), ("https://github.com/", "GitHub", ""),
                               ("https://g1.globo.com/", "g1", "Notícias"), ("https://www.bbc.com/portuguese", "BBC Brasil", "Notícias"),
                               ("https://mail.google.com/", "Gmail", "")):
        banco.adicionar_favorito(url, titulo, pasta)
    visitas = [("https://duiaos.com.br/documentacao", "Documentação do DuiaOS", 9), ("https://www.wikipedia.org/", "Wikipédia", 7),
               ("https://www.youtube.com/", "YouTube", 6), ("https://github.com/gustavoduia", "gustavoduia · GitHub", 5),
               ("https://www.google.com/search?q=receita+de+bolo", "receita de bolo - Pesquisa Google", 3),
               ("https://g1.globo.com/", "g1 — Notícias", 4), ("https://www.bbc.com/portuguese", "BBC News Brasil", 2),
               ("https://maps.google.com/", "Google Maps", 2)]
    for i, (url, titulo, n) in enumerate(visitas):
        for _ in range(n):
            banco.registrar_visita(url, titulo)
        banco._exec("UPDATE historico SET ultima = ? WHERE url = ?", (agora - i * 5400, url))
    banco.registrar_download("https://exemplo.invalid/relatorio.pdf", str(Path.home() / "Downloads/relatorio-anual.pdf"),
                             2_400_000, "concluido")
    banco.registrar_download("https://exemplo.invalid/foto.jpg", str(Path.home() / "Downloads/foto-da-viagem.jpg"),
                             812_000, "concluido")


def pagina_de_demonstracao():
    """Página local para a captura da aba web (sem internet)."""
    html = (PASTA / "demonstracao.html")
    return html.as_uri() if html.exists() else "about:blank"


def main():
    privada = "--privada" in sys.argv
    pedido = {"abrir": enderecos_da_linha_de_comando(), "privada": privada, "nova_janela": "--nova-janela" in sys.argv}
    captura = argumento("--captura")
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QtWebEngineQuick.initialize()
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import interface

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Ora")
    app.setOrganizationName("DuiaOS")
    app.setDesktopFileName("duiaos-ora")
    if not DEMONSTRACAO and entregar_a_janela_aberta(pedido):
        sys.exit(0)
    interface.ligar_registro("duiaos-ora")
    registrar("info", "ora_inicio", versao=VERSAO)

    servidor = None
    if not DEMONSTRACAO:
        QLocalServer.removeServer(NOME_SOQUETE)
        servidor = QLocalServer()
        servidor.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        servidor.listen(NOME_SOQUETE)

    config = dados.Configuracoes()
    perfil, privado = criar_perfis(config)
    interceptador = Bloqueador.criar(config)
    for p in (perfil, privado):
        p.setUrlRequestInterceptor(interceptador)

    motor = QQmlApplicationEngine()
    interface.preparar(motor)
    ora = Ora(motor, perfil, privado, config)
    ora._aplicar_perfil()
    if DEMONSTRACAO:
        preparar_demonstracao(ora.banco)
        if "--escuro" in sys.argv:
            try:
                interface.aparencia().definirEscuro(True)      # preferências da pasta temporária da demonstração
            except Exception:  # noqa: BLE001 — só a captura
                pass
    contexto = motor.rootContext()
    contexto.setContextProperty("ora", ora)
    contexto.setContextProperty("perfilPadrao", perfil)
    contexto.setContextProperty("perfilPrivado", privado)
    contexto.setContextProperty("capturaArquivo", captura)
    contexto.setContextProperty("paginaDemonstracao", argumento("--pagina", ""))
    contexto.setContextProperty("enderecoDemonstracao", pagina_de_demonstracao())
    import menu_do_app
    menu = menu_do_app.criar("ora", [])
    contexto.setContextProperty("menuDoApp", menu)

    if servidor is not None:
        def nova_conexao():
            conexao = servidor.nextPendingConnection()

            def ler():
                while conexao.canReadLine():
                    try:
                        ora.pedido_externo(json.loads(bytes(conexao.readLine()).decode()))
                    except ValueError:
                        pass
            conexao.readyRead.connect(ler)
        servidor.newConnection.connect(nova_conexao)

    iniciais = pedido["abrir"] and [endereco.normalizar(e, config["buscador"]) for e in pedido["abrir"]]
    ora.abrir_janela(privada, iniciais or ([] if privada else ora.enderecos_iniciais()))
    if not motor.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    ora._gravar_sessao()
    for janela in motor.rootObjects():
        janela.setProperty("visible", False)
    ora._motor = None               # o motor do QML sai antes do "ora", que as janelas usam
    del motor
    # Ordem de saída do Qt WebEngine: janelas, perfis, aplicativo
    for p in (perfil, privado):
        p.setUrlRequestInterceptor(None)
    del ora, interceptador, perfil, privado, menu
    del app
    sys.exit(codigo)


if __name__ == "__main__":
    main()
