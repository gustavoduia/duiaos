"""Testes da 2ª rodada da interface (ADR 045): Tela de Descanso no swayidle, modo escuro, fundos importados,
foto da conta e o serviço de notificações (D-Bus de verdade, quando o ambiente tem dbus-run-session e gi).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
sys.path.insert(0, str(RAIZ / "apps" / "configuracoes"))

import sessao  # noqa: E402

try:
    import gi  # noqa: F401
    TEM_GI = True
except ImportError:
    TEM_GI = False
try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False


class TesteSessao(unittest.TestCase):
    def test_descanso_antes_do_bloqueio(self):
        comando = sessao.comando_swayidle(10, 0, "/b", 5, "python3 /d/main.py")
        self.assertEqual(comando[:7], ["swayidle", "-w", "timeout", "300", "python3 /d/main.py", "resume", "pkill -f descanso/main.py"])
        self.assertIn("600", comando)
        self.assertNotIn("resume", sessao.comando_swayidle(10, 0, "/b", 0, "python3 /d/main.py"))

    def test_modo_escuro_grava_e_apaga(self):
        with tempfile.TemporaryDirectory() as pasta:
            antes, estilo = sessao.pastas.CONFIG, sessao.pastas.estilo_da_interface
            sessao.pastas.CONFIG = Path(pasta)
            sessao.pastas.estilo_da_interface = lambda: "padrao"       # o Clássico: no modo claro não há override
            try:
                sessao.aplicar_aparencia(True)
                override = Path(pasta, "labwc", "themerc-override")
                self.assertIn("window.active.title.bg.color", override.read_text())
                self.assertIn("gtk-application-prefer-dark-theme=1", Path(pasta, "gtk-3.0", "settings.ini").read_text())
                sessao.aplicar_aparencia(False)
                self.assertFalse(override.exists())
                self.assertIn("gtk-application-prefer-dark-theme=0", Path(pasta, "gtk-4.0", "settings.ini").read_text())
                # Um override da pessoa (sem a marca do DuiaOS) nunca é apagado
                override.write_text("window.active.title.bg.color: #000000\n")
                sessao.aplicar_aparencia(False)
                self.assertTrue(override.exists())
            finally:
                sessao.pastas.CONFIG, sessao.pastas.estilo_da_interface = antes, estilo


class TesteFundosEFoto(unittest.TestCase):
    def test_copiar_sem_sobrescrever(self):
        import operacoes_fundo
        with tempfile.TemporaryDirectory() as pasta:
            origem = Path(pasta, "praia.mp4")
            origem.write_bytes(b"video")
            destino = Path(pasta, "fundos")
            destino.mkdir()
            primeiro = operacoes_fundo.copiar_sem_sobrescrever(origem, destino)
            self.assertEqual(operacoes_fundo.copiar_sem_sobrescrever(origem, destino), primeiro)   # o mesmo: reaproveita
            origem.write_bytes(b"outro video")
            self.assertEqual(operacoes_fundo.copiar_sem_sobrescrever(origem, destino).name, "praia (2).mp4")

    @unittest.skipUnless(TEM_QT, "PySide6 não instalado")
    def test_foto_redonda(self):
        import operacoes_fundo
        from PySide6.QtGui import QGuiApplication, QImage
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QGuiApplication.instance() or QGuiApplication([])
        png = operacoes_fundo.foto_redonda("#2E6BE6", "Gustavo")
        self.assertTrue(png.startswith(b"\x89PNG"))
        imagem = QImage.fromData(png)
        self.assertEqual((imagem.width(), imagem.height()), (256, 256))
        self.assertEqual(imagem.pixelColor(2, 2).alpha(), 0)          # canto transparente: é redonda
        self.assertEqual(imagem.pixelColor(128, 30).alpha(), 255)
        with self.assertRaises(ValueError):
            operacoes_fundo.foto_redonda("/nao/existe.jpg")


@unittest.skipUnless(TEM_GI, "gi (PyGObject) não instalado")
class TesteNotificacoes(unittest.TestCase):
    def test_interpretar(self):
        sys.path.insert(0, str(RAIZ / "shell" / "notificacoes"))
        import servico
        dados = servico.interpretar("Firefox", 0, "firefox-esr", "Download concluído", "arquivo.zip",
                                    ["default", "Abrir", "pasta", "Mostrar na pasta"], {"urgency": 2}, -1)
        self.assertEqual(dados["urgencia"], 2)
        self.assertTrue(dados["temPadrao"])
        self.assertEqual(dados["acoes"], [{"chave": "pasta", "rotulo": "Mostrar na pasta"}])

    @unittest.skipUnless(TEM_QT and shutil.which("dbus-run-session"), "sem PySide6 ou dbus-run-session")
    def test_servico_no_dbus(self):
        with tempfile.TemporaryDirectory() as pasta:
            cliente = Path(pasta, "cliente.py")
            cliente.write_text(textwrap.dedent("""
                import time, gi
                gi.require_version("Gio", "2.0")
                from gi.repository import Gio, GLib
                c = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                for _ in range(50):
                    try:
                        r = c.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                            "org.freedesktop.Notifications", "Notify",
                            GLib.Variant("(susssasa{sv}i)", ("teste", 0, "", "Olá", "Corpo", ["default", "Abrir"],
                                         {"urgency": GLib.Variant("y", 1)}, 3000)), None, 0, -1, None)
                        print(r.unpack()[0]); break
                    except GLib.Error:
                        time.sleep(0.2)
                time.sleep(0.5)
            """))
            roteiro = Path(pasta, "roteiro.sh")
            roteiro.write_text(f"{sys.executable} {RAIZ}/shell/notificacoes/main.py --sem-janela & SERVICO=$!\n"
                               f"{sys.executable} {cliente}\nkill $SERVICO\n")
            ambiente = {**os.environ, "XDG_RUNTIME_DIR": pasta, "HOME": pasta, "QT_QPA_PLATFORM": "offscreen"}
            saida = subprocess.run(["dbus-run-session", "--", "sh", str(roteiro)], capture_output=True, text=True,
                                   timeout=60, env=ambiente).stdout
            self.assertIn("1", saida.split())
            historico = json.loads(Path(pasta, "duiaos-notificacoes.json").read_text())
            self.assertEqual(historico[0]["titulo"], "Olá")


if __name__ == "__main__":
    unittest.main()
