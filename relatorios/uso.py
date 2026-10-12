"""Uso agregado de "Ajude a melhorar o DuiaOS" (ADR 040, fase 2; nível "erros_e_uso" e acima).

Como o eos-metrics do Endless OS e o KUserFeedback do KDE: só eventos de uma LISTA CONHECIDA, com campos
de valores fechados, e somados neste computador antes de sair. Nunca vai texto livre, hora exata de cada
uso, nome de arquivo ou de pessoa: o relatório leva só "quantas vezes" por valor, no período da coleta.

Programas registram com o duiaos_registro:
    registro.info("uso.aplicativo_aberto", "Aplicativo aberto", aplicativo="firefox-esr.desktop", por="ilha")

Evento fora da lista, campo desconhecido ou valor fora do formato → descartado (contado em "descartados").
"""
import os
import re
from pathlib import Path

PASTA_APLICATIVOS = Path(os.environ.get("DUIAOS_APLICATIVOS", "/usr/share/applications"))
_ID_DESKTOP = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,78}\.desktop$")
_FERRAMENTA = re.compile(r"^[a-z][a-z0-9_]{1,40}$")
_MODELO = re.compile(r"^[a-z0-9][a-z0-9._-]{0,40}(:[a-z0-9._-]{1,20})?$")


def _aplicativo(valor):
    """Só aplicativos instalados pelo sistema (um .desktop em /usr/share/applications). Atalhos criados pela
    pessoa (~/.local/share/applications) podem ter nomes pessoais: viram "outro"."""
    if not isinstance(valor, str) or not _ID_DESKTOP.match(valor):
        return None
    return valor if (PASTA_APLICATIVOS / valor).is_file() else "outro"


def _um_de(*valores):
    permitidos = set(valores)
    return lambda valor: valor if valor in permitidos else None


def _formato(expressao):
    return lambda valor: valor if isinstance(valor, str) and expressao.match(valor) else None


# evento → {campo: validador}. Para acrescentar um evento: linha aqui + teste + documentação
# ("O que é enviado" na documentação para usuários).
EVENTOS = {
    "uso.aplicativo_aberto": {"aplicativo": _aplicativo, "por": _um_de("ilha", "central", "barra", "wise")},
    "uso.central_de_aplicativos": {"por": _um_de("botao", "atalho")},
    "uso.menu_de_energia": {"acao": _um_de("bloquear", "encerrar", "suspender", "reiniciar", "windows", "desligar")},
    "uso.wise_pedido": {"provedor": _um_de("local", "gemini")},
    "uso.wise_ferramenta": {"ferramenta": _formato(_FERRAMENTA)},
    "uso.wise_reclamacao": {},
    "uso.modelo_ativo": {"modelo": _formato(_MODELO)},
    "uso.ajude_a_melhorar": {"nivel": _um_de("desligado", "erros", "erros_e_uso")},
}


def validar(evento, dados):
    """Campos permitidos do evento, ou None se o evento não está na lista."""
    campos = EVENTOS.get(evento)
    if campos is None:
        return None
    limpos = {}
    for nome, validador in campos.items():
        valor = validador((dados or {}).get(nome))
        if valor is not None:
            limpos[nome] = valor
    return limpos


def agregar(registros):
    """registros: [(evento, dados)] → {"eventos": {evento: {"total": n, "por": {campo: {valor: n}}}},
    "descartados": n}. Vazio se não houve uso."""
    eventos, descartados = {}, 0
    for evento, dados in registros:
        campos = validar(evento, dados if isinstance(dados, dict) else {})
        if campos is None:
            descartados += 1
            continue
        soma = eventos.setdefault(evento, {"total": 0, "por": {}})
        soma["total"] += 1
        for nome, valor in campos.items():
            contagem = soma["por"].setdefault(nome, {})
            contagem[valor] = contagem.get(valor, 0) + 1
    if not eventos and not descartados:
        return {}
    return {"eventos": dict(sorted(eventos.items())), "descartados": descartados}
