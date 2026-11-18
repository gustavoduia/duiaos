"""Ora, o navegador do DuiaOS (ADR 072): barra de endereço, favoritos, histórico com busca, importação de
outros navegadores, configurações e as telas em modo de demonstração (com o motor Chromium de verdade).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "apps" / "ora"))

import dados  # noqa: E402
import endereco  # noqa: E402

try:
    from PySide6 import QtWebEngineQuick  # noqa: F401
    TEM_MOTOR = True
except ImportError:
    TEM_MOTOR = False


class TestEndereco(unittest.TestCase):
    def test_dominios_viram_https(self):
        self.assertEqual(endereco.normalizar("duiaos.com.br"), "https://duiaos.com.br")
        self.assertEqual(endereco.normalizar("www.exemplo.com/caminho?q=1"), "https://www.exemplo.com/caminho?q=1")
        self.assertEqual(endereco.normalizar("  g1.globo.com  "), "https://g1.globo.com")

    def test_enderecos_locais_viram_http(self):
        self.assertEqual(endereco.normalizar("localhost:8080/teste"), "http://localhost:8080/teste")
        self.assertEqual(endereco.normalizar("192.168.0.1"), "http://192.168.0.1")
        self.assertEqual(endereco.normalizar("impressora.local"), "http://impressora.local")

    def test_endereco_completo_fica_como_esta(self):
        for texto in ("https://exemplo.com", "http://exemplo.com:81/x", "about:blank", "file:///tmp/a.html",
                      "view-source:https://exemplo.com", "mailto:ana@exemplo.com", "ora://historico"):
            self.assertEqual(endereco.normalizar(texto), texto)

    def test_texto_vira_busca(self):
        self.assertEqual(endereco.normalizar("receita de bolo"), "https://www.google.com/search?q=receita+de+bolo")
        self.assertEqual(endereco.normalizar("python", "duckduckgo"), "https://duckduckgo.com/?q=python")
        self.assertTrue(endereco.normalizar("ç&ã ?", "bing").startswith("https://www.bing.com/search?q="))
        self.assertIn("q=arquivo.pdf", endereco.normalizar("arquivo.pdf").replace("%2E", "."))   # extensão não é domínio

    def test_caminho_de_arquivo(self):
        self.assertEqual(endereco.normalizar("/home/ana/pagina.html"), "file:///home/ana/pagina.html")

    def test_para_mostrar_e_dominio(self):
        self.assertEqual(endereco.para_mostrar("https://www.exemplo.com/"), "exemplo.com")
        self.assertEqual(endereco.para_mostrar("https://exemplo.com/a/b"), "exemplo.com/a/b")
        self.assertEqual(endereco.dominio("https://www.wikipedia.org/wiki/x"), "wikipedia.org")
        self.assertEqual(endereco.dominio("não é url"), "")


class TestDados(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.banco = dados.Banco(self.pasta / "ora.db")

    def tearDown(self):
        self.banco.fechar()
        shutil.rmtree(self.pasta)

    def test_favoritos(self):
        self.banco.adicionar_favorito("https://a.com/", "A")
        self.banco.adicionar_favorito("https://b.com/", "B", "Notícias")
        self.banco.adicionar_favorito("https://a.com/", "A novo")             # mesma página: só atualiza o nome
        self.assertTrue(self.banco.eh_favorito("https://a.com/"))
        self.assertEqual([f["titulo"] for f in self.banco.favoritos("")], ["A novo"])
        self.assertEqual(self.banco.pastas(), ["Notícias"])
        self.banco.remover_favorito("https://a.com/")
        self.assertFalse(self.banco.eh_favorito("https://a.com/"))

    def test_historico_conta_visitas_e_busca_sem_acento(self):
        self.banco.registrar_visita("https://receitas.com/bolo", "Receita de bolo de cenoura")
        self.banco.registrar_visita("https://receitas.com/bolo", "")
        self.banco.registrar_visita("https://noticias.com/", "Notícias do dia")
        self.banco.registrar_visita("about:blank", "não entra")
        self.banco.registrar_visita("ora://historico", "não entra")
        hist = self.banco.historico()
        self.assertEqual(len(hist), 2)
        self.assertEqual(next(h for h in hist if "bolo" in h["url"])["visitas"], 2)
        self.assertEqual(next(h for h in hist if "bolo" in h["url"])["titulo"], "Receita de bolo de cenoura")
        self.assertEqual([h["url"] for h in self.banco.historico("noticias")], ["https://noticias.com/"])   # sem acento
        self.assertEqual(len(self.banco.historico("cen")), 1)                                                  # prefixo
        self.assertEqual(self.banco.historico('"; DROP TABLE historico; --'), [])                              # sem sintaxe do FTS

    def test_sugestoes_favoritos_primeiro_sem_repetir(self):
        self.banco.registrar_visita("https://github.com/duiaos", "DuiaOS no GitHub")
        self.banco.adicionar_favorito("https://github.com/duiaos", "DuiaOS no GitHub")
        self.banco.registrar_visita("https://github.com/outro", "Outro projeto no GitHub")
        sugestoes = self.banco.sugestoes("github")
        self.assertEqual(sugestoes[0]["tipo"], "favorito")
        self.assertEqual(len(sugestoes), 2)

    def test_apagar_historico_por_periodo(self):
        self.banco.registrar_visita("https://velho.com/", "Velho")
        self.banco._exec("UPDATE historico SET ultima = 1000 WHERE url = ?", ("https://velho.com/",))
        self.banco.registrar_visita("https://novo.com/", "Novo")
        import time
        self.banco.apagar_historico(time.time() - 3600)
        self.assertEqual([h["url"] for h in self.banco.historico()], ["https://velho.com/"])
        self.banco.apagar_historico(0)
        self.assertEqual(self.banco.historico(), [])

    def test_importar_chrome(self):
        arquivo = self.pasta / "Bookmarks"
        arquivo.write_text(json.dumps({"roots": {
            "bookmark_bar": {"type": "folder", "name": "Barra", "children": [
                {"type": "url", "name": "DuiaOS", "url": "https://duiaos.com.br/"},
                {"type": "folder", "name": "Trabalho", "children": [{"type": "url", "name": "Git", "url": "https://github.com/"}]}]},
            "other": {"type": "folder", "name": "Outros", "children": [{"type": "url", "name": "X", "url": "javascript:alert(1)"}]}}}))
        lista = dados.ler_chrome(arquivo)
        self.assertIn({"url": "https://github.com/", "titulo": "Git", "pasta": "Trabalho"}, lista)
        n = self.banco.importar(lista, "Importados do Chrome")
        self.assertEqual(n, 2)                                   # o javascript: fica de fora
        self.assertIn("Importados do Chrome/Trabalho", self.banco.pastas())

    def test_importar_firefox(self):
        places = self.pasta / "places.sqlite"
        con = sqlite3.connect(places)
        con.executescript("""
            CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT);
            CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER, parent INTEGER, position INTEGER, title TEXT);
            INSERT INTO moz_places VALUES (1, 'https://www.mozilla.org/'), (2, 'https://exemplo.com/');
            INSERT INTO moz_bookmarks VALUES (1, 2, NULL, 0, 0, 'root'), (3, 2, NULL, 1, 0, 'toolbar'),
                (10, 2, NULL, 3, 0, 'Estudos'), (20, 1, 1, 3, 1, 'Mozilla'), (21, 1, 2, 10, 0, 'Exemplo');
        """)
        con.commit()
        con.close()
        lista = dados.ler_firefox(places)
        self.assertIn({"url": "https://exemplo.com/", "titulo": "Exemplo", "pasta": "Estudos"}, lista)
        self.assertIn({"url": "https://www.mozilla.org/", "titulo": "Mozilla", "pasta": ""}, lista)

    def test_exportar_e_importar_html(self):
        self.banco.adicionar_favorito("https://a.com/", "A & B")
        self.banco.adicionar_favorito("https://b.com/", "B", "Pasta 1")
        destino = self.pasta / "fav.html"
        dados.exportar_html(self.banco.favoritos(), destino)
        lista = dados.ler_html(destino)
        self.assertIn({"url": "https://a.com/", "titulo": "A & B", "pasta": ""}, lista)
        self.assertIn({"url": "https://b.com/", "titulo": "B", "pasta": "Pasta 1"}, lista)

    def test_navegadores_instalados(self):
        casa = self.pasta / "casa"
        (casa / ".config/google-chrome/Default").mkdir(parents=True)
        (casa / ".config/google-chrome/Default/Bookmarks").write_text("{}")
        (casa / ".mozilla/firefox/abc.default-release").mkdir(parents=True)
        (casa / ".mozilla/firefox/abc.default-release/places.sqlite").write_bytes(b"")
        ids = sorted(n["id"] for n in dados.navegadores_instalados(casa))
        self.assertEqual(ids, ["chrome", "firefox"])

    def test_configuracoes(self):
        config = dados.Configuracoes(self.pasta / "ora.json")
        self.assertEqual(config["buscador"], "google")
        config.definir("buscador", "duckduckgo")
        self.assertEqual(dados.Configuracoes(self.pasta / "ora.json")["buscador"], "duckduckgo")
        with self.assertRaises(KeyError):
            config.definir("inventada", 1)


@unittest.skipUnless(TEM_MOTOR and shutil.which("xvfb-run"), "precisa do PySide6 com o Qt WebEngine e do xvfb-run")
class TestTelasDoOra(unittest.TestCase):
    """Abre cada página do Ora em modo de demonstração e confere a captura (o motor Chromium de verdade)."""

    def capturar(self, pagina, extra=()):
        destino = Path(tempfile.mkdtemp()) / f"ora-{pagina}.png"
        ambiente = dict(os.environ, QTWEBENGINE_DISABLE_SANDBOX="1" if os.getuid() == 0 else "")
        resultado = subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1400x900x24", sys.executable,
                                    str(RAIZ / "apps/ora/main.py"), "--demonstracao", "--pagina", pagina, "--captura", str(destino),
                                    *extra], capture_output=True, text=True, timeout=120, env=ambiente)
        erros = [l for l in resultado.stderr.splitlines() if ".qml:" in l]
        self.assertEqual(erros, [], resultado.stderr[-2000:])
        self.assertEqual(resultado.returncode, 0, resultado.stderr[-1500:])
        self.assertTrue(destino.exists() and destino.stat().st_size > 20000, f"captura vazia: {pagina}")
        return destino

    def test_paginas(self):
        for pagina in ("inicio", "historico", "favoritos", "downloads", "configuracoes"):
            with self.subTest(pagina=pagina):
                self.capturar(pagina)

    def test_pagina_da_web_desenhada_pelo_motor(self):
        from PySide6.QtGui import QImage
        imagem = QImage(str(self.capturar("web")))
        # A página de demonstração tem fundo azul-noite (#0b1024): o conteúdo veio do Chromium
        cor = imagem.pixelColor(imagem.width() // 2, imagem.height() - 40)
        self.assertLess(cor.lightness(), 60)


if __name__ == "__main__":
    unittest.main()
