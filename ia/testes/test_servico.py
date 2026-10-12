"""Teste do serviço duiaos-ia de ponta a ponta: um D-Bus de sessão próprio,
um Ollama de mentira (HTTP) e o cliente de linha de comando.

Precisa de dbus-daemon e python3-gi; sem eles, o teste é pulado.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA_IA = Path(__file__).resolve().parents[1]

try:
    import gi  # noqa: F401
    gi.require_version("Gio", "2.0")
    TEM_GI = True
except (ImportError, ValueError):
    TEM_GI = False


class OllamaFalso(BaseHTTPRequestHandler):
    instalados = set()
    pausa = 0.05

    def log_message(self, *_):
        pass

    def _json(self, dados, codigo=200):
        corpo = json.dumps(dados).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")

    def do_GET(self):
        if self.path == "/api/version":
            self._json({"version": "0.40.3"})
        elif self.path == "/api/tags":
            self._json({"models": [{"name": n} for n in sorted(self.instalados)]})
        else:
            self._json({"error": "não existe"}, 404)

    def do_DELETE(self):
        nome = self._corpo()["model"]
        if nome in self.instalados:
            self.instalados.discard(nome)
            self._json({})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        nome = self._corpo()["model"]
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        linhas = [{"status": "pulling manifest"}]
        for passo in range(0, 101, 5):
            linhas.append({"status": "pulling abc", "digest": "sha256:abc",
                           "total": 1000, "completed": passo * 10})
        linhas += [{"status": "verifying sha256 digest"}, {"status": "success"}]
        try:
            for linha in linhas:
                self.wfile.write((json.dumps(linha) + "\n").encode())
                self.wfile.flush()
                time.sleep(self.pausa)
        except (BrokenPipeError, ConnectionResetError):
            return
        self.instalados.add(nome)


@unittest.skipUnless(TEM_GI and shutil.which("dbus-daemon"), "precisa de python3-gi e dbus-daemon")
class TesteServico(unittest.TestCase):
    def setUp(self):
        OllamaFalso.instalados = set()
        OllamaFalso.pausa = 0.05
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), OllamaFalso)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.pasta = tempfile.mkdtemp()
        self.dbus = subprocess.Popen(["dbus-daemon", "--session", "--nofork", "--print-address=1"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        endereco = self.dbus.stdout.readline().strip()
        self.env = dict(os.environ, DBUS_SESSION_BUS_ADDRESS=endereco, DUIAOS_IA_BARRAMENTO="sessao")
        self.servico = subprocess.Popen(
            [sys.executable, str(PASTA_IA / "servico.py"), "--sessao", "--sem-polkit",
             "--pasta", self.pasta, "--ollama", f"http://127.0.0.1:{self.http.server_port}",
             "--memoria-gb", "15.5"], env=self.env)
        for _ in range(50):
            if Path(self.pasta, "estado.json").exists():
                break
            time.sleep(0.1)

    def tearDown(self):
        self.servico.terminate()
        self.servico.wait(5)
        self.dbus.terminate()
        self.dbus.wait(5)
        self.dbus.stdout.close()
        self.http.shutdown()
        self.http.server_close()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def cli(self, *argumentos):
        return subprocess.run([sys.executable, str(PASTA_IA / "cliente.py"), *argumentos],
                              env=self.env, capture_output=True, text=True, timeout=60)

    def estado(self):
        return json.loads(Path(self.pasta, "estado.json").read_text())

    def esperar(self, condicao, segundos=15):
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            try:
                if condicao(self.estado()):
                    return True
            except (OSError, ValueError):
                pass
            time.sleep(0.1)
        return False

    def test_primeiro_login_baixa_e_ativa_o_padrao(self):
        self.assertEqual(self.estado()["ativo"], "")
        self.assertEqual(self.cli("garantir-padrao").returncode, 0)
        self.assertTrue(self.esperar(lambda e: e["tarefa"] and e["tarefa"]["fracao"] > 0.2))
        self.assertTrue(self.esperar(lambda e: e["ativo"] == "qwen3.5:4b" and not e["tarefa"]))
        self.assertEqual(self.estado()["ultima"]["resultado"], "ok")
        self.assertEqual(oct(Path(self.pasta, "estado.json").stat().st_mode & 0o777), "0o644")
        # Segundo login: nada a fazer
        self.cli("garantir-padrao")
        time.sleep(0.3)
        self.assertIsNone(self.estado()["tarefa"])

    def test_padrao_ja_baixado_so_ativa(self):
        OllamaFalso.instalados = {"qwen3.5:4b"}
        self.cli("garantir-padrao")
        self.assertTrue(self.esperar(lambda e: e["ativo"] == "qwen3.5:4b"))
        self.assertIsNone(self.estado()["tarefa"])

    def test_baixar_ativar_remover(self):
        OllamaFalso.instalados = {"qwen3.5:4b"}
        self.cli("garantir-padrao")
        resultado = self.cli("baixar", "phi4-mini:3.8b")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("baixado", resultado.stdout)
        self.assertEqual(self.estado()["ativo"], "qwen3.5:4b")      # baixar não troca o ativo
        self.assertEqual(self.cli("ativar", "phi4-mini:3.8b").returncode, 0)
        self.assertEqual(self.estado()["ativo"], "phi4-mini:3.8b")
        recusa = self.cli("remover", "phi4-mini:3.8b")
        self.assertNotEqual(recusa.returncode, 0)
        self.assertIn("modelo ativo", recusa.stderr)
        self.assertIn("qwen3.5:4b", self.estado()["instalados"])
        self.assertEqual(self.cli("remover", "qwen3.5:4b").returncode, 0)
        self.assertNotIn("qwen3.5:4b", OllamaFalso.instalados)
        # O estado público já sai sem o modelo removido (as telas atualizam na hora)
        self.assertEqual(self.estado()["instalados"], ["phi4-mini:3.8b"])
        catalogo = self.cli("catalogo").stdout
        self.assertIn("* phi4-mini:3.8b", catalogo)
        self.assertIn("x llama3.3:70b", catalogo)

    def test_recusas(self):
        self.assertIn("catálogo", self.cli("baixar", "malicioso:latest").stderr)
        self.assertIn("memória", self.cli("baixar", "llama3.3:70b").stderr)
        self.assertIn("Baixe", self.cli("ativar", "gemma4:e4b").stderr)

    def test_modelo_apagado_por_fora_aparece_sozinho(self):
        OllamaFalso.instalados = {"qwen3.5:4b", "phi4:14b"}
        self.cli("garantir-padrao")
        OllamaFalso.instalados.discard("phi4:14b")            # "ollama rm" pelo terminal
        self.assertTrue(self.esperar(lambda e: e["instalados"] == ["qwen3.5:4b"], segundos=15))

    def test_cancelar(self):
        OllamaFalso.pausa = 0.3
        processo = subprocess.Popen([sys.executable, str(PASTA_IA / "cliente.py"), "baixar", "qwen3:4b"],
                                    env=self.env, stdout=subprocess.DEVNULL)
        self.addCleanup(processo.wait, 10)
        self.assertTrue(self.esperar(lambda e: e["tarefa"] is not None))
        ocupado = self.cli("baixar", "qwen3:8b")
        self.assertIn("andamento", ocupado.stderr)
        self.cli("cancelar")
        self.assertTrue(self.esperar(lambda e: not e["tarefa"] and e["ultima"]["resultado"] == "cancelado"))
        self.assertNotIn("qwen3:4b", OllamaFalso.instalados)


if __name__ == "__main__":
    unittest.main()
