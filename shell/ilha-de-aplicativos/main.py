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

Opções (tamanho, ampliação, posição, ocultar, efeito ao minimizar…): efeitos.py,
gravadas em preferencias.conf [ilha] pelas Configurações e pelo botão direito no
fundo da Ilha; valem na hora. Minimizar com efeito (gênio ou escala): botão
amarelo da janela, Super+M ou o clique no aplicativo da frente; o labwc avisa a
Ilha pelo sinal SIGUSR2 (minimizar.sh).

Uso:
  main.py                                inicia a Ilha
  main.py --demonstracao [--central|--downloads|--menu|--menu-ilha|--genio|--ampliada]
                         [--posicao base|esquerda|direita] [--captura ARQUIVO]
                                         janela comum com dados de exemplo
Janelas abertas: comando wlrctl (protocolo wlr-foreign-toplevel do labwc).
"""
import configparser
import fcntl
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

PASTA_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos"
ARQUIVO_CONFIG = PASTA_CONFIG / "ilha-de-aplicativos.conf"
FIXADOS_PADRAO = ["duiaos-configuracoes.desktop", "duiaos-loja.desktop", "firefox-esr.desktop", "foot.desktop"]
WISE_DESKTOP = "duiaos-wise.desktop"
EXPLORADOR_DESKTOP = "duiaos-explorador-de-arquivos.desktop"
VERSAO_CONFIG = "3"
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

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QRect, QTimer, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QRegion, QWindow  # noqa: E402
import PySide6.QtQuick  # noqa: E402,F401  (as janelas do QML chegam ao Python como QQuickWindow)
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import efeitos  # noqa: E402
import interface  # noqa: E402
import pastas  # noqa: E402
import sistema as comum  # noqa: E402
import tipos  # noqa: E402
from aplicativos import comando_de_exec, iniciar, ler_desktop, listar_aplicativos, normalizar  # noqa: E402,F401


# ---------------------------------------------------------------- configuração

def ler_fixados():
    """Fixados da Ilha. Configuração antiga ganha, uma vez, o que chegou depois: as Configurações
    (versão 1) e a Duia App Store (versão 2)."""
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    texto = config.get("ilha", "fixados", fallback=";".join(FIXADOS_PADRAO))
    fixados = [item.strip() for item in texto.split(";") if item.strip()]
    versao = config.get("ilha", "versao", fallback="1")
    if ARQUIVO_CONFIG.exists() and versao != VERSAO_CONFIG:
        if versao == "1" and "duiaos-configuracoes.desktop" not in fixados:
            fixados.insert(0, "duiaos-configuracoes.desktop")
        if "duiaos-loja.desktop" not in fixados:          # versão 3: chegou a Duia App Store
            posicao = fixados.index("duiaos-configuracoes.desktop") + 1 if "duiaos-configuracoes.desktop" in fixados else 0
            fixados.insert(posicao, "duiaos-loja.desktop")
        gravar_fixados(fixados)
    return fixados


def ler_recentes():
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    return [i for i in config.get("ilha", "recentes", fallback="").split(";") if i.strip()][:3]


def gravar_recentes(recentes):
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    if not config.has_section("ilha"):
        config.add_section("ilha")
    config.set("ilha", "recentes", ";".join(recentes[:3]))
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Ilha de Aplicativos.\n")
        arquivo.write("# fixados: arquivos .desktop separados por ponto e vírgula (;)\n")
        config.write(arquivo)


def ler_opcoes():
    config = configparser.ConfigParser()
    config.read(pastas.PREFERENCIAS, encoding="utf-8")
    return efeitos.ler_opcoes(dict(config.items("ilha")) if config.has_section("ilha") else {})


def janela_ativa():
    """app_id da janela que está na frente (ou "")."""
    try:
        saida = subprocess.run(["wlrctl", "toplevel", "list", "state:active"], capture_output=True,
                               text=True, timeout=2, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return saida.splitlines()[0].split(":", 1)[0].strip() if saida.strip() else ""


def tem_janela(*filtros):
    try:
        return subprocess.run(["wlrctl", "toplevel", "find", *filtros], capture_output=True, timeout=2,
                              check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def gravar_fixados(fixados):
    recentes = ler_recentes() if ARQUIVO_CONFIG.exists() else []
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Ilha de Aplicativos.\n")
        arquivo.write("# fixados: arquivos .desktop separados por ponto e vírgula (;)\n")
        arquivo.write(f"[ilha]\nversao = {VERSAO_CONFIG}\nfixados = " + ";".join(fixados) + "\n")
        if recentes:
            arquivo.write("recentes = " + ";".join(recentes) + "\n")


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


def esvaziar_lixeira():
    """Apaga de vez o que está na Lixeira (mesma Lixeira do Explorador de Arquivos)."""
    for pasta in (Path("/usr/share/duiaos/explorador-de-arquivos"), PASTA.parents[1] / "apps" / "explorador-de-arquivos"):
        if (pasta / "operacoes.py").is_file():
            sys.path.insert(0, str(pasta))
            break
    try:
        import operacoes
        operacoes.esvaziar_lixeira()
    except Exception:          # noqa: BLE001 — falha ao apagar não pode derrubar a Ilha
        pass


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
    "duiaos-loja.desktop": {"nome": "Duia App Store", "iconeDuia": "sacola", "app": "loja"},
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
    opcoesMudou = Signal()
    efeito = Signal("QVariantMap")          # minimizar/restaurar: a Ilha desenha o efeito (EfeitoDeJanela.qml)
    pulando = Signal(str)                   # o aplicativo está abrindo: o ícone pula
    _efeito_pronto = Signal("QVariantMap")

    def __init__(self):
        super().__init__()
        self._downloads, self._downloads_visivel, self._ancora_downloads = [], False, 0.0
        self._lixeira_cheia = False
        self._opcoes = ler_opcoes() if not DEMONSTRACAO else efeitos.ler_opcoes({})
        self._capturas = {}                 # app_id → imagem e lugar da janela quando foi minimizada
        self._minimizando = False
        self._numero_efeito = 0
        self._efeito_pronto.connect(self.efeito)
        self._recentes = []
        if DEMONSTRACAO:
            self._preparar_demonstracao()
            return
        self._recentes = ler_recentes()
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

        PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
        self._vigia = QFileSystemWatcher([str(PASTA_CONFIG), str(ARQUIVO_CONFIG)], self)
        self._vigia.directoryChanged.connect(self._mudou_pasta_config)
        self._vigia.fileChanged.connect(self._mudou_pasta_config)
        self.recarregar_fixados()

        self._timer = QTimer(self, interval=1500, timeout=self.atualizar_abertos)
        self._timer.start()
        self.atualizar_abertos()

        # Atalho Super+Espaço: o labwc envia SIGUSR1; o timer deixa o Python tratá-lo.
        # Minimizar (botão amarelo, Super+M): SIGUSR2.
        signal.signal(signal.SIGUSR1, self._sinal_alternar)
        self._pedido_minimizar = False
        signal.signal(signal.SIGUSR2, self._sinal_minimizar)
        self._timer_sinal = QTimer(self, interval=150, timeout=self._verificar_sinal)
        self._timer_sinal.start()

        # Lixeira cheia ou vazia (ícone da Ilha)
        self._timer_lixeira = QTimer(self, interval=4000, timeout=self.atualizar_lixeira)
        self._timer_lixeira.start()
        self.atualizar_lixeira()

    def _preparar_demonstracao(self):
        exemplos = [
            ("duiaos-wise.desktop", "Wise", ""), (EXPLORADOR_DESKTOP, "", ""),
            ("duiaos-configuracoes.desktop", "", ""), ("duiaos-loja.desktop", "", ""), ("firefox-esr.desktop", "Firefox", ""),
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
        self._recentes = ["exemplo-gimp.desktop"]
        self._opcoes = efeitos.ler_opcoes({"posicao": argumento("--posicao", "base"),
                                           "recentes": "sim" if "--recentes" in sys.argv else "nao"})
        if self._opcoes["recentes"]:
            self._itens.append({"id": "exemplo-gimp.desktop", "nome": "GIMP", "icone": "", "exec": "", "classe": "",
                                "terminal": False, "descricao": "", "busca": "gimp", "fixado": False, "aberto": False,
                                "appId": "", "recente": True})
        if "--menu" in sys.argv:
            self.abrirMenu("app", 3, -120.0)
        if "--menu-ilha" in sys.argv:
            self.abrirMenu("ilha", -1, 200.0)

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

    # ----- menu do botão direito
    @Slot(str, int, float)
    def abrirMenu(self, tipo, indice, ancora):
        """tipo: app (indice em itens), central, aplicativos, downloads, lixeira ou ilha (o fundo).
        ancora: distância do centro da Ilha até o ícone, ao longo da Ilha."""
        self._downloads_visivel = False
        item = self._itens[indice] if tipo == "app" and 0 <= indice < len(self._itens) else {}
        fixo = item.get("id") in (WISE_DESKTOP, EXPLORADOR_DESKTOP)
        self._menu = {"tipo": tipo, "indice": indice, "nome": item.get("nome", ""), "aberto": bool(item.get("aberto")),
                      "fixado": bool(item.get("fixado")), "fixo": fixo, "podeFixar": bool(item.get("id")) and not fixo,
                      "lixeiraCheia": self._lixeira_cheia, "recente": bool(item.get("recente")),
                      "janelas": item.get("janelas", 0)}
        self._ancora_downloads = ancora
        self.downloadsMudou.emit()

    @Slot()
    def fecharMenu(self):
        if getattr(self, "_menu", None):
            self._menu = {}
            self.downloadsMudou.emit()

    @Slot(str)
    def acaoMenu(self, acao):
        menu = getattr(self, "_menu", {}) or {}
        self.fecharMenu()
        tipo, indice = menu.get("tipo"), menu.get("indice", -1)
        if tipo == "app" and 0 <= indice < len(self._itens):
            item = self._itens[indice]
            if acao == "abrir":
                self.ativar(indice)
            elif acao == "nova-janela" and not DEMONSTRACAO:
                iniciar(comando_de_exec(item))
            elif acao == "fixar" and item.get("id"):
                self.alternarFixado(item["id"])
            elif acao == "fechar" and item.get("appId") and not DEMONSTRACAO:
                iniciar(["wlrctl", "toplevel", "close", "app_id:" + item["appId"]])
            elif acao == "minimizar" and item.get("appId"):
                if not DEMONSTRACAO and tem_janela("app_id:" + item["appId"], "state:active"):
                    self.minimizar(item["appId"])
                elif not DEMONSTRACAO:
                    iniciar(["wlrctl", "toplevel", "minimize", "app_id:" + item["appId"]])
            elif acao == "mostrar-no-explorador":
                comum.abrir_app_duiaos("explorador-de-arquivos", "aplicativos:") if not DEMONSTRACAO else None
            elif acao == "esquecer" and item.get("recente"):
                self._recentes = [r for r in self._recentes if r != item.get("id")]
                if not DEMONSTRACAO:
                    gravar_recentes(self._recentes)
                self.montar()
        elif tipo == "central" and acao == "abrir":
            self.alternarCentral()
        elif tipo in ("aplicativos", "downloads", "lixeira") and acao == "abrir":
            self.abrirPasta(tipo)
        elif tipo == "lixeira" and acao == "esvaziar" and not DEMONSTRACAO:
            esvaziar_lixeira()
            self.atualizar_lixeira()
        elif acao.startswith("opcao:"):
            # opcao:CHAVE=VALOR, do menu do fundo da Ilha
            chave, _, valor = acao[6:].partition("=")
            self.definirOpcao(chave, valor)
        elif acao == "configuracoes" and not DEMONSTRACAO:
            comum.abrir_app_duiaos("configuracoes", "--secao", "barra")

    menu = Property("QVariantMap", lambda self: getattr(self, "_menu", {}) or {}, notify=downloadsMudou)

    @Slot(str)
    def abrirArquivo(self, caminho):
        self.fecharDownloads()
        if caminho and not DEMONSTRACAO:
            iniciar(["xdg-open", caminho])

    # ----- Ilha
    def _mudou_pasta_config(self, _caminho=None):
        """Mudou algo em ~/.config/duiaos: fixados (Ilha) ou preferências (opções)."""
        for arquivo in (ARQUIVO_CONFIG, pastas.PREFERENCIAS):
            if arquivo.exists() and str(arquivo) not in self._vigia.files():
                self._vigia.addPath(str(arquivo))   # editores recriam o arquivo: volta a vigiá-lo
        opcoes = ler_opcoes()
        if opcoes != self._opcoes:
            self._opcoes = opcoes
            self.opcoesMudou.emit()
            self.montar()
        self.recarregar_fixados()

    def recarregar_fixados(self, _caminho=None):
        if ARQUIVO_CONFIG.exists() and str(ARQUIVO_CONFIG) not in self._vigia.files():
            self._vigia.addPath(str(ARQUIVO_CONFIG))
        if pastas.PREFERENCIAS.exists() and str(pastas.PREFERENCIAS) not in self._vigia.files():
            self._vigia.addPath(str(pastas.PREFERENCIAS))
        ids = [i for i in ler_fixados() if i not in (WISE_DESKTOP, EXPLORADOR_DESKTOP)]
        ids.insert(0, EXPLORADOR_DESKTOP)  # o Explorador de Arquivos fica sempre na Ilha
        if ler_desktop(WISE_DESKTOP):
            ids.insert(0, WISE_DESKTOP)   # o Wise vem sempre primeiro
        self._ids_fixados = ids
        self._fixados = [d for d in (entrada_de(i) for i in self._ids_fixados) if d]
        self._recentes = ler_recentes()
        self.montar()
        self.buscar(self._consulta)

    def atualizar_abertos(self):
        abertos = janelas_abertas()
        if abertos != self._abertos:
            # Aplicativo não fixado que fechou vira "recente" (até 3)
            fechados = [a for a in self._abertos if a not in abertos]
            for app_id in fechados:
                self._capturas.pop(app_id, None)
                id_desktop = next((i["id"] for i in self._itens if i.get("appId") == app_id and i.get("id")), "")
                if id_desktop and id_desktop not in self._ids_fixados:
                    self._recentes = [id_desktop] + [r for r in self._recentes if r != id_desktop]
                    self._recentes = self._recentes[:3]
                    gravar_recentes(self._recentes)
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
        # Recentes (opção): usados há pouco, nem fixados nem abertos
        if self._opcoes.get("recentes"):
            presentes = {i.get("id") for i in itens}
            for id_desktop in self._recentes:
                app = entrada_de(id_desktop) if not DEMONSTRACAO else {
                    "id": id_desktop, "nome": "GIMP", "icone": "", "exec": "", "classe": "", "terminal": False,
                    "descricao": "", "busca": "gimp"}
                if app and id_desktop not in presentes:
                    itens.append({**app, "fixado": False, "aberto": False, "appId": "", "recente": True})
        self._itens = itens
        self.mudou.emit()

    @Slot(int)
    def ativar(self, indice):
        """Clique no ícone: abre; se já estiver aberto, traz para a frente (restaurando com o efeito
        se estava minimizado) ou, com "clique_minimiza", minimiza o que já está na frente."""
        if not 0 <= indice < len(self._itens):
            return
        item = self._itens[indice]
        if item["aberto"] and item["appId"]:
            app_id = item["appId"]
            if DEMONSTRACAO:
                return
            if self._opcoes["clique_minimiza"] and tem_janela("app_id:" + app_id, "state:active", "state:unminimized"):
                self.minimizar(app_id)
            elif app_id in self._capturas and tem_janela("app_id:" + app_id, "state:minimized"):
                self.restaurar(app_id)
            else:
                iniciar(["wlrctl", "toplevel", "focus", "app_id:" + app_id])
        else:
            if self._opcoes["animar_abrir"] and item.get("id"):
                self.pulando.emit(item["id"])
            if not DEMONSTRACAO:
                iniciar(comando_de_exec(item))
            if item.get("id"):
                registrar_uso("uso.aplicativo_aberto", aplicativo=item["id"], por="ilha")

    @Slot(str, int)
    def moverFixado(self, id_desktop, destino):
        """Arrastar na Ilha: muda a ordem dos fixados (destino = posição entre os itens da Ilha)."""
        fixos = [i for i in (WISE_DESKTOP, EXPLORADOR_DESKTOP) if i in self._ids_fixados]
        fixados = [i for i in self._ids_fixados if i not in fixos]
        if id_desktop not in fixados:
            return
        fixados.remove(id_desktop)
        posicao = max(0, min(len(fixados), destino - len(fixos)))
        fixados.insert(posicao, id_desktop)
        if DEMONSTRACAO:
            return
        gravar_fixados(fixados)
        self.recarregar_fixados()

    # ----- opções
    @Slot(str, str)
    def definirOpcao(self, chave, valor):
        texto = efeitos.texto_da_opcao(chave, valor)
        if texto is None:
            return
        if DEMONSTRACAO:
            self._opcoes = efeitos.ler_opcoes({**{k: str(v) for k, v in self._opcoes.items()}, chave: texto})
            self.opcoesMudou.emit()
            return
        pastas.gravar_preferencia("ilha", chave, texto)
        self._mudou_pasta_config()

    @Slot(QObject, int, int, int, int)
    def definirMascara(self, janela, x, y, largura, altura):
        """Onde a Ilha recebe cliques: só na faixa visível; o resto da janela (espaço para a
        ampliação ou a borda da Ilha escondida) deixa o clique passar para as janelas de baixo."""
        if isinstance(janela, QWindow):
            janela.setMask(QRegion(QRect(x, y, max(1, largura), max(1, altura))))

    # ----- minimizar e restaurar com efeito
    def _sinal_minimizar(self, _numero, _quadro):
        self._pedido_minimizar = True

    def minimizar(self, app_id=""):
        """Minimiza a janela da frente com o efeito escolhido."""
        if self._minimizando:
            return
        if self._opcoes["minimizar"] == "nenhum" or not shutil.which("grim") or not getattr(self, "_tela", ""):
            iniciar(["wlrctl", "toplevel", "minimize", "state:active"])
            return
        self._minimizando = True
        threading.Thread(target=self._minimizar_com_efeito, args=(app_id,), daemon=True).start()

    def _minimizar_com_efeito(self, app_id):
        inicio = time.monotonic()
        try:
            app_id = app_id or janela_ativa()
            pasta = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
            grande = subprocess.Popen(["grim", "-o", self._tela, "-t", "ppm", "-"], stdout=subprocess.PIPE)
            antes = subprocess.run(["grim", "-o", self._tela, "-s", "0.25", "-t", "ppm", "-"],
                                   capture_output=True, timeout=3, check=False).stdout
            imagem = grande.communicate(timeout=3)[0]
            subprocess.run(["wlrctl", "toplevel", "minimize", "state:active"], timeout=2, check=False)
            time.sleep(0.035)                     # o compositor desenha a tela sem a janela
            depois = subprocess.run(["grim", "-o", self._tela, "-s", "0.25", "-t", "ppm", "-"],
                                    capture_output=True, timeout=3, check=False).stdout
            a, b = efeitos.ler_ppm(antes), efeitos.ler_ppm(depois)
            if not a or not b or a[:2] != b[:2]:
                return
            regiao = efeitos.regiao_alterada(a[2], b[2], a[0], a[1], a[0] * 3, 3)
            if not regiao:
                return
            # Pequena (0,25 da tela lógica) → lógica; grande → pixels reais da tela
            x, y, w, h = (v * 4 for v in regiao)
            figura = QImage.fromData(imagem)
            escala = figura.width() / max(1, a[0] * 4)
            recorte = figura.copy(QRect(round(x * escala), round(y * escala), round(w * escala), round(h * escala)))
            self._numero_efeito += 1
            arquivo = pasta / f"duiaos-janela-{self._numero_efeito % 8}.ppm"
            recorte.save(str(arquivo), "PPM")
            dados = {"direcao": "minimizar", "efeito": self._opcoes["minimizar"], "appId": app_id,
                     "imagem": QUrl.fromLocalFile(str(arquivo)).toString() + f"?{self._numero_efeito}",
                     "x": x, "y": y, "w": w, "h": h}
            if app_id:
                self._capturas[app_id] = dados
            self._efeito_pronto.emit(dados)
        except (OSError, subprocess.SubprocessError, ValueError) as erro:
            print("Ilha: minimizar sem efeito:", erro, file=sys.stderr)
        finally:
            self._minimizando = False
            if time.monotonic() - inicio > 1.5:
                print("Ilha: o efeito de minimizar demorou", round(time.monotonic() - inicio, 2), "s", file=sys.stderr)

    def restaurar(self, app_id):
        """Traz de volta uma janela minimizada pela Ilha, com o efeito ao contrário."""
        dados = self._capturas.get(app_id)
        if not dados or self._opcoes["minimizar"] == "nenhum":
            iniciar(["wlrctl", "toplevel", "focus", "app_id:" + app_id])
            return
        self.efeito.emit({**dados, "direcao": "restaurar", "efeito": self._opcoes["minimizar"]})

    @Slot(str, str)
    def efeitoTerminou(self, app_id, direcao):
        """Fim do efeito de restaurar: agora a janela volta de verdade."""
        if direcao == "restaurar" and app_id and not DEMONSTRACAO:
            self._capturas.pop(app_id, None)
            iniciar(["wlrctl", "toplevel", "focus", "app_id:" + app_id])

    @Slot(str)
    def definirTela(self, nome):
        """Nome da saída (ex.: eDP-1) onde a Ilha está, para capturar a tela certa."""
        self._tela = nome

    # ----- Central de Aplicativos
    def _sinal_alternar(self, _numero, _quadro):
        self._pedido_alternar = True

    def _verificar_sinal(self):
        if self._pedido_alternar:
            self._pedido_alternar = False
            self._por_atalho = True
            self.alternarCentral()
        if getattr(self, "_pedido_minimizar", False):
            self._pedido_minimizar = False
            self.minimizar()

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
    opcoes = Property("QVariantMap", lambda self: self._opcoes, notify=opcoesMudou)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)


def janela_de_exemplo():
    """Imagem de uma janela de mentira (demonstração do efeito de minimizar)."""
    from PySide6.QtGui import QColor, QPainter
    import tempfile
    imagem = QImage(640, 420, QImage.Format_RGB32)
    imagem.fill(QColor("#FFFFFF"))
    pintor = QPainter(imagem)
    pintor.fillRect(0, 0, 640, 34, QColor("#EEF2F7"))
    for i, cor in enumerate(("#8DB8FF", "#3D7BF2", "#2447A8")):       # expandir, minimizar, fechar (à direita)
        pintor.setBrush(QColor(cor))
        pintor.setPen(QColor(cor))
        pintor.drawEllipse(640 - 66 + i * 20, 11, 12, 12)
    pintor.fillRect(0, 34, 160, 386, QColor("#F1F4F8"))
    for linha in range(8):
        pintor.fillRect(190, 70 + linha * 40, 400 - (linha % 3) * 60, 14, QColor("#C9D2DE"))
    pintor.fillRect(190, 400 - 60, 180, 40, QColor("#2E6BE6"))
    pintor.end()
    arquivo = Path(tempfile.gettempdir()) / "duiaos-janela-exemplo.png"
    imagem.save(str(arquivo))
    return QUrl.fromLocalFile(str(arquivo)).toString()


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
    engine.rootContext().setContextProperty("demoAmpliada", "--ampliada" in sys.argv)
    engine.rootContext().setContextProperty("demoGenio", janela_de_exemplo() if "--genio" in sys.argv or "--escala" in sys.argv else "")
    engine.rootContext().setContextProperty("demoEfeito", "escala" if "--escala" in sys.argv else "genio")
    engine.rootContext().setContextProperty("demoProgresso", float(argumento("--progresso", "0.45")))
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "IlhaDeAplicativos.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
