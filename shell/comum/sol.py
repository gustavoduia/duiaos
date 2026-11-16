"""DuiaOS — nascer e pôr do sol, para o modo Automático (claro de dia, escuro à noite; ADR 056).

Sem pedir a localização e sem internet: o lugar vem do fuso horário do computador. A tabela de
fusos do sistema (/usr/share/zoneinfo/zone1970.tab) traz as coordenadas da cidade de cada fuso
(America/Sao_Paulo → São Paulo). O erro de usar a cidade do fuso em vez da cidade da pessoa é de
alguns minutos a, no pior caso, cerca de uma hora — pouco para decidir entre claro e escuro.

O cálculo é o da NOAA (equação do nascer do sol), com precisão de um ou dois minutos.
"""
import datetime
import math
import os
import re
from pathlib import Path

TABELAS = (Path("/usr/share/zoneinfo/zone1970.tab"), Path("/usr/share/zoneinfo/zone.tab"))
# Sem tabela ou sem fuso reconhecido: dia das 6h às 18h
NASCER_PADRAO, POR_PADRAO = datetime.time(6, 0), datetime.time(18, 0)


def fuso_do_sistema(localtime="/etc/localtime", arquivo="/etc/timezone"):
    """Nome do fuso (ex.: America/Sao_Paulo), ou "" se não der para saber."""
    try:
        destino = os.path.realpath(localtime)
        if "/zoneinfo/" in destino:
            return destino.split("/zoneinfo/", 1)[1]
    except OSError:
        pass
    try:
        return Path(arquivo).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _graus(texto):
    """±DDMM, ±DDMMSS, ±DDDMM ou ±DDDMMSS (ISO 6709) → graus decimais."""
    sinal = -1 if texto[0] == "-" else 1
    numeros = texto[1:]
    graus = 2 if len(numeros) in (4, 6) else 3
    valor = int(numeros[:graus]) + int(numeros[graus:graus + 2]) / 60
    if len(numeros) > graus + 2:
        valor += int(numeros[graus + 2:graus + 4]) / 3600
    return sinal * valor


def coordenadas(fuso, tabelas=TABELAS):
    """(latitude, longitude) da cidade do fuso, ou None."""
    for tabela in tabelas:
        try:
            linhas = Path(tabela).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for linha in linhas:
            campos = linha.split("\t")
            if len(campos) >= 3 and not linha.startswith("#") and campos[2] == fuso:
                partes = re.fullmatch(r"([+-]\d{4,6})([+-]\d{5,7})", campos[1])
                if partes:
                    return _graus(partes.group(1)), _graus(partes.group(2))
    return None


def nascer_e_por(dia, latitude, longitude):
    """Horas do nascer e do pôr do sol em UTC (datetime com fuso), ou None nos dias sem um deles
    (perto dos polos)."""
    n = dia.timetuple().tm_yday
    gama = 2 * math.pi / 365 * (n - 1 + 0.5)
    equacao = 229.18 * (0.000075 + 0.001868 * math.cos(gama) - 0.032077 * math.sin(gama)
                        - 0.014615 * math.cos(2 * gama) - 0.040849 * math.sin(2 * gama))
    declinacao = (0.006918 - 0.399912 * math.cos(gama) + 0.070257 * math.sin(gama)
                  - 0.006758 * math.cos(2 * gama) + 0.000907 * math.sin(2 * gama)
                  - 0.002697 * math.cos(3 * gama) + 0.00148 * math.sin(3 * gama))
    lat = math.radians(latitude)
    cosseno = (math.cos(math.radians(90.833)) / (math.cos(lat) * math.cos(declinacao))
               - math.tan(lat) * math.tan(declinacao))
    if not -1 <= cosseno <= 1:
        return None
    angulo = math.degrees(math.acos(cosseno))
    meia_noite = datetime.datetime(dia.year, dia.month, dia.day, tzinfo=datetime.timezone.utc)
    nascer = meia_noite + datetime.timedelta(minutes=720 - 4 * (longitude + angulo) - equacao)
    por = meia_noite + datetime.timedelta(minutes=720 - 4 * (longitude - angulo) - equacao)
    return nascer, por


def e_noite(agora=None, fuso=None, tabelas=TABELAS):
    """True se, na hora local `agora`, o sol já se pôs (ou ainda não nasceu) no lugar do fuso."""
    agora = agora or datetime.datetime.now().astimezone()
    if agora.tzinfo is None:
        agora = agora.astimezone()
    lugar = coordenadas(fuso if fuso is not None else fuso_do_sistema(), tabelas)
    if lugar:
        # O dia local pode cair em dois dias UTC: confere o de hoje e os vizinhos
        for desvio in (0, -1, 1):
            horas = nascer_e_por(agora.date() + datetime.timedelta(days=desvio), *lugar)
            if horas and horas[0] <= agora <= horas[1]:
                return False
        if any(nascer_e_por(agora.date() + datetime.timedelta(days=d), *lugar) for d in (0, -1, 1)):
            return True
    hora = agora.time()
    return not NASCER_PADRAO <= hora < POR_PADRAO
