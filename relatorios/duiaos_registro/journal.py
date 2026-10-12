"""Envio ao journal do systemd pelo protocolo nativo (sem dependências).

Cada registro é um datagrama no socket /run/systemd/journal/socket com campos "NOME=valor". Valores com
quebra de linha (rastros) vão no formato binário: NOME, quebra, tamanho em 64 bits little-endian, valor.
Referência: systemd "Native Journal Protocol". Sem o socket (testes, outro sistema), escreve no stderr.
"""
import os
import re
import socket
import struct
import sys

SOCKET = os.environ.get("DUIAOS_JOURNAL_SOCKET", "/run/systemd/journal/socket")
LIMITE_CAMPO = 48 * 1024           # o datagrama inteiro precisa caber; rastros enormes são cortados
NOME_VALIDO = re.compile(r"^[A-Z0-9][A-Z0-9_]{0,63}$")


def montar(campos):
    partes = []
    for nome, valor in campos.items():
        if not NOME_VALIDO.match(nome):
            continue
        dados = str(valor).encode("utf-8", "replace")[:LIMITE_CAMPO]
        if b"\n" in dados:
            partes.append(nome.encode() + b"\n" + struct.pack("<Q", len(dados)) + dados + b"\n")
        else:
            partes.append(nome.encode() + b"=" + dados + b"\n")
    return b"".join(partes)


def enviar(campos):
    pacote = montar(campos)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as conexao:
            conexao.sendto(pacote, SOCKET)
        return True
    except OSError:
        try:
            sys.stderr.write(f"<{campos.get('PRIORITY', '6')}>{campos.get('SYSLOG_IDENTIFIER', '')}: "
                             f"{campos.get('MESSAGE', '')}\n")
            if campos.get("DUIAOS_RASTRO"):
                sys.stderr.write(campos["DUIAOS_RASTRO"])
        except (OSError, ValueError):
            pass
        return False
