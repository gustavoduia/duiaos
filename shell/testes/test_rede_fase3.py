"""Rede e Internet, Fase 3 (ADR 071): firewall e tipo de rede, celular (USB, Bluetooth, modem), VLAN,
ponte, agregação e diagnóstico.

As partes puras rodam em qualquer lugar. Com o laboratório de rede de pé (ferramentas/laboratorio-rede.sh)
elas rodam também num NetworkManager de verdade; com o firewalld rodando e as zonas do DuiaOS instaladas,
o teste confere que uma rede pública bloqueia uma conexão vinda de fora e a privada deixa passar o SSH.
(No contêiner do Claude o firewall-cmd precisa do python3.12: DUIAOS_FIREWALL_CMD="python3.12 /usr/bin/firewall-cmd".)

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
sys.path.insert(0, str(RAIZ / "shell" / "testes"))
import rede  # noqa: E402
from test_rede import laboratorio_de_pe  # noqa: E402

if os.environ.get("DUIAOS_FIREWALL_CMD"):
    rede.FIREWALL_CMD = os.environ["DUIAOS_FIREWALL_CMD"].split()


class TesteFirewallPuro(unittest.TestCase):
    def test_estado_e_zona(self):
        self.assertEqual(rede.interpretar_firewall("running\n", "duiaos-publica\n", "yes\n"),
                         {"instalado": True, "ligado": True, "padrao": "duiaos-publica", "ssh": True})
        self.assertFalse(rede.interpretar_firewall("ausente", "", "")["instalado"])
        self.assertEqual(rede.argumentos({"zona": "privada"}), ["connection.zone", "duiaos-privada"])
        self.assertEqual(rede.argumentos({"zona": ""}), ["connection.zone", ""])
        self.assertEqual(rede.TIPO_DA_ZONA["home"], "privada")

    def test_quem_ainda_nao_tem_tipo(self):
        conexoes = [{"uuid": "a", "tipo": "wifi", "ativa": True}, {"uuid": "b", "tipo": "vpn", "ativa": True},
                    {"uuid": "c", "tipo": "cabo", "ativa": False}, {"uuid": "d", "tipo": "cabo", "ativa": True}]
        self.assertEqual([c["uuid"] for c in rede.sem_tipo_de_rede(conexoes, {"d": "privada"})], ["a"])


class TesteCelular(unittest.TestCase):
    def test_celular_pelo_cabo_usb(self):
        with tempfile.TemporaryDirectory() as pasta:
            for placa, driver in (("usb0", "rndis_host"), ("enx1", "ipheth"), ("eth0", "e1000e")):
                (Path(pasta) / placa / "device").mkdir(parents=True)
                (Path(pasta) / "drivers" / driver).mkdir(parents=True, exist_ok=True)
                os.symlink(Path(pasta) / "drivers" / driver, Path(pasta) / placa / "device" / "driver")
            self.assertEqual(rede.celular_por_usb("usb0", pasta), "Android")
            self.assertEqual(rede.celular_por_usb("enx1", pasta), "iPhone")
            self.assertEqual(rede.celular_por_usb("eth0", pasta), "")
            self.assertEqual(rede.celular_por_usb("nada", pasta), "")

    def test_modem(self):
        saida = ("modem.3gpp.operator-name : VIVO\nmodem.generic.signal-quality.value : 71\n"
                 "modem.generic.access-technologies.value[1] : lte\nmodem.generic.state : registered\n"
                 "modem.generic.unlock-required : sim-pin\n")
        self.assertEqual(rede.interpretar_modem(saida), {"operadora": "VIVO", "sinal": 71, "tecnologia": "4G",
                                                         "estado": "registered", "bloqueado": True})
        with self.assertRaises(rede.ErroDeRede):
            rede.nova_celular("Vivo", "", rodar=lambda *a, **k: (0, "", ""))
        with self.assertRaises(rede.ErroDeRede):
            rede.nova_celular("Vivo", "zap.vivo.com.br", pin="12", rodar=lambda *a, **k: (0, "", ""))
        comandos = []
        rede.nova_celular("Vivo", "zap.vivo.com.br", "vivo", "vivo", "1234",
                          rodar=lambda c, **k: (comandos.append(c), (0, "Conexão (0f8fad5b-d9cb-469f-a165-70867728950e) adicionada.", ""))[1])
        self.assertIn("gsm.apn", comandos[0])
        self.assertIn("1234", comandos[0])
        with self.assertRaises(rede.ErroDeRede):
            rede.conectar_celular_bluetooth("não é endereço")


class TesteDiagnosticoPuro(unittest.TestCase):
    def _nmcli(self, dispositivos, detalhes, conectividade="full"):
        def rodar(comando, entrada=None, tempo=None):
            if "device" in comando and "show" not in comando:
                return 0, dispositivos, ""
            if "show" in comando:
                return 0, detalhes, ""
            if "connectivity" in comando:
                return 0, conectividade + "\n", ""
            return 1, "", ""
        return rodar

    def test_para_no_primeiro_problema(self):
        sem_cabo = self._nmcli("enp3s0:ethernet:unavailable::\n", "")
        passos = rede.diagnosticar(rodar=sem_cabo, resolver=lambda n: [], pingar=lambda ip: True)
        self.assertEqual([(p["nome"], p["ok"]) for p in passos], [("Conexão", False)])
        self.assertIn("cabo", passos[0]["dica"])

        detalhes = "IP4.ADDRESS[1]:192.168.0.23/24\nIP4.GATEWAY:192.168.0.1\n"
        conectado = "enp3s0:ethernet:connected:Casa:u1\n"

        def sem_dns(nome):
            raise socket.gaierror("sem DNS")
        passos = rede.diagnosticar(rodar=self._nmcli(conectado, detalhes), resolver=sem_dns, pingar=lambda ip: True)
        self.assertEqual([p["ok"] for p in passos], [True, True, True, False])
        self.assertIn("DNS", passos[-1]["nome"])

        passos = rede.diagnosticar(rodar=self._nmcli(conectado, detalhes, "portal"), resolver=lambda n: [], pingar=lambda ip: False)
        self.assertEqual(passos[-1]["nome"], "Internet")
        self.assertIn("login", passos[-1]["explicacao"])

        sem_ip = self._nmcli(conectado, "IP4.ADDRESS[1]:169.254.3.4/16\n")
        passos = rede.diagnosticar(rodar=sem_ip, resolver=lambda n: [], pingar=lambda ip: True)
        self.assertEqual((passos[-1]["nome"], passos[-1]["ok"]), ("Endereço", False))


class TesteAvancadoPuro(unittest.TestCase):
    def test_validacao(self):
        for numero in (0, 4095, "abc"):
            with self.assertRaises(rede.ErroDeRede):
                rede.nova_vlan("enp3s0", numero, rodar=lambda *a, **k: (0, "", ""))
        with self.assertRaises(rede.ErroDeRede):
            rede.nova_ponte("Ponte", [], rodar=lambda *a, **k: (0, "", ""))
        with self.assertRaises(rede.ErroDeRede):
            rede.nova_agregacao("Bond", ["enp3s0"], modo="inventado", rodar=lambda *a, **k: (0, "", ""))


def _nmcli(*args):
    return subprocess.run(["nmcli", *args], capture_output=True, text=True, timeout=30)


def _uuid_ativo(placa):
    for linha in _nmcli("-t", "-f", "UUID,DEVICE", "connection", "show", "--active").stdout.splitlines():
        uuid, _, dispositivo = linha.partition(":")
        if dispositivo == placa:
            return uuid
    return ""


def _firewall_de_pe():
    try:
        r = subprocess.run([*rede.FIREWALL_CMD, "--get-zones"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and "duiaos-publica" in r.stdout and "duiaos-privada" in r.stdout


@unittest.skipUnless(laboratorio_de_pe(), "laboratório de rede desligado (sudo bash ferramentas/laboratorio-rede.sh)")
class TesteFase3ComNetworkManagerDeVerdade(unittest.TestCase):
    def test_vlan_criar_e_apagar(self):
        uuid = rede.nova_vlan("veth-c", 42, "VLAN de teste")
        try:
            self.assertEqual(_nmcli("-t", "-g", "vlan.id,vlan.parent", "connection", "show", uuid).stdout.split(), ["42", "veth-c"])
        finally:
            rede.esquecer(uuid)

    def test_ponte_com_placa_e_apagar_junto(self):
        uuid = rede.nova_ponte("Ponte de teste", ["veth-c"])
        try:
            controladas = [linha for linha in _nmcli("-t", "-f", "NAME", "connection", "show").stdout.splitlines()
                           if linha.startswith("Ponte de teste · ")]
            self.assertEqual(controladas, ["Ponte de teste · veth-c"])
        finally:
            rede.apagar_com_membros(uuid)
        nomes = _nmcli("-t", "-f", "NAME", "connection", "show").stdout
        self.assertNotIn("Ponte de teste", nomes)

    def test_diagnostico_de_verdade(self):
        passos = rede.diagnosticar()
        self.assertTrue(passos)
        self.assertTrue(all(set(p) == {"nome", "ok", "explicacao", "dica"} for p in passos))

    @unittest.skipUnless(_firewall_de_pe(), "firewalld com as zonas do DuiaOS não está rodando")
    def test_rede_publica_bloqueia_e_privada_deixa_o_ssh(self):
        uuid = _uuid_ativo("veth-a")
        self.assertTrue(uuid, "veth-a sem conexão ativa")
        endereco = _nmcli("-t", "-g", "IP4.ADDRESS", "device", "show", "veth-a").stdout.split("/")[0].strip()
        antes = _nmcli("-t", "-g", "connection.zone", "connection", "show", uuid).stdout.strip()
        escuta = subprocess.Popen(["nc", "-l", "-k", "-s", endereco, "-p", "22"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def entra():
            return subprocess.run(["ip", "netns", "exec", "duiaos-com-dhcp", "nc", "-z", "-w", "2", endereco, "22"],
                                  capture_output=True, timeout=10).returncode == 0
        try:
            time.sleep(0.5)
            rede.definir_tipo_de_rede(uuid, "publica")
            time.sleep(1)
            self.assertEqual(rede.ler_zonas([{"uuid": uuid, "ativa": True}])[uuid], "publica")
            self.assertFalse(entra(), "rede pública deixou entrar")
            rede.definir_tipo_de_rede(uuid, "privada")
            time.sleep(1)
            self.assertTrue(entra(), "rede privada bloqueou o SSH")
            self.assertEqual(_uuid_ativo("veth-a"), uuid)          # mudou sem derrubar a conexão
        finally:
            escuta.terminate()
            escuta.wait(5)
            _nmcli("connection", "modify", uuid, "connection.zone", antes)
            _nmcli("device", "reapply", "veth-a")


if __name__ == "__main__":
    unittest.main()
