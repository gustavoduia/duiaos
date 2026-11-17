"""Configurações › Inteligência Artificial e › Wise (ADR 063): motores na nuvem, chaves e as duas páginas.
Dados inventados."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))

import motores_ia  # noqa: E402


class TesteMotores(unittest.TestCase):
    def test_so_modelos_de_conversa_os_mais_novos_primeiro(self):
        gemini = {"models": [{"name": "models/gemini-9-flash", "supportedGenerationMethods": ["generateContent"]},
                             {"name": "models/gemini-9-flash-tts", "supportedGenerationMethods": ["generateContent"]},
                             {"name": "models/gemini-embedding-1", "supportedGenerationMethods": ["embedContent"]},
                             {"name": "models/outro-modelo", "supportedGenerationMethods": ["generateContent"]}]}
        self.assertEqual(motores_ia.filtrar_modelos("gemini", gemini), ["gemini-9-flash"])
        openai = {"data": [{"id": "gpt-teste-mini", "created": 10}, {"id": "gpt-teste", "created": 20},
                           {"id": "gpt-teste-audio", "created": 30}, {"id": "text-embedding-x", "created": 40},
                           {"id": "gpt-ruim; rm -rf", "created": 50}]}
        self.assertEqual(motores_ia.filtrar_modelos("openai", openai), ["gpt-teste", "gpt-teste-mini"])

    def test_conferir_guarda_os_modelos_e_nunca_a_chave(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "ia.conf"
            pedidos = []

            def pedir(url, cabecalhos):
                pedidos.append((url, cabecalhos))
                return {"data": [{"id": "gpt-a", "created": 2}, {"id": "gpt-b", "created": 1}]}
            self.assertEqual(motores_ia.conferir("openai", "chave-secreta-123", pedir, arquivo), ["gpt-a", "gpt-b"])
            self.assertEqual(pedidos[0][1], {"Authorization": "Bearer chave-secreta-123"})
            self.assertNotIn("chave-secreta", arquivo.read_text())
            motores_ia.definir("openai", arquivo, ativado=True, modelo="gpt-b")
            motores_ia.definir("openai", arquivo, modelo="isto não é um modelo")      # ignorado
            openai = next(m for m in motores_ia.situacao(arquivo, tem_chave=lambda _m: True) if m["id"] == "openai")
            self.assertEqual((openai["ativado"], openai["modelo"], openai["modelos"]), (True, "gpt-b", ["gpt-a", "gpt-b"]))
            with self.assertRaises(motores_ia.Erro):
                motores_ia.conferir("openai", "chave", lambda *_: {"data": []}, arquivo)   # chave sem modelos de conversa
            with self.assertRaises(motores_ia.Erro):
                motores_ia.definir("inventado", arquivo, ativado=True)

    def test_chave_malformada_e_recusada_antes_do_cofre(self):
        for chave in ("", "curta", "com espaço no meio 123456", "x" * 500):
            with self.assertRaises(motores_ia.Erro):
                motores_ia.gravar_chave("gemini", chave)


class TesteTelas(unittest.TestCase):
    def test_paginas_ia_e_wise_em_demonstracao(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")
        with tempfile.TemporaryDirectory() as pasta:
            for secao in ("ia", "wise"):
                arquivo = Path(pasta) / f"{secao}.png"
                saida = subprocess.run([sys.executable, str(RAIZ / "apps/configuracoes/main.py"), "--demonstracao", "--secao", secao,
                                        "--captura", str(arquivo)], capture_output=True, text=True, timeout=60,
                                       env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
                self.assertTrue(arquivo.exists(), saida.stderr[-2000:])
                for ruim in ("TypeError", "ReferenceError", "Unable to assign"):
                    self.assertNotIn(ruim, saida.stderr, saida.stderr[-1500:])

    def test_a_central_de_ia_saiu(self):
        self.assertFalse((RAIZ / "apps" / "central-de-ia").exists())
        self.assertNotIn("central-de-ia", (RAIZ / "pacotes" / "construir.sh").read_text())


if __name__ == "__main__":
    unittest.main()
