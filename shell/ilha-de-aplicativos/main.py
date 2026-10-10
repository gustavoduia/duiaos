#!/usr/bin/env python3
"""DuiaOS — Ilha de Aplicativos (barra inferior de aplicativos).

Mostra os aplicativos fixados e os abertos. Um clique abre o aplicativo ou,
se ele já estiver aberto, traz a janela para a frente.
A interface fica em IlhaDeAplicativos.qml.

Aplicativos fixados: ~/.config/duiaos/ilha-de-aplicativos.conf
Janelas abertas: comando wlrctl (protocolo wlr-foreign-toplevel do labwc).
"""
import configparser
import fcntl
import os
import shlex
import subprocess
import sys
from pathlib import Path

PASTA_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos"
ARQUIVO_CONFIG = PASTA_CONFIG / "ilha-de-aplicativos.conf"
FIXADOS_PADRAO = ["foot.desktop"]
PASTAS_APLICATIVOS = [
    Path.home() / ".local/share/applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
]

# Uma instância só
_trava = open(os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "duiaos-ilha-de-aplicativos.lock"), "w")
try:
    fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    print("A Ilha de Aplicativos já está aberta. Para reiniciar: reiniciar.sh")
    sys.exit(0)

# A Ilha é uma "camada" do Wayland presa à borda de baixo (layer-shell).
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QSize, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQuick import QQuickImageProvider  # noqa: E402


def ler_fixados():
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    texto = config.get("ilha", "fixados", fallback=";".join(FIXADOS_PADRAO))
    return [item.strip() for item in texto.split(";") if item.strip()]


def gravar_fixados(fixados):
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Ilha de Aplicativos.\n")
        arquivo.write("# fixados: arquivos .desktop separados por ponto e vírgula (;)\n")
        arquivo.write("[ilha]\nfixados = " + ";".join(fixados) + "\n")


def ler_desktop(id_desktop):
    """Lê um arquivo .desktop e devolve um dicionário com nome, ícone e comando."""
    for pasta in PASTAS_APLICATIVOS:
        caminho = pasta / id_desktop
        if not caminho.is_file():
            continue
        dados, na_secao = {}, False
        for linha in caminho.read_text(encoding="utf-8", errors="ignore").splitlines():
            linha = linha.strip()
            if linha.startswith("["):
                na_secao = linha == "[Desktop Entry]"
                continue
            if na_secao and "=" in linha:
                chave, valor = linha.split("=", 1)
                dados.setdefault(chave.strip(), valor.strip())
        nome = dados.get("Name[pt_BR]") or dados.get("Name[pt]") or dados.get("Name", id_desktop)
        return {
            "id": id_desktop,
            "nome": nome,
            "icone": dados.get("Icon", ""),
            "exec": dados.get("Exec", ""),
            "classe": dados.get("StartupWMClass", "").lower(),
        }
    return None


def comando_de_exec(exec_desktop):
    """Converte a linha Exec= em lista de argumentos, sem os códigos %f, %U etc."""
    try:
        partes = shlex.split(exec_desktop)
    except ValueError:
        return []
    return [p for p in partes if not (len(p) == 2 and p.startswith("%"))]


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


class Icones(QQuickImageProvider):
    """Entrega ao QML os ícones do tema (image://icone/nome)."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, nome, tamanho, tamanho_pedido):
        lado = max(tamanho_pedido.width(), 48)
        if nome.startswith("/"):
            icone = QIcon(nome)
        else:
            icone = QIcon.fromTheme(nome)
        if icone.isNull():
            return QPixmap()
        return icone.pixmap(QSize(lado, lado))


class Ilha(QObject):
    mudou = Signal()

    def __init__(self):
        super().__init__()
        if not ARQUIVO_CONFIG.exists():
            gravar_fixados(FIXADOS_PADRAO)
        self._fixados = []
        self._abertos = []
        self._itens = []
        self._vigia = QFileSystemWatcher([str(PASTA_CONFIG), str(ARQUIVO_CONFIG)], self)
        self.recarregar_fixados()
        self._vigia.directoryChanged.connect(self.recarregar_fixados)
        self._vigia.fileChanged.connect(self.recarregar_fixados)
        self._timer = QTimer(self, interval=1500, timeout=self.atualizar_abertos)
        self._timer.start()
        self.atualizar_abertos()

    def recarregar_fixados(self, _caminho=None):
        # Editores recriam o arquivo: volta a vigiá-lo
        if ARQUIVO_CONFIG.exists() and str(ARQUIVO_CONFIG) not in self._vigia.files():
            self._vigia.addPath(str(ARQUIVO_CONFIG))
        self._fixados = [d for d in (ler_desktop(i) for i in ler_fixados()) if d]
        self.montar()

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
                "id": "", "nome": app_id, "icone": app_id, "exec": "", "classe": ""}
            itens.append({**app, "fixado": False, "aberto": True, "appId": app_id})
        self._itens = itens
        self.mudou.emit()

    @Slot(int)
    def ativar(self, indice):
        if not 0 <= indice < len(self._itens):
            return
        item = self._itens[indice]
        if item["aberto"] and item["appId"]:
            subprocess.Popen(["wlrctl", "toplevel", "focus", "app_id:" + item["appId"]],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        comando = comando_de_exec(item["exec"])
        if comando:
            subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)

    itens = Property("QVariantList", lambda self: self._itens, notify=mudou)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("duiaos-ilha-de-aplicativos")
    # Sem ambiente de desktop completo, o Qt não conhece as pastas de ícones
    # do sistema: informa as pastas padrão (XDG) e o tema base "hicolor".
    pastas_dados = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    pastas_icones = [str(Path.home() / ".local/share/icons")] + [p + "/icons" for p in pastas_dados if p]
    QIcon.setThemeSearchPaths(pastas_icones + QIcon.themeSearchPaths())
    QIcon.setFallbackSearchPaths(QIcon.fallbackSearchPaths() + ["/usr/share/pixmaps"])
    if not QIcon.themeName():
        QIcon.setThemeName("hicolor")

    ilha = Ilha()
    engine = QQmlApplicationEngine()
    engine.addImageProvider("icone", Icones())
    engine.rootContext().setContextProperty("ilha", ilha)
    engine.load(Path(__file__).with_name("IlhaDeAplicativos.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
