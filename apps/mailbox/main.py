#!/usr/bin/env python3
"""DuiaOS — Mail Box, o gerenciador de e-mails do DuiaOS (ADR 072).

Contas IMAP e POP3 com envio por SMTP; wizard que descobre os servidores pelo endereço (catálogo próprio,
MX, ISPDB, autoconfig, SRV); caixa de entrada unificada; leitura segura (sem JavaScript, imagens externas
bloqueadas até a pessoa liberar); escrever, responder, responder a todos e encaminhar, com anexos;
notificações de e-mails novos; menus na Barra de Recursos. Senhas no cofre do sistema.

Uso:
  main.py [mailto:ENDEREÇO]
  main.py --demonstracao [--pagina caixa|wizard|escrever] [--escuro] [--captura ARQUIVO]
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

PASTA = Path(__file__).resolve().parent
# Motor web do DuiaOS (pacote duiaos-motor-web, ADR 072): o Qt WebEngine recente vem antes do PySide6 do Debian,
# só neste processo (os programas que ele abre não herdam).
_MOTOR_WEB = Path(os.environ.get("DUIAOS_MOTOR_WEB", "/usr/lib/duiaos/motor-web"))
if (_MOTOR_WEB / "PySide6").is_dir():
    sys.path.insert(0, str(_MOTOR_WEB))
for _comum in (Path(os.environ.get("DUIAOS_SHELL", "/usr/share/duiaos/shell")) / "comum",
               PASTA.parents[1] / "shell" / "comum"):
    if (_comum / "interface.py").is_file():
        sys.path.insert(0, str(_comum))
        break
sys.path.insert(0, str(PASTA))

DEMONSTRACAO = "--demonstracao" in sys.argv
if DEMONSTRACAO:
    _TEMP = Path(tempfile.mkdtemp(prefix="mailbox-demo-"))
    os.environ["XDG_DATA_HOME"] = str(_TEMP / "dados")
    os.environ["XDG_CONFIG_HOME"] = str(_TEMP / "config")
    os.environ["DUIAOS_MAILBOX_COFRE"] = "memoria"

import caixa_postal  # noqa: E402
import autoconfig  # noqa: E402
import cofre as modulo_cofre  # noqa: E402
import mensagem  # noqa: E402
import provedores  # noqa: E402
import servidores  # noqa: E402
import sincronizador  # noqa: E402

from PySide6.QtCore import QObject, Property, QStandardPaths, QTimer, Signal, Slot, QCoreApplication, Qt  # noqa: E402

VERSAO = "0.1"
INTERVALO_SINCRONIA = 3 * 60 * 1000
ARQUIVO_PEDIDO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-mailbox.pedido"
MENSAGENS = {"mailbox_inicio": "Mail Box aberto", "mailbox_conta": "Conta adicionada no Mail Box",
             "mailbox_conta_removida": "Conta removida do Mail Box", "mailbox_erro": "Erro numa conta do Mail Box",
             "mailbox_enviada": "Mensagem enviada pelo Mail Box", "mailbox_falha_envio": "Falha ao enviar no Mail Box"}


def registrar(nivel, evento, **campos):
    """Registro do sistema. Nunca endereços, assuntos ou conteúdo de mensagens."""
    try:
        import duiaos_registro
    except ImportError:
        return
    getattr(duiaos_registro, nivel)(evento, MENSAGENS.get(evento, evento), **campos)


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def ler_mailto(url):
    """mailto:a@b?subject=..&body=..&cc=.. → campos da janela Escrever."""
    partes = urlsplit(url)
    consulta = {k.lower(): v[0] for k, v in parse_qs(partes.query).items()}
    return {"para": unquote(partes.path), "cc": consulta.get("cc", ""), "assunto": consulta.get("subject", ""),
            "corpo": consulta.get("body", ""), "em_resposta_a": "", "referencias": ""}


class MailBox(QObject):
    contasMudaram = Signal()
    pastasMudaram = Signal()
    mensagensMudaram = Signal()
    leituraMudou = Signal()
    estadoMudou = Signal()
    aviso = Signal(str)
    descoberto = Signal("QVariantMap", str)            # configuração, origem
    testeConcluido = Signal(bool, str)
    enviada = Signal()
    falhaEnvio = Signal(str)
    abrirEscrever = Signal("QVariantMap")               # a janela principal cria a janela Escrever
    _evento = Signal(str, "QVariantMap")                # da linha de trabalho para a linha da janela
    _resultado = Signal(str, "QVariantMap")

    def __init__(self, perfil_leitura, interceptador):
        super().__init__()
        self.perfil_leitura = perfil_leitura
        self.interceptador = interceptador
        self.contas = caixa_postal.Contas()
        self.banco = caixa_postal.Banco()
        self.cofre = modulo_cofre.abrir()
        self._pasta = -1                    # -1: a Entrada de todas as contas
        self._busca = ""
        self._leitura = {}
        self._estados = {}                  # conta → texto ("Sincronizando…")
        self._erros = {}                    # conta → último erro
        self._janelas_escrever = []
        self._evento.connect(self._tratar_evento)
        self._resultado.connect(self._tratar_resultado)
        self.motor = sincronizador.Motor(self.contas, self.banco, self.cofre, lambda e, d: self._evento.emit(e, d))
        self._relogio = QTimer(self, interval=INTERVALO_SINCRONIA, timeout=self.atualizar)

    def iniciar(self):
        if DEMONSTRACAO:
            return
        self.motor.iniciar()
        self.motor.sincronizar_todas()
        self._relogio.start()

    # ------------------------------------------------------------ eventos do motor
    def _tratar_evento(self, evento, dados):
        conta = dados.get("conta", "")
        if evento == "pastas":
            self.pastasMudaram.emit()
        elif evento == "mensagens":
            self.pastasMudaram.emit()
            if self._pasta == -1 or self._pasta == dados.get("pasta"):
                self.mensagensMudaram.emit()
        elif evento == "estado":
            self._estados[conta] = dados.get("texto", "")
            if dados.get("texto"):
                self._erros.pop(conta, None)
            self.estadoMudou.emit()
        elif evento == "erro":
            self._erros[conta] = dados.get("texto", "")
            registrar("aviso", "mailbox_erro", provedor=(self.contas.obter(conta) or {}).get("provedor", ""))
            self.estadoMudou.emit()
            self.aviso.emit(dados.get("texto", ""))
        elif evento == "novas":
            self._notificar(conta, dados.get("lista", []))
        elif evento == "corpo":
            if self._leitura.get("id") == dados.get("id"):
                self.abrirMensagem(dados["id"])
        elif evento == "enviada":
            registrar("info", "mailbox_enviada")
            self.enviada.emit()
            self.aviso.emit("Mensagem enviada.")
        elif evento == "falha_envio":
            registrar("aviso", "mailbox_falha_envio")
            self.falhaEnvio.emit(dados.get("texto", ""))

    def _notificar(self, id_conta, lista):
        if not lista or not shutil.which("notify-send"):
            return
        if len(lista) == 1:
            titulo = lista[0]["de_nome"] or lista[0]["de_email"]
            texto = lista[0]["assunto"] or "(sem assunto)"
        else:
            titulo, texto = f"{len(lista)} e-mails novos", ", ".join((m["de_nome"] or m["de_email"]) for m in lista[:3])
        try:
            subprocess.Popen(["notify-send", "--app-name=Mail Box", "--icon=duiaos-mailbox", titulo, texto],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

    # ------------------------------------------------------------ pastas e lista
    def _lista_pastas(self):
        saida = []
        contas = self.contas.lista
        if len(contas) > 1:
            total = sum(p["nao_lidas"] for p in self.banco.pastas() if p["papel"] == "entrada")
            saida.append({"id": -1, "conta": "", "nome": "Todas as caixas de entrada", "papel": "entrada", "nao_lidas": total,
                          "tipo": "pasta", "nivel": 0})
        for conta in contas:
            saida.append({"id": -100, "conta": conta["id"], "nome": conta["email"], "papel": "", "nao_lidas": 0,
                          "tipo": "conta", "nivel": 0, "estado": self._estados.get(conta["id"], ""),
                          "erro": self._erros.get(conta["id"], "")})
            for p in self.banco.pastas(conta["id"]):
                saida.append({"id": p["id"], "conta": conta["id"], "nome": p["nome"], "papel": p["papel"],
                              "nao_lidas": p["nao_lidas"], "tipo": "pasta", "nivel": 1})
        return saida

    def _lista_mensagens(self):
        if self._pasta == -1:
            lista = self.banco.mensagens(busca=self._busca, papel="entrada")
        else:
            lista = self.banco.mensagens(self._pasta, busca=self._busca)
        contas = {c["id"]: c for c in self.contas.lista}
        for m in lista:
            m["email_conta"] = contas.get(m["conta"], {}).get("email", "")
        return lista

    @Slot(int)
    def escolherPasta(self, id_pasta):
        self._pasta = id_pasta
        self._leitura = {}
        self.mensagensMudaram.emit()
        self.leituraMudou.emit()
        self.pastasMudaram.emit()
        pasta = self.banco.pasta(id_pasta) if id_pasta > 0 else None
        if pasta and not DEMONSTRACAO:
            self.motor.pedir(pasta["conta"], "sincronizar_pasta", id_pasta=id_pasta)

    @Slot(str)
    def buscar(self, texto):
        self._busca = texto
        self.mensagensMudaram.emit()

    @Slot()
    def atualizar(self):
        if not DEMONSTRACAO:
            self.motor.sincronizar_todas()

    # ------------------------------------------------------------ leitura
    def _bruto(self, m):
        return self.banco.ler_corpo(m["conta"], m["pasta"], m["uid"])

    @Slot(int)
    def abrirMensagem(self, id_mensagem, permitir_remoto=False):
        m = self.banco.mensagem(id_mensagem)
        if not m:
            self._leitura = {}
            self.leituraMudou.emit()
            return
        bruto = self._bruto(m)
        leitura = {"id": m["id"], "conta": m["conta"], "assunto": m["assunto"] or "(sem assunto)", "de_nome": m["de_nome"],
                   "de_email": m["de_email"], "para": m["para"], "cc": m["cc"], "data": m["data"], "lida": bool(m["lida"]),
                   "sinalizada": bool(m["sinalizada"]), "anexos": [], "html": "", "bloqueadas": 0, "carregando": bruto is None,
                   "remoto": permitir_remoto}
        if bruto is None:
            if not DEMONSTRACAO:
                self.motor.pedir(m["conta"], "baixar", id_mensagem=id_mensagem)
        else:
            msg = mensagem.ler(bruto)
            escuro = bool(_aparencia_escura())
            leitura["html"], leitura["bloqueadas"] = mensagem.html_para_leitura(msg, permitir_remoto, escuro)
            leitura["anexos"] = mensagem.anexos(msg)
        self.interceptador.permitir = permitir_remoto
        self._leitura = leitura
        self.leituraMudou.emit()
        if not m["lida"] and not DEMONSTRACAO:
            self.motor.pedir(m["conta"], "marcar", id_mensagem=id_mensagem, campo="lida", valor=True)

    @Slot()
    def mostrarImagens(self):
        if self._leitura.get("id"):
            self.abrirMensagem(self._leitura["id"], True)

    @Slot(int, bool)
    def marcarLida(self, id_mensagem, valor):
        self._acao(id_mensagem, "marcar", campo="lida", valor=valor)

    @Slot(int, bool)
    def sinalizar(self, id_mensagem, valor):
        self._acao(id_mensagem, "marcar", campo="sinalizada", valor=valor)

    @Slot(int)
    def apagar(self, id_mensagem):
        self._acao(id_mensagem, "apagar")
        self._fechar_leitura(id_mensagem)

    @Slot(int)
    def arquivar(self, id_mensagem):
        m = self.banco.mensagem(id_mensagem)
        if not m:
            return
        destino = self.banco.pasta_por_papel(m["conta"], "arquivo")
        if not destino:
            self.aviso.emit("Esta conta não tem uma pasta de arquivo.")
            return
        self._acao(id_mensagem, "mover", id_destino=destino["id"])
        self._fechar_leitura(id_mensagem)

    @Slot(int, int)
    def moverPara(self, id_mensagem, id_pasta):
        self._acao(id_mensagem, "mover", id_destino=id_pasta)
        self._fechar_leitura(id_mensagem)

    def _acao(self, id_mensagem, acao, **dados):
        m = self.banco.mensagem(id_mensagem)
        if not m:
            return
        if DEMONSTRACAO:
            if acao == "marcar":
                self.banco.marcar(id_mensagem, **{dados["campo"]: dados["valor"]})
                self.mensagensMudaram.emit()
            return
        self.motor.pedir(m["conta"], acao, id_mensagem=id_mensagem, **dados)

    def _fechar_leitura(self, id_mensagem):
        if self._leitura.get("id") == id_mensagem:
            self._leitura = {}
            self.leituraMudou.emit()

    @Slot(int, int, result=str)
    def salvarAnexo(self, id_mensagem, indice):
        m = self.banco.mensagem(id_mensagem)
        bruto = self._bruto(m) if m else None
        if bruto is None:
            return ""
        msg = mensagem.ler(bruto)
        info = next((a for a in mensagem.anexos(msg) if a["indice"] == indice), None)
        conteudo = mensagem.conteudo_do_anexo(msg, indice)
        if info is None or conteudo is None:
            return ""
        pasta = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or Path.home())
        pasta.mkdir(parents=True, exist_ok=True)
        nome = Path(info["nome"]).name or "anexo"
        destino, n = pasta / nome, 2
        while destino.exists():
            destino, n = pasta / f"{Path(nome).stem} ({n}){Path(nome).suffix}", n + 1
        destino.write_bytes(conteudo)
        return str(destino)

    @Slot(int, int)
    def abrirAnexo(self, id_mensagem, indice):
        caminho = self.salvarAnexo(id_mensagem, indice)
        if caminho and not DEMONSTRACAO:
            subprocess.Popen(["xdg-open", caminho], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.aviso.emit(f"Anexo salvo em Downloads: {Path(caminho).name}")

    @Slot(str)
    def abrirLink(self, url):
        if url.startswith(("http://", "https://")) and not DEMONSTRACAO:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif url.startswith("mailto:"):
            self.escrever(ler_mailto(url))

    # ------------------------------------------------------------ escrever
    def escrever(self, campos, conta=""):
        campos = dict(campos)
        campos.setdefault("conta", conta or (self.contas.lista[0]["id"] if self.contas.lista else ""))
        campos.setdefault("id_respondida", 0)
        self.abrirEscrever.emit(campos)

    @Slot()
    def novaMensagem(self):
        conta = self._leitura.get("conta") or (self.banco.pasta(self._pasta) or {}).get("conta", "")
        self.escrever({"para": "", "cc": "", "assunto": "", "corpo": "", "em_resposta_a": "", "referencias": ""}, conta)

    @Slot(int, bool)
    def responder(self, id_mensagem, todos):
        m = self.banco.mensagem(id_mensagem)
        bruto = self._bruto(m) if m else None
        if bruto is None:
            return
        conta = self.contas.obter(m["conta"]) or {}
        campos = mensagem.rascunho_de_resposta(mensagem.ler(bruto), conta.get("email", ""), todos)
        campos["id_respondida"] = id_mensagem
        self.escrever(campos, m["conta"])

    @Slot(int)
    def encaminhar(self, id_mensagem):
        m = self.banco.mensagem(id_mensagem)
        bruto = self._bruto(m) if m else None
        if bruto is not None:
            self.escrever(mensagem.rascunho_de_encaminhamento(mensagem.ler(bruto)), m["conta"])

    @Slot("QVariantMap")
    def enviar(self, campos):
        conta = campos.get("conta")
        if not self.contas.obter(conta):
            self.falhaEnvio.emit("Escolha a conta que envia.")
            return
        if DEMONSTRACAO:
            self.enviada.emit()
            return
        anexos = [str(a).replace("file://", "") for a in campos.get("anexos", [])]
        self.motor.pedir(conta, "enviar", de_nome=(self.contas.obter(conta) or {}).get("nome", ""), para=campos.get("para", ""),
                         assunto=campos.get("assunto", ""), corpo=campos.get("corpo", ""), cc=campos.get("cc", ""),
                         cco=campos.get("cco", ""), anexos=anexos, em_resposta_a=campos.get("em_resposta_a", ""),
                         referencias=campos.get("referencias", ""), id_respondida=int(campos.get("id_respondida") or 0))

    # ------------------------------------------------------------ contas e wizard
    def _em_fundo(self, nome, funcao):
        def rodar():
            try:
                self._resultado.emit(nome, {"ok": True, "valor": funcao()})
            except servidores.ErroDeConta as erro:
                self._resultado.emit(nome, {"ok": False, "texto": str(erro)})
            except Exception as erro:  # noqa: BLE001
                self._resultado.emit(nome, {"ok": False, "texto": f"Erro inesperado: {type(erro).__name__}"})
        threading.Thread(target=rodar, daemon=True).start()

    def _tratar_resultado(self, nome, r):
        if nome == "descobrir":
            config, origem = r.get("valor") or (None, "")
            self.descoberto.emit(config or {}, origem or "")
        elif nome == "testar":
            self.testeConcluido.emit(bool(r.get("ok")), r.get("texto", ""))

    @Slot(str)
    def descobrir(self, email):
        if DEMONSTRACAO:
            chave = provedores.por_dominio(email.rpartition("@")[2])
            self.descoberto.emit(provedores.configuracao(chave, email) if chave else {}, "catalogo" if chave else "")
            return
        self._em_fundo("descobrir", lambda: autoconfig.descobrir(email))

    @Slot(str, result="QVariantMap")
    def provedorDe(self, email):
        chave = provedores.por_dominio(email.rpartition("@")[2])
        return provedores.configuracao(chave, email) if chave else {}

    @Slot(str, str, result="QVariantMap")
    def configuracaoDoProvedor(self, chave, email):
        return provedores.configuracao(chave, email) if chave in provedores.PROVEDORES else {}

    @Slot(str, str, "QVariantMap")
    def testarConta(self, email, senha, config):
        conta = {"entrada": config["entrada"], "saida": config["saida"],
                 "verificar_certificado": config.get("verificar_certificado", True)}
        if DEMONSTRACAO:
            self.testeConcluido.emit(True, "")
            return

        def testar():
            servidores.testar_entrada(conta, senha)
            servidores.testar_saida(conta, senha)
        self._em_fundo("testar", testar)

    @Slot(str, str, str, "QVariantMap", result=str)
    def salvarConta(self, nome, email, senha, config):
        conta = self.contas.adicionar(nome, email, dict(config))
        self.cofre.guardar(conta["id"], "entrada", senha)
        registrar("info", "mailbox_conta", provedor=conta["provedor"], tipo=conta["entrada"]["tipo"])
        self.contasMudaram.emit()
        self.pastasMudaram.emit()
        if not DEMONSTRACAO:
            self.motor.pedir(conta["id"], "sincronizar")
        if not self.cofre.persistente:
            self.aviso.emit("O cofre do sistema não está disponível: a senha vale só até fechar o Mail Box.")
        return conta["id"]

    @Slot(str)
    def removerConta(self, id_conta):
        self.motor.remover(id_conta)
        self.cofre.apagar(id_conta)
        self.banco.remover_conta(id_conta)
        self.contas.remover(id_conta)
        registrar("info", "mailbox_conta_removida")
        if self._pasta != -1:
            self._pasta = -1
        self._leitura = {}
        self.contasMudaram.emit()
        self.pastasMudaram.emit()
        self.mensagensMudaram.emit()
        self.leituraMudou.emit()

    @Slot(str, str, str)
    def editarConta(self, id_conta, nome, assinatura):
        self.contas.atualizar(id_conta, nome=nome, assinatura=assinatura)
        self.contasMudaram.emit()

    @Slot(str)
    def abrirAjuda(self, url):
        if url.startswith("https://") and not DEMONSTRACAO:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _lista_contas(self):
        return [{"id": c["id"], "nome": c.get("nome", ""), "email": c["email"], "nome_provedor": c.get("nome_provedor", ""),
                 "assinatura": c.get("assinatura", ""), "tipo": c["entrada"]["tipo"], "servidor": c["entrada"]["host"],
                 "estado": self._estados.get(c["id"], ""), "erro": self._erros.get(c["id"], "")}
                for c in self.contas.lista]

    @Slot(result="QVariantList")
    def destaques(self):
        return [{"id": k, "nome": provedores.PROVEDORES[k]["nome"]} for k in provedores.DESTAQUES]

    # ------------------------------------------------------------ para o QML
    contasLista = Property("QVariantList", _lista_contas, notify=contasMudaram)
    pastas = Property("QVariantList", _lista_pastas, notify=pastasMudaram)
    mensagens = Property("QVariantList", _lista_mensagens, notify=mensagensMudaram)
    leitura = Property("QVariantMap", lambda self: self._leitura, notify=leituraMudou)
    pastaAtual = Property(int, lambda self: self._pasta, notify=pastasMudaram)
    sincronizando = Property(bool, lambda self: any(bool(v) for v in self._estados.values()), notify=estadoMudou)
    estado = Property(str, lambda self: next((v for v in self._estados.values() if v), ""), notify=estadoMudou)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)
    versao = Property(str, lambda self: VERSAO, constant=True)

    @Property("QVariantList", notify=pastasMudaram)
    def pastasParaMover(self):
        m = self.banco.mensagem(self._leitura.get("id", 0)) if self._leitura else None
        if not m:
            return []
        return [{"id": p["id"], "nome": p["nome"]} for p in self.banco.pastas(m["conta"]) if p["id"] != m["pasta"]]

    @Property(str, notify=pastasMudaram)
    def nomePastaAtual(self):
        if self._pasta == -1:
            return "Entrada" if len(self.contas.lista) <= 1 else "Todas as caixas de entrada"
        p = self.banco.pasta(self._pasta)
        return p["nome"] if p else ""


def _aparencia_escura():
    try:
        import interface
        return interface.aparencia().property("escuro")
    except Exception:  # noqa: BLE001
        return False


def criar_perfil_leitura():
    """Perfil sem disco para mostrar os e-mails; bloqueia toda requisição de rede até a pessoa liberar."""
    from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
    from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

    class Bloqueio(QWebEngineUrlRequestInterceptor):
        permitir = False

        def interceptRequest(self, info):
            esquema = info.requestUrl().scheme()
            if esquema in ("http", "https", "ws", "wss", "ftp") and not self.permitir:
                info.block(True)

    perfil = QQuickWebEngineProfile()
    interceptador = Bloqueio()
    perfil.setUrlRequestInterceptor(interceptador)
    return perfil, interceptador


# -------------------------------------------------------------------------------- demonstração
def preparar_demonstracao(caixa):
    agora = time.time()
    contas = caixa.contas
    pessoal = contas.adicionar("Gustavo", "gustavo@gmail.com", provedores.configuracao("gmail", "gustavo@gmail.com"))
    trabalho = contas.adicionar("Gustavo", "gustavo@duiaos.com.br", provedores.configuracao("hostinger", "gustavo@duiaos.com.br"))
    banco = caixa.banco
    for conta in (pessoal, trabalho):
        for caminho, papel in (("INBOX", "entrada"), ("Sent", "enviados"), ("Drafts", "rascunhos"), ("Trash", "lixeira"),
                               ("Junk", "spam")):
            banco.gravar_pasta(conta["id"], caminho, caixa_postal.NOMES_PAPEIS[papel], papel)
    banco.gravar_pasta(trabalho["id"], "Projetos/DuiaOS", "Projetos › DuiaOS")
    exemplos = [
        (trabalho, "Marina Costa", "marina@estudio.invalid", "Identidade visual do DuiaOS — versão final",
         "<div style='font-family:sans-serif'><h2 style='color:#2E6BE6'>Versão final aprovada</h2><p>Oi, Gustavo!</p>"
         "<p>Segue a versão final da identidade visual, com a paleta Aurora e os novos ícones de traço fino. "
         "Os arquivos estão no anexo, em SVG e PNG.</p><p><img src='https://rastreio.invalid/pixel.gif' width='1'></p>"
         "<p>Qualquer ajuste, me avise.<br>Abraço,<br><b>Marina</b></p></div>", 0.3, False, True),
        (pessoal, "Banco Exemplo", "avisos@banco.invalid", "Sua fatura de novembro chegou",
         None, 2.1, False, False),
        (trabalho, "Equipe GitHub", "noreply@github.invalid", "[gustavoduia/duiaos] Build da ISO 0.3.1 concluído",
         None, 4.5, True, False),
        (pessoal, "Ana Ribeiro", "ana@exemplo.invalid", "Fotos da viagem 📷", None, 8, True, True),
        (trabalho, "Ricardo Alves", "ricardo@parceiro.invalid", "Proposta de parceria para o DuiaOS",
         None, 26, True, False),
        (pessoal, "Loja Online", "pedidos@loja.invalid", "Seu pedido foi enviado", None, 30, True, False),
        (trabalho, "Calendário", "agenda@duiaos.invalid", "Lembrete: reunião de planejamento amanhã às 10h", None, 50, True, False),
    ]
    textos = {"Sua fatura de novembro chegou": "Olá, Gustavo. A fatura de novembro já está disponível no aplicativo.",
              "[gustavoduia/duiaos] Build da ISO 0.3.1 concluído": "O workflow construir-iso terminou com sucesso em 42 minutos.",
              "Fotos da viagem 📷": "Oi! Separei as melhores fotos da viagem. Estão no anexo. Beijos!",
              "Proposta de parceria para o DuiaOS": "Gustavo, gostaríamos de conversar sobre levar o DuiaOS para os nossos notebooks.",
              "Seu pedido foi enviado": "O seu pedido saiu para entrega e chega em até 3 dias úteis.",
              "Lembrete: reunião de planejamento amanhã às 10h": "Pauta: Ora, Mail Box e a próxima versão do Wise."}
    for i, (conta, nome, email_de, assunto, html, horas, lida, anexo) in enumerate(exemplos):
        from email.message import EmailMessage
        from email.utils import formatdate, make_msgid
        msg = EmailMessage()
        msg["From"] = f"{nome} <{email_de}>"
        msg["To"] = conta["email"]
        msg["Subject"] = assunto
        msg["Date"] = formatdate(agora - horas * 3600, localtime=True)
        msg["Message-ID"] = make_msgid(domain="exemplo.invalid")
        msg.set_content(textos.get(assunto, "Oi, Gustavo!"))
        if html:
            msg.add_alternative(html, subtype="html")
        if anexo:
            msg.add_attachment(b"%PDF-1.4 exemplo", maintype="application", subtype="pdf",
                               filename="identidade-visual.pdf" if conta is trabalho else "fotos.zip")
        bruto = msg.as_bytes()
        pasta = banco.pasta_por_papel(conta["id"], "entrada")
        r = mensagem.resumo(bruto, i + 1, {"\\Seen"} if lida else set())
        r["sinalizada"] = i == 4
        banco.gravar_mensagem(conta["id"], pasta["id"], r, bruto)
    for p in banco.pastas():
        banco.recontar(p["id"])


def main():
    captura = argumento("--captura")
    pedido_mailto = next((a for a in sys.argv[1:] if a.startswith("mailto:")), "")
    if not DEMONSTRACAO:
        trava = open(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-mailbox.lock", "w")
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            ARQUIVO_PEDIDO.write_text(pedido_mailto or "mostrar")
            sys.exit(0)
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QtWebEngineQuick.initialize()
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import interface

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Mail Box")
    app.setOrganizationName("DuiaOS")
    app.setDesktopFileName("duiaos-mailbox")
    interface.ligar_registro("duiaos-mailbox")
    registrar("info", "mailbox_inicio", versao=VERSAO)

    motor = QQmlApplicationEngine()
    interface.preparar(motor)
    perfil, interceptador = criar_perfil_leitura()
    caixa = MailBox(perfil, interceptador)
    pagina = argumento("--pagina", "caixa")
    if DEMONSTRACAO and pagina != "wizard":
        preparar_demonstracao(caixa)
    contexto = motor.rootContext()
    contexto.setContextProperty("caixa", caixa)
    contexto.setContextProperty("perfilLeitura", perfil)
    contexto.setContextProperty("capturaArquivo", captura)
    contexto.setContextProperty("paginaDemonstracao", pagina if DEMONSTRACAO else "")
    import menu_do_app
    menu = menu_do_app.criar("mailbox", [])
    contexto.setContextProperty("menuDoApp", menu)
    if DEMONSTRACAO and "--escuro" in sys.argv:
        interface.aparencia().setProperty("escuro", True)
    motor.load(PASTA / "JanelaMailBox.qml")
    if not motor.rootObjects():
        sys.exit(1)
    if DEMONSTRACAO and pagina == "caixa":
        primeira = caixa.banco.mensagens(papel="entrada")
        if primeira:
            caixa.abrirMensagem(primeira[0]["id"])
    if DEMONSTRACAO and pagina == "escrever":
        caixa.escrever({"para": "marina@estudio.invalid", "cc": "", "assunto": "Re: Identidade visual do DuiaOS — versão final",
                        "corpo": "Oi, Marina!\n\nFicou ótimo. Vou levar para a próxima versão.\n\nAbraço,\nGustavo",
                        "em_resposta_a": "", "referencias": ""})
    if pedido_mailto:
        caixa.escrever(ler_mailto(pedido_mailto))

    # Outro "duiaos-mailbox" aberto: mostra esta janela (ou abre o mailto pedido)
    def ver_pedido():
        if ARQUIVO_PEDIDO.exists():
            conteudo = ARQUIVO_PEDIDO.read_text().strip()
            ARQUIVO_PEDIDO.unlink(missing_ok=True)
            if conteudo.startswith("mailto:"):
                caixa.escrever(ler_mailto(conteudo))
            else:
                janela = motor.rootObjects()[0]
                janela.raise_()
                janela.requestActivate()
    relogio_pedido = QTimer(interval=700, timeout=ver_pedido)
    if not DEMONSTRACAO:
        relogio_pedido.start()
    caixa.iniciar()
    codigo = app.exec()
    relogio_pedido.stop()
    caixa.motor.encerrar()
    # As janelas QML usam "caixa": o motor do QML sai antes dele
    for janela in motor.rootObjects():
        janela.setProperty("visible", False)
    del motor
    # Ordem de saída do Qt WebEngine: janelas, depois o perfil, por último o aplicativo (sem isso, falha ao fechar)
    perfil.setUrlRequestInterceptor(None)
    del caixa, interceptador, perfil
    del app
    sys.exit(codigo)


if __name__ == "__main__":
    main()
