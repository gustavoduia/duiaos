#!/usr/bin/env python3
"""DuiaOS — "Ajude a melhorar o DuiaOS" (ADR 040, fase 2).

A pessoa escolhe o que o computador envia para o desenvolvimento: nada, erros, ou erros e uso. Abre sozinho
na 1ª entrada enquanto nada foi escolhido (sem opção marcada: nada sai antes) e fica na Central de
Aplicativos para mudar depois (até existir o aplicativo Configurações, que vai mostrar esta mesma página).

A escolha é gravada pelo `duiaos-relatorios escolher NIVEL`, como administrador, pelo pkexec (ação do polkit
org.duiaos.relatorios.escolher: o administrador que está no computador não digita senha).

Uso:
  main.py                     abre a janela
  main.py --primeira-entrada  abre só se a pessoa ainda não escolheu (usado pelo início da sessão)
  main.py --demonstracao      não grava nada (testar o visual); --captura ARQ salva uma imagem e sai
"""
import grp
import json
import os
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
ARQUIVO_CONFIG = Path(os.environ.get("DUIAOS_RELATORIOS_CONFIG", "/etc/duiaos/relatorios.conf"))
SITUACAO = Path(os.environ.get("DUIAOS_RELATORIOS_ESTADO", "/var/lib/duiaos-relatorios")) / "situacao.json"
ESCOLHER = "/usr/lib/duiaos/relatorios/escolher-nivel"
# Página "Ajude a melhorar o DuiaOS" da documentação (duiaos-websites, compartilhado/enderecos.js)
DOCUMENTACAO = "https://duiaos-docs.gustavoduia.workers.dev/entenda/ajude-a-melhorar-o-duiaos/"
NIVEIS = ("nao_escolhido", "desligado", "erros", "erros_e_uso", "desenvolvimento")


def nivel_atual(arquivo=None):
    """Lê o nível do arquivo público (0644) sem depender do pacote do coletor."""
    try:
        for linha in Path(arquivo or ARQUIVO_CONFIG).read_text(encoding="utf-8").splitlines():
            chave, _, valor = linha.partition("=")
            if chave.strip() == "nivel" and valor.strip() in NIVEIS:
                return valor.strip()
    except OSError:
        pass
    return "nao_escolhido"


def situacao(arquivo=None):
    try:
        dados = json.loads(Path(arquivo or SITUACAO).read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def administrador():
    try:
        return "sudo" in {grp.getgrgid(g).gr_name for g in os.getgroups()}
    except (KeyError, OSError):
        return False


def precisa_perguntar(argv):
    """--primeira-entrada: só abre se ainda não foi escolhido."""
    return "--primeira-entrada" not in argv or nivel_atual() == "nao_escolhido"


def main():
    argv = sys.argv[1:]
    if not precisa_perguntar(argv):
        return 0
    from PySide6.QtCore import QObject, Property, QProcess, QUrl, Signal, Slot
    from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine

    demonstracao = "--demonstracao" in argv
    captura = argv[argv.index("--captura") + 1] if "--captura" in argv else ""

    class Ajude(QObject):
        mudou = Signal()
        terminou = Signal(bool, str)        # ok, mensagem

        def __init__(self):
            super().__init__()
            self._nivel = "nao_escolhido" if demonstracao else nivel_atual()
            self._ocupado = False
            self._processo = None

        nivel = Property(str, lambda self: self._nivel, notify=mudou)
        ocupado = Property(bool, lambda self: self._ocupado, notify=mudou)
        primeiraEntrada = Property(bool, lambda self: "--primeira-entrada" in argv, constant=True)
        administrador = Property(bool, lambda self: demonstracao or administrador(), constant=True)
        situacaoJson = Property(str, lambda self: json.dumps(situacao()), notify=mudou)

        @Slot(str)
        def escolher(self, nivel):
            if self._ocupado or nivel not in ("desligado", "erros", "erros_e_uso"):
                return
            if demonstracao:
                self._nivel = nivel
                self.mudou.emit()
                self.terminou.emit(True, "")
                return
            self._ocupado = True
            self.mudou.emit()
            self._processo = QProcess(self)
            self._processo.finished.connect(lambda codigo, _estado: self._fim(codigo, nivel))
            self._processo.errorOccurred.connect(lambda _erro: self._fim(-1, nivel))
            self._processo.start("pkexec", [ESCOLHER, nivel])

        def _fim(self, codigo, nivel):
            if not self._ocupado:
                return
            self._ocupado = False
            if codigo == 0:
                self._nivel = nivel_atual()
                self.mudou.emit()
                self.terminou.emit(True, "")
                return
            self.mudou.emit()
            # 126/127: o pkexec não autorizou (não é administrador ou cancelou a senha)
            mensagem = ("Só quem administra este computador pode mudar esta escolha."
                        if codigo in (126, 127) else "Não consegui gravar a escolha. Tente de novo.")
            try:
                import duiaos_registro
                duiaos_registro.aviso("relatorios.escolha_falhou", "A escolha não foi gravada",
                                      codigo=codigo, nivel=nivel)
            except ImportError:
                pass
            self.terminou.emit(False, mensagem)

        @Slot()
        def abrirDocumentacao(self):
            QDesktopServices.openUrl(QUrl(DOCUMENTACAO))

    app = QGuiApplication(sys.argv)
    try:
        import duiaos_registro
        duiaos_registro.ligar("duiaos-ajude-a-melhorar", qt=True)
    except ImportError:
        pass
    app.setApplicationName("duiaos-ajude-a-melhorar")
    app.setApplicationDisplayName("Ajude a melhorar o DuiaOS")
    app.setDesktopFileName("duiaos-ajude-a-melhorar")
    app.setWindowIcon(QIcon.fromTheme("duiaos-ajude-a-melhorar"))
    ajude = Ajude()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("ajude", ajude)
    engine.load(PASTA / "AjudeAMelhorar.qml")
    if not engine.rootObjects():
        return 1
    if captura:                        # testes do visual: imagem da janela e sai
        from PySide6.QtCore import QTimer

        def capturar():
            import shiboken6
            from PySide6.QtQuick import QQuickWindow
            raiz = engine.rootObjects()[0]
            janela = shiboken6.wrapInstance(shiboken6.getCppPointer(raiz)[0], QQuickWindow)
            janela.grabWindow().save(captura)
            app.quit()
        QTimer.singleShot(900, capturar)
    codigo = app.exec()
    del engine                         # a interface sai antes do objeto que ela usa
    return codigo


if __name__ == "__main__":
    sys.exit(main())
