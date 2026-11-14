"""DuiaOS — aplicativos instalados (arquivos .desktop) e como abri-los.

Usado pela Ilha e pela Central de Aplicativos, pelo Explorador de Arquivos
(pasta Aplicativos e "Abrir com") e pelas Configurações (aplicativos padrão).
"""
import os
import shlex
import subprocess
import unicodedata
from pathlib import Path

PASTAS_APLICATIVOS = [
    Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
    # Aplicativos do Flathub instalados pela Duia App Store (na conta da pessoa e para todos)
    Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "flatpak/exports/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
]


def normalizar(texto):
    """Minúsculas e sem acentos, para a busca."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).casefold()


def ler_entrada(caminho):
    """Lê um arquivo .desktop. Devolve None se não for um aplicativo visível."""
    dados, na_secao = {}, False
    try:
        linhas = Path(caminho).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith("["):
            na_secao = linha == "[Desktop Entry]"
            continue
        if na_secao and "=" in linha:
            chave, valor = linha.split("=", 1)
            dados.setdefault(chave.strip(), valor.strip())
    if dados.get("Type", "Application") != "Application":
        return None
    if dados.get("NoDisplay", "").lower() == "true" or dados.get("Hidden", "").lower() == "true":
        return None

    def local(chave):
        return dados.get(chave + "[pt_BR]") or dados.get(chave + "[pt]") or dados.get(chave, "")

    caminho = Path(caminho)
    nome = local("Name") or caminho.stem
    descricao = local("GenericName") or local("Comment")
    return {
        "id": caminho.name,
        "nome": nome,
        "descricao": descricao,
        "icone": dados.get("Icon", ""),
        "exec": dados.get("Exec", ""),
        "terminal": dados.get("Terminal", "").lower() == "true",
        "classe": dados.get("StartupWMClass", "").lower(),
        "tipos": [t for t in dados.get("MimeType", "").split(";") if t],
        "categorias": [c for c in dados.get("Categories", "").split(";") if c],
        "busca": normalizar(" ".join([nome, descricao, local("Keywords"), caminho.stem])),
    }


def ler_desktop(id_desktop):
    """Procura o .desktop pelo nome do arquivo nas pastas de aplicativos."""
    for pasta in PASTAS_APLICATIVOS:
        caminho = pasta / id_desktop
        if caminho.is_file():
            return ler_entrada(caminho)
    return None


def listar_aplicativos():
    """Todos os aplicativos visíveis, em ordem alfabética."""
    encontrados = {}
    for pasta in PASTAS_APLICATIVOS:
        if not pasta.is_dir():
            continue
        for caminho in pasta.glob("*.desktop"):
            if caminho.name not in encontrados:   # a pasta do usuário tem prioridade
                encontrados[caminho.name] = ler_entrada(caminho)
    aplicativos = [a for a in encontrados.values() if a]
    aplicativos.sort(key=lambda a: normalizar(a["nome"]))
    return aplicativos


def comando_de_exec(app, arquivos=()):
    """Converte a linha Exec= em lista de argumentos.

    %f/%F/%u/%U recebem os arquivos (um ou todos); os outros códigos saem.
    """
    try:
        partes = shlex.split(app["exec"])
    except ValueError:
        return []
    arquivos = [str(a) for a in arquivos]
    comando, usou = [], False
    for parte in partes:
        if parte in ("%f", "%u"):
            if arquivos and not usou:
                comando.append(arquivos[0])
                usou = True
        elif parte in ("%F", "%U"):
            if arquivos and not usou:
                comando.extend(arquivos)
                usou = True
        elif len(parte) == 2 and parte.startswith("%"):
            continue
        else:
            comando.append(parte.replace("%%", "%"))
    if comando and arquivos and not usou:
        comando.extend(arquivos)       # Exec sem código: o arquivo vai no fim
    if comando and app.get("terminal"):
        comando = ["foot", "--"] + comando
    return comando


def aplicativos_para_tipo(tipo):
    """Aplicativos que declaram abrir o tipo MIME (para "Abrir com")."""
    geral = tipo.split("/")[0] + "/*"
    return [a for a in listar_aplicativos() if tipo in a["tipos"] or geral in a["tipos"]]


def iniciar(comando):
    """Abre um programa sem esperar e sem prendê-lo a quem abriu."""
    if not comando:
        return False
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        return True
    except OSError:
        return False


def abrir_arquivo(caminho):
    """Abre um arquivo ou pasta no aplicativo padrão (xdg-open)."""
    return iniciar(["xdg-open", str(caminho)])
