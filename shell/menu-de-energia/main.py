#!/usr/bin/env python3
"""DuiaOS — Menu de Energia da sessão.

Bloquear, Encerrar sessão, Suspender, Reiniciar, Reiniciar no Windows
(só aparece com dual boot) e Desligar. Abre pelo símbolo do DuiaOS na Barra
de Recursos ou com Ctrl+Alt+Delete. Se já estiver aberto, um novo pedido o fecha.

A interface fica em MenuDeEnergiaJanela.qml.
"""
import fcntl
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

import sistema  # noqa: E402

PASTA_EXECUCAO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
ARQUIVO_PID = PASTA_EXECUCAO / "duiaos-menu-de-energia.pid"

# Uma instância só: um segundo pedido fecha o menu aberto.
_trava = open(PASTA_EXECUCAO / "duiaos-menu-de-energia.lock", "w")
try:
    fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    try:
        os.kill(int(ARQUIVO_PID.read_text()), 15)
    except (OSError, ValueError):
        pass
    sys.exit(0)
ARQUIVO_PID.write_text(str(os.getpid()))

os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QObject, Property, QTimer, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402


class Menu(QObject):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self._opcoes = sistema.opcoes_de_energia(na_sessao=True)

    @Slot(str)
    def escolher(self, acao):
        sistema.executar_energia(acao)
        self._app.quit()

    @Slot()
    def fechar(self):
        self._app.quit()

    opcoes = Property("QVariantList", lambda self: self._opcoes, constant=True)


def main():
    import signal
    signal.signal(signal.SIGTERM, lambda *_: QGuiApplication.quit())
    app = QGuiApplication(sys.argv)
    # Devolve o controle ao Python de tempos em tempos para ele tratar o SIGTERM.
    vigia_sinal = QTimer(interval=200)
    vigia_sinal.timeout.connect(lambda: None)
    vigia_sinal.start()
    app.setApplicationName("duiaos-menu-de-energia")
    menu = Menu(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("menuEnergia", menu)
    engine.load(PASTA / "MenuDeEnergiaJanela.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    try:
        ARQUIVO_PID.unlink()
    except OSError:
        pass
    sys.exit(codigo)


if __name__ == "__main__":
    main()
