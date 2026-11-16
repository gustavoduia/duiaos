"""DuiaOS — preparação comum das janelas QML da interface e dos aplicativos próprios.

    import interface
    interface.preparar(engine)      # import DuiaOS, ícones próprios e ícones do tema

Os aplicativos (apps/*) acham esta pasta por DUIAOS_SHELL, pela instalação
(/usr/share/duiaos/shell) ou pelo repositório (desenvolvimento).
"""
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))
import icones  # noqa: E402


def configurar_tema_de_icones():
    """Sem ambiente de desktop completo, o Qt não conhece as pastas de ícones do sistema."""
    from PySide6.QtGui import QIcon
    pastas_dados = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    pastas_icones = [str(Path.home() / ".local/share/icons"),
                     str(Path.home() / ".local/share/flatpak/exports/share/icons"),       # Flathub (ADR 049)
                     "/var/lib/flatpak/exports/share/icons"] + [p + "/icons" for p in pastas_dados if p]
    QIcon.setThemeSearchPaths(pastas_icones + QIcon.themeSearchPaths())
    QIcon.setFallbackSearchPaths(QIcon.fallbackSearchPaths() + ["/usr/share/pixmaps"])
    if not QIcon.themeName():
        QIcon.setThemeName("hicolor")


def provedor_icones_do_tema():
    """Entrega ao QML os ícones do tema (image://icone/nome ou caminho absoluto)."""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QIcon, QPixmap
    from PySide6.QtQuick import QQuickImageProvider

    class Icones(QQuickImageProvider):
        def __init__(self):
            super().__init__(QQuickImageProvider.ImageType.Pixmap)

        def requestPixmap(self, nome, tamanho, tamanho_pedido):
            lado = max(tamanho_pedido.width(), 48)
            icone = QIcon(nome) if nome.startswith("/") else QIcon.fromTheme(nome)
            if icone.isNull():
                return QPixmap()
            return icone.pixmap(QSize(lado, lado))

    return Icones()


def aparencia():
    """Objeto "aparencia" do QML (modo escuro e estilo), igual em todas as janelas e atualizado na hora."""
    global _APARENCIA
    if _APARENCIA is None:
        _APARENCIA = _criar_aparencia()
    return _APARENCIA


_APARENCIA = None


def _criar_aparencia():
    from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QTimer, Signal, Slot
    import pastas

    class Aparencia(QObject):
        mudou = Signal()

        def __init__(self):
            super().__init__()
            self._escuro = pastas.ler_preferencia("aparencia", "modo", "claro") == "escuro"
            self._estilo = self._ler_estilo()
            pastas.PREFERENCIAS.parent.mkdir(parents=True, exist_ok=True)
            self._vigia = QFileSystemWatcher([str(pastas.PREFERENCIAS.parent)], self)
            self._vigia.directoryChanged.connect(lambda _c: self._atraso.start())
            self._atraso = QTimer(self, singleShot=True, interval=150, timeout=self.recarregar)

        @staticmethod
        def _ler_estilo():
            estilo = pastas.ler_preferencia("aparencia", "estilo", "padrao")
            return estilo if estilo in ("padrao", "futurista") else "padrao"

        def recarregar(self):
            escuro = pastas.ler_preferencia("aparencia", "modo", "claro") == "escuro"
            estilo = self._ler_estilo()
            if escuro != self._escuro or estilo != self._estilo:
                self._escuro, self._estilo = escuro, estilo
                self.mudou.emit()

        @Slot(str)
        def definirEstilo(self, estilo):
            """Estilo da interface (ADR 052): "padrao" ou "futurista" (Aurora). Vale na hora."""
            if estilo not in ("padrao", "futurista"):
                return
            pastas.gravar_preferencia("aparencia", "estilo", estilo)
            self.recarregar()
            import sessao
            import threading
            threading.Thread(target=sessao.aplicar_aparencia, daemon=True).start()

        @Slot(bool)
        def definirEscuro(self, escuro):
            pastas.gravar_preferencia("aparencia", "modo", "escuro" if escuro else "claro")
            self.recarregar()
            import sessao
            import threading
            threading.Thread(target=sessao.aplicar_aparencia, daemon=True).start()

        escuro = Property(bool, lambda self: self._escuro, notify=mudou)
        estilo = Property(str, lambda self: self._estilo, notify=mudou)

    return Aparencia()


def preparar(engine):
    configurar_tema_de_icones()
    engine.addImportPath(str(PASTA / "qml"))
    icones.registrar(engine)
    engine.addImageProvider("icone", provedor_icones_do_tema())
    engine.rootContext().setContextProperty("aparencia", aparencia())


def registrar_uso(evento, **dados):
    """Uso agregado de "Ajude a melhorar o DuiaOS" (relatorios/uso.py). Sem o duiaos_registro, nada."""
    try:
        import duiaos_registro
    except ImportError:
        return
    duiaos_registro.info(evento, evento, **dados)


def ligar_registro(nome):
    try:
        import duiaos_registro
        duiaos_registro.ligar(nome, qt=True)
    except ImportError:
        pass
