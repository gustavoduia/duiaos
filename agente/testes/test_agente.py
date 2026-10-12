"""Teste do duiaos-agente de ponta a ponta num D-Bus de sessão próprio, com o apt
de mentira (--simular-apt): nada muda no computador.

Também confere os arquivos de sistema do pacote (D-Bus, polkit, systemd).
Precisa de dbus-daemon, gdbus e python3-gi; sem eles, a parte do D-Bus é pulada.
"""
import ast
import configparser
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1]
RAIZ_PACOTE = PASTA.parent / "pacotes/duiaos-agente/raiz"
sys.path.insert(0, str(PASTA))
import plano as pl  # noqa: E402

try:
    import gi  # noqa: F401
    gi.require_version("Gio", "2.0")
    TEM_GI = True
except (ImportError, ValueError):
    TEM_GI = False


def valor(saida):
    """Saída do gdbus ('("texto",)') -> texto."""
    return ast.literal_eval(saida.strip())[0]


@unittest.skipUnless(TEM_GI and shutil.which("dbus-daemon") and shutil.which("gdbus"), "sem D-Bus para testar")
class TestAgenteNoDBus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.mkdtemp()
        cls.dbus = subprocess.Popen(["dbus-daemon", "--session", "--nofork", "--print-address"],
                                    stdout=subprocess.PIPE, text=True)
        cls.endereco = cls.dbus.stdout.readline().strip()
        cls.ambiente = {**os.environ, "DBUS_SESSION_BUS_ADDRESS": cls.endereco}
        cls.registro = Path(cls.temp) / "acoes.jsonl"
        cls.agente = subprocess.Popen([sys.executable, str(PASTA / "agente.py"), "--sessao", "--sem-polkit",
                                       "--simular-apt", "--registro", str(cls.registro)], env=cls.ambiente)
        for _ in range(50):
            if cls.chamar("Estado", check=False).returncode == 0:
                break
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.agente.terminate()
        cls.agente.wait(5)
        cls.dbus.terminate()
        cls.dbus.wait(5)
        shutil.rmtree(cls.temp, ignore_errors=True)

    @classmethod
    def chamar(cls, metodo, *argumentos, check=True):
        return subprocess.run(["gdbus", "call", "--session", "--dest", "org.duiaos.Agente1", "--object-path",
                               "/org/duiaos/Agente1", "--method", f"org.duiaos.Agente1.{metodo}", *argumentos],
                              capture_output=True, text=True, env=cls.ambiente, check=check, timeout=30)

    def esperar_fim(self, id_plano):
        for _ in range(100):
            estado = json.loads(valor(self.chamar("Estado").stdout))
            if estado["tarefa"] is None and estado["ultima"] and estado["ultima"]["id"] == id_plano:
                return estado["ultima"]
            time.sleep(0.05)
        self.fail("a ação não terminou")

    def test_preparar_executar_e_registrar(self):
        plano = json.loads(valor(self.chamar("Preparar", "instalar_aplicativo", '{"pacote": "vlc"}').stdout))
        self.assertIsNone(plano["recusa"])
        self.assertEqual(plano["mudancas"]["instalar"][0]["pacote"], "vlc")
        self.assertEqual(plano["baixar_bytes"], 1048576)
        self.chamar("Executar", plano["id"])
        ultima = self.esperar_fim(plano["id"])
        # O apt de mentira não instala: a verificação tem que perceber
        self.assertEqual(ultima["resultado"], "erro")
        self.assertIn("não aparece instalado", ultima["mensagem"])
        # Plano usado não vale de novo
        r = self.chamar("Executar", plano["id"], check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Vencido", r.stderr)
        eventos = [json.loads(l)["evento"] for l in self.registro.read_text().splitlines()]
        self.assertIn("preparado", eventos)
        self.assertIn("executado", eventos)

    def test_recusas_vem_no_plano(self):
        plano = json.loads(valor(self.chamar("Preparar", "remover_aplicativo", '{"pacote": "duiaos-shell"}').stdout))
        self.assertIsNotNone(plano["recusa"])
        r = self.chamar("Executar", plano["id"], check=False)
        self.assertNotEqual(r.returncode, 0)
        plano = json.loads(valor(self.chamar("Preparar", "instalar_aplicativo", '{"pacote": "instalado-ja"}').stdout))
        self.assertEqual(plano["recusa"]["codigo"], "JaInstalado")

    def test_argumentos_ruins(self):
        r = self.chamar("Preparar", "instalar_aplicativo", '{"pacote": "vlc; reboot"}', check=False)
        self.assertIn("Invalido", r.stderr)
        r = self.chamar("Preparar", "rodar_comando", "{}", check=False)
        self.assertIn("Invalido", r.stderr)

    def test_remover_com_sucesso(self):
        plano = json.loads(valor(self.chamar("Preparar", "remover_aplicativo", '{"pacote": "instalado-x"}').stdout))
        self.assertIsNone(plano["recusa"])
        self.assertTrue(plano["resumo"].startswith("Remover instalado-x"))


class TestArquivosDoPacote(unittest.TestCase):
    def test_polkit_tem_uma_acao_por_acao_do_agente(self):
        politica = ET.parse(RAIZ_PACOTE / "usr/share/polkit-1/actions/org.duiaos.agente.policy")
        ids = {a.get("id") for a in politica.findall("action")}
        self.assertEqual(ids, {f"org.duiaos.agente.{acao}" for acao in pl.ACOES})
        for acao in politica.findall("action"):
            self.assertNotEqual(acao.find("defaults/allow_any").text, "yes")

    def test_regra_exige_sessao_local_ativa_e_administrador(self):
        regra = (RAIZ_PACOTE / "usr/share/polkit-1/rules.d/50-duiaos-agente.rules").read_text()
        for trecho in ("subject.local", "subject.active", 'isInGroup("sudo")', '"org.duiaos.agente."'):
            self.assertIn(trecho, regra)

    def test_dbus_e_systemd(self):
        conf = ET.parse(RAIZ_PACOTE / "usr/share/dbus-1/system.d/org.duiaos.Agente1.conf")
        donos = [p.get("user") for p in conf.findall("policy")
                 if p.find("allow[@own='org.duiaos.Agente1']") is not None]
        self.assertEqual(donos, ["root"])
        unidade = configparser.ConfigParser(strict=False)
        unidade.read(RAIZ_PACOTE / "usr/lib/systemd/system/duiaos-agente.service")
        self.assertEqual(unidade["Service"]["BusName"], "org.duiaos.Agente1")
        self.assertIn("/usr/share/duiaos/agente/agente.py", unidade["Service"]["ExecStart"])


if __name__ == "__main__":
    unittest.main()
