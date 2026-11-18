"""Testes do agente de senhas de rede (shell/comum/agente_de_senhas.py, ADR 070).

Os pedidos de cada tipo de rede são conferidos sem nada instalado; com o laboratório de rede de pé
(ferramentas/laboratorio-rede.sh) e o python3-gi, o agente se registra num NetworkManager de verdade e
responde a um pedido de senha de rede corporativa (802.1X) numa placa virtual.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import subprocess
import sys
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
sys.path.insert(0, str(RAIZ / "shell" / "testes"))
import agente_de_senhas as ag  # noqa: E402


class TesteJanela(unittest.TestCase):
    """A janela de verdade (não a demonstração) abre com o pedido que o agente monta, sem erro no QML."""
    def test_janela_abre_com_o_pedido(self):
        import json
        import re
        import tempfile
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("PySide6 não instalado")
        pedido = ag.pedido({"connection": {"id": "Casa"}, "802-11-wireless": {"ssid": list(b"Casa")},
                            "802-11-wireless-security": {"key-mgmt": "wpa-psk"}}, "802-11-wireless-security")
        with tempfile.TemporaryDirectory() as pasta:
            captura = Path(pasta) / "senha.png"
            resultado = subprocess.run([sys.executable, str(RAIZ / "shell/barra-de-recursos/senha_de_rede.py"), "--captura", str(captura)],
                                       input=json.dumps(pedido), capture_output=True, text=True, timeout=60)
            erros = re.findall(r".*(?:TypeError|ReferenceError|is not defined|Cannot assign|Traceback).*", resultado.stderr)
            self.assertEqual(erros, [])
            self.assertTrue(captura.exists(), resultado.stderr[-1500:])


class TestePedidos(unittest.TestCase):
    def test_wifi_comum_e_wep(self):
        p = ag.pedido({"connection": {"id": "Casa"}, "802-11-wireless": {"ssid": list(b"Casa Duia")},
                       "802-11-wireless-security": {"key-mgmt": "wpa-psk"}}, "802-11-wireless-security")
        self.assertEqual(p["campos"], [{"chave": "psk", "rotulo": "Senha", "senha": True}])
        self.assertIn("Casa Duia", p["texto"])
        wep = ag.pedido({"connection": {"id": "Velha"}, "802-11-wireless-security": {"key-mgmt": "none"}},
                        "802-11-wireless-security", nova=True)
        self.assertEqual(wep["campos"][0]["chave"], "wep-key0")
        self.assertIn("não funcionou", wep["texto"])

    def test_rede_corporativa(self):
        sem_usuario = ag.pedido({"connection": {"id": "eduroam"}, "802-1x": {"eap": ["peap"], "identity": ""}}, "802-1x")
        self.assertEqual([c["chave"] for c in sem_usuario["campos"]], ["identity", "password"])
        certificado = ag.pedido({"connection": {"id": "Empresa"}, "802-1x": {"eap": ["tls"], "identity": "eu"}}, "802-1x")
        self.assertEqual([c["chave"] for c in certificado["campos"]], ["private-key-password"])

    def test_vpns(self):
        openvpn = ag.pedido({"connection": {"id": "Trabalho"}, "vpn": {"service-type": "org.freedesktop.NetworkManager.openvpn",
                                                                        "data": {"connection-type": "password", "username": "gu"}}}, "vpn")
        self.assertEqual([c["chave"] for c in openvpn["campos"]], ["password"])
        resposta = ag.responder(openvpn, {"valores": {"password": "x"}})
        self.assertEqual(resposta, {"vpn": {"secrets": {"password": "x"}}})
        oc = ag.pedido({"connection": {"id": "Empresa"}, "vpn": {"service-type": "org.freedesktop.NetworkManager.openconnect",
                                                                  "data": {"gateway": "vpn.empresa.com.br", "protocol": "gp"}}}, "vpn")
        segredos = ag.responder(oc, {"valores": {"usuario": "gu", "senha": "s"}},
                                autenticar=lambda g, p, u, s: {"cookie": f"{g}-{p}-{u}", "gateway": g, "gwcert": ""})
        self.assertEqual(segredos["vpn"]["secrets"]["cookie"], "vpn.empresa.com.br-gp-gu")
        wg = ag.pedido({"connection": {"id": "Casa"}}, "wireguard")
        self.assertEqual(ag.responder(wg, {"valores": {"private-key": "abc="}}), {"wireguard": {"private-key": "abc="}})
        with self.assertRaises(ValueError):
            ag.pedido({"connection": {"id": "x"}}, "pppoe")

    def test_openconnect_le_o_cookie(self):
        class Saida:
            returncode, stdout = 0, "COOKIE='abc123'\nHOST='198.51.100.7'\nCONNECT_URL='https://vpn.empresa.com.br'\nFINGERPRINT='pin-sha256:xyz'\n"
        segredos = ag.autenticar_openconnect("vpn.empresa.com.br", "anyconnect", "gu", "s", rodar=lambda c, e: Saida())
        self.assertEqual(segredos, {"cookie": "abc123", "gateway": "https://vpn.empresa.com.br", "gwcert": "pin-sha256:xyz"})

        class Falha:
            returncode, stdout = 1, "Login failed.\n"
        with self.assertRaises(ag.SemSenha):
            ag.autenticar_openconnect("vpn", "anyconnect", "gu", "errada", rodar=lambda c, e: Falha())

    def test_lembrar_grava_na_conexao(self):
        chamadas = []
        ag.lembrar("uuid-1", {"802-11-wireless-security": {"psk": "segredo"}}, rodar=chamadas.append)
        self.assertEqual(chamadas, [["nmcli", "connection", "modify", "uuid-1", "wifi-sec.psk", "segredo", "wifi-sec.psk-flags", "0"]])
        chamadas.clear()
        ag.lembrar("uuid-2", {"vpn": {"secrets": {"password": "x"}}}, rodar=chamadas.append)
        self.assertEqual(chamadas, [])


try:
    import gi  # noqa: F401
    gi.require_version("Gio", "2.0")
    TEM_GI = True
except (ImportError, ValueError):
    TEM_GI = False

try:
    from test_rede import laboratorio_de_pe
except ImportError:
    def laboratorio_de_pe():
        return False


@unittest.skipUnless(TEM_GI and laboratorio_de_pe(), "precisa do python3-gi e do laboratório de rede")
class TesteComNetworkManagerDeVerdade(unittest.TestCase):
    def test_responde_ao_pedido_de_senha_da_rede_corporativa(self):
        registrado, perguntas = [], []

        def perguntar(dados):
            perguntas.append(dados)
            return {"valores": {"password": "senha-de-teste"}, "lembrar": False}
        agente = ag.Agente(perguntar=perguntar, ao_registrar=registrado.append)
        agente.iniciar()
        for _ in range(100):
            if registrado:
                break
            time.sleep(0.05)
        self.assertEqual(registrado, [True])
        criar = subprocess.run(["nmcli", "connection", "add", "type", "ethernet", "con-name", "Laboratório 802.1X", "ifname", "veth-c",
                                "802-1x.eap", "md5", "802-1x.identity", "aluno", "802-1x.password-flags", "2",
                                "ipv4.method", "manual", "ipv4.addresses", "10.88.0.40/24", "ipv6.method", "disabled", "connection.autoconnect", "no"],
                               capture_output=True, text=True)
        self.assertEqual(criar.returncode, 0, criar.stderr)
        self.addCleanup(subprocess.run, ["nmcli", "connection", "delete", "Laboratório 802.1X"], capture_output=True)
        subir = subprocess.Popen(["nmcli", "--wait", "15", "connection", "up", "Laboratório 802.1X"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(subir.kill)
        for _ in range(200):
            if agente.pedidos:
                break
            time.sleep(0.05)
        self.assertEqual(agente.pedidos[:1], [("802-1x", "802-1x")])
        self.assertEqual([c["chave"] for c in perguntas[0]["campos"]], ["password"])


if __name__ == "__main__":
    unittest.main()
