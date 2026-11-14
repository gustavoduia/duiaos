"""Abre as janelas de verdade da sessão (Ilha, Área de Trabalho, Barra de Recursos, Notificações) por
alguns segundos, com um layer-shell de mentira (janela_real.py), e falha se o QML não carregar ou
acusar erro. Os modos de demonstração não usam esses arquivos: foi assim que a Ilha sumiu (14/11).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ERROS = re.compile(r"(failed to load component|TypeError|ReferenceError|SyntaxError|is not a type|Cannot assign|"
                   r"Invalid property|is not defined|non-existent property|Binding loop|Traceback)")

try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteJanelasReais(unittest.TestCase):
    def test_componentes(self):
        for componente in ("ilha-de-aplicativos", "area-de-trabalho", "barra-de-recursos", "notificacoes"):
            with self.subTest(componente=componente), tempfile.TemporaryDirectory() as inicio:
                ambiente = {**os.environ, "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config",
                            "XDG_RUNTIME_DIR": inicio, "XDG_DATA_HOME": inicio + "/.local/share"}
                resultado = subprocess.run([sys.executable, str(RAIZ / "shell/testes/janela_real.py"),
                                            str(RAIZ / "shell" / componente / "main.py"), "3"],
                                           capture_output=True, text=True, timeout=60, env=ambiente, cwd=RAIZ)
                saida = resultado.stdout + resultado.stderr
                erros = [linha for linha in saida.splitlines() if ERROS.search(linha)]
                self.assertEqual(erros, [], f"{componente}: erros")
                self.assertIn("JANELA-REAL-OK", saida, f"{componente}: a janela não abriu\n{saida[-2000:]}")


if __name__ == "__main__":
    unittest.main()
