"""DuiaOS — Ora: favoritos, histórico, downloads, sessão e configurações, guardados no computador.

Banco SQLite em ~/.local/share/duiaos/ora/ora.db (busca no histórico pelo FTS5); configurações em
~/.config/duiaos/ora.json. A janela privada não grava nada aqui.

Importação de favoritos: Chrome/Chromium (arquivo Bookmarks, JSON), Firefox (places.sqlite) e o
arquivo HTML de favoritos que todos os navegadores exportam.

Sem Qt: testável sozinho (shell/testes/test_ora.py).
"""
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import time
from html.parser import HTMLParser
from pathlib import Path

PASTA_DADOS = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "duiaos" / "ora"
ARQUIVO_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos" / "ora.json"

PADROES = {
    "buscador": "google",
    "ao_iniciar": "inicio",            # inicio | sessao | pagina
    "pagina_inicial": "",              # usada quando ao_iniciar = pagina
    "barra_de_favoritos": True,
    "zoom_padrao": 1.0,
    "perguntar_onde_salvar": False,
    "pasta_downloads": "",             # vazio: a pasta Downloads da pessoa
    "nao_rastrear": True,              # cabeçalho DNT/Sec-GPC nas requisições
    "bloquear_cookies_de_terceiros": False,
    "corretor_ortografico": True,
    "sessao": [],                      # abas da última vez: [{"url", "titulo"}]
}

ESQUEMA = """
CREATE TABLE IF NOT EXISTS favoritos (
    id INTEGER PRIMARY KEY, url TEXT NOT NULL, titulo TEXT NOT NULL DEFAULT '',
    pasta TEXT NOT NULL DEFAULT '', ordem REAL NOT NULL DEFAULT 0, criado REAL NOT NULL,
    UNIQUE (url, pasta));
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY, url TEXT NOT NULL UNIQUE, titulo TEXT NOT NULL DEFAULT '',
    visitas INTEGER NOT NULL DEFAULT 1, ultima REAL NOT NULL);
CREATE INDEX IF NOT EXISTS historico_ultima ON historico (ultima DESC);
CREATE VIRTUAL TABLE IF NOT EXISTS historico_busca USING fts5 (
    url, titulo, content='historico', content_rowid='id', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS historico_ai AFTER INSERT ON historico BEGIN
    INSERT INTO historico_busca (rowid, url, titulo) VALUES (new.id, new.url, new.titulo); END;
CREATE TRIGGER IF NOT EXISTS historico_ad AFTER DELETE ON historico BEGIN
    INSERT INTO historico_busca (historico_busca, rowid, url, titulo) VALUES ('delete', old.id, old.url, old.titulo); END;
CREATE TRIGGER IF NOT EXISTS historico_au AFTER UPDATE ON historico BEGIN
    INSERT INTO historico_busca (historico_busca, rowid, url, titulo) VALUES ('delete', old.id, old.url, old.titulo);
    INSERT INTO historico_busca (rowid, url, titulo) VALUES (new.id, new.url, new.titulo); END;
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY, url TEXT NOT NULL, arquivo TEXT NOT NULL, tamanho INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL, data REAL NOT NULL);
"""

# Endereços que não entram no histórico
_FORA_DO_HISTORICO = ("about:", "data:", "view-source:", "blob:", "chrome:", "ora:")


class Banco:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else PASTA_DADOS / "ora.db"
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._trava = threading.Lock()
        self._con = sqlite3.connect(self.caminho, check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.executescript(ESQUEMA)
        os.chmod(self.caminho, 0o600)

    def _exec(self, sql, parametros=()):
        with self._trava, self._con:
            return self._con.execute(sql, parametros)

    def _todos(self, sql, parametros=()):
        with self._trava:
            return [dict(l) for l in self._con.execute(sql, parametros).fetchall()]

    def fechar(self):
        self._con.close()

    # ---------------------------------------------------------------- favoritos
    def adicionar_favorito(self, url, titulo, pasta=""):
        if not url:
            return
        ordem = (self._todos("SELECT COALESCE(MAX(ordem), 0) AS m FROM favoritos WHERE pasta = ?", (pasta,))[0]["m"]) + 1
        self._exec("INSERT INTO favoritos (url, titulo, pasta, ordem, criado) VALUES (?, ?, ?, ?, ?) "
                   "ON CONFLICT (url, pasta) DO UPDATE SET titulo = excluded.titulo",
                   (url, titulo or url, pasta, ordem, time.time()))

    def remover_favorito(self, url):
        self._exec("DELETE FROM favoritos WHERE url = ?", (url,))

    def renomear_favorito(self, id_favorito, titulo, url=None):
        if url:
            self._exec("UPDATE favoritos SET titulo = ?, url = ? WHERE id = ?", (titulo, url, id_favorito))
        else:
            self._exec("UPDATE favoritos SET titulo = ? WHERE id = ?", (titulo, id_favorito))

    def mover_favorito(self, id_favorito, pasta):
        self._exec("UPDATE OR IGNORE favoritos SET pasta = ? WHERE id = ?", (pasta, id_favorito))

    def eh_favorito(self, url):
        return bool(url) and bool(self._todos("SELECT 1 FROM favoritos WHERE url = ? LIMIT 1", (url,)))

    def favoritos(self, pasta=None):
        if pasta is None:
            return self._todos("SELECT * FROM favoritos ORDER BY pasta, ordem")
        return self._todos("SELECT * FROM favoritos WHERE pasta = ? ORDER BY ordem", (pasta,))

    def pastas(self):
        return [l["pasta"] for l in self._todos("SELECT DISTINCT pasta FROM favoritos WHERE pasta != '' ORDER BY pasta")]

    # ---------------------------------------------------------------- histórico
    def registrar_visita(self, url, titulo=""):
        if not url or url.startswith(_FORA_DO_HISTORICO):
            return
        agora = time.time()
        self._exec("INSERT INTO historico (url, titulo, visitas, ultima) VALUES (?, ?, 1, ?) "
                   "ON CONFLICT (url) DO UPDATE SET visitas = visitas + 1, ultima = excluded.ultima, "
                   "titulo = CASE WHEN excluded.titulo != '' THEN excluded.titulo ELSE titulo END",
                   (url, titulo or "", agora))

    def atualizar_titulo(self, url, titulo):
        if url and titulo:
            self._exec("UPDATE historico SET titulo = ? WHERE url = ?", (titulo, url))

    def historico(self, busca="", limite=300):
        if busca.strip():
            return self._todos("SELECT h.* FROM historico_busca b JOIN historico h ON h.id = b.rowid "
                               "WHERE historico_busca MATCH ? ORDER BY h.ultima DESC LIMIT ?",
                               (_consulta_fts(busca), limite))
        return self._todos("SELECT * FROM historico ORDER BY ultima DESC LIMIT ?", (limite,))

    def remover_do_historico(self, id_item):
        self._exec("DELETE FROM historico WHERE id = ?", (id_item,))

    def apagar_historico(self, desde=0):
        """Apaga as visitas a partir de `desde` (segundos desde 1970; 0 = tudo)."""
        self._exec("DELETE FROM historico WHERE ultima >= ?", (desde,))

    def mais_visitados(self, limite=8):
        return self._todos("SELECT * FROM historico ORDER BY visitas DESC, ultima DESC LIMIT ?", (limite,))

    def sugestoes(self, texto, limite=6):
        """Favoritos e histórico que combinam com o que está sendo digitado (favoritos primeiro)."""
        texto = texto.strip()
        if not texto:
            return []
        parecido = f"%{texto}%"
        favs = self._todos("SELECT url, titulo, 'favorito' AS tipo FROM favoritos WHERE url LIKE ? OR titulo LIKE ? "
                           "ORDER BY ordem LIMIT ?", (parecido, parecido, limite))
        hist = self._todos("SELECT h.url, h.titulo, 'historico' AS tipo FROM historico_busca b "
                           "JOIN historico h ON h.id = b.rowid WHERE historico_busca MATCH ? "
                           "ORDER BY h.visitas DESC, h.ultima DESC LIMIT ?", (_consulta_fts(texto), limite * 2))
        vistos, saida = set(), []
        for item in favs + hist:
            if item["url"] not in vistos:
                vistos.add(item["url"])
                saida.append(item)
        return saida[:limite]

    # ---------------------------------------------------------------- downloads
    def registrar_download(self, url, arquivo, tamanho, estado):
        self._exec("INSERT INTO downloads (url, arquivo, tamanho, estado, data) VALUES (?, ?, ?, ?, ?)",
                   (url, arquivo, int(tamanho or 0), estado, time.time()))

    def downloads(self, limite=200):
        return self._todos("SELECT * FROM downloads ORDER BY data DESC LIMIT ?", (limite,))

    def limpar_downloads(self):
        self._exec("DELETE FROM downloads")

    # ---------------------------------------------------------------- importação
    def importar(self, favoritos, pasta):
        """Grava uma lista [{"url", "titulo", "pasta"}] dentro de `pasta` (ex.: "Importados do Chrome")."""
        n = 0
        for f in favoritos:
            if f.get("url", "").startswith(("http://", "https://", "file://")):
                sub = f.get("pasta", "")
                self.adicionar_favorito(f["url"], f.get("titulo", ""), f"{pasta}/{sub}" if sub else pasta)
                n += 1
        return n


def _consulta_fts(texto):
    """Cada palavra vira um prefixo entre aspas: "rec"* "bol"* (sem sintaxe do FTS5 vinda da pessoa)."""
    palavras = [p.replace('"', '""') for p in texto.split() if p]
    return " ".join(f'"{p}"*' for p in palavras) or '""'


# -------------------------------------------------------------------- configurações
class Configuracoes:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else ARQUIVO_CONFIG
        self.valores = dict(PADROES)
        try:
            self.valores.update(json.loads(self.caminho.read_text()))
        except (OSError, ValueError):
            pass

    def __getitem__(self, chave):
        return self.valores.get(chave, PADROES.get(chave))

    def definir(self, chave, valor):
        if chave not in PADROES:
            raise KeyError(chave)
        self.valores[chave] = valor
        self.salvar()

    def salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(json.dumps(self.valores, ensure_ascii=False, indent=2))
        temporario.replace(self.caminho)


# -------------------------------------------------------------------- importar de outros navegadores
def navegadores_instalados(casa=None):
    """Navegadores com favoritos neste computador: [{"id", "nome", "caminho"}]."""
    casa = Path(casa or Path.home())
    achados = []
    for nome, pasta in (("Google Chrome", ".config/google-chrome"), ("Chromium", ".config/chromium"),
                        ("Microsoft Edge", ".config/microsoft-edge"), ("Brave", ".config/BraveSoftware/Brave-Browser"),
                        ("Google Chrome (Flathub)", ".var/app/com.google.Chrome/config/google-chrome"),
                        ("Chromium (Flathub)", ".var/app/org.chromium.Chromium/config/chromium")):
        arquivo = casa / pasta / "Default" / "Bookmarks"
        if arquivo.is_file():
            achados.append({"id": "chrome", "nome": nome, "caminho": str(arquivo)})
    for nome, pasta in (("Firefox", ".mozilla/firefox"), ("Firefox (Flathub)", ".var/app/org.mozilla.firefox/.mozilla/firefox")):
        raiz = casa / pasta
        if raiz.is_dir():
            perfis = sorted(raiz.glob("*/places.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
            if perfis:
                achados.append({"id": "firefox", "nome": nome, "caminho": str(perfis[0])})
    return achados


def ler_chrome(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    saida = []

    def andar(no, pasta):
        if no.get("type") == "url":
            saida.append({"url": no.get("url", ""), "titulo": no.get("name", ""), "pasta": pasta})
        elif no.get("type") == "folder":
            sub = "/".join(p for p in (pasta, no.get("name", "")) if p)
            for filho in no.get("children", []):
                andar(filho, sub)

    raizes = dados.get("roots", {})
    for chave, rotulo in (("bookmark_bar", ""), ("other", "Outros"), ("synced", "Celular")):
        if chave in raizes:
            for filho in raizes[chave].get("children", []):
                andar(filho, rotulo)
    return saida


def ler_firefox(caminho):
    """places.sqlite fica travado com o Firefox aberto: lê uma cópia."""
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "places.sqlite"
        shutil.copy2(caminho, copia)
        for extra in ("-wal", "-shm"):
            if Path(str(caminho) + extra).exists():
                shutil.copy2(str(caminho) + extra, str(copia) + extra)
        con = sqlite3.connect(copia)
        try:
            pastas = {i: (t or "", p) for i, t, p in con.execute("SELECT id, title, parent FROM moz_bookmarks WHERE type = 2")}

            def caminho_pasta(id_pasta):
                partes = []
                while id_pasta in pastas:
                    titulo, pai = pastas[id_pasta]
                    if pai in (0, 1) or titulo in ("toolbar", "menu", "unfiled", "mobile", "tags"):
                        break
                    partes.append(titulo)
                    id_pasta = pai
                return "/".join(reversed(partes))

            linhas = con.execute("SELECT b.title, p.url, b.parent FROM moz_bookmarks b JOIN moz_places p ON p.id = b.fk "
                                 "WHERE b.type = 1 ORDER BY b.parent, b.position").fetchall()
            return [{"url": url, "titulo": titulo or "", "pasta": caminho_pasta(pai)} for titulo, url, pai in linhas]
        finally:
            con.close()


class _LeitorHtml(HTMLParser):
    def __init__(self):
        super().__init__()
        self.saida, self.pilha, self._link, self._texto, self._pasta_nova = [], [], None, "", None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._link, self._texto = dict(attrs).get("href", ""), ""
        elif tag == "h3":
            self._pasta_nova = ""
        elif tag == "dl" and self._pasta_nova is not None:
            self.pilha.append(self._pasta_nova)
            self._pasta_nova = None
        elif tag == "dl":
            self.pilha.append(None)

    def handle_endtag(self, tag):
        if tag == "a" and self._link is not None:
            pasta = "/".join(p for p in self.pilha if p)
            self.saida.append({"url": self._link, "titulo": self._texto.strip(), "pasta": pasta})
            self._link = None
        elif tag == "dl" and self.pilha:
            self.pilha.pop()

    def handle_data(self, data):
        if self._link is not None:
            self._texto += data
        elif self._pasta_nova is not None:
            self._pasta_nova += data.strip()


def ler_html(caminho):
    leitor = _LeitorHtml()
    leitor.feed(Path(caminho).read_text(encoding="utf-8", errors="replace"))
    return leitor.saida


def exportar_html(favoritos, caminho):
    """Arquivo de favoritos no formato que todos os navegadores importam."""
    from html import escape
    linhas = ["<!DOCTYPE NETSCAPE-Bookmark-file-1>", '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
              "<TITLE>Favoritos do Ora</TITLE>", "<H1>Favoritos</H1>", "<DL><p>"]
    por_pasta = {}
    for f in favoritos:
        por_pasta.setdefault(f.get("pasta", ""), []).append(f)
    for pasta in sorted(por_pasta):
        recuo = "    "
        if pasta:
            linhas.append(f"    <DT><H3>{escape(pasta)}</H3>")
            linhas.append("    <DL><p>")
            recuo = "        "
        for f in por_pasta[pasta]:
            linhas.append(f'{recuo}<DT><A HREF="{escape(f["url"])}">{escape(f.get("titulo") or f["url"])}</A>')
        if pasta:
            linhas.append("    </DL><p>")
    linhas.append("</DL><p>")
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")
