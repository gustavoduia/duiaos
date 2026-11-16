"""Entrar sem tela preta, modo Automático e o tom azul das telas de acesso (ADR 056).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import datetime
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))

import papel  # noqa: E402
import pastas  # noqa: E402
import sessao  # noqa: E402
import sol  # noqa: E402


class TesteSol(unittest.TestCase):
    TABELA = "# comentário\nBR\t-2332-04637\tAmerica/Sao_Paulo\tBrazil (southeast)\nJP\t+353916+1394441\tAsia/Tokyo\nNO\t+7800+01600\tArctic/Longyearbyen\n"

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.tabela = Path(self.pasta.name) / "zone.tab"
        self.tabela.write_text(self.TABELA)

    def tearDown(self):
        self.pasta.cleanup()

    def test_coordenadas_do_fuso(self):
        lat, lon = sol.coordenadas("America/Sao_Paulo", (self.tabela,))
        self.assertAlmostEqual(lat, -23.533, places=2)
        self.assertAlmostEqual(lon, -46.617, places=2)
        lat, lon = sol.coordenadas("Asia/Tokyo", (self.tabela,))
        self.assertAlmostEqual(lat, 35.654, places=2)
        self.assertAlmostEqual(lon, 139.745, places=2)
        self.assertIsNone(sol.coordenadas("Marte/Olimpo", (self.tabela,)))
        self.assertIsNone(sol.coordenadas("America/Sao_Paulo", (Path("/nao/existe"),)))

    def test_nascer_e_por_em_sao_paulo(self):
        fuso = ZoneInfo("America/Sao_Paulo")
        nascer, por = sol.nascer_e_por(datetime.date(2026, 11, 16), -23.533, -46.617)
        nascer, por = nascer.astimezone(fuso), por.astimezone(fuso)
        self.assertEqual((nascer.hour, por.hour), (5, 18))             # 5h14 e 18h29, a poucos minutos
        self.assertLess(abs(nascer.minute - 14), 6)
        self.assertLess(abs(por.minute - 29), 6)

    def test_dia_e_noite(self):
        fuso = ZoneInfo("America/Sao_Paulo")
        for hora, noite in ((3, True), (5, True), (6, False), (12, False), (18, False), (19, True), (23, True)):
            agora = datetime.datetime(2026, 11, 16, hora, 0, tzinfo=fuso)
            self.assertEqual(sol.e_noite(agora, "America/Sao_Paulo", (self.tabela,)), noite, hora)
        toquio = ZoneInfo("Asia/Tokyo")                                 # o dia local cai em dois dias UTC
        self.assertFalse(sol.e_noite(datetime.datetime(2026, 6, 21, 5, 0, tzinfo=toquio), "Asia/Tokyo", (self.tabela,)))
        self.assertTrue(sol.e_noite(datetime.datetime(2026, 6, 21, 3, 0, tzinfo=toquio), "Asia/Tokyo", (self.tabela,)))

    def test_sem_fuso_conhecido_vale_das_6_as_18(self):
        fuso = ZoneInfo("America/Sao_Paulo")
        self.assertFalse(sol.e_noite(datetime.datetime(2026, 1, 1, 7, 0, tzinfo=fuso), "", (self.tabela,)))
        self.assertTrue(sol.e_noite(datetime.datetime(2026, 1, 1, 18, 30, tzinfo=fuso), "", (self.tabela,)))

    def test_perto_do_polo_nao_quebra(self):
        fuso = ZoneInfo("Arctic/Longyearbyen")
        self.assertIsNone(sol.nascer_e_por(datetime.date(2026, 6, 21), 78.0, 16.0))    # sol da meia-noite
        self.assertIn(sol.e_noite(datetime.datetime(2026, 6, 21, 12, 0, tzinfo=fuso), "Arctic/Longyearbyen", (self.tabela,)),
                      (True, False))


class TesteModoAutomatico(unittest.TestCase):
    def test_troca_so_no_automatico_e_so_quando_muda(self):
        with tempfile.TemporaryDirectory() as pasta:
            preferencias = Path(pasta) / "preferencias.conf"
            with mock.patch.object(pastas, "PREFERENCIAS", preferencias):
                preferencias.write_text("[aparencia]\nmodo = claro\n")
                with mock.patch.object(sol, "e_noite", return_value=True):
                    self.assertFalse(sessao.atualizar_modo_automatico())           # não está no automático
                    self.assertEqual(pastas.ler_preferencia("aparencia", "modo"), "claro")
                    pastas.gravar_preferencia("aparencia", "automatico", "sim")
                    self.assertTrue(sessao.atualizar_modo_automatico())            # anoiteceu
                    self.assertEqual(pastas.ler_preferencia("aparencia", "modo"), "escuro")
                    self.assertFalse(sessao.atualizar_modo_automatico())           # já está escuro
                with mock.patch.object(sol, "e_noite", return_value=False):
                    self.assertTrue(sessao.atualizar_modo_automatico())            # amanheceu
                    self.assertEqual(pastas.ler_preferencia("aparencia", "modo"), "claro")
                    self.assertEqual(pastas.ler_preferencia("aparencia", "automatico"), "sim")


class TesteAcesso(unittest.TestCase):
    def test_valores_e_limites(self):
        self.assertEqual(papel.acesso({}), {"veu": 15, "brilho": "radial", "brilho_extra": False})
        self.assertEqual(papel.acesso({"veu": "100", "brilho": "linear", "brilho_extra": "sim"}),
                         {"veu": 100, "brilho": "linear", "brilho_extra": True})
        self.assertEqual(papel.acesso({"veu": "250", "brilho": "neon"}), {"veu": 100, "brilho": "radial", "brilho_extra": False})
        self.assertEqual(papel.acesso({"veu": "muito"})["veu"], 15)

    def test_bloqueio_e_entrada_trazem_o_acesso(self):
        with tempfile.TemporaryDirectory() as pasta:
            preferencias, conf = Path(pasta) / "p.conf", Path(pasta) / "papel.conf"
            preferencias.write_text("[papel-bloqueio]\nveu = 40\nbrilho = nenhum\n")
            self.assertEqual(papel.ler_bloqueio(preferencias, Path(pasta) / "x.jpg")["acesso"],
                             {"veu": 40, "brilho": "nenhum", "brilho_extra": False})
            conf.write_text("[papel]\nmodo = padrao\nveu = 0\nbrilho = linear\nbrilho_extra = sim\n")
            self.assertEqual(papel.ler_entrada(conf, Path(pasta) / "x.jpg")["acesso"],
                             {"veu": 0, "brilho": "linear", "brilho_extra": True})

    def test_ajudante_da_entrada_grava_e_preserva(self):
        caminho = RAIZ / "pacotes/duiaos-shell/raiz/usr/lib/duiaos/papel-entrada"
        carregador = importlib.machinery.SourceFileLoader("papel_entrada", str(caminho))
        ajudante = importlib.util.module_from_spec(importlib.util.spec_from_loader("papel_entrada", carregador))
        carregador.exec_module(ajudante)
        with tempfile.TemporaryDirectory() as pasta:
            ajudante.PASTA, ajudante.CONF = pasta, os.path.join(pasta, "papel.conf")

            def rodar(*argumentos):
                with mock.patch.object(os, "geteuid", return_value=0), mock.patch.dict(os.environ, {"PKEXEC_UID": "1000"}), \
                        mock.patch.object(sys, "argv", ["papel-entrada", *argumentos]):
                    return ajudante.main()
            self.assertEqual(rodar("estilo", "padrao"), 0)
            self.assertEqual(rodar("acesso", "35", "linear", "sim"), 0)
            conf = Path(pasta) / "papel.conf"
            self.assertEqual(papel.ler_entrada(conf, Path(pasta) / "x.jpg")["acesso"],
                             {"veu": 35, "brilho": "linear", "brilho_extra": True})
            self.assertEqual(papel.estilo_da_entrada(conf), "padrao")                  # o estilo continua
            self.assertEqual(rodar("padrao", "sim"), 0)                               # mudar o papel não apaga o tom
            self.assertEqual(papel.ler_entrada(conf, Path(pasta) / "x.jpg")["acesso"]["veu"], 35)
            for errado in (("acesso", "101", "radial", "nao"), ("acesso", "10", "neon", "nao"),
                           ("acesso", "10", "radial", "talvez"), ("acesso", "-5", "radial", "nao"), ("acesso", "10 ; rm", "radial", "nao")):
                self.assertEqual(rodar(*errado), 2, errado)


class TesteFundoImediato(unittest.TestCase):
    """O fundo imediato (swaybg) aparece ao entrar e sai quando a Área de Trabalho avisa."""

    def test_dica(self):
        area = {"padrao": {"arquivo": "/fotos/praia.JPG", "cor": "#0F1724", "ajuste": "ajustar"}}
        self.assertEqual(papel.dica_de_inicio(area), "/fotos/praia.JPG\n#0F1724\nfit\n")
        area["padrao"].update(arquivo="/videos/mar.mp4", ajuste="estranho")
        self.assertEqual(papel.dica_de_inicio(area), "\n#0F1724\nfill\n")              # vídeo: só a cor
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "sub" / "papel-inicio"
            papel.gravar_dica(area, destino)
            self.assertEqual(destino.read_text(), "\n#0F1724\nfill\n")

    def _rodar(self, pasta, dica):
        caixa, runtime, cache = Path(pasta) / "bin", Path(pasta) / "run", Path(pasta) / "cache"
        for p in (caixa, runtime, cache / "duiaos"):
            p.mkdir(parents=True, exist_ok=True)
        registro = Path(pasta) / "chamadas"
        falso = caixa / "swaybg"
        falso.write_text(f"#!/bin/sh\necho \"$@\" >> '{registro}'\necho $$ > '{pasta}/pid'\nexec sleep 30\n")
        falso.chmod(0o755)
        if dica is not None:
            (cache / "duiaos" / "papel-inicio").write_text(dica)
        ambiente = {"PATH": f"{caixa}:/usr/bin:/bin", "HOME": pasta, "XDG_RUNTIME_DIR": str(runtime), "XDG_CACHE_HOME": str(cache)}
        inicio = time.monotonic()
        resultado = subprocess.run(["sh", str(RAIZ / "shell/sessao/fundo-imediato")], env=ambiente, timeout=20,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        self.assertEqual(resultado.returncode, 0)
        self.assertLess(time.monotonic() - inicio, 2, "o fundo imediato não pode segurar o início da sessão")
        for _ in range(40):
            if registro.exists() and (Path(pasta) / "pid").exists():
                break
            time.sleep(0.05)
        return registro.read_text().strip(), int((Path(pasta) / "pid").read_text()), runtime

    def test_mostra_a_imagem_e_sai_quando_a_area_avisa(self):
        with tempfile.TemporaryDirectory() as pasta:
            foto = Path(pasta) / "foto com espaço.jpg"
            foto.write_bytes(b"x")
            chamada, pid, runtime = self._rodar(pasta, f"{foto}\n#0F1724\nfit\n")
            self.assertEqual(chamada, f"-i {foto} -m fit -c #0F1724")
            os.kill(pid, 0)                                             # está no ar
            (runtime / "duiaos-area-pronta").touch()
            for _ in range(60):
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail("o fundo imediato não saiu depois do aviso da Área de Trabalho")

    def test_dica_estranha_vira_cor(self):
        for dica in ("/nao/existe.jpg\n#12345G\ndiagonal\n", "\n#0A0B0C\nfill\n", "lixo"):
            with tempfile.TemporaryDirectory() as pasta:
                chamada, pid, runtime = self._rodar(pasta, dica)
                self.assertTrue(chamada.startswith("-c #"), chamada)
                self.assertNotIn("-i", chamada)
                (runtime / "duiaos-area-pronta").touch()
                os.kill(pid, 15)

    def test_sem_swaybg_nao_atrapalha(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = subprocess.run(["/bin/sh", str(RAIZ / "shell/sessao/fundo-imediato")], env={"PATH": pasta, "HOME": pasta},
                                       timeout=10, check=False)
            self.assertEqual(resultado.returncode, 0)


class TesteAutostart(unittest.TestCase):
    def test_ordem_de_entrada(self):
        texto = (RAIZ / "shell/sessao/autostart").read_text()
        self.assertEqual(subprocess.run(["sh", "-n", str(RAIZ / "shell/sessao/autostart")], check=False).returncode, 0)
        ordem = [texto.index(trecho) for trecho in ("sessao/fundo-imediato", "dbus-update-activation-environment",
                                                    "area-de-trabalho/main.py", "barra-de-recursos ilha-de-aplicativos",
                                                    "comum/sessao.py", "/usr/bin/duiaos-wise --fundo")]
        self.assertEqual(ordem, sorted(ordem))
        self.assertIn("sleep 8\n    while", texto)                      # o Wise (que aquece a IA) entra depois da área de trabalho


if __name__ == "__main__":
    unittest.main()


class TesteBarraDosNavegadores(unittest.TestCase):
    """Chrome e afins com a barra do DuiaOS; os aplicativos com barra própria com os três botões (ADR 058)."""

    def test_liga_a_barra_do_sistema_sem_estragar_o_perfil(self):
        import json
        with tempfile.TemporaryDirectory() as pasta:
            config = Path(pasta)
            perfil = config / "google-chrome" / "Default" / "Preferences"
            perfil.parent.mkdir(parents=True)
            perfil.write_text(json.dumps({"browser": {"window_placement": {"top": 10}}, "profile": {"name": "Pessoa"}}))
            outro = config / "google-chrome" / "Profile 2" / "Preferences"
            outro.parent.mkdir(parents=True)
            outro.write_text("{}")
            instalado = lambda nomes: nomes[0] in ("google-chrome", "chromium")      # noqa: E731
            mudados = sessao.barra_do_sistema_nos_navegadores(config, instalado)
            self.assertEqual(sorted(p.parent.name for p in mudados), ["Default", "Default", "Profile 2"])  # chromium nasce com a opção
            dados = json.loads(perfil.read_text())
            self.assertIs(dados["browser"]["custom_chrome_frame"], False)
            self.assertEqual(dados["browser"]["window_placement"], {"top": 10})      # o resto fica
            self.assertEqual(dados["profile"]["name"], "Pessoa")
            self.assertFalse((config / "BraveSoftware").exists())                    # não instalado: nada
            self.assertEqual(sessao.barra_do_sistema_nos_navegadores(config, instalado), [])   # já ligado: nada

    def test_nao_mexe_em_navegador_aberto_nem_em_arquivo_estranho(self):
        with tempfile.TemporaryDirectory() as pasta:
            config = Path(pasta)
            (config / "google-chrome" / "Default").mkdir(parents=True)
            (config / "google-chrome" / "Default" / "Preferences").write_text('{"browser": {}}')
            (config / "google-chrome" / "SingletonLock").symlink_to("dell-1234")
            (config / "chromium" / "Default").mkdir(parents=True)
            (config / "chromium" / "Default" / "Preferences").write_text("isto não é json")
            mudados = sessao.barra_do_sistema_nos_navegadores(config, lambda nomes: True)
            self.assertNotIn(config / "google-chrome" / "Default" / "Preferences", mudados)
            self.assertEqual((config / "chromium" / "Default" / "Preferences").read_text(), "isto não é json")

    def test_botoes_dos_aplicativos_gtk(self):
        self.assertEqual(sessao.BOTOES_GTK, ":maximize,minimize,close")
        override = (RAIZ / "pacotes/duiaos-shell/raiz/usr/share/glib-2.0/schemas/90_duiaos.gschema.override").read_text()
        self.assertIn("button-layout=':maximize,minimize,close'", override)
        with tempfile.TemporaryDirectory() as pasta, mock.patch.object(sessao.pastas, "CONFIG", Path(pasta)), \
                mock.patch.object(sessao, "_rodar"), mock.patch.object(sessao.pastas, "estilo_da_interface", lambda: "padrao"):
            sessao.aplicar_aparencia(False)
            sessao.aplicar_aparencia(True)
            texto = (Path(pasta) / "gtk-3.0" / "settings.ini").read_text()
            self.assertEqual(texto.count("gtk-decoration-layout=:maximize,minimize,close"), 1)
