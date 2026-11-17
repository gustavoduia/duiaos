"""Seleção por arraste (retângulo) e Descompactar no Explorador de Arquivos e na Área de Trabalho (ADR 067).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

try:
    import PySide6  # noqa: F401
    TEM_PYSIDE = True
except ImportError:
    TEM_PYSIDE = False


@unittest.skipUnless(TEM_PYSIDE, "precisa do PySide6")
class TesteSelecaoPorArraste(unittest.TestCase):
    def rodar(self, *argumentos):
        with tempfile.TemporaryDirectory() as inicio:
            ambiente = {**os.environ, "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config",
                        "XDG_RUNTIME_DIR": inicio, "XDG_DATA_HOME": inicio + "/.local/share"}
            pasta = Path(inicio) / "Documentos"
            pasta.mkdir()
            for i in range(60):
                (pasta / f"arquivo {i:02d}.txt").write_text(str(i))
            with zipfile.ZipFile(pasta / "Pacote.zip", "w") as z:
                z.writestr("dentro/a.txt", "a")
                z.writestr("dentro/b.txt", "b")
                z.writestr("leia.txt", "c")
            resultado = subprocess.run([sys.executable, str(RAIZ / "shell/testes/selecao_por_arraste.py"),
                                        *[a.replace("@PASTA", str(pasta)) for a in argumentos]],
                                       capture_output=True, text=True, timeout=120, env=ambiente, cwd=RAIZ)
        self.assertIn("SELECAO-OK", resultado.stdout, resultado.stdout[-1500:] + resultado.stderr[-1500:])

    def test_explorador(self):
        """Retângulo, Ctrl que inverte, clique que limpa, roda do mouse, rolagem automática e Descompactar."""
        self.rodar("explorador", str(RAIZ / "apps/explorador-de-arquivos/main.py"), "@PASTA")

    def test_area_de_trabalho(self):
        self.rodar("area", str(RAIZ / "shell/area-de-trabalho/main.py"))


if __name__ == "__main__":
    unittest.main()
