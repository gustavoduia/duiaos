"""Abre cada tela da interface em modo de demonstração (sem a sessão do DuiaOS, plataforma offscreen),
salva a imagem e falha se o QML acusar erro. Pula sem o PySide6.

Rodar: python3 -m unittest discover -s shell/testes -t .
As imagens ficam em $DUIAOS_CAPTURAS (padrão: uma pasta temporária) para conferir o visual.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ERROS = re.compile(r"(TypeError|ReferenceError|SyntaxError|is not a type|Cannot assign|"
                   r"Cannot read property|Unable to assign|is not defined|Type error|non-existent property)")

try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteTelas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capturas = Path(os.environ.get("DUIAOS_CAPTURAS") or tempfile.mkdtemp(prefix="duiaos-capturas-"))
        cls.capturas.mkdir(parents=True, exist_ok=True)
        cls._inicio = tempfile.TemporaryDirectory()
        cls.inicio = Path(cls._inicio.name)
        for nome in ("Área de Trabalho", "Documentos/Trabalho", "Downloads", "Imagens", "Música", "Vídeos"):
            (cls.inicio / nome).mkdir(parents=True)
        for nome in ("Contrato.pdf", "Orçamento.xlsx", "Notas.txt"):
            (cls.inicio / "Documentos" / nome).write_text("exemplo")

    @classmethod
    def tearDownClass(cls):
        cls._inicio.cleanup()

    def abrir(self, nome, comando):
        arquivo = self.capturas / f"{nome}.png"
        ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": str(self.inicio),
                    "XDG_CONFIG_HOME": str(self.inicio / ".config"), "XDG_RUNTIME_DIR": str(self.inicio)}
        resultado = subprocess.run([sys.executable, *comando, "--captura", str(arquivo)], capture_output=True,
                                   text=True, timeout=60, env=ambiente, cwd=RAIZ)
        erros = [linha for linha in resultado.stderr.splitlines() if ERROS.search(linha)]
        self.assertEqual(erros, [], f"{nome}: erros no QML")
        self.assertTrue(arquivo.is_file(), f"{nome}: a tela não abriu\n{resultado.stderr[-2000:]}")

    def test_barra_de_recursos(self):
        for painel in ("", "menu", "central", "wifi", "som", "bateria", "brilho", "bluetooth", "luz", "calendario",
                       "balao", "atualizacoes", "confirmar:desligar"):
            with self.subTest(painel=painel):
                self.abrir("barra-" + (painel.replace(":", "-") or "sozinha"),
                           ["shell/barra-de-recursos/main.py", "--demonstracao", "--painel", painel])

    def test_area_de_trabalho_descanso_e_notificacoes(self):
        for menu in ("", "fundo", "item"):
            with self.subTest(menu=menu):
                self.abrir("area-de-trabalho-" + (menu or "sozinha"), ["shell/area-de-trabalho/main.py", "--demonstracao", "--menu", menu])
        self.abrir("descanso", ["shell/descanso/main.py", "--demonstracao"])
        self.abrir("notificacoes", ["shell/notificacoes/main.py", "--demonstracao"])

    def test_modo_escuro(self):
        (self.inicio / ".config" / "duiaos").mkdir(parents=True, exist_ok=True)
        preferencias = self.inicio / ".config" / "duiaos" / "preferencias.conf"
        preferencias.write_text("[aparencia]\nmodo = escuro\n")
        try:
            self.abrir("escuro-barra", ["shell/barra-de-recursos/main.py", "--demonstracao", "--painel", "central"])
            self.abrir("escuro-configuracoes", ["apps/configuracoes/main.py", "--demonstracao", "--secao", "aparencia"])
            self.abrir("escuro-explorador", ["apps/explorador-de-arquivos/main.py", str(self.inicio / "Documentos")])
        finally:
            preferencias.unlink()

    def test_ilha_de_aplicativos(self):
        for modo in ("", "--central", "--downloads", "--menu"):
            with self.subTest(modo=modo):
                self.abrir("ilha" + modo, ["shell/ilha-de-aplicativos/main.py", "--demonstracao", *([modo] if modo else [])])

    def test_explorador_de_arquivos(self):
        documentos = str(self.inicio / "Documentos")
        self.abrir("explorador-icones", ["apps/explorador-de-arquivos/main.py", documentos])
        self.abrir("explorador-lista", ["apps/explorador-de-arquivos/main.py", documentos, "--lista"])
        self.abrir("explorador-lixeira", ["apps/explorador-de-arquivos/main.py", "lixeira:"])
        self.abrir("explorador-aplicativos", ["apps/explorador-de-arquivos/main.py", "aplicativos:"])

    def test_configuracoes(self):
        for secao in ("wifi", "bluetooth", "notificacoes", "som", "tela", "energia", "aparencia", "papel", "descanso",
                      "barra", "usuario", "data", "teclado", "padroes", "atualizacoes", "privacidade", "ia", "sobre"):
            with self.subTest(secao=secao):
                self.abrir("configuracoes-" + secao, ["apps/configuracoes/main.py", "--demonstracao", "--secao", secao])
        self.abrir("configuracoes-atualizando", ["apps/configuracoes/main.py", "--demonstracao", "--secao", "atualizacoes", "--atualizando"])


if __name__ == "__main__":
    unittest.main()
