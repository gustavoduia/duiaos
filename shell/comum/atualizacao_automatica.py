"""DuiaOS — o que a sessão mostra da atualização automática (ADR 058): o ícone ao lado do relógio e
os avisos. Quem procura, baixa e instala é o sistema (agente/automatica.py, como root); aqui só se lê
o que ele deixou em /var/lib/duiaos/atualizacoes/estado.json e o modo em /etc/duiaos/atualizacoes.conf.

Os modos e os caminhos repetem os do agente de propósito: são pacotes diferentes (duiaos-shell e
duiaos-agente), e a sessão não pode depender do código do agente.
"""
import configparser
import json
import time
from pathlib import Path

MODOS = ("desativado", "avisar", "baixar", "instalar-avisando", "instalar")
MODO_PADRAO = "baixar"
CONF = Path("/etc/duiaos/atualizacoes.conf")
ESTADO = Path("/var/lib/duiaos/atualizacoes/estado.json")

NOMES = {
    "desativado": "Desativada",
    "avisar": "Só avisar quando houver atualizações",
    "baixar": "Avisar e baixar, sem instalar",
    "instalar-avisando": "Avisar, baixar e instalar",
    "instalar": "Baixar e instalar sem avisar",
}
EXPLICACOES = {
    "desativado": "O DuiaOS não procura atualizações sozinho. Use Procurar quando quiser.",
    "avisar": "O DuiaOS procura a cada hora e avisa quando houver atualizações. Você decide quando baixar e instalar.",
    "baixar": "O DuiaOS procura, avisa e já deixa as atualizações baixadas. Instalar fica com você, e é mais rápido.",
    "instalar-avisando": "O DuiaOS procura, baixa e instala sozinho, e avisa quando encontra e quando termina.",
    "instalar": "O DuiaOS procura, baixa e instala sozinho, sem avisos. Só avisa se for preciso reiniciar.",
}


def ler_modo(conf=CONF):
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(conf, encoding="utf-8")
    except (configparser.Error, OSError):
        return MODO_PADRAO
    modo = config.get("automatica", "modo", fallback=MODO_PADRAO)
    return modo if modo in MODOS else MODO_PADRAO


def ler_estado(arquivo=ESTADO):
    try:
        dados = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def momento_do_inicio(uptime="/proc/uptime"):
    """Quando o computador ligou (segundos desde 1970)."""
    try:
        return time.time() - float(Path(uptime).read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return 0.0


def _quantas(n):
    return "1 atualização" if n == 1 else f"{n} atualizações"


def avisos(estado, modo, avisados, inicio_do_computador, inicio_da_sessao):
    """O que a sessão mostra agora:
    {"icone": bool, "dica": texto do ícone, "notificacoes": [{"chave", "titulo", "texto"}]}.
    avisados: {"disponiveis": assinatura já avisada, "instalacao": quando da instalação já avisada}.
    A chave de cada notificação vai para `avisados` depois de enviada (cada coisa é avisada uma vez)."""
    resultado = {"icone": False, "dica": "", "notificacoes": []}
    instalacao = estado.get("instalacao") or {}
    quando = instalacao.get("quando", 0)
    reiniciar = instalacao.get("reiniciar", "nao") if instalacao.get("resultado") == "ok" else "nao"
    # Reiniciar pendente: a instalação foi depois de o computador (ou a sessão) começar
    falta_reiniciar = (reiniciar == "computador" and quando > inicio_do_computador) or \
                      (reiniciar == "sessao" and quando > inicio_da_sessao)
    disponiveis = int(estado.get("disponiveis") or 0)
    avisa_disponiveis = modo in ("avisar", "baixar", "instalar-avisando")

    if falta_reiniciar:
        resultado["icone"] = True
        resultado["dica"] = ("Reinicie o computador para concluir a atualização" if reiniciar == "computador"
                             else "Saia e entre de novo na sessão para concluir a atualização")
    elif disponiveis and avisa_disponiveis:
        resultado["icone"] = True
        resultado["dica"] = (f"{_quantas(disponiveis)} baixada{'s' if disponiveis > 1 else ''}, pronta{'s' if disponiveis > 1 else ''} para instalar"
                             if estado.get("baixadas") else f"{_quantas(disponiveis)} disponíve{'is' if disponiveis > 1 else 'l'}")

    if disponiveis and avisa_disponiveis and estado.get("assinatura") and estado["assinatura"] != avisados.get("disponiveis"):
        partes = [f"{_quantas(disponiveis)} para o seu computador"]
        if estado.get("duiaos"):
            partes.append("inclui novidades do DuiaOS")
        if modo == "instalar-avisando":
            fim = "O DuiaOS vai instalar sozinho; clique para ver o que muda."
        elif estado.get("baixadas"):
            fim = "Já baixadas: clique para ver e instalar."
        else:
            fim = "Clique para ver e instalar."
        resultado["notificacoes"].append({"chave": ("disponiveis", estado["assinatura"]),
                                          "titulo": "Atualizações disponíveis",
                                          "texto": ", ".join(partes) + ". " + fim})

    if quando and quando != avisados.get("instalacao") and instalacao.get("automatica") and instalacao.get("resultado") == "ok":
        texto_reinicio = {"computador": "Reinicie o computador quando puder para concluir.",
                          "sessao": "Saia e entre de novo na sessão quando puder para concluir.",
                          "nao": "Não é preciso reiniciar."}[reiniciar]
        if modo == "instalar-avisando":
            resultado["notificacoes"].append({"chave": ("instalacao", quando), "titulo": "Atualizações instaladas",
                                              "texto": f"{_quantas(instalacao.get('quantidade', 0))} instalada{'s' if instalacao.get('quantidade', 0) != 1 else ''}. {texto_reinicio}"})
        elif modo == "instalar" and falta_reiniciar:
            resultado["notificacoes"].append({"chave": ("instalacao", quando), "titulo": "Atualização instalada",
                                              "texto": texto_reinicio})
    elif quando and quando != avisados.get("instalacao") and instalacao.get("automatica") and instalacao.get("resultado") == "erro" \
            and modo in ("instalar-avisando", "instalar"):
        resultado["notificacoes"].append({"chave": ("instalacao", quando), "titulo": "A atualização automática não terminou",
                                          "texto": "Clique para ver o motivo e tentar de novo."})
    return resultado
