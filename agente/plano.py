"""DuiaOS — duiaos-agente: o que cada ação faria, antes de fazer (ADR 034).

Só a biblioteca padrão. Este módulo não muda nada no sistema: valida os
argumentos, lê a simulação do apt ("apt-get -s") e diz o impacto e se a ação
é recusada. Quem executa é agente.py, e só um plano que este módulo aprovou.

Ações (lista fechada):
  atualizar_sistema                 apt-get full-upgrade (depois de apt-get update)
  instalar_aplicativo {"pacote"}    apt-get install PACOTE
  remover_aplicativo  {"pacote"}    apt-get remove PACOTE (nunca o que é essencial)
"""
import re

ACOES = ("atualizar_sistema", "instalar_aplicativo", "remover_aplicativo")
NOME_PACOTE = re.compile(r"^[a-z0-9][a-z0-9+.-]{1,62}$")      # política do Debian
SIMULACAO = re.compile(r"^(Inst|Remv|Purg) (\S+)(?: \[([^\]]+)\])?(?: \((\S+))?")

# Nunca saem por um pedido da IA, mesmo que a pessoa aprove: sem eles o
# computador não liga, não entra na sessão ou não se atualiza mais.
PROTEGIDOS_FIXOS = {
    "apt", "dpkg", "base-files", "bash", "coreutils", "dbus", "debconf", "init", "libc6",
    "linux-image-amd64", "linux-image-arm64", "login", "network-manager", "polkitd", "python3",
    "sudo", "systemd", "systemd-sysv", "grub-efi-amd64", "grub-efi-arm64", "grub-common",
    "shim-signed", "greetd", "labwc", "cage",
}
PREFIXOS_PROTEGIDOS = ("duiaos-",)


class Recusa(Exception):
    """A ação não é aceita; a mensagem é para a pessoa."""

    def __init__(self, codigo, mensagem):
        super().__init__(mensagem)
        self.codigo = codigo


def validar(acao, argumentos):
    """Confere a ação e os argumentos; devolve os argumentos limpos."""
    if acao not in ACOES:
        raise Recusa("Invalido", f"Ação desconhecida: {str(acao)[:40]!r}.")
    if not isinstance(argumentos, dict):
        raise Recusa("Invalido", "Os argumentos devem ser um objeto.")
    if acao == "atualizar_sistema":
        return {}
    pacote = argumentos.get("pacote")
    if not isinstance(pacote, str) or not NOME_PACOTE.match(pacote):
        raise Recusa("Invalido", f"Nome de pacote inválido: {str(pacote)[:70]!r}.")
    return {"pacote": pacote}


def comando_apt(acao, argumentos):
    """Argumentos do apt-get para a ação (sem o "-s" da simulação)."""
    if acao == "atualizar_sistema":
        return ["full-upgrade"]
    if acao == "instalar_aplicativo":
        return ["install", "--no-remove", argumentos["pacote"]]
    return ["remove", argumentos["pacote"]]


def ler_simulacao(saida):
    """Lê a saída de "apt-get -s ..." (linhas Inst/Remv/Purg).
    Devolve {"instalar": [...], "atualizar": [...], "remover": [...]}, cada item
    {"pacote", "de", "para"} (versões; "de" vazio quando é novo)."""
    resultado = {"instalar": [], "atualizar": [], "remover": []}
    for linha in saida.splitlines():
        # "Inst vlc (3.0.21-1 Debian:13.1/stable [amd64])"            (novo)
        # "Inst libc6 [2.41-11] (2.41-12 Debian:13.2/stable [amd64])"  (atualização)
        # "Remv vlc [3.0.21-1]"
        m = SIMULACAO.match(linha)
        if not m:
            continue
        tipo, pacote, de, para = m.group(1), m.group(2).split(":")[0], m.group(3) or "", m.group(4) or ""
        if not NOME_PACOTE.match(pacote):
            continue
        if tipo == "Inst":
            resultado["atualizar" if de else "instalar"].append({"pacote": pacote, "de": de, "para": para})
        else:
            resultado["remover"].append({"pacote": pacote, "de": de, "para": ""})
    return resultado


def ler_protegidos(saida_dpkg):
    """Pacotes instalados que nunca podem sair: essenciais, prioridade
    required/important, os do DuiaOS e a lista fixa. saida_dpkg vem de
    dpkg-query -W -f '${Package}\\t${Essential}\\t${Priority}\\n'."""
    protegidos = set(PROTEGIDOS_FIXOS)
    for linha in saida_dpkg.splitlines():
        campos = linha.split("\t")
        if len(campos) < 3:
            continue
        nome, essencial, prioridade = campos[0], campos[1], campos[2]
        if essencial == "yes" or prioridade in ("required", "important") or nome.startswith(PREFIXOS_PROTEGIDOS):
            protegidos.add(nome)
    return protegidos


def avaliar(acao, argumentos, mudancas, protegidos, instalado, candidato):
    """Decide se o plano pode seguir. instalado/candidato: versões do pacote
    pedido (vazias quando não há). Devolve (resumo para a pessoa, recusa ou None)."""
    pacote = argumentos.get("pacote", "")
    saem = [m["pacote"] for m in mudancas["remover"]]
    proibidos = sorted(p for p in saem if p in protegidos or p.startswith(PREFIXOS_PROTEGIDOS))
    if acao == "instalar_aplicativo":
        if instalado:
            return f"{pacote} já está instalado ({instalado}).", Recusa("JaInstalado", f"{pacote} já está instalado.")
        if not candidato:
            return "", Recusa("NaoEncontrado", f"Não achei {pacote} nos repositórios deste computador.")
    if acao == "remover_aplicativo":
        if not instalado:
            return "", Recusa("NaoInstalado", f"{pacote} não está instalado.")
        if pacote in protegidos or pacote.startswith(PREFIXOS_PROTEGIDOS):
            return "", Recusa("Protegido", f"{pacote} é parte essencial do sistema e não pode ser removido.")
    if proibidos:
        return "", Recusa("Protegido", "Isso tiraria partes essenciais do sistema ("
                                       + ", ".join(proibidos[:5]) + "). Não vou fazer.")
    n_inst, n_atu, n_rem = (len(mudancas[k]) for k in ("instalar", "atualizar", "remover"))
    if acao == "atualizar_sistema":
        if not (n_inst or n_atu or n_rem):
            return "O sistema já está atualizado.", Recusa("NadaAFazer", "O sistema já está atualizado.")
        resumo = f"Atualizar {n_atu} pacote{'s' if n_atu != 1 else ''}"
    elif acao == "instalar_aplicativo":
        resumo = f"Instalar {pacote} ({candidato})"
        if n_inst > 1:
            resumo += f" e mais {n_inst - 1} pacote{'s' if n_inst > 2 else ''} que ele precisa"
    else:
        resumo = f"Remover {pacote}"
        if n_rem > 1:
            resumo += f" e mais {n_rem - 1} pacote{'s' if n_rem > 2 else ''} que dependem dele"
    extras = []
    if acao != "instalar_aplicativo" and n_inst:
        extras.append(f"{n_inst} novo{'s' if n_inst > 1 else ''}")
    if acao != "remover_aplicativo" and n_rem:
        extras.append(f"{n_rem} removido{'s' if n_rem > 1 else ''}")
    if extras:
        resumo += " (" + ", ".join(extras) + ")"
    return resumo + ".", None


def ler_progresso(linha):
    """Linha do APT::Status-Fd -> (fração 0–1 ou None, mensagem).
    Formatos: "dlstatus:1:45.5:Baixando ..." e "pmstatus:pacote:72.0:Instalando ..."."""
    partes = linha.strip().split(":", 3)
    if len(partes) < 4 or partes[0] not in ("dlstatus", "pmstatus"):
        return None, ""
    try:
        porcento = float(partes[2])
    except ValueError:
        return None, ""
    # Baixar é a primeira metade da barra; instalar, a segunda
    fracao = porcento / 200 if partes[0] == "dlstatus" else 0.5 + porcento / 200
    return round(max(0.0, min(fracao, 1.0)), 3), partes[3][:120]


def ler_politica(saida):
    """Lê "apt-cache policy PACOTE" -> (instalado, candidato); "" quando não há."""
    instalado = candidato = ""
    for linha in saida.splitlines():
        linha = linha.strip()
        if linha.startswith(("Installed:", "Instalado:")):
            instalado = linha.split(":", 1)[1].strip()
        elif linha.startswith(("Candidate:", "Candidato:")):
            candidato = linha.split(":", 1)[1].strip()
    vazio = ("(none)", "(nenhum)", "")
    return ("" if instalado in vazio else instalado), ("" if candidato in vazio else candidato)


def tamanhos(saida_cache_show):
    """Soma de "Size:" (download) e "Installed-Size:" (KB) de "apt-cache show --no-all-versions"."""
    baixar = espaco = 0
    for linha in saida_cache_show.splitlines():
        if linha.startswith("Size:"):
            baixar += int(linha.split(":", 1)[1].strip() or 0)
        elif linha.startswith("Installed-Size:"):
            espaco += int(linha.split(":", 1)[1].strip() or 0) * 1024
    return baixar, espaco
