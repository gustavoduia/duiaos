#!/usr/bin/env python3
"""DuiaOS — Central de IA (ADRs 029 e 030).

Escolhe o modelo de IA local ativo do sistema (um só, usado por todos os
programas), baixa e remove modelos do catálogo. Fala com o serviço duiaos-ia
pelo D-Bus do sistema (org.duiaos.IA1); a interface fica em CentralDeIA.qml.

Uso:
  main.py                  abre a Central de IA
  main.py --demonstracao   abre com dados de exemplo, sem o serviço (testar o visual)
  main.py --captura ARQ    (com --demonstracao) salva uma imagem da janela e sai
"""
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

NOME = "org.duiaos.IA1"
CAMINHO = "/org/duiaos/IA1"
PASTA = Path(__file__).resolve().parent


class Central(QObject):
    """Ponte entre a interface e o serviço duiaos-ia."""

    mudou = Signal()
    erro = Signal(str)

    def __init__(self):
        super().__init__()
        from PySide6.QtDBus import QDBusConnection
        sessao = os.environ.get("DUIAOS_IA_BARRAMENTO") == "sessao"
        self._barramento = QDBusConnection.sessionBus() if sessao else QDBusConnection.systemBus()
        self._estado = {}
        self._vigias = []
        self._barramento.connect(NOME, CAMINHO, NOME, "Mudou", self, "1aoMudar(QString)")
        QTimer.singleShot(0, self.recarregar)

    # ------------------------------------------------------------ leitura
    @Slot()
    def recarregar(self):
        self._chamar("Estado", ao_responder=self._ao_estado)

    def _ao_estado(self, argumentos):
        try:
            self._estado = json.loads(argumentos[0])
        except (IndexError, TypeError, ValueError):
            return
        self.mudou.emit()

    @Slot(str)
    def aoMudar(self, texto):
        try:
            publico = json.loads(texto)
        except ValueError:
            return
        anterior = self._estado
        self._estado = {**anterior, **publico}
        self.mudou.emit()
        # Terminou um download ou trocou o ativo: a lista de baixados mudou
        if (anterior.get("tarefa") and not publico.get("tarefa")) or anterior.get("ativo") != publico.get("ativo"):
            self.recarregar()

    estadoJson = Property(str, lambda self: json.dumps(self._estado), notify=mudou)
    servicoOk = Property(bool, lambda self: bool(self._estado), notify=mudou)

    # ------------------------------------------------------------ ações
    def _chamar(self, metodo, *argumentos, ao_responder=None):
        from PySide6.QtDBus import QDBusMessage, QDBusPendingCallWatcher
        mensagem = QDBusMessage.createMethodCall(NOME, CAMINHO, NOME, metodo)
        mensagem.setArguments(list(argumentos))
        vigia = QDBusPendingCallWatcher(self._barramento.asyncCall(mensagem, 120000), self)
        self._vigias.append(vigia)      # guarda a referência até a resposta chegar

        def terminou(v):
            self._vigias.remove(v)
            resposta = v.reply()
            if v.isError():
                if metodo != "Estado":
                    self.erro.emit(v.error().message())
                elif not self._estado:
                    self.erro.emit("O serviço de IA do sistema (duiaos-ia) não respondeu.")
            elif ao_responder:
                ao_responder(resposta.arguments())
            v.deleteLater()

        vigia.finished.connect(terminou)

    @Slot(str)
    def baixar(self, modelo):
        self._chamar("Baixar", modelo)

    @Slot(str)
    def ativar(self, modelo):
        self._chamar("Ativar", modelo)

    @Slot(str)
    def remover(self, modelo):
        self._chamar("Remover", modelo)

    @Slot()
    def cancelar(self):
        self._chamar("Cancelar")

    @Slot(str)
    def abrirEndereco(self, url):
        if url.startswith("https://"):
            QDesktopServices.openUrl(QUrl(url))


class CentralDemonstracao(QObject):
    """Dados de exemplo para ver o visual sem o serviço."""

    mudou = Signal()
    erro = Signal(str)

    def __init__(self):
        super().__init__()
        sys.path.insert(0, str(PASTA.parents[1] / "ia"))
        import catalogo as cat
        catalogo = cat.carregar()
        self._estado = {
            "ativo": "qwen3.5:4b", "padrao": "qwen3.5:4b", "ollama": True, "memoria_gb": 15.5,
            "tarefa": {"tipo": "baixar", "modelo": "phi4:14b", "concluido": int(3.9 * 1024 ** 3),
                       "total": int(9.1 * 1024 ** 3), "fracao": 0.43, "status": "pulling"},
            "ultima": None,
            "familias": cat.montar(catalogo, {"qwen3.5:4b", "gemma4:e4b"}, "qwen3.5:4b", 15.5),
        }

    estadoJson = Property(str, lambda self: json.dumps(self._estado), notify=mudou)
    servicoOk = Property(bool, lambda self: True, notify=mudou)

    @Slot()
    def recarregar(self):
        self.mudou.emit()

    @Slot(str)
    def baixar(self, modelo):
        self.erro.emit(f"Demonstração: baixaria {modelo}.")

    @Slot(str)
    def ativar(self, modelo):
        self._estado["ativo"] = modelo
        for familia in self._estado["familias"]:
            for item in familia["modelos"]:
                item["ativo"] = item["id"] == modelo
        self.mudou.emit()

    @Slot(str)
    def remover(self, modelo):
        self.erro.emit(f"Demonstração: removeria {modelo}.")

    @Slot()
    def cancelar(self):
        self._estado["tarefa"] = None
        self.mudou.emit()

    @Slot(str)
    def abrirEndereco(self, url):
        print("abrir", url)


def main():
    demonstracao = "--demonstracao" in sys.argv
    captura = sys.argv[sys.argv.index("--captura") + 1] if "--captura" in sys.argv else ""
    app = QGuiApplication(sys.argv)
    app.setApplicationName("duiaos-central-de-ia")
    app.setApplicationDisplayName("Central de IA")
    app.setDesktopFileName("duiaos-central-de-ia")
    app.setWindowIcon(QIcon.fromTheme("duiaos-central-de-ia"))

    central = CentralDemonstracao() if demonstracao else Central()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("central", central)
    engine.rootContext().setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / "CentralDeIA.qml")
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
