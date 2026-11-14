"""DuiaOS — papéis de parede: área de trabalho (por tela), Tela de Bloqueio e Tela de Entrada (ADR 051).

Só a biblioteca padrão. Quem lê: a Área de Trabalho, a Tela de Bloqueio, a Tela de Entrada e as
Configurações (que também gravam).

Preferências da pessoa (~/.config/duiaos/preferencias.conf):
  [papel-de-parede]        arquivo, cor, ajuste            o papel de todas as telas (ou o padrão)
                           telas = mesmo | separado | estender
                           alternar = 0 | minutos          troca sozinho entre as imagens do DuiaOS e importadas
  [papel-de-parede:SAIDA]  arquivo, cor, ajuste            com telas = separado (SAIDA: eDP-1, HDMI-A-1…)
  [papel-bloqueio]         modo = area | proprio, arquivo, cor, ajuste, desfocar = sim | nao

Tela de Entrada (vale para todas as contas; a Tela de Entrada roda como _greetd e não lê a pasta
pessoal): /var/lib/duiaos/entrada/papel.conf, seção [papel] com modo = padrao | proprio, arquivo
(a cópia em /var/lib/duiaos/entrada/), cor, ajuste e desfocar. Quem grava é /usr/lib/duiaos/papel-entrada,
pelo pkexec.

Ajustes (como a imagem ocupa a tela):
  preencher    cobre a tela inteira, cortando o que sobra (padrão)
  ajustar      a imagem inteira aparece; sobra a cor nas bordas
  esticar      ocupa a tela, deformando se as proporções forem diferentes
  centralizar  tamanho original, no meio
  lado-a-lado  repetida, como azulejos
"""
import configparser
from pathlib import Path

AJUSTES = ("preencher", "ajustar", "esticar", "centralizar", "lado-a-lado")
MODOS_TELAS = ("mesmo", "separado", "estender")
COR_PADRAO = "#E8F0FE"
PAPEL_PADRAO = Path("/usr/share/duiaos/papel-de-parede/orbita.jpg")
PASTA_ENTRADA = Path("/var/lib/duiaos/entrada")
ENTRADA_CONF = PASTA_ENTRADA / "papel.conf"
INTERVALOS = (0, 15, 30, 60, 180, 1440)
EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")


def _ler(arquivo):
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(arquivo, encoding="utf-8")
    except (configparser.Error, OSError):
        pass
    return config


def _papel(secao, padrao):
    """Seção (dict) → {arquivo, cor, ajuste}, completando com o padrão."""
    secao = secao or {}
    ajuste = secao.get("ajuste", padrao.get("ajuste", "preencher"))
    return {"arquivo": secao.get("arquivo", padrao.get("arquivo", "")),
            "cor": secao.get("cor", padrao.get("cor", COR_PADRAO)) or COR_PADRAO,
            "ajuste": ajuste if ajuste in AJUSTES else "preencher"}


def _existe_ou_padrao(papel, papel_padrao=PAPEL_PADRAO):
    """Arquivo que sumiu (pendrive tirado, apagado) volta ao papel do DuiaOS."""
    arquivo = papel["arquivo"]
    if arquivo and not Path(arquivo).is_file():
        papel = {**papel, "arquivo": str(papel_padrao) if Path(papel_padrao).is_file() else ""}
    return papel


def ler_area(preferencias, papel_padrao=PAPEL_PADRAO):
    """Configuração da área de trabalho: {telas, alternar, padrao, porTela: {SAIDA: papel}}."""
    config = _ler(preferencias)
    geral = dict(config.items("papel-de-parede")) if config.has_section("papel-de-parede") else {}
    padrao = _existe_ou_padrao(_papel(geral, {"arquivo": str(papel_padrao)}), papel_padrao)
    telas = geral.get("telas", "mesmo")
    try:
        alternar = int(geral.get("alternar", "0"))
    except ValueError:
        alternar = 0
    por_tela = {}
    for secao in config.sections():
        if secao.startswith("papel-de-parede:"):
            por_tela[secao.split(":", 1)[1]] = _existe_ou_padrao(_papel(dict(config.items(secao)), padrao), papel_padrao)
    return {"telas": telas if telas in MODOS_TELAS else "mesmo", "alternar": alternar if alternar in INTERVALOS else 0,
            "padrao": padrao, "porTela": por_tela}


def papel_da_tela(area, saida):
    """O papel que uma tela mostra (com telas = separado, o dela; senão, o padrão)."""
    if area["telas"] == "separado" and saida in area["porTela"]:
        return area["porTela"][saida]
    return area["padrao"]


def ler_bloqueio(preferencias, papel_padrao=PAPEL_PADRAO):
    """Papel da Tela de Bloqueio: o da área de trabalho (tela principal) ou um próprio; e se desfoca."""
    config = _ler(preferencias)
    secao = dict(config.items("papel-bloqueio")) if config.has_section("papel-bloqueio") else {}
    area = ler_area(preferencias, papel_padrao)
    desfocar = secao.get("desfocar", "nao") == "sim"
    if secao.get("modo", "area") == "proprio":
        papel = _so_imagem(_existe_ou_padrao(_papel(secao, area["padrao"]), papel_padrao), papel_padrao)
        return {**papel, "modo": "proprio", "desfocar": desfocar}
    return {**_so_imagem(area["padrao"], papel_padrao), "modo": "area", "desfocar": desfocar}


def _so_imagem(papel, papel_padrao):
    """As Telas de Entrada e de Bloqueio mostram imagens; vídeo ou GIF ali vira o papel do DuiaOS."""
    if papel["arquivo"] and not papel["arquivo"].lower().endswith(EXTENSOES_IMAGEM):
        return {**papel, "arquivo": str(papel_padrao) if Path(papel_padrao).is_file() else ""}
    return papel


def ler_entrada(conf=ENTRADA_CONF, papel_padrao=PAPEL_PADRAO):
    """Papel da Tela de Entrada (arquivo do sistema, legível por todos)."""
    config = _ler(conf)
    secao = dict(config.items("papel")) if config.has_section("papel") else {}
    desfocar = secao.get("desfocar", "nao") == "sim"
    if secao.get("modo") == "proprio":
        papel = _so_imagem(_existe_ou_padrao(_papel(secao, {"arquivo": str(papel_padrao)}), papel_padrao), papel_padrao)
        return {**papel, "modo": "proprio", "desfocar": desfocar}
    return {"arquivo": str(papel_padrao) if Path(papel_padrao).is_file() else "", "cor": COR_PADRAO,
            "ajuste": "preencher", "modo": "padrao", "desfocar": desfocar}


def proximo_da_lista(lista, atual):
    """Troca automática: a imagem depois da atual (volta ao começo no fim)."""
    imagens = [i for i in lista if str(i).lower().endswith(EXTENSOES_IMAGEM)]
    if not imagens:
        return ""
    if atual in imagens:
        return imagens[(imagens.index(atual) + 1) % len(imagens)]
    return imagens[0]


def recorte_estendido(telas, saida):
    """telas = estender: que parte da imagem cada tela mostra. telas: [{nome, x, y, largura, altura}]
    (coordenadas lógicas). Devolve {x, y, largura, altura} da área inteira e o deslocamento da tela."""
    if not telas:
        return None
    x0 = min(t["x"] for t in telas)
    y0 = min(t["y"] for t in telas)
    x1 = max(t["x"] + t["largura"] for t in telas)
    y1 = max(t["y"] + t["altura"] for t in telas)
    tela = next((t for t in telas if t["nome"] == saida), telas[0])
    return {"largura": x1 - x0, "altura": y1 - y0, "dx": tela["x"] - x0, "dy": tela["y"] - y0}


def eh_imagem(dados):
    """Confere pelo começo do arquivo (não pelo nome) que é JPEG, PNG ou WebP."""
    return (dados.startswith(b"\xff\xd8\xff") or dados.startswith(b"\x89PNG\r\n\x1a\n")
            or (dados[:4] == b"RIFF" and dados[8:12] == b"WEBP"))
