"""DuiaOS — Configurações › Atualizações: o que cada atualização traz (ADR 046), sem interface (testado).

- Fichas do DuiaOS (código DUIA-AAAA-NNNN, descrição, detalhes): catálogo publicado com o repositório apt
  (atualizacoes.json, lido pela internet) e o catálogo instalado (/usr/share/duiaos/atualizacoes.json,
  o histórico deste computador).
- Pacotes do Debian: versões, origem (selo de segurança), descrição e registro de mudanças, pelo apt
  (sem ser administrador: só simulação e leitura).
"""
import json
import re
import subprocess
import urllib.request
from pathlib import Path

CATALOGO_INSTALADO = Path("/usr/share/duiaos/atualizacoes.json")
FONTES_DUIAOS = Path("/etc/apt/sources.list.d/duiaos.sources")
SIMULACAO = re.compile(r"^Inst (\S+)(?: \[([^\]]+)\])? \((\S+) ([^\[)]*?)(?: \[[^\]]*\])?\)")


def _rodar(*comando, tempo=60):
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=tempo, check=False,
                                   env={"LC_ALL": "C.UTF-8", "LANGUAGE": "pt_BR:pt", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"})
        return resultado.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def interpretar_simulacao(saida):
    """Linhas "Inst" de "apt-get -s full-upgrade" → [{pacote, de, para, origem, seguranca}]."""
    pacotes = []
    for linha in saida.splitlines():
        achado = SIMULACAO.match(linha)
        if not achado:
            continue
        origem = achado.group(4).strip()
        pacotes.append({"pacote": achado.group(1).split(":")[0], "de": achado.group(2) or "", "para": achado.group(3),
                        "origem": origem, "seguranca": "security" in origem.lower() or "segurança" in origem.lower()})
    return pacotes


def simular():
    return interpretar_simulacao(_rodar("apt-get", "-s", "-o", "Debug::NoLocking=1", "full-upgrade"))


def interpretar_apt_cache(saida):
    """'apt-cache show --no-all-versions ...' → {pacote: descrição curta} (português quando houver)."""
    descricoes, pacote = {}, None
    for linha in saida.splitlines():
        if linha.startswith("Package: "):
            pacote = linha[9:].strip()
        elif pacote and linha.startswith("Description-pt_BR: "):
            descricoes[pacote] = linha.split(": ", 1)[1].strip()
        elif pacote and linha.startswith(("Description: ", "Description-en: ")) and pacote not in descricoes:
            descricoes[pacote] = linha.split(": ", 1)[1].strip()
    return descricoes


def descricoes(pacotes):
    if not pacotes:
        return {}
    return interpretar_apt_cache(_rodar("apt-cache", "show", "--no-all-versions", *pacotes[:300]))


def registro_de_mudancas(pacote, limite=6000):
    """Começo do registro de mudanças (changelog) do pacote, baixado pelo apt."""
    texto = _rodar("apt-get", "changelog", pacote, tempo=40).strip()
    if not texto:
        return "Não foi possível baixar o registro de mudanças deste pacote (sem internet ou sem registro publicado)."
    blocos = re.split(r"\n(?=\S+ \([^)]+\) )", texto)          # uma entrada por versão
    return "\n\n".join(blocos[:3])[:limite]


# ----------------------------------------------------------------- fichas

def data_da_versao(versao):
    """'0.2.0+git20261114161951.4920161' → '20261114161951'; versão lançada ou local → ''."""
    achado = re.search(r"\+git(\d{14})\.", versao or "")
    return achado.group(1) if achado else ""


def endereco_do_catalogo(fontes=FONTES_DUIAOS):
    try:
        for linha in Path(fontes).read_text(encoding="utf-8").splitlines():
            if linha.startswith("URIs:"):
                return linha.split(":", 1)[1].strip().split()[0].rstrip("/") + "/atualizacoes.json"
    except OSError:
        pass
    return ""


def ler_catalogo_instalado(caminho=CATALOGO_INSTALADO):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8")).get("atualizacoes", [])
    except (OSError, ValueError, AttributeError):
        return []


def baixar_catalogo(endereco):
    if not endereco:
        return []
    try:
        with urllib.request.urlopen(endereco, timeout=15) as resposta:
            return json.loads(resposta.read().decode("utf-8")).get("atualizacoes", [])
    except (OSError, ValueError, AttributeError):
        return []


def fichas_pendentes(publicado, instalado, mudancas_duiaos):
    """Fichas que esta atualização traz: publicadas, ainda não instaladas e dentro das versões que mudam.

    mudancas_duiaos: [{pacote, de, para}] dos pacotes duiaos-*."""
    if not mudancas_duiaos:
        return []
    ja_tem = {f["codigo"] for f in instalado}
    datas_de = [data_da_versao(m["de"]) for m in mudancas_duiaos if m.get("de")]
    datas_para = [data_da_versao(m["para"]) for m in mudancas_duiaos]
    desde = min((d for d in datas_de if d), default="")
    ate = max((d for d in datas_para if d), default="")
    pacotes = {m["pacote"] for m in mudancas_duiaos}
    pendentes = []
    for ficha in publicado:
        if ficha.get("codigo") in ja_tem:
            continue
        quando = ficha.get("publicada", "")
        if desde and quando and quando <= desde:
            continue
        if ate and quando and quando > ate:
            continue
        if not pacotes.intersection(ficha.get("pacotes", [])):
            continue
        pendentes.append(ficha)
    return pendentes


def versao_instalada(pacote="duiaos-desktop"):
    saida = _rodar("dpkg-query", "-W", "-f=${Version}", pacote, tempo=10)
    return saida.strip() if isinstance(saida, str) else ""


def nivel_de_atualizacao(instalado, compilacao):
    """Até onde este computador está atualizado (ADR 074): a ficha mais nova instalada e a compilação.

    instalado: catálogo de fichas instalado; compilacao: versão do duiaos-desktop (ex.: 0.3.1+git20261123….abc1234).
    A Central compara com o catálogo publicado: tudo o que saiu depois vem numa atualização acumulada."""
    nivel = {"codigo": "", "titulo": "", "data": "", "compilacao": compilacao or "", "texto": ""}
    if instalado:
        ultima = max(instalado, key=lambda f: (f.get("publicada", ""), f.get("codigo", "")))
        nivel.update(codigo=ultima.get("codigo", ""), titulo=ultima.get("titulo", ""))
        nivel["data"] = "/".join(reversed((ultima.get("data") or "").split("-")))
    quando = data_da_versao(compilacao)
    data_compilacao = f"{quando[6:8]}/{quando[4:6]}/{quando[:4]}" if quando else ""
    partes = []
    if nivel["codigo"]:
        partes.append(f"Atualizado até {nivel['codigo']}" + (f" ({nivel['data']})" if nivel["data"] else ""))
    if compilacao:
        partes.append(f"compilação {compilacao}" + (f" de {data_compilacao}" if data_compilacao else ""))
    nivel["texto"] = " · ".join(partes) or "Nível de atualização desconhecido (sistema gerado sem o histórico)."
    return nivel


def maior_reinicio(fichas):
    ordem = ["nao", "sessao", "computador"]
    return max((f.get("reiniciar", "nao") for f in fichas), key=lambda r: ordem.index(r) if r in ordem else 0, default="nao")
