"""DuiaOS — Configurações › Inteligência Artificial e Configurações › Wise (ADR 063).

Objeto "ia" do QML. Junta três coisas:
  IA local     o serviço do sistema duiaos-ia (D-Bus do sistema, org.duiaos.IA1): modelo ativo, catálogo,
               baixar, usar, remover — o que a antiga Central de IA fazia.
  IA na nuvem  os motores da pessoa (shell/comum/motores_ia.py): ativar, chave no cofre, modelos.
  Wise         as preferências do Wise, pelo D-Bus da sessão (org.duiaos.Wise1). Nenhum código do Wise
               mora aqui: esta tela só lê o Estado e manda Definir e Acao (o Wise confere tudo).
"""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shell" / "comum"))
import motores_ia  # noqa: E402

IA = ("org.duiaos.IA1", "/org/duiaos/IA1")
WISE = ("org.duiaos.Wise1", "/org/duiaos/Wise1")
COMANDO_WISE = "/usr/bin/duiaos-wise"


class InteligenciaArtificial(QObject):
    mudou = Signal()            # IA local
    motoresMudou = Signal()     # IA na nuvem
    wiseMudou = Signal()
    aviso = Signal(str)
    _pronto = Signal(str, object)

    def __init__(self, demonstracao=False):
        super().__init__()
        self._demonstracao = demonstracao
        self._estado, self._motores, self._wise = {}, [], {}
        self._ocupados, self._mensagens = {}, {}
        self._vigias = []
        self._ligado = False
        self._pronto.connect(self._ao_pronto)
        if demonstracao:
            self._estado, self._motores, self._wise = exemplo()

    # ------------------------------------------------------------ ligação
    @Slot()
    def abrir(self):
        """A página abriu: liga os sinais e busca tudo."""
        if self._demonstracao:
            return
        if not self._ligado:
            from PySide6.QtDBus import QDBusConnection
            self._ligado = True
            QDBusConnection.systemBus().connect(IA[0], IA[1], IA[0], "Mudou", self, "1aoMudarIA(QString)")
            QDBusConnection.sessionBus().connect(WISE[0], WISE[1], WISE[0], "Mudou", self, "1aoMudarWise(QString)")
            self._tempo = QTimer(self, interval=4000, timeout=self._buscar_wise)     # o Wise pode ligar ou desligar
            self._tempo.start()
        self._chamar(True, IA, "Estado", ao_responder=lambda r: self._ao_estado_ia(r[0]))
        self._buscar_wise()
        self.recarregarMotores()

    def _chamar(self, sistema, destino, metodo, *argumentos, ao_responder=None, ao_falhar=None):
        from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusPendingCallWatcher
        barramento = QDBusConnection.systemBus() if sistema else QDBusConnection.sessionBus()
        mensagem = QDBusMessage.createMethodCall(destino[0], destino[1], destino[0], metodo)
        mensagem.setArguments(list(argumentos))
        vigia = QDBusPendingCallWatcher(barramento.asyncCall(mensagem, 120000), self)
        self._vigias.append(vigia)

        def terminou(v):
            self._vigias.remove(v)
            if v.isError():
                if ao_falhar:
                    ao_falhar(v.error().message())
                elif metodo != "Estado":
                    self.aviso.emit(v.error().message())
            elif ao_responder:
                ao_responder(v.reply().arguments())
            v.deleteLater()
        vigia.finished.connect(terminou)

    # ------------------------------------------------------------ IA local
    def _ao_estado_ia(self, texto):
        try:
            self._estado = json.loads(texto)
        except (TypeError, ValueError):
            return
        self.mudou.emit()

    @Slot(str)
    def aoMudarIA(self, texto):
        try:
            publico = json.loads(texto)
        except ValueError:
            return
        anterior = self._estado
        self._estado = {**anterior, **publico}
        self.mudou.emit()
        # Um modelo entrou ou saiu, terminou um download ou trocou o ativo: o catálogo vem de novo
        if (anterior.get("instalados") != publico.get("instalados") or (anterior.get("tarefa") and not publico.get("tarefa"))
                or anterior.get("ativo") != publico.get("ativo")):
            self._chamar(True, IA, "Estado", ao_responder=lambda r: self._ao_estado_ia(r[0]))

    def _acao_ia(self, metodo, *argumentos):
        if self._demonstracao:
            self.aviso.emit("Demonstração: nada foi mudado.")
            return
        self._chamar(True, IA, metodo, *argumentos,
                     ao_responder=lambda _r: self._chamar(True, IA, "Estado", ao_responder=lambda r: self._ao_estado_ia(r[0])))

    @Slot(str)
    def baixar(self, modelo):
        self._acao_ia("Baixar", modelo)

    @Slot(str)
    def usar(self, modelo):
        self._acao_ia("Ativar", modelo)

    @Slot(str)
    def remover(self, modelo):
        self._acao_ia("Remover", modelo)

    @Slot()
    def cancelar(self):
        self._acao_ia("Cancelar")

    @Slot(bool)
    def pausar(self, pausar):
        self._acao_ia("Pausar", bool(pausar))

    @Slot(str)
    def abrirEndereco(self, url):
        if url.startswith("https://") and not self._demonstracao:
            QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------ IA na nuvem
    def _em_fundo(self, nome, funcao):
        def tarefa():
            try:
                resultado = funcao()
            except motores_ia.Erro as erro:
                resultado = erro
            except Exception as erro:  # noqa: BLE001 — nunca derrubar a janela
                resultado = motores_ia.Erro(f"Não deu certo ({type(erro).__name__}).")
            self._pronto.emit(nome, resultado)
        threading.Thread(target=tarefa, daemon=True).start()

    @Slot()
    def recarregarMotores(self):
        if not self._demonstracao:
            self._em_fundo("motores", motores_ia.situacao)        # o cofre pode demorar: fora da linha da interface

    def _ao_pronto(self, nome, resultado):
        if nome == "motores":
            if not isinstance(resultado, Exception):
                self._motores = resultado
                self.motoresMudou.emit()
            return
        motor = nome.partition(":")[2]
        self._ocupados.pop(motor, None)
        if isinstance(resultado, Exception):
            self._mensagens[motor] = str(resultado)
        else:
            self._mensagens[motor] = resultado or ""
            self._avisar_wise()
        self.motoresMudou.emit()
        self.recarregarMotores()

    def _avisar_wise(self):
        if self._wise:
            self._chamar(False, WISE, "Acao", "recarregar", "{}", ao_falhar=lambda _m: None)

    def _no_motor(self, motor, mensagem, funcao):
        if self._demonstracao:
            self.aviso.emit("Demonstração: nada foi mudado.")
            return
        if motor not in motores_ia.MOTORES or motor in self._ocupados:
            return
        self._ocupados[motor] = mensagem
        self._mensagens.pop(motor, None)
        self.motoresMudou.emit()
        self._em_fundo("motor:" + motor, funcao)

    @Slot(str, str)
    def salvarChave(self, motor, chave):
        """Guarda a chave no cofre e confere no serviço (a lista de modelos vem junto)."""
        def trabalho():
            motores_ia.gravar_chave(motor, chave)
            modelos = motores_ia.conferir(motor, chave.strip())
            motores_ia.definir(motor, ativado=True)
            return f"Chave guardada e conferida: {len(modelos)} modelos disponíveis."
        self._no_motor(motor, "Conferindo a chave…", trabalho)

    @Slot(str)
    def removerChave(self, motor):
        def trabalho():
            motores_ia.apagar_chave(motor)
            motores_ia.definir(motor, ativado=False, modelos=[], modelo="")
            return "Chave removida."
        self._no_motor(motor, "Removendo…", trabalho)

    @Slot(str)
    def atualizarModelos(self, motor):
        self._no_motor(motor, "Buscando os modelos…",
                       lambda: f"{len(motores_ia.conferir(motor))} modelos disponíveis.")

    @Slot(str, bool)
    def ativarMotor(self, motor, ativado):
        self._no_motor(motor, "", lambda: motores_ia.definir(motor, ativado=bool(ativado)))

    @Slot(str, str)
    def modeloDoMotor(self, motor, modelo):
        self._no_motor(motor, "", lambda: motores_ia.definir(motor, modelo=modelo))

    # ------------------------------------------------------------ Wise
    def _buscar_wise(self):
        def falhou(_mensagem):
            if self._wise:
                self._wise = {}
                self.wiseMudou.emit()
        self._chamar(False, WISE, "Estado", ao_responder=lambda r: self.aoMudarWise(r[0]), ao_falhar=falhou)

    @Slot(str)
    def aoMudarWise(self, texto):
        try:
            estado = json.loads(texto)
        except (TypeError, ValueError):
            return
        if isinstance(estado, dict) and estado != self._wise:
            self._wise = estado
            self.wiseMudou.emit()

    @Slot(str, str)
    def definirWise(self, chave, valor):
        if self._demonstracao:
            self._wise = {**self._wise, chave: valor}
            self.wiseMudou.emit()
            return
        self._chamar(False, WISE, "Definir", chave, valor)

    @Slot(str, "QVariantMap")
    def acaoWise(self, nome, dados):
        if self._demonstracao:
            self.aviso.emit("Demonstração: nada foi mudado.")
            return
        self._chamar(False, WISE, "Acao", nome, json.dumps(dict(dados), ensure_ascii=False))

    @Slot()
    def abrirWise(self):
        """Abre a janela do Wise (e o liga, se estava desligado)."""
        if not self._demonstracao and os.access(COMANDO_WISE, os.X_OK):
            subprocess.Popen([COMANDO_WISE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            QTimer.singleShot(2500, self._buscar_wise)

    @Slot()
    def desligarWise(self):
        if not self._demonstracao:
            self._chamar(False, WISE, "Acao", "desligar", "{}")
            QTimer.singleShot(1200, self._buscar_wise)

    estado = Property("QVariantMap", lambda self: self._estado, notify=mudou)
    servicoOk = Property(bool, lambda self: bool(self._estado), notify=mudou)
    motores = Property("QVariantList", lambda self: [
        {**m, "ocupado": self._ocupados.get(m["id"], ""), "esperando": m["id"] in self._ocupados,
         "mensagem": self._mensagens.get(m["id"], "")} for m in self._motores], notify=motoresMudou)
    wise = Property("QVariantMap", lambda self: self._wise, notify=wiseMudou)
    wiseLigado = Property(bool, lambda self: bool(self._wise), notify=wiseMudou)
    wiseInstalado = Property(bool, lambda self: os.access(COMANDO_WISE, os.X_OK) or self._demonstracao, constant=True)


def exemplo():
    """Dados inventados para a demonstração e as capturas de tela."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ia"))
    import catalogo as cat
    estado = {"ativo": "qwen3.5:4b", "padrao": "qwen3.5:4b", "ollama": True, "memoria_gb": 15.5, "carregado": True,
              "pausado": False, "calibrando": False,
              "tarefa": {"tipo": "baixar", "modelo": "phi4:14b", "concluido": int(3.9 * 1024 ** 3),
                         "total": int(9.1 * 1024 ** 3), "fracao": 0.43, "status": "pulling"},
              "ultima": None, "familias": cat.montar(cat.carregar(), {"qwen3.5:4b", "gemma4:e4b"}, "qwen3.5:4b", 15.5)}
    motores = [{"id": m, **info, "ativado": m == "gemini", "tem_chave": m == "gemini",
                "modelos": ["gemini-3.8-flash", "gemini-3.8-pro"] if m == "gemini" else [],
                "modelo": "gemini-3.8-flash" if m == "gemini" else ""} for m, info in motores_ia.MOTORES.items()]
    mb = 1000 ** 2
    wise = {"versao": "0.4.0", "motor_padrao": "local", "reserva_na_nuvem": True, "saudacao": "fala_e_escrita",
            "aprovar_toda_acao": False, "cidade": "Curitiba, Paraná, Brasil", "cidade_opcoes": [], "cidade_mensagem": "",
            "contas_agenda": [{"id": "1", "nome": "Agenda do trabalho", "tipo": "Google"}], "agenda_ocupada": False,
            "agenda_mensagem": "", "login_google": True, "login_microsoft": True,
            "motores": [{"id": "local", "titulo": "Local", "nuvem": False, "pronto": True, "motivo": "", "modelo": "qwen3.5:4b",
                         "modelos": [{"id": "qwen3.5:4b", "nome": "Qwen3.5 4B"}, {"id": "gemma4:e4b", "nome": "Gemma 4 E4B"}]},
                        {"id": "gemini", "titulo": "Google Gemini", "nuvem": True, "pronto": True, "motivo": "",
                         "modelo": "gemini-3.8-flash", "modelos": [{"id": "gemini-3.8-flash", "nome": "gemini-3.8-flash"}]}],
            "voz": {"disponivel": True, "falar_respostas": True, "conversa_continua": True, "voz_na_nuvem": True, "motor_da_voz": "gemini",
                    "voz": "dora", "velocidade": 1.0,
                    "ouvir": True,
                    "baixando": {"faber": 0.37}, "mensagem": "",
                    "vozes": [{"id": "dora", "nome": "Dora — feminina, natural", "pacote": "kokoro", "instalada": True, "tamanho": 132 * mb},
                              {"id": "alex", "nome": "Alex — masculina, natural", "pacote": "kokoro", "instalada": True, "tamanho": 132 * mb},
                              {"id": "santa", "nome": "Santa — masculina, grave", "pacote": "kokoro", "instalada": True, "tamanho": 132 * mb},
                              {"id": "faber", "nome": "Faber — masculina, leve e rápida", "pacote": "faber", "instalada": False, "tamanho": 67 * mb}],
                    "pacotes": {"kokoro": {"instalado": True, "rapido": False, "tamanho": 350 * mb}, "faber": {"instalado": False, "tamanho": 67 * mb},
                                "ouvir": {"instalado": True, "tamanho": 465 * mb}},
                    "reconhecimento": "parakeet",
                    "teste_microfone": {"estado": "pronto", "texto": "Qual é a previsão do tempo para amanhã?", "motivo": ""}}}
    return estado, motores, wise
