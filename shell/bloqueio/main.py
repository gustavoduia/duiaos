#!/usr/bin/env python3
"""DuiaOS — Tela de Bloqueio (desbloquear uma sessão aberta).

Mesmo visual da Tela de Entrada (../comum/TelaDeAcesso.qml), cobrindo todos
os monitores na camada mais alta do Wayland. A senha é conferida pelo PAM
(serviço /etc/pam.d/duiaos-bloqueio), como no login.

Não abra este programa direto: use o script bloquear, que o abre de novo se
ele for encerrado sem a senha correta.

Saída: código 0 somente quando a senha estiver correta.

Uso:
  main.py                  bloqueia a tela (chamado pelo script bloquear)
  main.py --demonstracao   abre numa janela comum; a senha "duia" desbloqueia
"""
import os
import sys
import threading
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

import sistema  # noqa: E402

DEMONSTRACAO = "--demonstracao" in sys.argv
SERVICO_PAM = "duiaos-bloqueio"
PASTA_EXECUCAO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
ARQUIVO_PRONTA = PASTA_EXECUCAO / "duiaos-bloqueio.pronta"

os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
if not DEMONSTRACAO:
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QObject, Property, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402


def conferir_senha(usuario, senha):
    """True se a senha do usuário estiver correta (PAM)."""
    if DEMONSTRACAO:
        time.sleep(0.8)
        return senha == "duia"
    import pamela
    try:
        # resetcred=0: só confere a senha; a sessão já está aberta.
        pamela.authenticate(usuario, senha, service=SERVICO_PAM, resetcred=0)
        return True
    except pamela.PAMError:
        return False


class Bloqueio(QObject):
    mudou = Signal()
    falhou = Signal(str)
    _resultado = Signal(bool)

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._ocupado = False
        self._usuario = sistema.usuario_atual()
        self._opcoes = sistema.opcoes_de_energia(na_sessao=False)
        self._resultado.connect(self._ao_conferir)

    @Slot()
    def pronta(self):
        """A tela apareceu: avisa o script bloquear (e o swayidle) que já é seguro suspender."""
        try:
            ARQUIVO_PRONTA.write_text(str(os.getpid()))
        except OSError:
            pass

    @Slot(str)
    def desbloquear(self, senha):
        if self._ocupado:
            return
        self._ocupado = True
        self.mudou.emit()
        usuario = self._usuario["usuario"]
        threading.Thread(target=lambda: self._resultado.emit(conferir_senha(usuario, senha)),
                         daemon=True).start()

    def _ao_conferir(self, correta):
        if correta:
            self._app.exit(0)
            return
        self._ocupado = False
        self.mudou.emit()
        self.falhou.emit("Senha incorreta. Tente de novo.")

    @Slot(str)
    def energia(self, acao):
        if DEMONSTRACAO:
            print("Demonstração: ação de energia", acao)
            return
        sistema.executar_energia(acao)

    usuario = Property("QVariantMap", lambda self: self._usuario, constant=True)
    opcoesEnergia = Property("QVariantList", lambda self: self._opcoes, constant=True)
    versao = Property(str, lambda self: sistema.versao(), constant=True)
    papelDeParede = Property(str, lambda self: sistema.papel_de_parede(), constant=True)
    ocupado = Property(bool, lambda self: self._ocupado, notify=mudou)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("duiaos-bloqueio")
    # Fechar janelas não desbloqueia: só a senha correta encerra o programa.
    app.setQuitOnLastWindowClosed(False)
    bloqueio = Bloqueio(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bloqueio", bloqueio)
    if DEMONSTRACAO:
        engine.load(PASTA / "Demonstracao.qml")
    else:
        engine.load(PASTA / "TelaDeBloqueio.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    try:
        ARQUIVO_PRONTA.unlink()
    except OSError:
        pass
    sys.exit(codigo)


if __name__ == "__main__":
    main()
