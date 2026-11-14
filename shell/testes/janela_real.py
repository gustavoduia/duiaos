"""Abre um componente da interface de verdade (não a demonstração) na plataforma offscreen, com um
módulo org.kde.layershell de mentira, por alguns segundos. Usado por test_janelas_reais.py: pega
erros que só aparecem nas janelas do sistema (ex.: o QML da Ilha que não carregava, 14/11).

Uso: python3 janela_real.py CAMINHO/main.py [segundos]
"""
import importlib.util
import os
import sys
import tempfile
import threading
from enum import IntEnum

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("XDG_RUNTIME_DIR", tempfile.mkdtemp())
principal = os.path.abspath(sys.argv[1])
segundos = float(sys.argv[2]) if len(sys.argv) > 2 else 4
sys.argv = [principal]
sys.path.insert(0, os.path.dirname(principal))

from PySide6.QtCore import Property, QEnum, QObject, Signal  # noqa: E402
from PySide6.QtQml import QmlAttached, QmlElement, QmlUncreatable  # noqa: E402

QML_IMPORT_NAME = "org.kde.layershell"
QML_IMPORT_MAJOR_VERSION = 1


class Anexo(QObject):
    mudou = Signal()

    def __init__(self, pai=None):
        super().__init__(pai)
        self._valores = {}

    def _propriedade(nome, tipo, padrao, mudou=mudou):
        return Property(tipo, lambda s: s._valores.get(nome, padrao),
                        lambda s, v: s._valores.__setitem__(nome, v), notify=mudou)
    anchors = _propriedade("anchors", int, 0)
    layer = _propriedade("layer", int, 0)
    exclusionZone = _propriedade("exclusionZone", int, 0)
    keyboardInteractivity = _propriedade("keyboardInteractivity", int, 0)
    scope = _propriedade("scope", str, "")
    margins = _propriedade("margins", int, 0)


@QmlElement
@QmlUncreatable("só propriedades anexas")
@QmlAttached(Anexo)
class Window(QObject):
    class Anchor(IntEnum):
        AnchorNone = 0
        AnchorTop = 1
        AnchorBottom = 2
        AnchorLeft = 4
        AnchorRight = 8

    class Layer(IntEnum):
        LayerBackground = 0
        LayerBottom = 1
        LayerTop = 2
        LayerOverlay = 3

    class Teclado(IntEnum):
        KeyboardInteractivityNone = 0
        KeyboardInteractivityExclusive = 1
        KeyboardInteractivityOnDemand = 2
    QEnum(Anchor)
    QEnum(Layer)
    QEnum(Teclado)

    @staticmethod
    def qmlAttachedProperties(self, objeto):
        return Anexo(objeto)


especificacao = importlib.util.spec_from_file_location("componente", principal)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)
threading.Timer(segundos, lambda: (print("JANELA-REAL-OK", flush=True), os._exit(0))).start()
modulo.main()
