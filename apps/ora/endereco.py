"""DuiaOS — Ora: o que a pessoa digita na barra de endereço vira um endereço ou uma busca.

    normalizar("duiaos.com.br")        → "https://duiaos.com.br"
    normalizar("receita de bolo")      → busca no buscador escolhido
    normalizar("localhost:8080/teste") → "http://localhost:8080/teste"

Sem Qt: testável sozinho (shell/testes/test_ora.py).
"""
import ipaddress
import re
from urllib.parse import quote_plus, urlsplit

# Buscadores oferecidos nas Configurações do Ora. "%s" recebe o texto já codificado.
BUSCADORES = {
    "google": {"nome": "Google", "busca": "https://www.google.com/search?q=%s",
               "sugestoes": "https://suggestqueries.google.com/complete/search?client=firefox&q=%s"},
    "duckduckgo": {"nome": "DuckDuckGo", "busca": "https://duckduckgo.com/?q=%s",
                   "sugestoes": "https://duckduckgo.com/ac/?type=list&q=%s"},
    "bing": {"nome": "Bing", "busca": "https://www.bing.com/search?q=%s",
             "sugestoes": "https://api.bing.com/osjson.aspx?query=%s"},
    "brave": {"nome": "Brave Search", "busca": "https://search.brave.com/search?q=%s",
              "sugestoes": "https://search.brave.com/api/suggest?q=%s"},
    "ecosia": {"nome": "Ecosia", "busca": "https://www.ecosia.org/search?q=%s",
               "sugestoes": "https://ac.ecosia.org/autocomplete?type=list&q=%s"},
}
BUSCADOR_PADRAO = "google"

ESQUEMAS = ("http", "https", "file", "about", "view-source", "data", "mailto", "ftp", "blob", "chrome", "ora")
# Domínio: rótulos de letras, números e hífens, com um final só de letras (ou "localhost")
_ROTULO = r"(?!-)[a-z0-9\-À-￿]{1,63}(?<!-)"
_DOMINIO = re.compile(rf"^(?:{_ROTULO}\.)+[a-zÀ-￿]{{2,63}}\.?$", re.IGNORECASE)


def url_de_busca(texto, buscador=BUSCADOR_PADRAO):
    modelo = BUSCADORES.get(buscador, BUSCADORES[BUSCADOR_PADRAO])["busca"]
    return modelo.replace("%s", quote_plus(texto))


# Extensões de arquivo que não viram domínio quando digitadas sozinhas ("relatorio.pdf" é busca)
_EXTENSOES = {"pdf", "txt", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "jpg", "jpeg", "png", "gif",
              "svg", "webp", "mp3", "mp4", "avi", "mkv", "mov", "wav", "exe", "deb", "iso", "tar", "gz", "rar", "html",
              "htm", "json", "csv", "js", "css", "xml", "bin", "dll"}


def _eh_host(host):
    host = host.strip("[]")
    if host.lower() == "localhost":
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return bool(_DOMINIO.match(host))


def parece_endereco(texto):
    """Sem espaços e com cara de domínio, IP ou localhost (com porta e caminho opcionais)."""
    if not texto or any(c.isspace() for c in texto):
        return False
    partes = urlsplit("//" + texto)
    try:
        host, porta = partes.hostname or "", partes.port      # porta inválida levanta ValueError
    except ValueError:
        return False
    if not host:
        return False
    sem_mais = partes.path in ("", "/") and porta is None and not texto.lower().startswith("www.")
    if sem_mais and host.rsplit(".", 1)[-1].lower() in _EXTENSOES:
        return False
    return _eh_host(host)


def normalizar(texto, buscador=BUSCADOR_PADRAO):
    """Endereço pronto para abrir, a partir do que a pessoa digitou."""
    texto = (texto or "").strip()
    if not texto:
        return ""
    esquema = texto.split(":", 1)[0].lower() if ":" in texto else ""
    if esquema in ESQUEMAS and (texto[len(esquema) + 1:].startswith("//") or esquema in (
            "about", "data", "mailto", "view-source", "blob")):
        return texto
    if texto.startswith("/") and " " not in texto:
        return "file://" + texto
    if parece_endereco(texto):
        host = (urlsplit("//" + texto).hostname or "").lower()
        local = host == "localhost" or host.endswith(".local") or _ip_privado(host)
        return ("http://" if local else "https://") + texto
    return url_de_busca(texto, buscador)


def _ip_privado(host):
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback


def para_mostrar(url):
    """Endereço como aparece na barra quando ela não está em foco: sem https:// e sem a barra final."""
    if not url:
        return ""
    texto = re.sub(r"^https://", "", url)
    texto = re.sub(r"^www\.", "", texto)
    return texto[:-1] if texto.endswith("/") and texto.count("/") == 1 else texto


def dominio(url):
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host
