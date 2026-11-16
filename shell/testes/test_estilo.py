"""Estilos da interface (ADR 052): padrão e futurista ("Aurora"), nos modos claro e escuro — janelas do
labwc, Tela de Entrada e as telas em demonstração nos dois estilos.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))

import papel  # noqa: E402
import sessao  # noqa: E402

try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False
ERROS = ("TypeError", "ReferenceError", "SyntaxError", "is not a type", "Cannot assign",
         "Invalid property", "is not defined", "non-existent property", "failed to load", "Binding loop")


class TesteJanelas(unittest.TestCase):
    def test_tema_das_janelas(self):
        self.assertEqual(sessao.tema_das_janelas(False, False), "")
        self.assertEqual(sessao.tema_das_janelas(True, False), sessao.TEMA_ESCURO)
        claro, escuro = sessao.tema_das_janelas(False, True), sessao.tema_das_janelas(True, True)
        for texto in (claro, escuro, sessao.TEMA_ESCURO):
            self.assertTrue(texto.startswith("# DuiaOS — "))        # só apagamos o que geramos
        self.assertIn("window.active.title.bg.color: #121933", escuro)
        self.assertIn("window.active.title.bg.color: #F7F8FF", claro)
        self.assertNotEqual(claro, escuro)

    def test_estilo_da_entrada(self):
        with tempfile.TemporaryDirectory() as pasta:
            conf = Path(pasta) / "papel.conf"
            self.assertEqual(papel.estilo_da_entrada(conf), "padrao")
            conf.write_text("[papel]\nmodo = padrao\nestilo = futurista\n")
            self.assertEqual(papel.estilo_da_entrada(conf), "futurista")
            conf.write_text("[papel]\nestilo = neon\n")
            self.assertEqual(papel.estilo_da_entrada(conf), "padrao")


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteTelasNosEstilos(unittest.TestCase):
    def test_telas(self):
        capturas = Path(os.environ.get("DUIAOS_CAPTURAS") or tempfile.mkdtemp(prefix="duiaos-capturas-"))
        capturas.mkdir(parents=True, exist_ok=True)
        telas = [("configuracoes", ["apps/configuracoes/main.py", "--demonstracao", "--secao", "aparencia"]),
                 ("atualizacoes", ["apps/configuracoes/main.py", "--demonstracao", "--secao", "atualizacoes"]),
                 ("barra", ["shell/barra-de-recursos/main.py", "--demonstracao", "--painel", "central"]),
                 ("ilha", ["shell/ilha-de-aplicativos/main.py", "--demonstracao", "--menu"]),
                 ("loja", ["apps/loja/main.py", "--demonstracao"]),
                 ("bloqueio", ["shell/bloqueio/main.py", "--demonstracao"])]
        for modo in ("claro", "escuro"):
            with tempfile.TemporaryDirectory() as inicio:
                (Path(inicio) / ".config/duiaos").mkdir(parents=True)
                (Path(inicio) / ".config/duiaos/preferencias.conf").write_text(f"[aparencia]\nestilo = futurista\nmodo = {modo}\n")
                ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": inicio,
                            "XDG_CONFIG_HOME": inicio + "/.config", "XDG_RUNTIME_DIR": inicio}
                for nome, comando in telas:
                    with self.subTest(modo=modo, tela=nome):
                        arquivo = capturas / f"futurista-{modo}-{nome}.png"
                        resultado = subprocess.run([sys.executable, *comando, "--captura", str(arquivo)], capture_output=True,
                                                   text=True, timeout=60, env=ambiente, cwd=RAIZ)
                        erros = [l for l in resultado.stderr.splitlines() if any(e in l for e in ERROS)]
                        self.assertEqual(erros, [])
                        self.assertTrue(arquivo.is_file(), resultado.stderr[-1500:])

    def test_bloqueio_padrao_continua_abrindo(self):
        with tempfile.TemporaryDirectory() as inicio:
            arquivo = Path(inicio) / "b.png"
            ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config"}
            resultado = subprocess.run([sys.executable, "shell/bloqueio/main.py", "--demonstracao", "--captura", str(arquivo)],
                                       capture_output=True, text=True, timeout=60, env=ambiente, cwd=RAIZ)
            self.assertEqual([l for l in resultado.stderr.splitlines() if any(e in l for e in ERROS)], [])
            self.assertTrue(arquivo.is_file())


if __name__ == "__main__":
    unittest.main()
