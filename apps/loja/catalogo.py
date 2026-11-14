"""DuiaOS — Duia App Store: o catálogo de aplicativos (ADR 049).

Duas fontes, as mesmas que alimentam as lojas do GNOME e do KDE, lidas aqui pelo
próprio DuiaOS (nenhum código delas):

  Debian   metadados AppStream do arquivo do Debian (DEP-11, YAML) que o apt baixa
           junto com as listas de pacotes (pacote "appstream"); ícones já
           extraídos em /var/lib/swcatalog/icons. Instalação pelo duiaos-agente.
  Flathub  metadados AppStream (XML) que o flatpak baixa do remoto "flathub" da
           pessoa (flatpak --user). Instalação pelo flatpak, sem senha.

Cada aplicativo vira um dicionário simples para a interface:
  {id, fonte, componente, pacote, nome, resumo, descricao, desenvolvedor, licenca,
   livre, categorias, icone, iconeReserva, capturas, site, versao, verificado, lancador, busca}

Só a biblioteca padrão (o YAML do Debian é lido pelo PyYAML, licença MIT, quando
existe). O resultado de cada fonte fica num cache em ~/.cache/duiaos/loja.
"""
import gzip
import html
import json
import lzma
import os
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "duiaos" / "loja"
LISTAS_APT = Path("/var/lib/apt/lists")
PASTAS_YAML = tuple(Path(p) for p in os.environ.get("DUIAOS_LOJA_LISTAS", "").split(":") if p) or (
    Path("/var/lib/swcatalog/yaml"), LISTAS_APT)                 # DUIAOS_LOJA_LISTAS: só para testes
PASTAS_ICONES = (Path("/var/lib/swcatalog/icons"), Path("/var/cache/swcatalog/icons"),
                 Path("/var/lib/app-info/icons"), Path("/var/cache/app-info/icons"))
FLATHUB = "flathub"
FLATHUB_REPO = "https://dl.flathub.org/repo/flathub.flatpakrepo"
VERSAO_CACHE = 3

# Categorias principais do freedesktop.org → nome em português, ícone e cor do ladrilho
CATEGORIAS = [
    {"id": "Office", "nome": "Escritório", "icone": "documento", "cor": "azul"},
    {"id": "Graphics", "nome": "Fotos e design", "icone": "imagem", "cor": "noite"},
    {"id": "AudioVideo", "nome": "Música e vídeo", "icone": "musica", "cor": "azul"},
    {"id": "Network", "nome": "Internet", "icone": "globo", "cor": "noite"},
    {"id": "Game", "nome": "Jogos", "icone": "controles", "cor": "azul"},
    {"id": "Education", "nome": "Educação", "icone": "estrela", "cor": "noite"},
    {"id": "Development", "nome": "Desenvolvimento", "icone": "codigo", "cor": "azul"},
    {"id": "Science", "nome": "Ciência", "icone": "ia", "cor": "noite"},
    {"id": "Utility", "nome": "Utilitários", "icone": "engrenagem", "cor": "azul"},
    {"id": "System", "nome": "Sistema", "icone": "computador", "cor": "noite"},
]
_SINONIMOS = {"Audio": "AudioVideo", "Video": "AudioVideo", "Player": "AudioVideo", "Recorder": "AudioVideo",
              "Photography": "Graphics", "2DGraphics": "Graphics", "3DGraphics": "Graphics",
              "RasterGraphics": "Graphics", "VectorGraphics": "Graphics", "WebBrowser": "Network",
              "Email": "Network", "Chat": "Network", "InstantMessaging": "Network", "IDE": "Development",
              "TextEditor": "Utility", "Accessories": "Utility", "Settings": "System", "Spreadsheet": "Office",
              "WordProcessor": "Office", "Presentation": "Office"}
IDS_CATEGORIAS = {c["id"] for c in CATEGORIAS}

# Licenças livres mais comuns (SPDX); o resto aparece como "proprietária" ou como veio
_LIVRES = re.compile(r"^(?:L?GPL|AGPL|MIT|BSD|Apache|MPL|ISC|Zlib|CC0|CC-BY|Artistic|EPL|EUPL|OFL|Unlicense|"
                     r"WTFPL|PSF|Python|BSL|Ruby|PHP|curl|X11|Vim|GFDL|0BSD|MS-PL|NCSA|Unicode)", re.I)


# ------------------------------------------------------------------ texto

def normalizar(texto):
    """Minúsculas e sem acentos, para a busca."""
    sem = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in sem if not unicodedata.combining(c)).lower()


IDIOMAS_NOME = ("C", "en", "pt_BR", "pt")       # o nome é a marca: "GIMP", não a tradução do nome


def traduzido(valor, idiomas=("pt_BR", "pt-BR", "pt", "C", "en")):
    """Texto no idioma da pessoa: {"C": ..., "pt_BR": ...} → o melhor que houver."""
    if isinstance(valor, str):
        return valor
    if not isinstance(valor, dict) or not valor:
        return ""
    for idioma in idiomas:
        if valor.get(idioma):
            return str(valor[idioma])
    return str(next(iter(valor.values())))


def html_para_texto(texto):
    """Descrição do AppStream (<p>, <ul><li>, <em>…) → parágrafos de texto simples."""
    if not texto:
        return ""
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"<li[^>]*>", "\n• ", texto, flags=re.I)
    texto = re.sub(r"</(p|ul|ol)>", "\n\n", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", "", texto)
    linhas = [linha.strip() for linha in html.unescape(texto).split("\n")]
    texto = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def eh_livre(licenca):
    licenca = (licenca or "").strip()
    if not licenca or "LicenseRef-proprietary" in licenca:
        return False
    return all(_LIVRES.match(parte.strip("() ")) for parte in re.split(r"\s+(?:AND|OR|WITH)\s+", licenca)
               if parte.strip("() ") and "exception" not in parte.lower())


def nome_da_licenca(licenca):
    licenca = (licenca or "").strip()
    if not licenca:
        return "Não informada"
    if "LicenseRef-proprietary" in licenca:
        return "Proprietária"
    return licenca.replace(" AND ", " e ").replace(" OR ", " ou ")


def categorias_principais(lista):
    """Categorias do .desktop → as principais da loja, sem repetir."""
    saida = []
    for categoria in lista or []:
        principal = categoria if categoria in IDS_CATEGORIAS else _SINONIMOS.get(categoria)
        if principal and principal not in saida:
            saida.append(principal)
    return saida


def montar(fonte, componente, pacote, nome, resumo="", descricao="", desenvolvedor="", licenca="",
           categorias=(), icone="", capturas=(), site="", versao="", verificado=False, lancador=""):
    categorias = categorias_principais(categorias)
    return {"id": f"{fonte}:{pacote if fonte == 'debian' else componente}", "fonte": fonte,
            "componente": componente, "pacote": pacote, "nome": nome, "resumo": resumo,
            "descricao": descricao, "desenvolvedor": desenvolvedor, "licenca": nome_da_licenca(licenca),
            "livre": eh_livre(licenca), "categorias": categorias, "icone": icone,
            "capturas": list(capturas)[:6], "site": site, "versao": versao, "verificado": bool(verificado),
            "lancador": lancador,
            # Ícone do tema do sistema com o mesmo nome, para quando o ícone do catálogo não existir
            "iconeReserva": icone if icone and "/" not in icone else (lancador or componente).removesuffix(".desktop"),
            "busca": normalizar(" ".join([nome, resumo, componente, pacote, desenvolvedor]))}


# ------------------------------------------------------------- Debian (DEP-11)

def documentos_dep11(texto):
    """Divide o YAML do DEP-11 em (cabeçalho, [documentos de aplicativos de área de trabalho])."""
    partes = re.split(r"^---\s*$", texto, flags=re.M)
    partes = [p for p in partes if p.strip()]
    if not partes:
        return "", []
    # Só os aplicativos de área de trabalho são lidos de verdade (o resto — fontes, codecs,
    # bibliotecas — é a maior parte do arquivo e não aparece na loja)
    return partes[0], [p for p in partes[1:] if re.search(r"^Type:\s*desktop-application\s*$", p[:400], re.M)]


def _yaml():
    try:
        import yaml
    except ImportError:
        return None
    carregador = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return lambda texto: yaml.load(texto, Loader=carregador)  # noqa: S506 (SafeLoader)


def icone_debian(dados, origem, base_midia, pastas_icones=PASTAS_ICONES):
    """Ícone do componente: o arquivo já extraído pelo appstream, o endereço remoto ou o nome do tema."""
    icones = dados.get("Icon") or {}
    for cacheado in sorted(icones.get("cached") or [], key=lambda i: -int(i.get("width", 0) or 0)):
        tamanho = f"{cacheado.get('width', 64)}x{cacheado.get('height', 64)}"
        for pasta in pastas_icones:
            caminho = pasta / origem / tamanho / str(cacheado.get("name", ""))
            if caminho.is_file():
                return str(caminho)
    for remoto in icones.get("remote") or []:
        url = str(remoto.get("url", ""))
        if url:
            return url if url.startswith("http") else base_midia.rstrip("/") + "/" + url
    stock = icones.get("stock")
    return str(stock) if stock else ""


def capturas_debian(dados, base_midia):
    urls = []
    for captura in dados.get("Screenshots") or []:
        imagem = (captura.get("source-image") or {}).get("url") or ""
        miniaturas = sorted(captura.get("thumbnails") or [], key=lambda m: -int(m.get("width", 0) or 0))
        for miniatura in miniaturas:
            if 600 <= int(miniatura.get("width", 0) or 0) <= 1300:
                imagem = miniatura.get("url") or imagem
                break
        if imagem:
            url = imagem if imagem.startswith("http") else base_midia.rstrip("/") + "/" + imagem
            (urls.insert(0, url) if captura.get("default") else urls.append(url))
    return urls


def ler_dep11(texto, pastas_icones=PASTAS_ICONES, carregar=None):
    """Texto de um Components-ARQ.yml → lista de aplicativos (fonte "debian")."""
    carregar = carregar or _yaml()
    if carregar is None:
        return []
    cabecalho, documentos = documentos_dep11(texto)
    try:
        cab = carregar(cabecalho) or {}
    except Exception:
        cab = {}
    origem, base_midia = str(cab.get("Origin", "")), str(cab.get("MediaBaseUrl", ""))
    apps = []
    for documento in documentos:
        try:
            dados = carregar(documento) or {}
        except Exception:
            continue                                     # um componente estragado não derruba a loja
        pacote = dados.get("Package")
        if not pacote or not dados.get("Name"):
            continue
        desenvolvedor = traduzido((dados.get("Developer") or {}).get("name")) or traduzido(dados.get("DeveloperName"))
        apps.append(montar("debian", str(dados.get("ID", "")), str(pacote), traduzido(dados["Name"], IDIOMAS_NOME),
                           traduzido(dados.get("Summary")), html_para_texto(traduzido(dados.get("Description"))),
                           desenvolvedor, str(dados.get("ProjectLicense", "")), dados.get("Categories") or [],
                           icone_debian(dados, origem, base_midia, pastas_icones), capturas_debian(dados, base_midia),
                           str((dados.get("Url") or {}).get("homepage", "")),
                           lancador=str(((dados.get("Launchable") or {}).get("desktop-id") or [""])[0])))
    return apps


def abrir_comprimido(caminho):
    """Lê um arquivo da lista do apt, comprimido ou não."""
    caminho = Path(caminho)
    if caminho.suffix == ".gz":
        return gzip.decompress(caminho.read_bytes()).decode("utf-8", "replace")
    if caminho.suffix == ".xz":
        return lzma.decompress(caminho.read_bytes()).decode("utf-8", "replace")
    if caminho.suffix == ".lz4":
        try:
            saida = subprocess.run(["lz4cat", str(caminho)], capture_output=True, timeout=60, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            return ""
        return saida.decode("utf-8", "replace")
    return caminho.read_text(encoding="utf-8", errors="replace")


def arquivos_dep11(pastas=PASTAS_YAML):
    """Arquivos de componentes do Debian que o apt baixou (um por origem/seção), sem repetir."""
    vistos, arquivos = set(), []
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        for caminho in sorted(pasta.iterdir()):
            if "Components-" not in caminho.name or ".yml" not in caminho.name:
                continue
            real = caminho.resolve()
            chave = real.name.split(".yml")[0]
            if chave in vistos or not real.is_file():
                continue
            vistos.add(chave)
            arquivos.append(real)
    return arquivos


def catalogo_debian(pastas=PASTAS_YAML, pastas_icones=PASTAS_ICONES):
    apps = {}
    for arquivo in arquivos_dep11(pastas):
        for app in ler_dep11(abrir_comprimido(arquivo), pastas_icones):
            apps.setdefault(app["id"], app)          # o primeiro arquivo (a origem principal) ganha
    return list(apps.values())


# ---------------------------------------------------------- Flathub (AppStream)

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _texto_traduzido(componente, etiqueta, idiomas=None):
    valores = {}
    for elemento in componente.findall(etiqueta):
        valores[elemento.get(_XML_LANG, "C")] = (elemento.text or "").strip()
    return traduzido(valores, idiomas) if idiomas else traduzido(valores)


def _descricao_xml(componente):
    """<description> → texto simples, em português quando houver tradução (os parágrafos traduzidos
    vêm no mesmo <description>, cada um com xml:lang)."""
    for idioma in ("pt_BR", "pt", None):
        partes = []
        for descricao in componente.findall("description"):
            idioma_descricao = descricao.get(_XML_LANG)
            for filho in descricao:
                idioma_filho = filho.get(_XML_LANG, idioma_descricao)
                if filho.tag == "p" and idioma_filho == idioma:
                    partes.append(" ".join("".join(filho.itertext()).split()))
                elif filho.tag in ("ul", "ol"):
                    itens = [i for i in filho.findall("li") if i.get(_XML_LANG, idioma_filho) == idioma]
                    if itens:
                        partes.append("\n".join("• " + " ".join("".join(i.itertext()).split()) for i in itens))
        texto = "\n\n".join(p for p in partes if p)
        if texto:
            return texto
    return ""


def ler_appstream_xml(conteudo, pasta_icones=None, arquitetura="x86_64"):
    """AppStream XML do Flathub → lista de aplicativos (fonte "flathub")."""
    raiz = ET.fromstring(conteudo)
    apps = []
    for componente in raiz.findall("component"):
        if componente.get("type") not in ("desktop-application", "desktop"):
            continue
        componente_id = (componente.findtext("id") or "").strip().removesuffix(".desktop")
        nome = _texto_traduzido(componente, "name", IDIOMAS_NOME)
        if not componente_id or not nome:
            continue
        ref = (componente.findtext("bundle[@type='flatpak']") or "").strip()
        app_id = ref.split("/")[1] if ref.count("/") >= 2 else componente_id
        icone = ""
        for elemento in sorted(componente.findall("icon"), key=lambda i: -int(i.get("width", "0") or 0)):
            if elemento.get("type") == "cached" and pasta_icones:
                caminho = Path(pasta_icones) / f"{elemento.get('width', '128')}x{elemento.get('height', '128')}" / (elemento.text or "").strip()
                if caminho.is_file():
                    icone = str(caminho)
                    break
            if elemento.get("type") == "remote" and not icone:
                icone = (elemento.text or "").strip()
        capturas = []
        for captura in componente.findall("screenshots/screenshot"):
            imagens = captura.findall("image")
            escolhida = next((i for i in imagens if i.get("type") == "thumbnail" and 600 <= int(i.get("width", "0") or 0) <= 1300), None)
            if escolhida is None:                       # (um Element sem filhos é "falso": comparar com None)
                escolhida = next((i for i in imagens if i.get("type") == "source"), None)
            if escolhida is None and imagens:
                escolhida = imagens[0]
            if escolhida is not None and escolhida.text:
                url = escolhida.text.strip()
                (capturas.insert(0, url) if captura.get("type") == "default" else capturas.append(url))
        desenvolvedor = _texto_traduzido(componente, "developer/name") or _texto_traduzido(componente, "developer_name")
        verificado = any(v.get("key") == "flathub::verification::verified" and (v.text or "").strip() == "true"
                         for v in componente.findall("custom/value") + componente.findall("metadata/value"))
        versao = ""
        release = componente.find("releases/release")
        if release is not None:
            versao = release.get("version", "")
        apps.append(montar("flathub", componente_id, app_id, nome, _texto_traduzido(componente, "summary"),
                           _descricao_xml(componente), desenvolvedor, (componente.findtext("project_license") or "").strip(),
                           [c.text.strip() for c in componente.findall("categories/category") if c.text],
                           icone, capturas, (componente.findtext("url[@type='homepage']") or "").strip(), versao,
                           verificado, (componente.findtext("launchable[@type='desktop-id']") or "").strip()))
    return apps


def pasta_appstream_flathub(arquitetura=None):
    """Onde o flatpak guardou o AppStream do Flathub (da pessoa primeiro, depois o do sistema)."""
    arquitetura = arquitetura or {"aarch64": "aarch64", "arm64": "aarch64"}.get(os.uname().machine, "x86_64")
    for base in (Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "flatpak",
                 Path("/var/lib/flatpak")):
        pasta = base / "appstream" / FLATHUB / arquitetura / "active"
        if (pasta / "appstream.xml.gz").is_file() or (pasta / "appstream.xml").is_file():
            return pasta
    return None


def catalogo_flathub(pasta=None):
    pasta = pasta or pasta_appstream_flathub()
    if not pasta:
        return []
    arquivo = pasta / "appstream.xml.gz"
    conteudo = gzip.decompress(arquivo.read_bytes()) if arquivo.is_file() else (pasta / "appstream.xml").read_bytes()
    return ler_appstream_xml(conteudo, pasta / "icons")


# ------------------------------------------------------------------- cache

def assinatura_fontes(fonte):
    """Data e tamanho dos arquivos de origem: se mudarem, o cache é refeito."""
    if fonte == "debian":
        arquivos = arquivos_dep11()
    else:
        pasta = pasta_appstream_flathub()
        arquivos = [p for p in (pasta / "appstream.xml.gz", pasta / "appstream.xml") if p.is_file()] if pasta else []
    return [[str(a), int(a.stat().st_mtime), a.stat().st_size] for a in arquivos]


def carregar(fonte, gerar=None, pasta_cache=None):
    """Catálogo de uma fonte, do cache quando as origens não mudaram."""
    pasta_cache = Path(pasta_cache or CACHE)
    arquivo = pasta_cache / f"{fonte}.json"
    assinatura = assinatura_fontes(fonte)
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        if dados.get("versao") == VERSAO_CACHE and dados.get("assinatura") == assinatura:
            return dados["apps"]
    except (OSError, ValueError, KeyError):
        pass
    gerar = gerar or {"debian": catalogo_debian, "flathub": catalogo_flathub}[fonte]
    apps = gerar() if assinatura else []
    try:
        pasta_cache.mkdir(parents=True, exist_ok=True)
        temporario = arquivo.with_suffix(".tmp")
        temporario.write_text(json.dumps({"versao": VERSAO_CACHE, "assinatura": assinatura, "criado": int(time.time()),
                                          "apps": apps}, ensure_ascii=False), encoding="utf-8")
        temporario.replace(arquivo)
    except OSError:
        pass
    return apps


# ------------------------------------------------------- o que está instalado

def interpretar_dpkg(saida):
    """dpkg-query -W -f='${Package}\\t${db:Status-Abbrev}\\t${Version}\\n' → {pacote: versão}."""
    instalados = {}
    for linha in saida.splitlines():
        partes = linha.split("\t")
        if len(partes) >= 3 and partes[1].startswith("ii"):
            instalados[partes[0].split(":")[0]] = partes[2]
    return instalados


def interpretar_flatpak_lista(saida):
    """flatpak list --app --columns=application,version,installation → {id: {versao, instalacao}}."""
    instalados = {}
    for linha in saida.splitlines():
        partes = linha.split("\t")
        if partes and partes[0].strip() and "." in partes[0]:
            instalados[partes[0].strip()] = {"versao": partes[1].strip() if len(partes) > 1 else "",
                                             "instalacao": partes[2].strip() if len(partes) > 2 else "user"}
    return instalados


def _rodar(comando, tempo=30):
    try:
        return subprocess.run(comando, capture_output=True, text=True, timeout=tempo, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def instalados_debian():
    return interpretar_dpkg(_rodar(["dpkg-query", "-W", "-f=${Package}\t${db:Status-Abbrev}\t${Version}\n"]))


def instalados_flathub():
    return interpretar_flatpak_lista(_rodar(["flatpak", "list", "--app", "--columns=application,version,installation"]))


def atualizacoes_flathub():
    """IDs dos aplicativos do Flathub com versão nova (das duas instalações)."""
    saida = _rodar(["flatpak", "remote-ls", "--updates", "--app", "--columns=application"], tempo=90)
    return sorted({linha.strip() for linha in saida.splitlines() if "." in linha.strip()})


def flatpak_disponivel():
    from shutil import which
    return which("flatpak") is not None


def preparar_flathub(forcar=False):
    """Liga o Flathub para a pessoa (sem senha) e baixa o catálogo quando tem mais de 1 dia.
    Devolve "" ou a mensagem de erro."""
    if not flatpak_disponivel():
        return "o flatpak não está instalado; dá para ver os aplicativos, mas não para instalá-los."
    pasta = pasta_appstream_flathub()
    if pasta and not forcar and time.time() - max((p.stat().st_mtime for p in pasta.iterdir()), default=0) < 86400:
        return ""
    for comando in (["flatpak", "remote-add", "--user", "--if-not-exists", FLATHUB, FLATHUB_REPO],
                    ["flatpak", "update", "--user", "--appstream", FLATHUB]):
        try:
            resultado = subprocess.run(comando, capture_output=True, text=True, timeout=300, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return "não respondeu (confira a internet); a lista pode estar desatualizada."
        if resultado.returncode != 0:
            return (resultado.stderr.strip().splitlines() or ["Não consegui ligar o Flathub."])[-1][:200]
    return ""


# ------------------------------------------------------------ busca e vitrine

def buscar(apps, termo, limite=200):
    """Aplicativos que contêm todas as palavras do termo; o nome conta mais que o resto."""
    palavras = normalizar(termo).split()
    if not palavras:
        return []
    achados = []
    for app in apps:
        if all(p in app["busca"] for p in palavras):
            nome = normalizar(app["nome"])
            nota = (0 if nome == " ".join(palavras) else 1 if nome.startswith(palavras[0]) else
                    2 if all(p in nome for p in palavras) else 3)
            achados.append((nota, nome, app))
    achados.sort(key=lambda a: (a[0], a[1]))
    return [a[2] for a in achados[:limite]]


def juntar(debian, flathub, preferir="flathub"):
    """As duas fontes numa lista só. Um mesmo aplicativo (mesmo componente) aparece uma vez, pela
    fonte preferida, e leva a outra em "alternativa" para a pessoa poder escolher."""
    por_componente = {}
    ordem = (flathub, debian) if preferir == "flathub" else (debian, flathub)
    for lista in ordem:
        for app in lista:
            chave = app["componente"].removesuffix(".desktop").lower() or app["id"]
            if chave in por_componente:
                por_componente[chave].setdefault("alternativa", {"id": app["id"], "fonte": app["fonte"]})
            else:
                por_componente[chave] = dict(app)
    return sorted(por_componente.values(), key=lambda a: normalizar(a["nome"]))


def ler_destaques(arquivo):
    try:
        return json.loads(Path(arquivo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"destaques": [], "colecoes": []}


def vitrine(apps, destaques):
    """Página Descobrir: destaques e coleções curadas (destaques.json), só com o que existe no catálogo."""
    por_componente = {app["componente"].lower(): app for app in apps}
    por_pacote = {app["pacote"].lower(): app for app in apps}

    def achar(refs):
        """"org.gimp.GIMP|gimp": a primeira opção que existir no catálogo."""
        for ref in refs.lower().split("|"):
            app = por_componente.get(ref) or por_componente.get(ref + ".desktop") or por_pacote.get(ref)
            if app:
                return app
        return None

    grandes = []
    for destaque in destaques.get("destaques", []):
        app = achar(destaque.get("app", ""))
        if app:
            grandes.append({**destaque, "app": app})
    colecoes = []
    for colecao in destaques.get("colecoes", []):
        itens, vistos = [], set()
        for app in (achar(r) for r in colecao.get("apps", [])):
            if app and app["id"] not in vistos:          # o componente e o pacote podem achar o mesmo
                vistos.add(app["id"])
                itens.append(app)
        if itens:
            colecoes.append({"titulo": colecao.get("titulo", ""), "apps": itens})
    return {"destaques": grandes, "colecoes": colecoes}


# ------------------------------------------------------- andamento do flatpak

_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_ETAPA = re.compile(r"^(Installing|Updating|Uninstalling)\s+(\d+)/(\d+)")
_PORCENTO = re.compile(r"(\d{1,3})%")


def limpar_terminal(texto):
    """Tira as sequências de cor e de cursor que o flatpak escreve no terminal."""
    return _ANSI.sub("", texto).replace("\u2588", "").replace("\u2026", "…").strip()


def ler_linha_flatpak(linha, acao):
    """Uma linha do flatpak (em inglês, num terminal) → (fração 0–1 ou None, mensagem em português).
    Com várias partes ("Installing 2/3… 40%"), a fração é a do conjunto."""
    linha = limpar_terminal(linha)
    if not linha:
        return None, ""
    porcentos = _PORCENTO.findall(linha)
    parte = int(porcentos[-1]) / 100 if porcentos else None
    etapa = _ETAPA.match(linha)
    verbo = {"instalar": "Instalando", "atualizar": "Atualizando", "remover": "Removendo"}.get(acao, "Trabalhando")
    if etapa:
        atual, total = int(etapa.group(2)), max(1, int(etapa.group(3)))
        fracao = ((atual - 1) + (parte or 0)) / total
        return fracao, f"{verbo} (parte {atual} de {total})" + (f" — {porcentos[-1]}%" if porcentos else "")
    minuscula = linha.lower()
    if minuscula.startswith(("installing", "updating", "uninstalling")):
        return parte, verbo + (f" — {porcentos[-1]}%" if porcentos else "")
    if "looking for matches" in minuscula:
        return None, "Conferindo o que precisa"
    if minuscula.startswith(("error", "erro")):
        return None, linha[:160]
    return parte, (verbo + f" — {porcentos[-1]}%") if porcentos else ""
