"""DuiaOS — duiaos-agente: mover para a Lixeira da pessoa o que está numa pasta que ela não pode mudar (ADR 068).

Caso típico: uma pasta dentro da pasta pessoal criada por um programa que rodou como administrador (o
Docker de um build, um "sudo") pertence ao root; a pessoa é dona do arquivo, mas não da pasta, e no Linux
quem decide se um arquivo sai de uma pasta é o dono da pasta. O Finder do macOS, nesse caso, pede a senha
de administrador e move. Aqui é o mesmo: a interface pede ao agente (polkit
org.duiaos.agente.mover_para_lixeira) e ele move, como root, para a Lixeira DA PESSOA QUE PEDIU, que passa
a ser dona do que foi movido (para conseguir esvaziar a Lixeira depois).

Limites (conferidos aqui, não na interface):
- só caminhos absolutos DENTRO da pasta pessoal de quem pediu (o uid vem do D-Bus, nunca do pedido);
- nada em pastas escondidas (configurações dos programas), nada que já esteja na Lixeira;
- a pasta onde o item está é resolvida sem atalhos (realpath) e precisa continuar dentro da pasta pessoal;
  o próprio item não é seguido (um atalho vai para a Lixeira como atalho);
- nada de pontos de montagem, nem de outro disco (move sem copiar);
- no máximo 500 itens por pedido.
"""
import datetime
import os
import pwd
import stat
import urllib.parse
from pathlib import Path

LIMITE_ITENS = 500


class Recusado(Exception):
    """Pedido inválido: a mensagem vai para a pessoa."""


def _dentro(caminho, pasta):
    return caminho == pasta or caminho.startswith(pasta.rstrip("/") + "/")


def conferir(caminho, casa):
    """Caminho seguro (str) para mover, ou Recusado com o motivo."""
    if not isinstance(caminho, str) or not caminho or "\0" in caminho:
        raise Recusado("Caminho inválido.")
    if not caminho.startswith("/"):
        raise Recusado(f"O caminho precisa ser completo: {caminho[:80]}")
    caminho = os.path.normpath(caminho)
    casa = os.path.realpath(casa)
    pasta, nome = os.path.split(caminho)
    if nome in ("", ".", ".."):
        raise Recusado("Caminho inválido.")
    pasta_real = os.path.realpath(pasta)
    if not _dentro(pasta_real, casa):
        raise Recusado(f"Só dá para mover arquivos da sua pasta pessoal ({caminho[:120]}).")
    relativo = os.path.relpath(os.path.join(pasta_real, nome), casa)
    if relativo == "." or any(parte.startswith(".") for parte in relativo.split("/")):
        raise Recusado(f"Arquivos de configuração (pastas escondidas) não vão para a Lixeira por aqui ({caminho[:120]}).")
    alvo = os.path.join(pasta_real, nome)
    try:
        info = os.lstat(alvo)
    except FileNotFoundError:
        raise Recusado(f"“{nome}” não existe mais.")
    if stat.S_ISDIR(info.st_mode) and os.path.ismount(alvo):
        raise Recusado(f"“{nome}” é um disco montado.")
    if os.lstat(casa).st_dev != info.st_dev:
        raise Recusado(f"“{nome}” está em outro disco.")
    return alvo


def _nome_livre(arquivos, infos, nome):
    candidato, numero = nome, 2
    base, extensao = os.path.splitext(nome) if not nome.startswith(".") else (nome, "")
    while os.path.lexists(os.path.join(arquivos, candidato)) or os.path.lexists(os.path.join(infos, candidato + ".trashinfo")):
        candidato = f"{base} ({numero}){extensao}"
        numero += 1
    return candidato


def _criar_da_pessoa(pasta, uid, gid, chown):
    """Cria a pasta (e as de cima que faltarem) com a pessoa como dona."""
    faltando = []
    atual = Path(pasta)
    while not atual.exists():
        faltando.append(atual)
        atual = atual.parent
    for item in reversed(faltando):
        item.mkdir(mode=0o700)
        chown(str(item), uid, gid)


def _passar_para(caminho, uid, gid, chown):
    """O que foi movido passa a ser da pessoa (inclusive o que está dentro), sem seguir atalhos."""
    chown(caminho, uid, gid)
    if os.path.isdir(caminho) and not os.path.islink(caminho):
        for raiz, pastas, arquivos in os.walk(caminho):
            for nome in pastas + arquivos:
                chown(os.path.join(raiz, nome), uid, gid)


def mover(caminhos, uid, agora=None, chown=os.lchown, casa=None):
    """Move para a Lixeira de `uid`. Devolve {"movidos": [nomes na Lixeira], "recusados": [{caminho, motivo}]}."""
    if not isinstance(caminhos, list) or not caminhos:
        raise Recusado("Escolha o que mover para a Lixeira.")
    if len(caminhos) > LIMITE_ITENS:
        raise Recusado(f"No máximo {LIMITE_ITENS} itens de cada vez.")
    pessoa = pwd.getpwuid(uid)
    casa = casa or pessoa.pw_dir
    gid = pessoa.pw_gid
    lixeira = os.path.join(os.path.realpath(casa), ".local", "share", "Trash")
    arquivos, infos = os.path.join(lixeira, "files"), os.path.join(lixeira, "info")
    _criar_da_pessoa(arquivos, uid, gid, chown)
    _criar_da_pessoa(infos, uid, gid, chown)
    agora = agora or datetime.datetime.now()
    movidos, recusados = [], []
    for caminho in caminhos:
        try:
            alvo = conferir(caminho, casa)
        except Recusado as motivo:
            recusados.append({"caminho": str(caminho)[:300], "motivo": str(motivo)})
            continue
        nome = _nome_livre(arquivos, infos, os.path.basename(alvo))
        info = os.path.join(infos, nome + ".trashinfo")
        with open(info, "x", encoding="utf-8") as saida:
            saida.write("[Trash Info]\n"
                        f"Path={urllib.parse.quote(alvo)}\n"
                        f"DeletionDate={agora.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        chown(info, uid, gid)
        destino = os.path.join(arquivos, nome)
        try:
            os.rename(alvo, destino)
        except OSError as erro:
            os.unlink(info)
            recusados.append({"caminho": alvo, "motivo": f"Não foi possível mover ({erro.strerror})."})
            continue
        _passar_para(destino, uid, gid, chown)
        movidos.append(nome)
    return {"movidos": movidos, "recusados": recusados}
