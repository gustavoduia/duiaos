"""Envio dos relatórios pendentes (ADR 040).

Transporte "git" (computadores de teste, nível desenvolvimento): cópia do repositório privado
gustavoduia/duiaos-diagnosticos em /var/lib/duiaos-relatorios/repositorio, chave SSH só deste computador
(deploy key com escrita só nesse repositório) e chave do GitHub fixada (known_hosts). Grava
maquinas/<maquina>/<AAAA-MM-DD>/<HHMMSS>.json e maquinas/<maquina>/perfil.json, num commit por envio.

Transporte "https" (usuários; fase 3): o Worker do site recebe, sem credencial no computador, e grava no
mesmo repositório em lotes.

Depois do envio o relatório vai para enviados/ (os últimos GUARDAR_ENVIADOS ficam para a pessoa conferir,
como no Ubuntu Insights). A situação do nível é conferida de novo na hora de enviar.
"""
import json
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from . import config as cfg

GUARDAR_ENVIADOS = 50
GUARDAR_PENDENTES_DIAS = 30
TEMPO_GIT = 120


class ErroDeEnvio(Exception):
    pass


def _git(argumentos, pasta, executar=subprocess.run):
    ambiente = {"PATH": "/usr/bin:/bin", "HOME": str(cfg.PASTA_ESTADO), "LC_ALL": "C.UTF-8",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_SSH_COMMAND": (f"ssh -i {shlex.quote(str(cfg.CHAVE_GIT))} -o IdentitiesOnly=yes "
                                    f"-o BatchMode=yes -o UserKnownHostsFile={shlex.quote(str(cfg.HOSTS_GITHUB))} "
                                    "-o StrictHostKeyChecking=yes -o ConnectTimeout=20")}
    resultado = executar(["git", *argumentos], cwd=pasta, env=ambiente, capture_output=True, text=True,
                         timeout=TEMPO_GIT)
    if resultado.returncode != 0:
        raise ErroDeEnvio(f"git {argumentos[0]}: {(resultado.stderr or resultado.stdout).strip()[-400:]}")
    return resultado.stdout.strip()


def _ramo(pasta):
    try:
        return _git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], pasta).split("/", 1)[1]
    except ErroDeEnvio:
        return "main"


def _copia(config, pasta):
    copia = pasta / "repositorio"
    if not (copia / ".git").exists():
        if copia.exists():
            shutil.rmtree(copia)
        _git(["clone", "--depth", "3", config.repositorio, str(copia)], pasta)
    _git(["fetch", "--depth", "3", "origin"], copia)
    ramo = _ramo(copia)
    _git(["checkout", "-q", "-B", ramo, f"origin/{ramo}"], copia)
    _git(["reset", "-q", "--hard", f"origin/{ramo}"], copia)
    _git(["clean", "-fdq"], copia)
    return copia, ramo


def _nome_da_maquina(relatorio):
    nome = relatorio.get("maquina") or relatorio.get("instalacao", "")[:12] or "desconhecida"
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in nome)


def enviar_git(config, relatorios, pasta):
    copia, ramo = _copia(config, pasta)
    for caminho, relatorio in relatorios:
        maquina = _nome_da_maquina(relatorio)
        dia, hora = caminho.stem.split("-", 1)
        destino = copia / "maquinas" / maquina / f"{dia[:4]}-{dia[4:6]}-{dia[6:]}" / f"{hora}.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(caminho, destino)
        if "perfil" in relatorio:
            (copia / "maquinas" / maquina / "perfil.json").write_text(
                json.dumps({"atualizado": relatorio.get("gerado"), **relatorio["perfil"]}, ensure_ascii=False,
                           indent=2) + "\n")
    falhas = sum(r.get("resumo", {}).get("falhas", 0) for _, r in relatorios)
    erros = sum(r.get("resumo", {}).get("erros", 0) for _, r in relatorios)
    maquinas = ", ".join(sorted({_nome_da_maquina(r) for _, r in relatorios}))
    _git(["add", "-A", "maquinas"], copia)
    _git(["-c", "user.name=DuiaOS", "-c", "user.email=relatorios@duiaos.invalid", "commit", "-q", "-m",
          f"{maquinas}: {len(relatorios)} relatório(s), {falhas} falha(s), {erros} erro(s)"], copia)
    try:
        _git(["push", "-q", "origin", f"HEAD:{ramo}"], copia)
    except ErroDeEnvio:                                   # outro computador enviou antes
        _git(["pull", "-q", "--rebase", "origin", ramo], copia)
        _git(["push", "-q", "origin", f"HEAD:{ramo}"], copia)


def enviar_pendentes(config, pasta=None, transporte=None):
    """Envia tudo o que está em pendentes/. Devolve {"enviados": n} ou {"erro": "..."}."""
    pasta = Path(pasta or cfg.PASTA_ESTADO)
    pendentes = sorted((pasta / "pendentes").glob("*.json"))
    limite = time.time() - GUARDAR_PENDENTES_DIAS * 86400
    for caminho in list(pendentes):                      # sem envio por 30 dias: descarta
        if caminho.stat().st_mtime < limite:
            caminho.unlink(missing_ok=True)
            pendentes.remove(caminho)
    if not config.coleta:
        return {"enviados": 0, "motivo": f"nível {config.nivel}: nada é enviado"}
    if not pendentes:
        return {"enviados": 0}
    relatorios = []
    for caminho in pendentes:
        try:
            relatorios.append((caminho, json.loads(caminho.read_text())))
        except (OSError, ValueError):
            caminho.unlink(missing_ok=True)
    if transporte is None:
        if config.transporte == "git":
            if not config.repositorio or not cfg.CHAVE_GIT.exists():
                return {"enviados": 0, "erro": "transporte git sem repositório ou sem chave "
                                              "(ferramentas/configurar-relatorios.sh)"}
            transporte = enviar_git
        else:
            return {"enviados": 0, "erro": "o envio pelo site ainda não está disponível (fase 3)"}
    try:
        transporte(config, relatorios, pasta)
    except (ErroDeEnvio, OSError, subprocess.SubprocessError) as erro:
        return {"enviados": 0, "erro": str(erro)}
    enviados = pasta / "enviados"
    enviados.mkdir(exist_ok=True)
    for caminho, _ in relatorios:
        caminho.replace(enviados / caminho.name)
    antigos = sorted(enviados.glob("*.json"))[:-GUARDAR_ENVIADOS]
    for caminho in antigos:
        caminho.unlink(missing_ok=True)
    return {"enviados": len(relatorios)}
