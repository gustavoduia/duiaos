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
(a cópia em /var/lib/duiaos/entrada/), cor, ajuste, desfocar e estilo = padrao | futurista (ADR 052). Quem grava é /usr/lib/duiaos/papel-entrada,
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

import pastas

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


BRILHOS = ("radial", "linear", "nenhum")
ACESSO_PADRAO = {"veu": 15, "brilho": "radial", "brilho_extra": False}


def acesso(secao):
    """Tom azul e brilho das Telas de Bloqueio e de Entrada no estilo futurista (ADR 056), de uma seção (dict):
    veu = transparência do tom azul, 0 (azul cheio) a 100 (só o papel de parede); brilho = radial | linear |
    nenhum; brilho_extra = o brilho também atrás do relógio das outras telas."""
    secao = secao or {}
    try:
        veu = max(0, min(100, int(secao.get("veu", ACESSO_PADRAO["veu"]))))
    except ValueError:
        veu = ACESSO_PADRAO["veu"]
    brilho = secao.get("brilho", ACESSO_PADRAO["brilho"])
    return {"veu": veu, "brilho": brilho if brilho in BRILHOS else ACESSO_PADRAO["brilho"],
            "brilho_extra": secao.get("brilho_extra", "nao") == "sim"}


def ler_bloqueio(preferencias, papel_padrao=PAPEL_PADRAO):
    """Papel da Tela de Bloqueio: o da área de trabalho (tela principal) ou um próprio; e se desfoca."""
    config = _ler(preferencias)
    secao = dict(config.items("papel-bloqueio")) if config.has_section("papel-bloqueio") else {}
    area = ler_area(preferencias, papel_padrao)
    desfocar = secao.get("desfocar", "nao") == "sim"
    if secao.get("modo", "area") == "proprio":
        papel = _so_imagem(_existe_ou_padrao(_papel(secao, area["padrao"]), papel_padrao), papel_padrao)
        return {**papel, "modo": "proprio", "desfocar": desfocar, "acesso": acesso(secao)}
    return {**_so_imagem(area["padrao"], papel_padrao), "modo": "area", "desfocar": desfocar, "acesso": acesso(secao)}


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
        return {**papel, "modo": "proprio", "desfocar": desfocar, "acesso": acesso(secao)}
    return {"arquivo": str(papel_padrao) if Path(papel_padrao).is_file() else "", "cor": COR_PADRAO,
            "ajuste": "preencher", "modo": "padrao", "desfocar": desfocar, "acesso": acesso(secao)}


def estilo_da_entrada(conf=ENTRADA_CONF):
    """Estilo da Tela de Entrada ("futurista", o inicial, ou "padrao" = Clássico; ADR 052 e 054), do arquivo do sistema."""
    config = _ler(conf)
    estilo = config.get("papel", "estilo", fallback=pastas.ESTILO_INICIAL) if config.has_section("papel") else pastas.ESTILO_INICIAL
    return estilo if estilo in pastas.ESTILOS else pastas.ESTILO_INICIAL


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


# ------------------------------------------------------------- fundo imediato
# Ao entrar na sessão, o autostart mostra o papel de parede na hora com o swaybg
# (shell/sessao/fundo-imediato), antes de a Área de Trabalho terminar de abrir. Ele lê esta
# dica, que a Área de Trabalho grava a cada mudança: três linhas (arquivo, cor, modo do swaybg).
MODOS_SWAYBG = {"preencher": "fill", "ajustar": "fit", "esticar": "stretch", "centralizar": "center", "lado-a-lado": "tile"}
IMAGENS_SWAYBG = (".jpg", ".jpeg", ".png")


def arquivo_da_dica():
    import os
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "duiaos" / "papel-inicio"


def dica_de_inicio(area):
    """Texto da dica para o fundo imediato: só imagens que o swaybg abre; senão, só a cor."""
    papel = area["padrao"]
    arquivo = papel.get("arquivo", "")
    if not arquivo.lower().endswith(IMAGENS_SWAYBG) or "\n" in arquivo:
        arquivo = ""
    return f"{arquivo}\n{papel.get('cor') or COR_PADRAO}\n{MODOS_SWAYBG.get(papel.get('ajuste'), 'fill')}\n"


def gravar_dica(area, destino=None):
    destino = Path(destino or arquivo_da_dica())
    texto = dica_de_inicio(area)
    try:
        if destino.is_file() and destino.read_text(encoding="utf-8") == texto:
            return
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
    except OSError:
        pass
