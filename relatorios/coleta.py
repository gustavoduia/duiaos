"""Coleta: lê o journal desde a última vez, escolhe o que o nível permite e grava um relatório pendente.

O que entra, por nível (ADR 040):
  erros            falhas de programas (Python pelo duiaos_registro; nativos pelo systemd-coredump),
                   serviços que falharam, erros (prioridade 0–3) de todo o sistema, avisos dos componentes
                   do DuiaOS, e o perfil do computador. Textos anonimizados.
  erros_e_uso      o mesmo + uso agregado (relatorios/uso.py: lista conhecida, só contagens).
  desenvolvimento  tudo dos componentes do DuiaOS (inclusive informação), avisos de todo o sistema e os
                   eventos com conteúdo (ex.: conversas do Wise). Textos sem anonimizar (só sem segredos).
Mensagens repetidas viram uma linha com o número de repetições; falhas iguais (mesma assinatura) são
agrupadas, como no Error Tracker do Ubuntu.
"""
import hashlib
import json
import os
import pwd
import re
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from duiaos_registro.privacidade import anonimizar, limpar_segredos

from . import config as cfg
from . import perfil as perfil_mod
from . import uso as uso_mod

ID_COREDUMP = "fc2e22bc6ee647b6b90729ab34a250b1"          # systemd-coredump: "Process … dumped core"
UNIDADES_DUIAOS = {"duiaos-ia.service", "duiaos-agente.service", "ollama.service", "greetd.service",
                   "duiaos-relatorios.service"}
PRIMEIRA_COLETA = 24 * 3600                                 # sem cursor: as últimas 24 h
LIMITE_ENTRADAS = 60000
LIMITE_EVENTOS = 4000
PERFIL_A_CADA = 30 * 86400
CAMPOS = {"DUIAOS_EVENTO": "evento", "DUIAOS_ASSINATURA": "assinatura", "DUIAOS_RASTRO": "rastro",
          "CODE_FILE": "arquivo", "CODE_LINE": "linha", "CODE_FUNC": "funcao", "MESSAGE_ID": "id",
          "COREDUMP_EXE": "programa", "COREDUMP_SIGNAL_NAME": "sinal", "COREDUMP_PACKAGE_NAME": "pacote",
          "UNIT_RESULT": "resultado", "EXIT_CODE": "saida", "EXIT_STATUS": "status_saida", "UNIT": "unidade_afetada"}


def _texto(valor):
    if isinstance(valor, list):                       # o journal manda bytes que não são UTF-8 como lista
        return bytes(valor).decode("utf-8", "replace")
    return "" if valor is None else str(valor)


def ler_journal(cursor, desde=None, executar=subprocess.Popen):
    """(entradas, cursor_novo). Lê em fluxo para não guardar tudo na memória."""
    comando = ["journalctl", "--no-pager", "-o", "json", "--show-cursor"]
    comando += ["--after-cursor", cursor] if cursor else ["--since", f"@{int(desde or time.time() - PRIMEIRA_COLETA)}"]
    entradas, novo = [], cursor
    processo = executar(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "SYSTEMD_COLORS": "0"})
    cortado = False
    for linha in processo.stdout:
        if linha.startswith("-- cursor: "):
            novo = linha[len("-- cursor: "):].strip()
            continue
        if len(entradas) >= LIMITE_ENTRADAS:
            # Muito para uma vez só: para aqui e a próxima coleta continua deste ponto (nada é pulado)
            cortado = True
            processo.kill()
            break
        try:
            entradas.append(json.loads(linha))
        except ValueError:
            pass
    processo.wait()
    if entradas and (cortado or novo == cursor):       # cortado, ou sem a linha de cursor: a última lida
        novo = entradas[-1].get("__CURSOR", cursor)
    return entradas, novo


def contexto_do_servico(unidade, boot, linhas=15, executar=subprocess.run):
    """Últimas linhas do serviço que falhou, naquele início (o que o `systemctl status` mostraria): a causa
    costuma estar em mensagens comuns do próprio serviço, que o nível não levaria."""
    if not unidade or not boot:
        return []
    try:
        saida = executar(["journalctl", "--no-pager", "-o", "json", "-u", unidade, f"_BOOT_ID={boot}",
                          "-n", str(linhas)], capture_output=True, text=True, timeout=20,
                         env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"}).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    resultado = []
    for linha in saida.splitlines():
        try:
            e = json.loads(linha)
        except ValueError:
            continue
        resultado.append(f"{_texto(e.get('SYSLOG_IDENTIFIER') or e.get('_COMM'))}: {_texto(e.get('MESSAGE'))}")
    return resultado


def _do_duiaos(e):
    origem = _texto(e.get("SYSLOG_IDENTIFIER") or e.get("_COMM"))
    unidade = _texto(e.get("_SYSTEMD_UNIT") or e.get("_SYSTEMD_USER_UNIT"))
    return bool(e.get("DUIAOS_COMPONENTE")) or origem.startswith("duiaos") or unidade in UNIDADES_DUIAOS


def classificar(e, nivel):
    """Tipo do registro para o relatório, ou None se o nível não permite."""
    try:
        prioridade = int(_texto(e.get("PRIORITY", "6")) or 6)
    except ValueError:
        prioridade = 6
    duiaos = _do_duiaos(e)
    if _texto(e.get("MESSAGE_ID")) == ID_COREDUMP:
        return "falha_nativa"
    if _texto(e.get("DUIAOS_EVENTO")) == "falha":
        return "falha"
    resultado = _texto(e.get("UNIT_RESULT"))
    if resultado and resultado != "success":
        return "servico_falhou"
    if prioridade <= 3:
        return "erro"
    if duiaos and prioridade <= 4:
        return "aviso"
    evento = _texto(e.get("DUIAOS_EVENTO"))
    if evento.startswith("uso.") and nivel in ("erros_e_uso", "desenvolvimento"):
        return "uso"
    if nivel == "desenvolvimento" and (duiaos or prioridade <= 4):
        return "registro"
    return None


def assinatura_nativa(e):
    """Programa + sinal + as 5 primeiras funções do rastro da 1ª thread (systemd-coredump)."""
    funcoes = []
    for linha in _texto(e.get("MESSAGE")).splitlines():
        achado = re.match(r"\s*#\d+\s+0x[0-9a-f]+\s+(\S+)", linha)
        if achado:
            funcoes.append(achado.group(1))
            if len(funcoes) >= 5:
                break
        elif funcoes and not linha.strip():
            break
    base = "|".join([os.path.basename(_texto(e.get("COREDUMP_EXE"))), _texto(e.get("COREDUMP_SIGNAL_NAME")),
                     *funcoes])
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def compactar(e, tipo):
    try:
        quando = int(_texto(e.get("__REALTIME_TIMESTAMP")) or 0) / 1e6
    except ValueError:
        quando = 0
    registro = {"tipo": tipo, "t": round(quando, 3), "boot": _texto(e.get("_BOOT_ID"))[:8],
                "prioridade": int(_texto(e.get("PRIORITY", "6")) or 6),
                "origem": _texto(e.get("SYSLOG_IDENTIFIER") or e.get("_COMM")),
                "unidade": _texto(e.get("_SYSTEMD_UNIT") or e.get("_SYSTEMD_USER_UNIT")),
                "mensagem": _texto(e.get("MESSAGE"))}
    for campo, nome in CAMPOS.items():
        if e.get(campo) not in (None, ""):
            registro[nome] = _texto(e[campo])
    if e.get("DUIAOS_DADOS"):
        try:
            registro["dados"] = json.loads(_texto(e["DUIAOS_DADOS"]))
        except ValueError:
            registro["dados"] = _texto(e["DUIAOS_DADOS"])
    if tipo == "falha_nativa":
        registro["assinatura"] = assinatura_nativa(e)
    return registro


def _chave_repeticao(r):
    return (r["tipo"], r["origem"], re.sub(r"\d+", "#", r["mensagem"])[:200])


def montar(entradas, nivel, nomes=(), contexto=None):
    """Eventos e falhas agrupadas, já com a privacidade do nível."""
    eventos, falhas, repetidos = [], {}, {}
    for e in entradas:
        tipo = classificar(e, nivel)
        if tipo is None or tipo == "uso":       # uso nunca sai um a um: só somado (agregar_uso)
            continue
        r = compactar(e, tipo)
        if tipo == "servico_falhou" and contexto is not None:
            r["contexto"] = contexto(_texto(e.get("UNIT")), _texto(e.get("_BOOT_ID")))
        if nivel != "desenvolvimento":
            r = anonimizar(r, nomes)
        else:
            r = limpar_segredos(r)
        if tipo in ("falha", "falha_nativa"):
            chave = r.get("assinatura") or hashlib.sha1(r["mensagem"].encode()).hexdigest()[:16]
            grupo = falhas.get(chave)
            if grupo is None:
                falhas[chave] = {"assinatura": chave, "tipo": tipo, "origem": r["origem"],
                                 "mensagem": r["mensagem"].splitlines()[0][:300] if r["mensagem"] else "",
                                 "programa": r.get("programa", ""), "sinal": r.get("sinal", ""),
                                 "contagem": 1, "primeira": r["t"], "ultima": r["t"],
                                 "exemplo": {k: v for k, v in r.items() if k not in ("tipo",)}}
            else:
                grupo["contagem"] += 1
                grupo["ultima"] = r["t"]
            continue
        chave = _chave_repeticao(r)
        if chave in repetidos:
            repetidos[chave]["repeticoes"] = repetidos[chave].get("repeticoes", 1) + 1
            repetidos[chave]["ultima"] = r["t"]
            continue
        if len(eventos) < LIMITE_EVENTOS:
            repetidos[chave] = r
            eventos.append(r)
    return eventos, sorted(falhas.values(), key=lambda f: -f["contagem"])


def agregar_uso(entradas, nivel):
    """Contagens dos eventos de uso da lista conhecida (vazio abaixo de "erros_e_uso")."""
    registros = []
    for e in entradas:
        if classificar(e, nivel) != "uso":
            continue
        try:
            dados = json.loads(_texto(e.get("DUIAOS_DADOS")) or "{}")
        except ValueError:
            dados = {}
        registros.append((_texto(e.get("DUIAOS_EVENTO")), dados))
    return uso_mod.agregar(registros)


def nomes_pessoais():
    """Nomes de usuário (contas de pessoas) e do computador, para anonimizar."""
    nomes = {socket.gethostname()}
    try:
        for conta in pwd.getpwall():
            if conta.pw_uid >= 1000 and conta.pw_uid < 65534:
                nomes.add(conta.pw_name)
                nomes.update(p for p in conta.pw_gecos.split(",")[0].split() if len(p) >= 3)
    except (KeyError, OSError):
        pass
    return nomes


def _ler_estado(pasta):
    try:
        return json.loads((pasta / "estado.json").read_text())
    except (OSError, ValueError):
        return {}


def _salvar_estado(pasta, estado):
    temporario = pasta / "estado.json.tmp"
    temporario.write_text(json.dumps(estado, ensure_ascii=False, indent=1))
    temporario.replace(pasta / "estado.json")


def coletar(config, pasta=None, journal=ler_journal, coletar_perfil=perfil_mod.coletar, agora=None, nomes=None,
            contexto=contexto_do_servico):
    """Gera um relatório em pendentes/ se houver algo. Devolve o caminho (ou None)."""
    if not config.coleta:
        return None
    pasta = Path(pasta or cfg.PASTA_ESTADO)
    for nome in ("pendentes", "enviados"):            # relatórios: só o root lê (podem ter dados pessoais)
        (pasta / nome).mkdir(mode=0o700, parents=True, exist_ok=True)
    agora = agora or time.time()
    estado = _ler_estado(pasta)
    inicio = estado.get("coletado_ate") or agora - PRIMEIRA_COLETA
    entradas, cursor = journal(estado.get("cursor"), inicio)
    nomes = nomes_pessoais() if nomes is None else nomes
    eventos, falhas = montar(entradas, config.nivel, nomes, contexto)
    uso = agregar_uso(entradas, config.nivel)

    perfil = None
    atual = coletar_perfil()
    resumo_perfil = perfil_mod.resumo(atual)
    if resumo_perfil != estado.get("perfil_resumo") or agora - estado.get("perfil_em", 0) > PERFIL_A_CADA:
        perfil = atual if config.nivel == "desenvolvimento" else anonimizar(atual, nomes)

    estado.update(cursor=cursor, coletado_ate=agora)
    if not eventos and not falhas and not uso and perfil is None:
        _salvar_estado(pasta, estado)
        return None
    relatorio = {
        "formato": 1, "instalacao": cfg.identificador(pasta), "nivel": config.nivel,
        "maquina": config.maquina if config.nivel == "desenvolvimento" else "",
        "gerado": datetime.fromtimestamp(agora).astimezone().isoformat(timespec="seconds"),
        "periodo": {"de": round(inicio, 3), "ate": round(agora, 3)},
        "versao_duiaos": perfil_mod.sistema_operacional().get("version_id", ""),
        "resumo": {"falhas": sum(f["contagem"] for f in falhas), "falhas_diferentes": len(falhas),
                   "erros": sum(1 for e in eventos if e["tipo"] in ("erro", "servico_falhou")),
                   "avisos": sum(1 for e in eventos if e["tipo"] == "aviso"), "eventos": len(eventos),
                   "entradas_lidas": len(entradas)},
        "falhas": falhas, "eventos": eventos,
    }
    if uso:
        relatorio["uso"] = uso
    if perfil is not None:
        relatorio["perfil"] = perfil
        estado.update(perfil_resumo=resumo_perfil, perfil_em=agora)
    nome = time.strftime("%Y%m%d-%H%M%S", time.localtime(agora)) + ".json"
    caminho = pasta / "pendentes" / nome
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(relatorio, ensure_ascii=False))
    os.chmod(temporario, 0o600)
    temporario.replace(caminho)
    _salvar_estado(pasta, estado)                      # o cursor só avança com o relatório gravado
    return caminho


def publicar_situacao(pasta=None, **dados):
    """situacao.json (0644): o que `duiaos-relatorios estado` mostra sem sudo — horários e contagens, sem
    conteúdo dos relatórios."""
    pasta = Path(pasta or cfg.PASTA_ESTADO)
    arquivo = pasta / "situacao.json"
    try:
        atual = json.loads(arquivo.read_text())
    except (OSError, ValueError):
        atual = {}
    atual.update(dados)
    atual["pendentes"] = len(list((pasta / "pendentes").glob("*.json"))) if (pasta / "pendentes").is_dir() else 0
    atual["enviados"] = len(list((pasta / "enviados").glob("*.json"))) if (pasta / "enviados").is_dir() else 0
    temporario = pasta / "situacao.json.tmp"
    temporario.write_text(json.dumps(atual, ensure_ascii=False))
    os.chmod(temporario, 0o644)
    temporario.replace(arquivo)
    return atual
