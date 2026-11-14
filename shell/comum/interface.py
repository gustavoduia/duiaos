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
    pastas_icones = [str(Path.home() / ".local/share/icons")] + [p + "/icons" for p in pastas_dados if p]
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


def preparar(engine):
    configurar_tema_de_icones()
    engine.addImportPath(str(PASTA / "qml"))
    icones.registrar(engine)
    engine.addImageProvider("icone", provedor_icones_do_tema())


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
