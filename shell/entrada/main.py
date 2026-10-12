#!/usr/bin/env python3
"""DuiaOS — Tela de Entrada (iniciar uma sessão).

É o "greeter" do greetd: roda como o usuário _greetd, dentro do compositor
cage (veja o script iniciar), mostra a Tela de Entrada e conversa com o greetd
pelo socket $GREETD_SOCK para conferir a senha e abrir a sessão do DuiaOS.
O Wise só existe depois do login: nada dele roda aqui.

A interface fica em TelaDeEntrada.qml, que usa o visual comum
../comum/TelaDeAcesso.qml (o mesmo da Tela de Bloqueio).

Uso:
  main.py                  modo normal (chamado pelo greetd)
  main.py --demonstracao   abre numa janela, sem greetd; a senha "duia" entra
"""
import json
import os
import socket
import struct
import sys
import threading
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

import sistema  # noqa: E402

DEMONSTRACAO = "--demonstracao" in sys.argv

# Comando e variáveis da sessão gráfica do DuiaOS
COMANDO_SESSAO = [str(PASTA.parent / "sessao" / "iniciar-sessao")]
AMBIENTE_SESSAO = [
    "XDG_SESSION_TYPE=wayland",
    "XDG_SESSION_DESKTOP=duiaos",
    "XDG_CURRENT_DESKTOP=DuiaOS:wlroots",
]

# Última pessoa que entrou (a pasta pessoal do _greetd é /var/lib/greetd)
ARQUIVO_ULTIMO = Path.home() / "ultimo-usuario"

os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

from PySide6.QtCore import QObject, Property, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402


class Greetd:
    """Cliente do protocolo do greetd: tamanho (u32, ordem nativa) + JSON."""

    def __init__(self, caminho):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(caminho)

    def pedir(self, mensagem):
        dados = json.dumps(mensagem).encode("utf-8")
        self._socket.sendall(struct.pack("=I", len(dados)) + dados)
        tamanho = struct.unpack("=I", self._receber(4))[0]
        return json.loads(self._receber(tamanho).decode("utf-8"))

    def _receber(self, quantidade):
        partes = b""
        while len(partes) < quantidade:
            parte = self._socket.recv(quantidade - len(partes))
            if not parte:
                raise ConnectionError("o greetd fechou a conexão")
            partes += parte
        return partes


class GreetdDemonstracao:
    """Simula o greetd para testar a tela sem ele: a senha 'duia' entra."""

    def __init__(self):
        self._senha_ok = False
        self._sessao = False

    def pedir(self, mensagem):
        import time
        tipo = mensagem["type"]
        if tipo == "cancel_session":
            self._sessao = False
            return {"type": "success"}
        if tipo == "create_session":
            # Como o greetd: uma sessão por vez; depois de um erro, é preciso cancelar
            if self._sessao:
                return {"type": "error", "error_type": "error", "description": "a session is already being configured"}
            self._sessao = True
            return {"type": "auth_message", "auth_message_type": "secret", "auth_message": "Password: "}
        if tipo == "post_auth_message_response":
            time.sleep(0.8)
            if mensagem.get("response") == "duia":
                self._senha_ok = True
                return {"type": "success"}
            return {"type": "error", "error_type": "auth_error", "description": "pam_authenticate: AUTH_ERR"}
        if tipo == "start_session":
            print("Demonstração: abriria a sessão com", mensagem["cmd"])
            return {"type": "success"}
        return {"type": "success"}


class Entrada(QObject):
    mudou = Signal()
    falhou = Signal(str)
    _resultado = Signal(bool, str)   # da thread de autenticação para a interface

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._ocupado = False
        self._usuarios = sistema.usuarios()
        if DEMONSTRACAO and not self._usuarios:
            self._usuarios = [{"usuario": "duia", "nome": "Duia"}]
        self._usuario_inicial = self._indice_do_ultimo()
        self._opcoes = sistema.opcoes_de_energia(na_sessao=False)
        self._greetd = None
        self._resultado.connect(self._ao_terminar)

    def _indice_do_ultimo(self):
        try:
            ultimo = ARQUIVO_ULTIMO.read_text(encoding="utf-8").strip()
        except OSError:
            return 0
        for indice, pessoa in enumerate(self._usuarios):
            if pessoa["usuario"] == ultimo:
                return indice
        return 0

    def _conexao(self):
        if self._greetd is None:
            if DEMONSTRACAO:
                self._greetd = GreetdDemonstracao()
            else:
                self._greetd = Greetd(os.environ["GREETD_SOCK"])
        return self._greetd

    @Slot(str, str)
    def entrar(self, usuario, senha):
        if self._ocupado:
            return
        self._ocupado = True
        self.mudou.emit()
        threading.Thread(target=self._autenticar, args=(usuario, senha), daemon=True).start()

    def _autenticar(self, usuario, senha):
        """Conversa com o greetd (fora da thread da interface: o PAM pode demorar)."""
        try:
            greetd = self._conexao()
            resposta = greetd.pedir({"type": "create_session", "username": usuario})
            senha_enviada = False
            aviso = ""
            while True:
                tipo = resposta.get("type")
                if tipo == "success":
                    break
                if tipo == "error":
                    # O greetd mantém a sessão "em configuração" depois de um erro (senha
                    # errada inclusive): sem cancelar, a próxima tentativa recebe "a session
                    # is already being configured" e a Tela de Entrada trava.
                    self._cancelar(greetd)
                    if resposta.get("error_type") == "auth_error":
                        self._resultado.emit(False, "Senha incorreta. Tente de novo.")
                    else:
                        self._resultado.emit(False, aviso or "Não foi possível entrar: "
                                             + resposta.get("description", "erro desconhecido"))
                    return
                # auth_message: pergunta do PAM
                tipo_mensagem = resposta.get("auth_message_type")
                if tipo_mensagem == "secret" and not senha_enviada:
                    senha_enviada = True
                    resposta = greetd.pedir({"type": "post_auth_message_response", "response": senha})
                elif tipo_mensagem in ("info", "error"):
                    aviso = resposta.get("auth_message", "").strip()
                    resposta = greetd.pedir({"type": "post_auth_message_response", "response": None})
                else:
                    # Pergunta que esta tela ainda não sabe responder (ex.: trocar a senha vencida)
                    self._cancelar(greetd)
                    self._resultado.emit(False, aviso or "Esta conta pede uma etapa extra que a "
                                         "Tela de Entrada ainda não suporta: "
                                         + resposta.get("auth_message", "").strip())
                    return

            resposta = greetd.pedir({"type": "start_session", "cmd": COMANDO_SESSAO, "env": AMBIENTE_SESSAO})
            if resposta.get("type") != "success":
                self._cancelar(greetd)
                self._resultado.emit(False, "Não foi possível abrir a sessão: "
                                     + resposta.get("description", "erro desconhecido"))
                return
            try:
                ARQUIVO_ULTIMO.write_text(usuario + "\n", encoding="utf-8")
            except OSError:
                pass
            self._resultado.emit(True, "")
        except (OSError, ConnectionError, KeyError, ValueError) as erro:
            # Conexão nova na próxima tentativa (o greetd descarta a sessão da conexão perdida)
            self._greetd = None
            self._resultado.emit(False, f"Falha na comunicação com o sistema de login ({erro}).")

    def _cancelar(self, greetd):
        """Descarta a sessão em configuração para a próxima tentativa começar do zero."""
        try:
            greetd.pedir({"type": "cancel_session"})
        except (OSError, ConnectionError, ValueError):
            self._greetd = None

    def _ao_terminar(self, sucesso, mensagem):
        if sucesso:
            # O greetd abre a sessão quando a Tela de Entrada fecha.
            self._app.quit()
            return
        self._ocupado = False
        self.mudou.emit()
        self.falhou.emit(mensagem)

    @Slot(str)
    def energia(self, acao):
        if DEMONSTRACAO:
            print("Demonstração: ação de energia", acao)
            return
        sistema.executar_energia(acao)

    usuarios = Property("QVariantList", lambda self: self._usuarios, constant=True)
    usuarioInicial = Property(int, lambda self: self._usuario_inicial, constant=True)
    opcoesEnergia = Property("QVariantList", lambda self: self._opcoes, constant=True)
    versao = Property(str, lambda self: sistema.versao(), constant=True)
    papelDeParede = Property(str, lambda self: sistema.papel_de_parede(), constant=True)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)
    ocupado = Property(bool, lambda self: self._ocupado, notify=mudou)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("duiaos-entrada")
    entrada = Entrada(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("entrada", entrada)
    engine.load(PASTA / "TelaDeEntrada.qml")
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
