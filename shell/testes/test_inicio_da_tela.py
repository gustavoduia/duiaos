"""A tela gráfica tem de abrir sempre: os scripts que o greetd chama (Tela de Entrada e sessão) precisam
chegar ao compositor mesmo sem o journal, sem XDG_RUNTIME_DIR ou com ele apontando para onde não se
pode escrever. Em 16/11 um "systemd-cat" na frente do compositor deixou o Dell no login em modo texto.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SCRIPTS = {"shell/entrada/iniciar": "cage", "shell/sessao/iniciar-sessao": "labwc"}


class TesteInicioDaTela(unittest.TestCase):
    def _rodar(self, script, compositor, pasta, runtime):
        """Roda o script com um compositor de mentira, que só deixa uma marca; devolve se a marca apareceu."""
        caixa = Path(pasta) / "bin"
        caixa.mkdir(exist_ok=True)
        marca = Path(pasta) / "abriu"
        marca.unlink(missing_ok=True)
        falso = caixa / compositor
        falso.write_text(f"#!/bin/sh\necho mensagem-do-compositor\ntouch '{marca}'\n")
        falso.chmod(0o755)
        ambiente = {"PATH": f"{caixa}:/usr/bin:/bin", "HOME": pasta}       # sem o systemd-cat de verdade por perto
        if runtime is not None:
            ambiente["XDG_RUNTIME_DIR"] = runtime
        resultado = subprocess.run(["sh", str(RAIZ / script)], env=ambiente, capture_output=True, text=True,
                                   timeout=30, stdin=subprocess.DEVNULL, check=False)
        return marca.exists(), resultado

    def test_o_compositor_abre_em_qualquer_situacao(self):
        for script, compositor in SCRIPTS.items():
            with tempfile.TemporaryDirectory() as pasta:
                bom = Path(pasta) / "runtime"
                bom.mkdir()
                for nome, runtime in (("normal", str(bom)), ("sem XDG_RUNTIME_DIR", None),
                                      ("XDG_RUNTIME_DIR que não existe", pasta + "/nao-existe")):
                    with self.subTest(script=script, caso=nome):
                        abriu, resultado = self._rodar(script, compositor, pasta, runtime)
                        self.assertTrue(abriu, f"o compositor não foi chamado: {resultado.stderr[-300:]}")
                        self.assertEqual(resultado.returncode, 0)
                        self.assertNotIn("mensagem-do-compositor", resultado.stdout)      # nada vai para o terminal

    def test_as_mensagens_vao_para_o_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            abriu, _ = self._rodar("shell/sessao/iniciar-sessao", "labwc", pasta, pasta)
            self.assertTrue(abriu)
            self.assertIn("mensagem-do-compositor", (Path(pasta) / "duiaos-sessao.log").read_text())

    def test_nenhum_programa_na_frente_do_compositor(self):
        for script, compositor in SCRIPTS.items():
            ultima = [l for l in (RAIZ / script).read_text().splitlines() if l.strip()][-1]
            self.assertTrue(ultima.startswith(f"exec {compositor}"), f"{script}: {ultima}")


if __name__ == "__main__":
    unittest.main()
