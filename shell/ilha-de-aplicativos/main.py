#!/usr/bin/env python3
"""DuiaOS — Ilha de Aplicativos e Central de Aplicativos.

Ilha de Aplicativos: barra inferior com os aplicativos fixados e os abertos.
Um clique abre o aplicativo ou, se ele já estiver aberto, traz a janela
para a frente.

Central de Aplicativos: tela com todos os aplicativos instalados e busca.
Abre pelo botão no início da Ilha ou pelo atalho Super+Espaço (que envia
o sinal SIGUSR1 a este programa).

A interface fica em IlhaDeAplicativos.qml.
Aplicativos fixados: ~/.config/duiaos/ilha-de-aplicativos.conf
O Wise (duiaos-wise.desktop), quando instalado, é sempre o primeiro da Ilha
e não pode ser desafixado; o Explorador de Arquivos vem logo depois, também fixo.
À direita, depois da divisória: a pasta Aplicativos, a pilha de Downloads (um
balão com os arquivos mais novos) e a Lixeira.

Uso:
  main.py                                inicia a Ilha
  main.py --demonstracao [--central|--downloads] [--captura ARQUIVO]
                                         janela comum com dados de exemplo
Janelas abertas: comando wlrctl (protocolo wlr-foreign-toplevel do labwc).
"""
import configparser
import fcntl
import os
import signal
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

PASTA_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos"
ARQUIVO_CONFIG = PASTA_CONFIG / "ilha-de-aplicativos.conf"
FIXADOS_PADRAO = ["duiaos-configuracoes.desktop", "firefox-esr.desktop", "foot.desktop"]
WISE_DESKTOP = "duiaos-wise.desktop"
EXPLORADOR_DESKTOP = "duiaos-explorador-de-arquivos.desktop"
VERSAO_CONFIG = "2"
DEMONSTRACAO = "--demonstracao" in sys.argv

if not DEMONSTRACAO:
    # Uma instância só
    _trava = open(os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "duiaos-ilha-de-aplicativos.lock"), "w")
    try:
        fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("A Ilha de Aplicativos já está aberta. Para reiniciar: reiniciar.sh")
        sys.exit(0)

    # Número do processo, usado pelo atalho Super+Espaço (alternar-central.sh)
    ARQUIVO_PID = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-ilha-de-aplicativos.pid"
    ARQUIVO_PID.write_text(str(os.getpid()))

    # A Ilha e a Central são "camadas" do Wayland (layer-shell).
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import interface  # noqa: E402
import pastas  # noqa: E402
import sistema as comum  # noqa: E402
import tipos  # noqa: E402
from aplicativos import comando_de_exec, iniciar, ler_desktop, listar_aplicativos, normalizar  # noqa: E402,F401


# ---------------------------------------------------------------- configuração

def ler_fixados():
    """Fixados da Ilha. Configuração da versão 1 (antes das Configurações): ganha as Configurações uma vez."""
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    texto = config.get("ilha", "fixados", fallback=";".join(FIXADOS_PADRAO))
    fixados = [item.strip() for item in texto.split(";") if item.strip()]
    if ARQUIVO_CONFIG.exists() and config.get("ilha", "versao", fallback="1") != VERSAO_CONFIG:
        if "duiaos-configuracoes.desktop" not in fixados:
            fixados.insert(0, "duiaos-configuracoes.desktop")
        gravar_fixados(fixados)
    return fixados


def gravar_fixados(fixados):
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Ilha de Aplicativos.\n")
        arquivo.write("# fixados: arquivos .desktop separados por ponto e vírgula (;)\n")
        arquivo.write(f"[ilha]\nversao = {VERSAO_CONFIG}\nfixados = " + ";".join(fixados) + "\n")


def janelas_abertas():
    """Lista os app_id das janelas abertas (ex.: 'foot')."""
    try:
        saida = subprocess.run(["wlrctl", "toplevel", "list"], capture_output=True,
                               text=True, timeout=2, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    abertos = []
    for linha in saida.splitlines():
        app_id = linha.split(":", 1)[0].strip()
        if app_id and app_id not in abertos:
            abertos.append(app_id)
    return abertos


def registrar_uso(evento, **dados):
    """Uso agregado de "Ajude a melhorar o DuiaOS" (relatorios/uso.py, evento uso.aplicativo_aberto e
    uso.central_de_aplicativos): só sai do computador somado e no nível "erros e uso"."""
    interface.registrar_uso(evento, **dados)


def downloads_recentes(pasta=None, limite=12):
    """Os arquivos mais novos da pasta Downloads, para a pilha da Ilha."""
    pasta = Path(pasta) if pasta else pastas.pasta("DOWNLOAD")
    itens = []
    try:
        with os.scandir(pasta) as entradas:
            for entrada in entradas:
                if entrada.name.startswith(".") or entrada.name.endswith((".part", ".crdownload")):
                    continue
                try:
                    momento = entrada.stat().st_mtime
                except OSError:
                    continue
                itens.append((momento, entrada))
    except OSError:
        return []
    itens.sort(key=lambda par: par[0], reverse=True)
    lista = []
    for _, entrada in itens[:limite]:
        eh_pasta = entrada.is_dir()
        icone, descricao, miniatura = tipos.tipo(entrada.path, eh_pasta)
        lista.append({"nome": entrada.name, "caminho": entrada.path, "icone": icone,
                      "miniatura": Path(entrada.path).as_uri() if miniatura else "", "descricao": descricao})
    return lista


def lixeira_vazia(lixeira=None):
    pasta = Path(lixeira or pastas.LIXEIRA) / "files"
    try:
        return not any(os.scandir(pasta))
    except OSError:
        return True


# ------------------------------------------------------- estado para o QML

# Aplicativos do próprio DuiaOS: ícone desenhado (shell/comum/icones.py) e comando de reserva,
# para funcionarem também direto do repositório.
SISTEMA = {
    EXPLORADOR_DESKTOP: {"nome": "Explorador de Arquivos", "iconeDuia": "pasta", "app": "explorador-de-arquivos"},
    "duiaos-configuracoes.desktop": {"nome": "Configurações", "iconeDuia": "engrenagem", "app": "configuracoes"},
}


def entrada_de(id_desktop):
    """.desktop do aplicativo; os do DuiaOS ganham o ícone próprio (e existem mesmo sem o .desktop)."""
    app = ler_desktop(id_desktop)
    extra = SISTEMA.get(id_desktop)
    if not extra:
        return app
    base = app or {"id": id_desktop, "descricao": "", "icone": "", "exec": "", "terminal": False,
                   "classe": "", "tipos": [], "categorias": [], "busca": normalizar(extra["nome"])}
    return {**base, "nome": extra["nome"], "iconeDuia": extra["iconeDuia"],
            "exec": base["exec"] or " ".join(comum.comando_app_duiaos(extra["app"])),
            "classe": base["classe"] or "duiaos-" + extra["app"]}


class Ilha(QObject):
    mudou = Signal()
    centralMudou = Signal()
    downloadsMudou = Signal()

    def __init__(self):
        super().__init__()
        self._downloads, self._downloads_visivel, self._ancora_downloads = [], False, 0.0
        self._lixeira_cheia = False
        if DEMONSTRACAO:
            self._preparar_demonstracao()
            return
        if not ARQUIVO_CONFIG.exists():
            gravar_fixados(FIXADOS_PADRAO)
        self._ids_fixados = []
        self._fixados = []
        self._abertos = []
        self._itens = []
        self._todos = []
        self._resultados = []
        self._consulta = ""
        self._central_visivel = False
        self._pedido_alternar = False

        self._vigia = QFileSystemWatcher([str(PASTA_CONFIG), str(ARQUIVO_CONFIG)], self)
        self._vigia.directoryChanged.connect(self.recarregar_fixados)
        self._vigia.fileChanged.connect(self.recarregar_fixados)
        self.recarregar_fixados()

        self._timer = QTimer(self, interval=1500, timeout=self.atualizar_abertos)
        self._timer.start()
        self.atualizar_abertos()

        # Atalho Super+Espaço: o labwc envia SIGUSR1; o timer deixa o Python tratá-lo.
        signal.signal(signal.SIGUSR1, self._sinal_alternar)
        self._timer_sinal = QTimer(self, interval=150, timeout=self._verificar_sinal)
        self._timer_sinal.start()

        # Lixeira cheia ou vazia (ícone da Ilha)
        self._timer_lixeira = QTimer(self, interval=4000, timeout=self.atualizar_lixeira)
        self._timer_lixeira.start()
        self.atualizar_lixeira()

    def _preparar_demonstracao(self):
        exemplos = [
            ("duiaos-wise.desktop", "Wise", ""), (EXPLORADOR_DESKTOP, "", ""),
            ("duiaos-configuracoes.desktop", "", ""), ("firefox-esr.desktop", "Firefox", ""),
            ("foot.desktop", "Terminal", ""), ("libreoffice-writer.desktop", "LibreOffice Writer", ""),
        ]
        self._itens = []
        for id_desktop, nome, icone in exemplos:
            app = entrada_de(id_desktop) or {"id": id_desktop, "nome": nome, "icone": icone, "exec": "", "classe": "",
                                              "terminal": False, "descricao": "", "busca": normalizar(nome)}
            self._itens.append({**app, "fixado": True, "aberto": id_desktop in (EXPLORADOR_DESKTOP, "firefox-esr.desktop"),
                                "appId": ""})
        self._todos = [dict(i) for i in self._itens] + [
            {"id": f"exemplo{n}.desktop", "nome": nome, "icone": "", "exec": "", "classe": "", "terminal": False,
             "descricao": "", "busca": normalizar(nome)}
            for n, nome in enumerate(["Calculadora", "Calendário", "Câmera", "Central de IA", "Editor de Texto",
                                      "Fotos", "GIMP", "Inkscape", "LibreOffice Calc", "LibreOffice Impress",
                                      "Mapas", "Música", "Relógio", "Thunderbird", "VLC", "Visualizador de PDF",
                                      "Ajude a melhorar o DuiaOS", "Gravador de Som"])]
        self._todos.sort(key=lambda a: normalizar(a["nome"]))
        self._ids_fixados = [i["id"] for i in self._itens]
        self._resultados = [{**a, "fixado": a["id"] in self._ids_fixados} for a in self._todos]
        self._consulta, self._central_visivel, self._abertos = "", "--central" in sys.argv, []
        self._lixeira_cheia = True
        self._downloads = [
            {"nome": n, "caminho": "", "icone": tipos.tipo(n)[0], "miniatura": "", "descricao": tipos.tipo(n)[1]}
            for n in ["Contrato de aluguel.pdf", "Fotos da viagem.zip", "Planilha de gastos.xlsx", "Apresentação.pptx",
                      "papel-de-parede.png", "Música nova.mp3", "Relatório final.docx", "instalador.deb"]]
        self._downloads_visivel = "--downloads" in sys.argv
        self._ancora_downloads = 760.0

    def atualizar_lixeira(self):
        cheia = not lixeira_vazia()
        if cheia != self._lixeira_cheia:
            self._lixeira_cheia = cheia
            self.downloadsMudou.emit()

    # ----- pastas à direita da Ilha
    @Slot(str)
    def abrirPasta(self, nome):
        """Abre a pasta Aplicativos, Downloads ou a Lixeira no Explorador de Arquivos."""
        self.fecharDownloads()
        if DEMONSTRACAO:
            return
        destino = {"aplicativos": "aplicativos:", "lixeira": "lixeira:",
                   "downloads": str(pastas.pasta("DOWNLOAD"))}.get(nome, nome)
        comum.abrir_app_duiaos("explorador-de-arquivos", destino)

    @Slot(float)
    def alternarDownloads(self, ancora):
        if self._downloads_visivel:
            self.fecharDownloads()
            return
        if not DEMONSTRACAO:
            self._downloads = downloads_recentes()
        self._downloads_visivel, self._ancora_downloads = True, ancora
        self.downloadsMudou.emit()

    @Slot()
    def fecharDownloads(self):
        if self._downloads_visivel:
            self._downloads_visivel = False
            self.downloadsMudou.emit()

    @Slot(str)
    def abrirArquivo(self, caminho):
        self.fecharDownloads()
        if caminho and not DEMONSTRACAO:
            iniciar(["xdg-open", caminho])

    # ----- Ilha
    def recarregar_fixados(self, _caminho=None):
        # Editores recriam o arquivo: volta a vigiá-lo
        if ARQUIVO_CONFIG.exists() and str(ARQUIVO_CONFIG) not in self._vigia.files():
            self._vigia.addPath(str(ARQUIVO_CONFIG))
        ids = [i for i in ler_fixados() if i not in (WISE_DESKTOP, EXPLORADOR_DESKTOP)]
        ids.insert(0, EXPLORADOR_DESKTOP)  # o Explorador de Arquivos fica sempre na Ilha
        if ler_desktop(WISE_DESKTOP):
            ids.insert(0, WISE_DESKTOP)   # o Wise vem sempre primeiro
        self._ids_fixados = ids
        self._fixados = [d for d in (entrada_de(i) for i in self._ids_fixados) if d]
        self.montar()
        self.buscar(self._consulta)

    def atualizar_abertos(self):
        abertos = janelas_abertas()
        if abertos != self._abertos:
            self._abertos = abertos
            self.montar()

    @staticmethod
    def corresponde(app, app_id):
        app_id = app_id.lower()
        base = app["id"].removesuffix(".desktop").lower()
        return app_id in (base, app["classe"]) or base.endswith("." + app_id)

    def montar(self):
        itens, usados = [], set()
        for app in self._fixados:
            aberto = next((a for a in self._abertos if self.corresponde(app, a)), "")
            if aberto:
                usados.add(aberto)
            itens.append({**app, "fixado": True, "aberto": bool(aberto), "appId": aberto})
        # Abertos que não estão fixados aparecem depois dos fixados
        for app_id in self._abertos:
            if app_id in usados:
                continue
            app = ler_desktop(app_id + ".desktop") or {
                "id": "", "nome": app_id, "icone": app_id, "exec": "", "classe": "",
                "terminal": False, "descricao": "", "busca": ""}
            itens.append({**app, "fixado": False, "aberto": True, "appId": app_id})
        self._itens = itens
        self.mudou.emit()

    @Slot(int)
    def ativar(self, indice):
        if not 0 <= indice < len(self._itens):
            return
        item = self._itens[indice]
        if item["aberto"] and item["appId"]:
            iniciar(["wlrctl", "toplevel", "focus", "app_id:" + item["appId"]])
        else:
            iniciar(comando_de_exec(item))
            if item.get("id"):
                registrar_uso("uso.aplicativo_aberto", aplicativo=item["id"], por="ilha")

    # ----- Central de Aplicativos
    def _sinal_alternar(self, _numero, _quadro):
        self._pedido_alternar = True

    def _verificar_sinal(self):
        if self._pedido_alternar:
            self._pedido_alternar = False
            self._por_atalho = True
            self.alternarCentral()

    @Slot()
    def alternarCentral(self):
        if self._central_visivel:
            self.fecharCentral()
        else:
            if not DEMONSTRACAO:
                self._todos = listar_aplicativos()   # inclui aplicativos instalados agora
            self.buscar("")
            self._central_visivel = True
            self.centralMudou.emit()
            registrar_uso("uso.central_de_aplicativos",
                          por="atalho" if getattr(self, "_por_atalho", False) else "botao")
        self._por_atalho = False

    @Slot()
    def fecharCentral(self):
        if self._central_visivel:
            self._central_visivel = False
            self.centralMudou.emit()

    @Slot(str)
    def buscar(self, texto):
        self._consulta = texto
        palavras = normalizar(texto).split()
        resultados = [a for a in self._todos if all(p in a["busca"] for p in palavras)]
        self._resultados = [{**a, "fixado": a["id"] in self._ids_fixados} for a in resultados]
        self.mudou.emit()

    @Slot(str)
    def abrirAplicativo(self, id_desktop):
        app = next((a for a in self._todos if a["id"] == id_desktop), None)
        if app:
            iniciar(comando_de_exec(app))
            registrar_uso("uso.aplicativo_aberto", aplicativo=id_desktop, por="central")
        self.fecharCentral()

    @Slot(str)
    def alternarFixado(self, id_desktop):
        if id_desktop in (WISE_DESKTOP, EXPLORADOR_DESKTOP):
            return   # o Wise e o Explorador de Arquivos ficam sempre na Ilha
        fixados = [i for i in self._ids_fixados if i not in (WISE_DESKTOP, EXPLORADOR_DESKTOP)]
        if id_desktop in fixados:
            fixados.remove(id_desktop)
        else:
            fixados.append(id_desktop)
        gravar_fixados(fixados)
        self.recarregar_fixados()

    itens = Property("QVariantList", lambda self: self._itens, notify=mudou)
    downloads = Property("QVariantList", lambda self: self._downloads, notify=downloadsMudou)
    downloadsVisivel = Property(bool, lambda self: self._downloads_visivel, notify=downloadsMudou)
    ancoraDownloads = Property(float, lambda self: self._ancora_downloads, notify=downloadsMudou)
    lixeiraCheia = Property(bool, lambda self: self._lixeira_cheia, notify=downloadsMudou)
    resultados = Property("QVariantList", lambda self: self._resultados, notify=mudou)
    centralVisivel = Property(bool, lambda self: self._central_visivel, notify=centralMudou)


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    if DEMONSTRACAO and "--captura" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    # Registros e falhas no journal do sistema (duiaos_registro, ADR 040)
    interface.ligar_registro("duiaos-ilha-de-aplicativos")
    # A integração layer-shell vale só para este painel: sem isto, os programas
    # abertos daqui (Wise, aplicativos Qt) herdariam a variável e virariam
    # "painéis" sem barra de título, sem botões e sem redimensionar.
    os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)
    app.setApplicationName("duiaos-ilha-de-aplicativos")

    ilha = Ilha()
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    engine.rootContext().setContextProperty("ilha", ilha)
    engine.rootContext().setContextProperty("papelDeParede", comum.papel_de_parede())
    engine.rootContext().setContextProperty("capturaArquivo", argumento("--captura"))
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "IlhaDeAplicativos.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
