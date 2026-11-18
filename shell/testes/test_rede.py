"""Testes de shell/comum/rede.py (Configurações › Rede e Internet, Barra; ADR 069).

Duas partes:
- leitura e validação com saídas do nmcli gravadas (sempre rodam);
- um NetworkManager de verdade, no laboratório de ferramentas/laboratorio-rede.sh (placas virtuais veth-a,
  com DHCP, e veth-c, sem DHCP). Só rodam quando o laboratório está de pé; nunca mexem em outra placa.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import subprocess
import sys
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
import rede  # noqa: E402

DISPOSITIVOS = """\
enp3s0:ethernet:connected:Conexão cabeada 1:11111111-1111-1111-1111-111111111111
wlp2s0:wifi:disconnected::
wg0:wireguard:connected:Trabalho:22222222-2222-2222-2222-222222222222
lo:loopback:connected (externally):lo:33333333-3333-3333-3333-333333333333
p2p-dev-wlp2s0:wifi-p2p:disconnected::
docker0:bridge:unmanaged::
"""

DETALHES = """\
GENERAL.HWADDR:3C\\:52\\:82\\:AA\\:BB\\:CC
GENERAL.MTU:1500
GENERAL.METERED:no (guessed)
CAPABILITIES.SPEED:1000 Mb/s
WIRED-PROPERTIES.CARRIER:on
IP4.ADDRESS[1]:192.168.0.23/24
IP4.GATEWAY:192.168.0.1
IP4.DNS[1]:192.168.0.1
IP4.DNS[2]:1.1.1.1
IP6.ADDRESS[1]:2804:14c::23/64
IP6.ADDRESS[2]:fe80::3e52:82ff:feaa:bbcc/64
IP6.GATEWAY:fe80::1
"""

CONEXAO = """\
connection.id:Escritório
connection.uuid:11111111-1111-1111-1111-111111111111
connection.type:802-3-ethernet
connection.interface-name:enp3s0
connection.autoconnect:yes
connection.autoconnect-priority:10
connection.metered:yes
connection.permissions:
connection.zone:home
802-3-ethernet.cloned-mac-address:stable
802-3-ethernet.mtu:auto
ipv4.method:manual
ipv4.dns:1.1.1.1,9.9.9.9
ipv4.addresses:192.168.10.5/24
ipv4.gateway:192.168.10.1
ipv4.routes:
ipv4.ignore-auto-dns:yes
ipv6.method:auto
ipv6.addresses:
ipv6.gateway:
ipv6.dns:
ipv6.ignore-auto-dns:no
"""


class TesteLeitura(unittest.TestCase):
    def test_dispositivos_so_os_que_a_pessoa_usa(self):
        lista = rede.interpretar_dispositivos(DISPOSITIVOS)
        self.assertEqual([(d["dispositivo"], d["tipo"], d["estado"]) for d in lista],
                         [("enp3s0", "cabo", "conectado"), ("wlp2s0", "wifi", "desconectado"), ("wg0", "vpn", "conectado")])

    def test_detalhes(self):
        d = rede.interpretar_detalhes(DETALHES)
        self.assertEqual(d["mac"], "3C:52:82:AA:BB:CC")
        self.assertEqual(d["velocidade"], "1000 Mbit/s")
        self.assertEqual(d["ipv4"], ["192.168.0.23/24"])
        self.assertEqual(d["dns4"], ["192.168.0.1", "1.1.1.1"])
        self.assertEqual(d["ipv6"], ["2804:14c::23/64"])            # o endereço local (fe80) fica de fora
        self.assertTrue(d["cabo"])
        self.assertFalse(d["limitada"])

    def test_conexao(self):
        c = rede.interpretar_conexao(CONEXAO)
        self.assertEqual(c["nome"], "Escritório")
        self.assertEqual(c["tipo"], "cabo")
        self.assertEqual(c["limitada"], "sim")
        self.assertEqual(c["ipv4"]["metodo"], "manual")
        self.assertEqual(c["ipv4"]["enderecos"], [{"endereco": "192.168.10.5", "prefixo": "24"}])
        self.assertEqual(c["ipv4"]["dns"], ["1.1.1.1", "9.9.9.9"])
        self.assertTrue(c["ipv4"]["soDnsManual"])
        self.assertEqual(c["mac"], "stable")
        self.assertEqual(c["zona"], "home")

    def test_resumo(self):
        lista = rede.interpretar_dispositivos(DISPOSITIVOS)
        self.assertEqual(rede.resumo(lista, "full"), "Conectado pelo cabo · Internet funcionando · VPN Trabalho")
        self.assertEqual(rede.resumo(lista[:1], "portal"), "Conectado pelo cabo · Esta rede pede login")
        self.assertEqual(rede.resumo([], "none"), "Nenhuma placa de rede encontrada")
        sem_cabo = [{"dispositivo": "enp3s0", "tipo": "cabo", "estado": "indisponivel", "conexao": "", "uuid": ""}]
        self.assertEqual(rede.resumo(sem_cabo, "none"), "Cabo de rede desconectado")


class TesteValidacao(unittest.TestCase):
    def test_mascara(self):
        self.assertEqual(rede.prefixo_de("255.255.255.0"), 24)
        self.assertEqual(rede.prefixo_de("/16"), 16)
        self.assertEqual(rede.prefixo_de("64", 6), 64)
        for ruim in ("255.0.255.0", "33", "", "abc"):
            with self.assertRaises(rede.ErroDeRede):
                rede.prefixo_de(ruim)

    def test_erros_em_portugues(self):
        def erros(**ipv4):
            return rede.validar({"ipv4": {"metodo": "manual", **ipv4}})
        self.assertEqual(erros(enderecos=[{"endereco": "192.168.0.10", "prefixo": "255.255.255.0"}], gateway="192.168.0.1",
                               dns=["1.1.1.1", "2606:4700:4700::1111"]), [])
        self.assertIn("mesma rede", " ".join(erros(enderecos=[{"endereco": "192.168.0.10", "prefixo": "24"}], gateway="10.0.0.1")))
        self.assertIn("inválido", " ".join(erros(enderecos=[{"endereco": "192.168.0.300", "prefixo": "24"}])))
        self.assertIn("pelo menos um endereço", " ".join(erros(enderecos=[])))
        self.assertIn("própria rede", " ".join(erros(enderecos=[{"endereco": "192.168.0.0", "prefixo": "24"}])))
        self.assertIn("DNS inválido", " ".join(rede.validar({"ipv4": {"metodo": "auto", "dns": ["1.1.1"]}})))
        self.assertIn("MTU", " ".join(rede.validar({"mtu": "70000"})))

    def test_argumentos(self):
        args = rede.argumentos({"tipo": "cabo", "automatico": True, "limitada": "sim", "mac": "random",
                                "ipv4": {"metodo": "manual", "enderecos": [{"endereco": "10.0.0.5", "prefixo": "255.255.255.0"}],
                                         "gateway": "10.0.0.1", "dns": ["1.1.1.1"]}})
        pares = dict(zip(args[::2], args[1::2]))
        self.assertEqual(pares["ipv4.method"], "manual")
        self.assertEqual(pares["ipv4.addresses"], "10.0.0.5/24")
        self.assertEqual(pares["ipv4.ignore-auto-dns"], "yes")
        self.assertEqual(pares["connection.metered"], "yes")
        self.assertEqual(pares["802-3-ethernet.cloned-mac-address"], "random")
        auto = dict(zip(*[iter(rede.argumentos({"ipv4": {"metodo": "auto", "dns": []}}))] * 2))
        self.assertEqual((auto["ipv4.method"], auto["ipv4.addresses"], auto["ipv4.ignore-auto-dns"]), ("auto", "", "no"))


def laboratorio_de_pe():
    try:
        saida = subprocess.run(["nmcli", "-t", "-f", "DEVICE,STATE", "device"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    estados = dict(linha.split(":", 1) for linha in saida.splitlines() if ":" in linha)
    return estados.get("veth-a", "unmanaged") != "unmanaged" and estados.get("veth-c", "unmanaged") != "unmanaged"


@unittest.skipUnless(laboratorio_de_pe(), "laboratório de rede desligado (sudo bash ferramentas/laboratorio-rede.sh)")
class TesteComNetworkManagerDeVerdade(unittest.TestCase):
    """Rede sem DHCP (veth-c): só funciona com IP fixo — o caso da VM que o Gustavo descreveu."""

    def setUp(self):
        self.criadas = []

    def tearDown(self):
        for uuid in self.criadas:
            subprocess.run(["nmcli", "connection", "delete", uuid], capture_output=True)

    def esperar_ip(self, dispositivo, esperado, segundos=15):
        fim = time.time() + segundos
        while time.time() < fim:
            if rede.ler_detalhes(dispositivo).get("ipv4") == esperado:
                return
            time.sleep(0.5)
        self.fail(f"{dispositivo} não ficou com {esperado}: {rede.ler_detalhes(dispositivo)}")

    def test_cabo_com_dhcp_aparece_conectado(self):
        lista = rede.ler_dispositivos()
        cabo = next(d for d in lista if d["dispositivo"] == "veth-a")
        self.assertEqual((cabo["tipo"], cabo["estado"]), ("cabo", "conectado"))
        detalhes = rede.ler_detalhes("veth-a")
        self.assertTrue(detalhes["ipv4"][0].startswith("10.77.0."))
        self.assertEqual(detalhes["gateway4"], "10.77.0.1")
        self.assertNotIn("enp0s8", [d["dispositivo"] for d in lista])      # placas não gerenciadas não aparecem

    def test_ip_fixo_trocar_e_voltar_atras(self):
        fixo = {"ipv4": {"metodo": "manual", "enderecos": [{"endereco": "10.88.0.10", "prefixo": "255.255.255.0"}],
                         "gateway": "10.88.0.1", "dns": ["9.9.9.9"]}, "ipv6": {"metodo": "desligado"}}
        uuid = rede.nova_conexao_cabo("veth-c", "Laboratório fixo", fixo)
        self.criadas.append(uuid)
        rede.ativar(uuid)
        self.esperar_ip("veth-c", ["10.88.0.10/24"])
        self.assertEqual(rede.ler_detalhes("veth-c")["dns4"], ["9.9.9.9"])
        lida = rede.ler_conexao(uuid)
        self.assertEqual((lida["ipv4"]["metodo"], lida["ipv4"]["gateway"]), ("manual", "10.88.0.1"))
        # Troca o endereço (com a conexão em uso: reativa sozinha) e volta atrás, como o "Manter?" das Configurações
        volta = rede.aplicar(uuid, {"tipo": "cabo", "ipv4": {**fixo["ipv4"], "enderecos": [{"endereco": "10.88.0.20", "prefixo": "24"}]}})
        self.esperar_ip("veth-c", ["10.88.0.20/24"])
        rede.voltar(uuid, volta)
        self.esperar_ip("veth-c", ["10.88.0.10/24"])
        # Configuração errada não chega ao NetworkManager
        with self.assertRaises(rede.ErroDeRede):
            rede.aplicar(uuid, {"tipo": "cabo", "ipv4": {"metodo": "manual", "enderecos": [{"endereco": "10.88.0.30", "prefixo": "24"}],
                                                         "gateway": "192.168.1.1"}})
        self.assertEqual(rede.ler_detalhes("veth-c")["ipv4"], ["10.88.0.10/24"])

    def test_desconectar_e_conectar_o_cabo(self):
        rede.desconectar_dispositivo("veth-a")
        self.assertEqual(next(d for d in rede.ler_dispositivos() if d["dispositivo"] == "veth-a")["estado"], "desconectado")
        rede.conectar_dispositivo("veth-a")
        fim = time.time() + 20
        while time.time() < fim and next(d for d in rede.ler_dispositivos() if d["dispositivo"] == "veth-a")["estado"] != "conectado":
            time.sleep(0.5)
        self.assertEqual(next(d for d in rede.ler_dispositivos() if d["dispositivo"] == "veth-a")["estado"], "conectado")


if __name__ == "__main__":
    unittest.main()


try:
    import PySide6  # noqa: F401
    TEM_PYSIDE = True
except ImportError:
    TEM_PYSIDE = False


@unittest.skipUnless(TEM_PYSIDE and laboratorio_de_pe(), "precisa do PySide6 e do laboratório de rede")
class TesteManterOuVoltar(unittest.TestCase):
    """O objeto "rede" das Configurações: mudança de endereço pede "Manter?" e, sem resposta, volta sozinha."""

    def test_sem_resposta_a_configuracao_anterior_volta(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtTest import QTest
        import rede_interface
        QGuiApplication.instance() or QGuiApplication([])
        rede_interface.TEMPO_CONFIRMAR = 3
        fixo = {"metodo": "manual", "enderecos": [{"endereco": "10.88.0.11", "prefixo": "24"}], "gateway": "10.88.0.1", "dns": []}
        uuid = rede.nova_conexao_cabo("veth-c", "Laboratório confirmar", {"ipv4": fixo, "ipv6": {"metodo": "desligado"}})
        self.addCleanup(subprocess.run, ["nmcli", "connection", "delete", uuid], capture_output=True)
        rede.ativar(uuid)
        objeto = rede_interface.Rede()
        objeto.abrirConexao(uuid)
        for _ in range(100):
            QTest.qWait(50)
            if objeto.property("conexao").get("uuid") == uuid:
                break
        avisos = []
        objeto.aviso.connect(avisos.append)
        objeto.aplicarConexao({"uuid": uuid, "tipo": "cabo", "ipv4": {**fixo, "enderecos": [{"endereco": "10.88.0.12", "prefixo": "24"}]}})
        for _ in range(300):
            QTest.qWait(50)
            if objeto.property("confirmando") > 0:
                break
        self.assertGreater(objeto.property("confirmando"), 0, avisos)
        for _ in range(100):
            if rede.ler_detalhes("veth-c").get("ipv4") == ["10.88.0.12/24"]:
                break
            QTest.qWait(50)
        self.assertEqual(rede.ler_detalhes("veth-c")["ipv4"], ["10.88.0.12/24"])
        for _ in range(200):                                  # ninguém clica em "Manter"
            QTest.qWait(50)
            if rede.ler_detalhes("veth-c").get("ipv4") == ["10.88.0.11/24"]:
                break
        self.assertEqual(rede.ler_detalhes("veth-c")["ipv4"], ["10.88.0.11/24"])
        self.assertIn("A configuração anterior voltou.", avisos)
        objeto._vigia.kill()
        objeto._vigia.waitForFinished(2000)
        objeto.deleteLater()


@unittest.skipUnless(TEM_PYSIDE, "precisa do PySide6")
class TesteAvisoDePortal(unittest.TestCase):
    def test_avisa_uma_vez_quando_a_rede_pede_login(self):
        import importlib.util
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QObject, Property, Signal
        sys.argv = [sys.argv[0], "--demonstracao"]
        espec = importlib.util.spec_from_file_location("barra_main", RAIZ / "shell/barra-de-recursos/main.py")
        barra = importlib.util.module_from_spec(espec)
        espec.loader.exec_module(barra)

        class Falsa(QObject):
            mudou = Signal()

            def __init__(self):
                super().__init__()
                self._c = "full"
            conectividade = Property(str, lambda self: self._c, notify=mudou)

        falsa, avisos = Falsa(), []
        barra.vigiar_portal(falsa, mandar=lambda: avisos.append(1))
        for estado in ("full", "portal", "portal", "full", "portal"):
            falsa._c = estado
            falsa.mudou.emit()
        self.assertEqual(len(avisos), 2)
