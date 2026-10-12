"""duiaos_registro — o jeito único de os programas do DuiaOS registrarem o que acontece (ADR 040).

Tudo vai para o journal do systemd (o registro do sistema, como nas outras distribuições), com campos
padronizados que o coletor (duiaos-relatorios) e o `journalctl` entendem:

  SYSLOG_IDENTIFIER   programa (ex.: duiaos-barra-de-recursos, duiaos-wise)
  PRIORITY            0 emergência … 3 erro, 4 aviso, 6 informação, 7 depuração
  DUIAOS_COMPONENTE   o mesmo nome do programa
  DUIAOS_EVENTO       código estável do evento: "falha", "wise.tarefa", "ia.modelo_carregado"…
  DUIAOS_DADOS        detalhes em JSON (já sem segredos)
  DUIAOS_ASSINATURA   nas falhas: identifica falhas iguais em computadores diferentes
  DUIAOS_RASTRO       nas falhas: o rastro (traceback) completo
  MESSAGE_ID          eventos do catálogo (journalctl -x mostra a explicação)

Uso:
    import duiaos_registro as registro
    registro.instalar_ganchos("duiaos-barra-de-recursos")   # falhas não tratadas viram registro
    registro.info("ia.modelo_carregado", "Modelo carregado", modelo="qwen3.5:4b", segundos=4.2)
    registro.aviso("wise.argumento_inventado", "Cidade não dita pela pessoa", ferramenta="definir_cidade")
    try: ...
    except Exception: registro.falha("ao abrir a Central")

Sem journal (testes, outro sistema), escreve no stderr. Nunca levanta exceção.
"""
import hashlib
import json
import os
import re
import sys
import threading
import traceback

from . import journal
from .privacidade import limpar_segredos

__all__ = ["ligar", "registrar", "info", "aviso", "erro", "falha", "instalar_ganchos", "instalar_no_qt", "nivel",
           "assinatura", "NIVEIS", "limpar_segredos"]

EMERGENCIA, ALERTA, CRITICO, ERRO, AVISO, NOTA, INFO, DEPURACAO = range(8)
ARQUIVO_CONFIG = os.environ.get("DUIAOS_RELATORIOS_CONFIG", "/etc/duiaos/relatorios.conf")
# Níveis de "Ajude a melhorar o DuiaOS" (o que pode sair do computador)
NIVEIS = ("nao_escolhido", "desligado", "erros", "erros_e_uso", "desenvolvimento")
ID_FALHA = "0b0f983a3fad41bb9a9730053146311a"       # MESSAGE_ID do catálogo: falha de um programa
_componente = os.path.basename(sys.argv[0] or "python3") or "python3"


def nivel():
    """Nível escolhido pela pessoa. Componentes que guardam conteúdo pessoal (ex.: o texto das conversas do
    Wise) só o registram no nível "desenvolvimento"."""
    try:
        with open(ARQUIVO_CONFIG, encoding="utf-8") as arquivo:
            for linha in arquivo:
                chave, _, valor = linha.partition("=")
                if chave.strip() == "nivel" and valor.strip() in NIVEIS:
                    return valor.strip()
    except OSError:
        pass
    return "nao_escolhido"


def registrar(prioridade, evento, mensagem, componente=None, message_id=None, **dados):
    componente = componente or _componente
    campos = {"MESSAGE": str(mensagem), "PRIORITY": str(int(prioridade)), "SYSLOG_IDENTIFIER": componente,
              "DUIAOS_COMPONENTE": componente, "DUIAOS_EVENTO": str(evento)}
    if message_id:
        campos["MESSAGE_ID"] = message_id
    for nome in ("assinatura", "rastro"):
        if nome in dados:
            campos[f"DUIAOS_{nome.upper()}"] = str(dados.pop(nome))
    quadro = sys._getframe(1)
    while quadro is not None and quadro.f_code.co_filename == __file__:
        quadro = quadro.f_back
    if quadro is not None:
        campos.update(CODE_FILE=quadro.f_code.co_filename, CODE_LINE=str(quadro.f_lineno),
                      CODE_FUNC=quadro.f_code.co_name)
    if dados:
        campos["DUIAOS_DADOS"] = json.dumps(limpar_segredos(dados), ensure_ascii=False, default=str)
    campos = {chave: limpar_segredos(valor) for chave, valor in campos.items()}
    journal.enviar(campos)


def info(evento, mensagem, **dados):
    registrar(INFO, evento, mensagem, **dados)


def aviso(evento, mensagem, **dados):
    registrar(AVISO, evento, mensagem, **dados)


def erro(evento, mensagem, **dados):
    registrar(ERRO, evento, mensagem, **dados)


def assinatura(componente, excecao, rastro):
    """Igual para a mesma falha em qualquer computador: componente, tipo do erro e as funções do rastro
    (sem números de linha, caminhos de usuário nem a mensagem, que muda com os dados)."""
    funcoes = []
    for quadro in traceback.extract_tb(rastro)[-6:] if rastro else []:
        arquivo = re.sub(r"^.*/(site|dist)-packages/", "", quadro.filename)
        arquivo = re.sub(r"^/home/[^/]+/", "~/", arquivo)
        funcoes.append(f"{arquivo}:{quadro.name}")
    base = "|".join([componente, type(excecao).__name__ if excecao else "?", *funcoes])
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def falha(onde="", excecao=None, rastro=None, componente=None, prioridade=ERRO, **dados):
    """Registra uma falha com o rastro completo. Dentro de um `except`, sem argumentos."""
    if excecao is None:
        excecao = sys.exc_info()[1]
    if rastro is None and excecao is not None:
        rastro = excecao.__traceback__
    componente = componente or _componente
    texto = "".join(traceback.format_exception(type(excecao), excecao, rastro)) if excecao else ""
    resumo = f"{type(excecao).__name__}: {excecao}" if excecao else "falha"
    registrar(prioridade, "falha", f"Falha{(' ' + onde) if onde else ''}: {resumo}", componente=componente,
              message_id=ID_FALHA, assinatura=assinatura(componente, excecao, rastro), rastro=texto,
              onde=onde, tipo=type(excecao).__name__ if excecao else "", **dados)


def instalar_ganchos(componente):
    """Chamar no início de cada programa: dá o nome do componente e registra as falhas não tratadas (como o
    apport faz no Ubuntu), sem mudar o que o programa já fazia com elas."""
    global _componente
    _componente = componente
    anterior = sys.excepthook

    def ao_falhar(tipo, valor, rastro):
        if not issubclass(tipo, KeyboardInterrupt):
            falha("não tratada", valor, rastro, prioridade=CRITICO)
        anterior(tipo, valor, rastro)
    sys.excepthook = ao_falhar
    anterior_thread = threading.excepthook

    def ao_falhar_na_thread(args):
        if args.exc_type is not SystemExit:
            nome = args.thread.name if args.thread else "?"
            falha(f"não tratada na thread {nome}", args.exc_value, args.exc_traceback, prioridade=CRITICO)
        anterior_thread(args)
    threading.excepthook = ao_falhar_na_thread


def instalar_no_qt(repeticoes=5):
    """Avisos e erros do Qt/QML (ex.: "TypeError: Cannot read property") viram registro. Chamar depois de
    criar a aplicação. Cada mensagem igual entra no máximo `repeticoes` vezes por execução."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    niveis = {QtMsgType.QtWarningMsg: AVISO, QtMsgType.QtCriticalMsg: ERRO, QtMsgType.QtFatalMsg: CRITICO}
    vistas = {}

    def tratar(tipo, contexto, mensagem):
        sys.stderr.write(mensagem + "\n")
        prioridade = niveis.get(tipo)
        if prioridade is None:
            return
        vistas[mensagem] = vistas.get(mensagem, 0) + 1
        if vistas[mensagem] <= repeticoes:
            registrar(prioridade, "qt", mensagem, arquivo_qml=getattr(contexto, "file", None),
                      linha_qml=getattr(contexto, "line", None))
    qInstallMessageHandler(tratar)


def ligar(componente, qt=False):
    """Atalho para o início de cada programa do DuiaOS: nome do componente, falhas não tratadas e (com
    qt=True, depois de criar a aplicação) os avisos do Qt/QML."""
    instalar_ganchos(componente)
    if qt:
        try:
            instalar_no_qt()
        except ImportError:
            pass
