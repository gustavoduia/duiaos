"""DuiaOS — pastas do usuário (padrão XDG) e preferências da interface.

As pastas seguem o xdg-user-dirs (~/.config/user-dirs.dirs), com os nomes em
português do Debian: Área de Trabalho, Documentos, Downloads, Imagens, Música,
Vídeos. Usado pelo Explorador de Arquivos, pela Ilha de Aplicativos (Downloads
e Lixeira) e pelas Configurações.
"""
import configparser
import os
import re
from pathlib import Path

INICIO = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", INICIO / ".config"))
DADOS = Path(os.environ.get("XDG_DATA_HOME", INICIO / ".local/share"))
LIXEIRA = DADOS / "Trash"
PREFERENCIAS = CONFIG / "duiaos" / "preferencias.conf"

# chave XDG → (nome padrão em português, ícone, nome visível)
PADRAO = {
    "DESKTOP": ("Área de Trabalho", "monitor", "Área de Trabalho"),
    "DOCUMENTS": ("Documentos", "documento", "Documentos"),
    "DOWNLOAD": ("Downloads", "download", "Downloads"),
    "PICTURES": ("Imagens", "imagem", "Imagens"),
    "MUSIC": ("Música", "musica", "Música"),
    "VIDEOS": ("Vídeos", "video", "Vídeos"),
}


def ler_user_dirs(arquivo=None, inicio=None):
    """Lê ~/.config/user-dirs.dirs: {'DOWNLOAD': Path(...), ...}."""
    arquivo = Path(arquivo) if arquivo else CONFIG / "user-dirs.dirs"
    inicio = Path(inicio) if inicio else INICIO
    pastas = {}
    try:
        linhas = arquivo.read_text(encoding="utf-8").splitlines()
    except OSError:
        linhas = []
    for linha in linhas:
        achado = re.match(r'^\s*XDG_([A-Z]+)_DIR\s*=\s*"(.*)"\s*$', linha)
        if not achado:
            continue
        valor = achado.group(2).replace("$HOME", str(inicio))
        caminho = Path(valor)
        if caminho != inicio:            # XDG usa $HOME para "desligado"
            pastas[achado.group(1)] = caminho
    return pastas


def pasta(chave, arquivo=None, inicio=None):
    """Caminho de uma pasta do usuário (ex.: 'DOWNLOAD'), mesmo sem o user-dirs.dirs."""
    inicio = Path(inicio) if inicio else INICIO
    return ler_user_dirs(arquivo, inicio).get(chave) or inicio / PADRAO[chave][0]


def favoritos(arquivo=None, inicio=None):
    """Itens fixos da barra lateral do Explorador, na ordem."""
    inicio = Path(inicio) if inicio else INICIO
    itens = [{"nome": "Início", "icone": "casa", "caminho": str(inicio)}]
    for chave in ("DESKTOP", "DOCUMENTS", "DOWNLOAD", "PICTURES", "MUSIC", "VIDEOS"):
        _, icone, nome = PADRAO[chave]
        itens.append({"nome": nome, "icone": icone, "caminho": str(pasta(chave, arquivo, inicio))})
    return itens


def criar_pastas_padrao(arquivo=None, inicio=None):
    """Garante que as pastas do usuário existam (1ª entrada)."""
    for chave in PADRAO:
        try:
            pasta(chave, arquivo, inicio).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


# ---------------------------------------------------------------- preferências

def ler_preferencia(secao, chave, padrao="", arquivo=None):
    config = configparser.ConfigParser()
    config.read(arquivo or PREFERENCIAS, encoding="utf-8")
    return config.get(secao, chave, fallback=padrao)


def gravar_preferencia(secao, chave, valor, arquivo=None):
    arquivo = Path(arquivo or PREFERENCIAS)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config.read(arquivo, encoding="utf-8")
    if not config.has_section(secao):
        config.add_section(secao)
    config.set(secao, chave, str(valor))
    temporario = arquivo.with_suffix(".tmp")
    with open(temporario, "w", encoding="utf-8") as saida:
        saida.write("# DuiaOS — preferências da interface (Configurações).\n")
        config.write(saida)
    os.replace(temporario, arquivo)
