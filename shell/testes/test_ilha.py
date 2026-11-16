"""Ilha de Aplicativos (ADR 050): opções, região da janela minimizada, recentes, ordem dos fixados e
as telas em modo de demonstração (ampliação, posições, menus e efeitos). Dados inventados.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "ilha-de-aplicativos"))

import efeitos  # noqa: E402

try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False


def imagem(largura, altura, retangulos, fundo=(230, 236, 245)):
    """Imagem RGB crua com retângulos (x, y, w, h, cor) pintados por cima do fundo."""
    pixels = bytearray(bytes(fundo) * largura * altura)
    for x, y, w, h, cor in retangulos:
        for yy in range(y, y + h):
            inicio = (yy * largura + x) * 3
            pixels[inicio:inicio + w * 3] = bytes(cor) * w
    return bytes(pixels)


class TesteOpcoes(unittest.TestCase):
    def test_padroes_e_limites(self):
        self.assertEqual(efeitos.ler_opcoes({}), efeitos.PADROES)
        opcoes = efeitos.ler_opcoes({"tamanho": "200", "ampliacao": "nao", "posicao": "topo", "minimizar": "explodir",
                                     "ocultar": "sim", "tamanho_ampliado": "abc"})
        self.assertEqual(opcoes["tamanho"], 80)
        self.assertFalse(opcoes["ampliacao"])
        self.assertEqual(opcoes["posicao"], "base")          # a Ilha não vai para o alto (é da Barra)
        self.assertEqual(opcoes["minimizar"], "genio")
        self.assertTrue(opcoes["ocultar"])
        self.assertEqual(opcoes["tamanho_ampliado"], 80)     # nunca menor que o tamanho normal

    def test_texto_gravado(self):
        self.assertEqual(efeitos.texto_da_opcao("ampliacao", True), "sim")
        self.assertEqual(efeitos.texto_da_opcao("ampliacao", "nao"), "nao")
        self.assertEqual(efeitos.texto_da_opcao("tamanho", "12"), "32")
        self.assertEqual(efeitos.texto_da_opcao("posicao", "esquerda"), "esquerda")
        self.assertIsNone(efeitos.texto_da_opcao("posicao", "meio"))
        self.assertIsNone(efeitos.texto_da_opcao("cor", "azul"))


class TesteRegiaoDaJanela(unittest.TestCase):
    L, A = 160, 100

    def regiao(self, antes, depois):
        return efeitos.regiao_alterada(antes, depois, self.L, self.A, self.L * 3, 3)

    def test_janela_que_sumiu(self):
        antes = imagem(self.L, self.A, [(40, 20, 60, 40, (255, 255, 255)), (40, 20, 60, 6, (200, 200, 210))])
        depois = imagem(self.L, self.A, [])
        self.assertEqual(self.regiao(antes, depois), (40, 20, 60, 40))

    def test_ignora_barra_de_titulo_da_janela_de_baixo(self):
        # A janela de baixo (maior) ganha o foco: só a barra de título dela muda de cor
        baixo = (10, 10, 140, 80, (250, 250, 250))
        antes = imagem(self.L, self.A, [baixo, (10, 10, 140, 4, (215, 215, 220)), (60, 30, 60, 50, (40, 90, 200))])
        depois = imagem(self.L, self.A, [baixo, (10, 10, 140, 4, (180, 180, 190))])
        x, y, w, h = self.regiao(antes, depois)
        self.assertEqual((x, w), (60, 60))
        self.assertTrue(28 <= y <= 32 and 48 <= h <= 52, (y, h))

    def test_nada_mudou_ou_mudou_pouco(self):
        tela = imagem(self.L, self.A, [(40, 20, 60, 40, (255, 255, 255))])
        self.assertIsNone(self.regiao(tela, tela))
        # Só o relógio mudou (6 x 6): pequeno demais para ser uma janela
        relogio = imagem(self.L, self.A, [(150, 2, 6, 6, (0, 0, 0))])
        self.assertIsNone(efeitos.regiao_alterada(relogio, imagem(self.L, self.A, []), self.L, self.A, self.L * 3, 3, minimo=12))

    def test_rapido_na_tela_reduzida(self):
        # Tela 1920x1080 capturada a 0,25: 480x270
        largura, altura = 480, 270
        antes = imagem(largura, altura, [(100, 50, 200, 150, (255, 255, 255))])
        depois = imagem(largura, altura, [])
        inicio = time.monotonic()
        self.assertEqual(efeitos.regiao_alterada(antes, depois, largura, altura, largura * 3, 3), (100, 48, 200, 152))
        self.assertLess(time.monotonic() - inicio, 0.5)

    def test_ppm(self):
        dados = b"P6\n# grim\n4 2\n255\n" + bytes(range(24))
        self.assertEqual(efeitos.ler_ppm(dados), (4, 2, bytes(range(24))))
        self.assertIsNone(efeitos.ler_ppm(b"P3\n1 1\n255\n0 0 0"))


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteConfiguracaoDaIlha(unittest.TestCase):
    def setUp(self):
        especificacao = importlib.util.spec_from_file_location("ilha_main_t", RAIZ / "shell" / "ilha-de-aplicativos" / "main.py")
        self.ilha = importlib.util.module_from_spec(especificacao)
        with mock.patch.dict(os.environ), mock.patch.object(sys, "argv", ["main.py", "--demonstracao"]):
            especificacao.loader.exec_module(self.ilha)
        self.pasta = tempfile.TemporaryDirectory()
        self.ilha.PASTA_CONFIG = Path(self.pasta.name)
        self.ilha.ARQUIVO_CONFIG = Path(self.pasta.name) / "ilha.conf"

    def tearDown(self):
        self.pasta.cleanup()

    def test_recentes_sobrevivem_a_mudanca_dos_fixados(self):
        self.ilha.gravar_fixados(["a.desktop"])
        self.ilha.gravar_recentes(["x.desktop", "y.desktop", "z.desktop", "w.desktop"])
        self.assertEqual(self.ilha.ler_recentes(), ["x.desktop", "y.desktop", "z.desktop"])
        self.ilha.gravar_fixados(["a.desktop", "b.desktop"])
        self.assertEqual(self.ilha.ler_fixados(), ["a.desktop", "b.desktop"])
        self.assertEqual(self.ilha.ler_recentes(), ["x.desktop", "y.desktop", "z.desktop"])

    def test_opcoes_das_preferencias(self):
        preferencias = Path(self.pasta.name) / "preferencias.conf"
        preferencias.write_text("[ilha]\ntamanho = 60\nposicao = direita\n")
        with mock.patch.object(self.ilha.pastas, "PREFERENCIAS", preferencias):
            opcoes = self.ilha.ler_opcoes()
        self.assertEqual((opcoes["tamanho"], opcoes["posicao"]), (60, "direita"))


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteTelasDaIlha(unittest.TestCase):
    def test_telas(self):
        capturas = Path(os.environ.get("DUIAOS_CAPTURAS") or tempfile.mkdtemp(prefix="duiaos-capturas-"))
        capturas.mkdir(parents=True, exist_ok=True)
        casos = [["--ampliada"], ["--menu-ilha"], ["--recentes"], ["--genio"], ["--escala", "--progresso", "0.5"],
                 ["--posicao", "esquerda", "--ampliada"], ["--posicao", "direita", "--menu-ilha"],
                 ["--posicao", "esquerda", "--downloads"], ["--posicao", "direita", "--genio"]]
        with tempfile.TemporaryDirectory() as inicio:
            for extra in casos:
                with self.subTest(extra=extra):
                    arquivo = capturas / ("ilha" + "-".join(extra).replace("--", "-") + ".png")
                    ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": inicio,
                                "XDG_CONFIG_HOME": inicio + "/.config", "XDG_RUNTIME_DIR": inicio}
                    resultado = subprocess.run([sys.executable, "shell/ilha-de-aplicativos/main.py", "--demonstracao", *extra,
                                                "--captura", str(arquivo)], capture_output=True, text=True, timeout=60,
                                               env=ambiente, cwd=RAIZ)
                    erros = [linha for linha in resultado.stderr.splitlines()
                             if any(e in linha for e in ("TypeError", "ReferenceError", "SyntaxError", "is not a type",
                                                         "Cannot assign", "is not defined", "non-existent property",
                                                         "Binding loop"))]
                    self.assertEqual(erros, [])
                    self.assertTrue(arquivo.is_file(), resultado.stderr[-2000:])




try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False


class TesteLimites(unittest.TestCase):
    def test_grade_e_ajuste(self):
        dados = bytes([0, 0, 0, 9, 0, 0, 0, 2, 0, 0, 0, 0])              # 4 células numa linha
        self.assertEqual(efeitos.grade_da_diferenca(dados, 4, 1, 12, 3, 1), [[False, True, True, False]])
        perfil = [False] * 10 + [True] * 30 + [False] * 10
        self.assertEqual(efeitos.ajustar_limites(perfil, 16, 32, 16), (10, 40))     # das células ao pixel
        self.assertEqual(efeitos.ajustar_limites([False] * 50, 16, 32, 16), (16, 32))   # sem sinal: fica como estava
        solto = [False] * 5 + [True] + [False] * 4 + [True] * 30 + [False] * 10    # um risco solto não é a borda
        self.assertEqual(efeitos.ajustar_limites(solto, 16, 32, 16), (10, 40))


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteRegiaoComTelaCongelada(unittest.TestCase):
    """Minimizar sem piscar (ADR 056): as capturas são feitas com a tela congelada por cima, a 75%."""

    def _capturas(self, janela, cor_janela, cor_fundo=(232, 240, 254)):
        from PySide6.QtGui import QColor, QImage, QPainter
        fundo = QImage(1920, 1080, QImage.Format.Format_RGB32)
        fundo.fill(QColor(*cor_fundo))
        pintor = QPainter(fundo)
        for i in range(0, 1920, 120):                                   # um papel de parede com desenho
            pintor.fillRect(i, 0, 40, 1080, QColor(cor_fundo[0] - 12, cor_fundo[1] - 8, cor_fundo[2]))
        pintor.end()
        com_janela = fundo.copy()
        pintor = QPainter(com_janela)
        pintor.fillRect(*janela, QColor(*cor_janela))
        pintor.fillRect(janela[0], janela[1], janela[2], 30, QColor(cor_janela[0] - 20, cor_janela[1] - 20, cor_janela[2] - 20))
        pintor.end()
        # Depois de minimizar: 75% da tela congelada (com a janela) + 25% da tela de verdade (sem ela)
        depois = fundo.copy()
        pintor = QPainter(depois)
        pintor.setOpacity(0.75)
        pintor.drawImage(0, 0, com_janela)
        pintor.end()
        return com_janela, depois

    def _modulo(self):
        especificacao = importlib.util.spec_from_file_location("ilha_main", RAIZ / "shell/ilha-de-aplicativos/main.py")
        modulo = importlib.util.module_from_spec(especificacao)
        with mock.patch.object(sys, "argv", ["main.py", "--demonstracao"]):
            especificacao.loader.exec_module(modulo)
        return modulo

    def test_acha_a_janela_ao_pixel(self):
        modulo = self._modulo()
        for janela, cor in (((301, 97, 803, 611), (255, 255, 255)), ((40, 40, 1500, 900), (30, 34, 52)),
                            ((1000, 500, 333, 222), (250, 250, 252))):
            antes, depois = self._capturas(janela, cor)
            regiao = modulo.regiao_da_janela(antes, depois)
            self.assertIsNotNone(regiao, janela)
            for achado, certo in zip(regiao, janela):
                self.assertLessEqual(abs(achado - certo), 2, (regiao, janela))

    def test_nada_mudou(self):
        modulo = self._modulo()
        antes, _ = self._capturas((10, 10, 50, 50), (255, 255, 255))
        self.assertIsNone(modulo.regiao_da_janela(antes, antes.copy()))


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteAmpliacao(unittest.TestCase):
    """Os ícones piscavam ao passar o mouse (16/11): cada mudança de tamanho refazia a imagem do ícone,
    e o foco era medido nos ícones já ampliados. O auxiliar passa o mouse pela Ilha e confere os dois."""

    def test_pulo_de_icone_ampliado_nao_e_cortado(self):
        """O ícone clicado (ampliado, com o mouse em cima) pula ao abrir: saía 7,7 px pelo alto (16/11)."""
        raiz = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as inicio:
            ambiente = {**os.environ, "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config",
                        "XDG_RUNTIME_DIR": inicio, "XDG_DATA_HOME": inicio + "/.local/share"}
            resultado = subprocess.run([sys.executable, str(raiz / "shell/testes/ilha_pulo.py"),
                                        str(raiz / "shell/ilha-de-aplicativos/main.py")],
                                       capture_output=True, text=True, timeout=120, env=ambiente, cwd=raiz)
        self.assertIn("PULO-OK", resultado.stdout, resultado.stdout[-1500:] + resultado.stderr[-1500:])

    def test_ampliacao_estavel_e_sem_recarregar_imagens(self):
        raiz = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as inicio:
            ambiente = {**os.environ, "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config",
                        "XDG_RUNTIME_DIR": inicio, "XDG_DATA_HOME": inicio + "/.local/share"}
            resultado = subprocess.run([sys.executable, str(raiz / "shell/testes/ilha_ampliacao.py"),
                                        str(raiz / "shell/ilha-de-aplicativos/main.py")],
                                       capture_output=True, text=True, timeout=120, env=ambiente, cwd=raiz)
        self.assertIn("AMPLIACAO-OK", resultado.stdout, resultado.stdout[-1500:] + resultado.stderr[-1500:])


if __name__ == "__main__":
    unittest.main()
