"""Papéis de parede (ADR 051): por tela, estendido, Tela de Bloqueio, Tela de Entrada, troca automática
e o ajudante da Tela de Entrada. Dados inventados.

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

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


class TestePapel(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.p = Path(self.pasta.name)
        self.padrao = self.p / "orbita.jpg"
        self.padrao.write_bytes(b"\xff\xd8\xff")
        self.foto = self.p / "praia.jpg"
        self.foto.write_bytes(b"\xff\xd8\xff")
        self.prefs = self.p / "preferencias.conf"

    def tearDown(self):
        self.pasta.cleanup()

    def escrever(self, texto):
        self.prefs.write_text(texto.replace("FOTO", str(self.foto)))

    def test_padroes_sem_preferencias(self):
        area = papel.ler_area(self.prefs, self.padrao)
        self.assertEqual(area["telas"], "mesmo")
        self.assertEqual(area["padrao"], {"arquivo": str(self.padrao), "cor": papel.COR_PADRAO, "ajuste": "preencher"})
        self.assertEqual(area["alternar"], 0)

    def test_uma_para_cada_tela(self):
        self.escrever("[papel-de-parede]\narquivo = FOTO\ntelas = separado\najuste = ajustar\n"
                      "[papel-de-parede:HDMI-A-1]\narquivo =\ncor = #1A3A73\n")
        area = papel.ler_area(self.prefs, self.padrao)
        self.assertEqual(papel.papel_da_tela(area, "eDP-1")["arquivo"], str(self.foto))
        hdmi = papel.papel_da_tela(area, "HDMI-A-1")
        self.assertEqual((hdmi["arquivo"], hdmi["cor"], hdmi["ajuste"]), ("", "#1A3A73", "ajustar"))   # o ajuste vem do geral
        # Voltando para "o mesmo em todas", as seções das telas ficam guardadas mas não valem
        self.escrever("[papel-de-parede]\narquivo = FOTO\ntelas = mesmo\n[papel-de-parede:HDMI-A-1]\ncor = #1A3A73\n")
        self.assertEqual(papel.papel_da_tela(papel.ler_area(self.prefs, self.padrao), "HDMI-A-1")["arquivo"], str(self.foto))

    def test_valores_errados_e_arquivo_que_sumiu(self):
        self.escrever("[papel-de-parede]\narquivo = /nao/existe.jpg\najuste = girar\ntelas = tudo\nalternar = 7\n")
        area = papel.ler_area(self.prefs, self.padrao)
        self.assertEqual((area["padrao"]["arquivo"], area["padrao"]["ajuste"], area["telas"], area["alternar"]),
                         (str(self.padrao), "preencher", "mesmo", 0))

    def test_bloqueio(self):
        self.escrever("[papel-de-parede]\narquivo = FOTO\n")
        self.assertEqual(papel.ler_bloqueio(self.prefs, self.padrao)["arquivo"], str(self.foto))
        video = self.p / "mar.mp4"
        video.write_bytes(b"0")
        self.prefs.write_text(f"[papel-de-parede]\narquivo = {video}\n[papel-bloqueio]\ndesfocar = sim\n")
        bloqueio = papel.ler_bloqueio(self.prefs, self.padrao)
        self.assertEqual(bloqueio["arquivo"], str(self.padrao))          # vídeo não vai para a Tela de Bloqueio
        self.assertTrue(bloqueio["desfocar"])
        self.escrever("[papel-bloqueio]\nmodo = proprio\narquivo =\ncor = #0F1724\n")
        self.assertEqual((papel.ler_bloqueio(self.prefs, self.padrao)["arquivo"], papel.ler_bloqueio(self.prefs, self.padrao)["cor"]),
                         ("", "#0F1724"))

    def test_entrada(self):
        conf = self.p / "papel.conf"
        self.assertEqual(papel.ler_entrada(conf, self.padrao)["modo"], "padrao")
        conf.write_text(f"[papel]\nmodo = proprio\narquivo = {self.foto}\najuste = esticar\ndesfocar = sim\n")
        entrada = papel.ler_entrada(conf, self.padrao)
        self.assertEqual((entrada["arquivo"], entrada["ajuste"], entrada["desfocar"]), (str(self.foto), "esticar", True))

    def test_troca_automatica(self):
        lista = ["/a/1.jpg", "/a/2.mp4", "/a/3.png"]
        self.assertEqual(papel.proximo_da_lista(lista, "/a/1.jpg"), "/a/3.png")
        self.assertEqual(papel.proximo_da_lista(lista, "/a/3.png"), "/a/1.jpg")
        self.assertEqual(papel.proximo_da_lista(lista, "/outro.jpg"), "/a/1.jpg")
        self.assertEqual(papel.proximo_da_lista([], ""), "")

    def test_estendido(self):
        telas = [{"nome": "eDP-1", "x": 0, "y": 360, "largura": 1920, "altura": 1080},
                 {"nome": "HDMI-A-1", "x": 1920, "y": 0, "largura": 2560, "altura": 1440}]
        self.assertEqual(papel.recorte_estendido(telas, "eDP-1"), {"largura": 4480, "altura": 1440, "dx": 0, "dy": 360})
        self.assertEqual(papel.recorte_estendido(telas, "HDMI-A-1"), {"largura": 4480, "altura": 1440, "dx": 1920, "dy": 0})

    def test_tipo_da_imagem(self):
        self.assertTrue(papel.eh_imagem(PNG))
        self.assertTrue(papel.eh_imagem(b"RIFF0000WEBPVP8 "))
        self.assertFalse(papel.eh_imagem(b"<svg>"))


class TesteAjudanteEntrada(unittest.TestCase):
    """O ajudante roda como root pelo pkexec; aqui, só a recusa sem pkexec (não muda nada)."""

    def test_recusa_sem_pkexec(self):
        ajudante = RAIZ / "pacotes/duiaos-shell/raiz/usr/lib/duiaos/papel-entrada"
        ambiente = {k: v for k, v in os.environ.items() if k != "PKEXEC_UID"}
        resultado = subprocess.run([sys.executable, str(ajudante), "padrao", "nao"], capture_output=True, env=ambiente,
                                   timeout=20, check=False)
        self.assertEqual(resultado.returncode, 2)


if __name__ == "__main__":
    unittest.main()
