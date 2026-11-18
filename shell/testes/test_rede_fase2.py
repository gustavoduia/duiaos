"""Rede e Internet, Fase 2 (ADR 070): VPN, Wi-Fi corporativo, proxy, ponto de acesso e QR da Wi-Fi.

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
sys.path.insert(0, str(RAIZ / "shell" / "testes"))
import proxy  # noqa: E402
import rede  # noqa: E402
from test_rede import laboratorio_de_pe  # noqa: E402

try:
    import cryptography  # noqa: F401
    TEM_CRIPTOGRAFIA = True
except ImportError:
    TEM_CRIPTOGRAFIA = False

CHAVE = "YCgg3/FdHQ6Eq3V8CdcmUoEVG3Zh2aXOzVnmQ9Ej3WY="


class TesteVpn(unittest.TestCase):
    def test_nome_de_interface(self):
        self.assertEqual(rede._nome_de_interface("Trabalho São Paulo"), "wg-trabalho-sao")
        self.assertEqual(rede._nome_de_interface("!!!"), "wg-vpn")

    @unittest.skipUnless(TEM_CRIPTOGRAFIA, "precisa do python3-cryptography")
    def test_chaves_e_arquivo_do_wireguard(self):
        privada, publica = rede.gerar_chaves_wireguard()
        self.assertEqual((len(privada), len(publica)), (44, 44))
        texto = rede.configuracao_wireguard("10.0.0.2/32", privada, publica, "vpn.exemplo.com:51820", dns="1.1.1.1")
        self.assertIn("[Interface]", texto)
        self.assertIn("Endpoint = vpn.exemplo.com:51820", texto)
        self.assertIn("AllowedIPs = 0.0.0.0/0, ::/0", texto)
        for errado in ({"endereco": "10.0.0.300/32"}, {"servidor": "sem-porta"}, {"chave_servidor": "curta"}, {"dns": "1.1.1"}):
            args = {"endereco": "10.0.0.2/32", "chave_privada": privada, "chave_servidor": publica, "servidor": "vpn:51820", **errado}
            with self.assertRaises(rede.ErroDeRede):
                rede.configuracao_wireguard(**args)

    def test_qr_da_wifi(self):
        self.assertEqual(rede.texto_qr_wifi("Casa Duia", "abc;123"), "WIFI:T:WPA;S:Casa Duia;P:abc\;123;;")
        self.assertEqual(rede.texto_qr_wifi("Café", ""), "WIFI:T:nopass;S:Café;;")

    def test_wifi_corporativo_confere_antes(self):
        chamadas = []
        with self.assertRaises(rede.ErroDeRede):
            rede.conectar_empresa("eduroam", usuario="", senha="x", sem_verificar=True, rodar=lambda *a, **k: chamadas.append(a))
        with self.assertRaises(rede.ErroDeRede):          # sem o certificado da instituição e sem marcar "não verificar"
            rede.conectar_empresa("eduroam", usuario="eu@uni.br", senha="x", rodar=lambda *a, **k: chamadas.append(a))
        self.assertEqual(chamadas, [])

        def falso(comando, entrada=None, tempo=None):
            chamadas.append(comando)
            return 0, "Connection 'eduroam' (11111111-2222-3333-4444-555555555555) successfully added.", ""
        rede.conectar_empresa("eduroam", usuario="eu@uni.br", senha="segredo", dominio="uni.br", certificado_ca="/tmp/ca.pem", rodar=falso)
        criar = chamadas[0]
        self.assertEqual(criar[criar.index("802-1x.eap") + 1], "peap")
        self.assertEqual(criar[criar.index("802-1x.domain-suffix-match") + 1], "uni.br")
        self.assertEqual(chamadas[1][:3], ["nmcli", "connection", "up"])

    def test_ponto_de_acesso_pede_senha_de_8(self):
        with self.assertRaises(rede.ErroDeRede):
            rede.ligar_ponto_de_acesso("wlp2s0", "Duia", "curta", rodar=lambda *a, **k: (0, "", ""))


class TesteProxy(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.antes = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self.pasta.name

    def tearDown(self):
        if self.antes is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.antes
        self.pasta.cleanup()

    def test_manual_grava_chaves_e_ambiente(self):
        comandos = []
        config = {"modo": "manual", "http": {"servidor": "proxy.empresa", "porta": 3128}, "https": {"servidor": "", "porta": 0},
                  "socks": {"servidor": "", "porta": 0}, "excecoes": ["localhost", "*.empresa"]}
        variaveis = proxy.gravar(config, rodar=lambda c: (comandos.append(c), (0, ""))[1])
        self.assertIn(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"], comandos)
        self.assertEqual(variaveis["http_proxy"], "http://proxy.empresa:3128/")
        self.assertEqual(variaveis["HTTPS_PROXY"], "http://proxy.empresa:3128/")
        self.assertEqual(variaveis["no_proxy"], "localhost,*.empresa")
        self.assertEqual(proxy.ambiente_salvo()["http_proxy"], "http://proxy.empresa:3128/")
        self.assertIn('Acquire::http::Proxy "http://proxy.empresa:3128/";', proxy.configuracao_apt(config))
        # Desligar apaga as variáveis
        proxy.gravar({"modo": "desligado"}, rodar=lambda c: (0, ""))
        self.assertEqual(proxy.ambiente_salvo(), {})

    def test_validacao(self):
        self.assertIn("pelo menos um servidor", " ".join(proxy.validar({"modo": "manual"})))
        self.assertIn("Porta", " ".join(proxy.validar({"modo": "manual", "http": {"servidor": "p", "porta": 70000}})))
        self.assertIn("automática", " ".join(proxy.validar({"modo": "automatico", "pac": "proxy.pac"})))
        self.assertEqual(proxy.validar({"modo": "automatico", "pac": "http://p/proxy.pac"}), [])

    def test_le_o_gsettings(self):
        respostas = {("org.gnome.system.proxy", "mode"): "'manual'", ("org.gnome.system.proxy.http", "host"): "'p.br'",
                     ("org.gnome.system.proxy.http", "port"): "8080", ("org.gnome.system.proxy", "ignore-hosts"): "['localhost', '10.0.0.0/8']"}
        config = proxy.ler(rodar=lambda c: (0, respostas.get((c[2], c[3]), "''")))
        self.assertEqual((config["modo"], config["http"], config["excecoes"]), ("manual", {"servidor": "p.br", "porta": 8080}, ["localhost", "10.0.0.0/8"]))

    def test_programas_abertos_recebem_o_proxy(self):
        import aplicativos
        proxy.gravar({"modo": "manual", "http": {"servidor": "p.br", "porta": 8080}}, rodar=lambda c: (0, ""))
        saida = Path(self.pasta.name) / "ambiente.txt"
        aplicativos.iniciar(["sh", "-c", f'echo "$http_proxy" > {saida}'])
        for _ in range(50):
            if saida.exists() and saida.read_text().strip():
                break
            import time
            time.sleep(0.05)
        self.assertEqual(saida.read_text().strip(), "http://p.br:8080/")


def tem_plugin(nome):
    return Path(f"/usr/lib/NetworkManager/VPN/nm-{nome}-service.name").exists()


@unittest.skipUnless(laboratorio_de_pe() and TEM_CRIPTOGRAFIA, "precisa do laboratório de rede")
class TesteVpnComNetworkManagerDeVerdade(unittest.TestCase):
    def apagar(self, nome):
        self.addCleanup(subprocess.run, ["nmcli", "connection", "delete", nome], capture_output=True)

    def test_wireguard_criada_pela_tela(self):
        privada, publica = rede.gerar_chaves_wireguard()
        nome = rede.nova_wireguard("Laboratório WG", rede.configuracao_wireguard("10.66.0.2/32", privada, publica, "10.77.0.1:51820"))
        self.apagar(nome)
        vpn = next(c for c in rede.ler_conexoes() if c["nome"] == "Laboratório WG")
        self.assertEqual(vpn["tipo"], "vpn")
        lida = rede.ler_conexao(vpn["uuid"])
        self.assertEqual(lida["vpn"], "wireguard")

    @unittest.skipUnless(tem_plugin("openvpn"), "sem o plugin do OpenVPN")
    def test_importar_ovpn(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "Escritório.ovpn"
            arquivo.write_text("client\ndev tun\nproto udp\nremote vpn.exemplo.com 1194\nauth-user-pass\n"
                               "<ca>\n-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n</ca>\n")
            nome = rede.importar_vpn(arquivo)
        self.apagar(nome)
        vpn = next(c for c in rede.ler_conexoes() if c["nome"] == nome)
        self.assertEqual(rede.ler_conexao(vpn["uuid"])["vpn"], "openvpn")

    @unittest.skipUnless(tem_plugin("openconnect"), "sem o plugin do OpenConnect")
    def test_vpn_de_empresa(self):
        rede.nova_openconnect("Laboratório Empresa", "vpn.empresa.com.br", "gp")
        self.apagar("Laboratório Empresa")
        vpn = next(c for c in rede.ler_conexoes() if c["nome"] == "Laboratório Empresa")
        self.assertEqual(rede.ler_conexao(vpn["uuid"])["vpn"], "openconnect")


if __name__ == "__main__":
    unittest.main()


class TesteWifiCorporativo(unittest.TestCase):
    def test_rede_802_1x_e_marcada_como_de_empresa(self):
        import controles
        saida = "*:Casa:80:WPA2\n :Universidade:60:WPA2 802.1X\n :Café:40:\n"
        redes = {r["ssid"]: r for r in controles.interpretar_redes(saida)}
        self.assertTrue(redes["Universidade"]["empresa"])
        self.assertFalse(redes["Casa"]["empresa"])
        self.assertFalse(redes["Café"]["segura"])


class TesteProxyNaInterface(unittest.TestCase):
    """O objeto `rede` da janela recusa proxy inválido com uma mensagem e não grava nada na demonstração."""
    def test_proxy_invalido_vira_aviso(self):
        from PySide6.QtGui import QGuiApplication
        app = QGuiApplication.instance() or QGuiApplication(["teste", "-platform", "offscreen"])  # noqa: F841
        import rede_interface
        objeto = rede_interface.Rede(demonstracao=True)
        avisos = []
        objeto.aviso.connect(avisos.append)
        objeto.gravarProxy({"modo": "manual", "http": {"servidor": "", "porta": 0}})
        objeto.gravarProxy({"modo": "manual", "http": {"servidor": "proxy.exemplo.com", "porta": 3128}})
        self.assertEqual(len(avisos), 2)
        self.assertIn("Demonstração", avisos[1])
