"""Testes de agente/firewall.py (ADR 071): preparar uma vez sem trancar quem já usava o computador.

Roda sem firewalld: o firewall-cmd e o nmcli são trocados por um de mentira que anota os comandos.
"""
import sys
import tempfile
import unittest
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA))
import firewall  # noqa: E402


class Mentira:
    def __init__(self, ligado=True, conexoes="u1:802-3-ethernet:enp3s0\nu2:802-11-wireless:\nu3:vpn:\nu4:802-3-ethernet:\n",
                 zonas=None):
        self.ligado, self.saida_conexoes, self.zonas, self.comandos = ligado, conexoes, zonas or {"u4": "home"}, []

    def __call__(self, comando, tempo=30):
        self.comandos.append(comando)
        if comando[-1] == "--state":
            return (0, "running\n", "") if self.ligado else (252, "not running\n", "")
        if comando[:5] == ["nmcli", "-t", "-f", "UUID,TYPE,DEVICE", "connection"]:
            return 0, self.saida_conexoes, ""
        if comando[:4] == ["nmcli", "-t", "-g", "connection.zone"]:
            return 0, self.zonas.get(comando[-1], "") + "\n", ""
        return 0, "", ""


class TestePreparar(unittest.TestCase):
    def test_conexoes_existentes_ficam_privadas_antes_da_zona_padrao(self):
        rodar = Mentira()
        with tempfile.TemporaryDirectory() as pasta:
            marca = Path(pasta) / "marca"
            feito = firewall.preparar(rodar, marca)
            textos = [" ".join(c) for c in rodar.comandos]
            modificadas = [t for t in textos if "connection modify" in t]
            self.assertEqual(len(modificadas), 2)               # u1 e u2; a VPN e a que já tinha zona ficam
            self.assertTrue(all("duiaos-privada" in t for t in modificadas))
            self.assertIn("firewall-cmd --zone=duiaos-privada --change-interface=enp3s0", textos)  # vale já (o SSH em uso)
            padrao = textos.index("firewall-cmd --set-default-zone=duiaos-publica")
            self.assertGreater(padrao, max(textos.index(t) for t in modificadas))
            self.assertIn("zona padrão pública", feito)
            self.assertTrue(marca.exists())
            self.assertEqual(firewall.preparar(Mentira(), marca), ["já preparado"])

    def test_iso_em_construcao_grava_so_a_zona_padrao(self):
        rodar = Mentira(ligado=False)
        with tempfile.TemporaryDirectory() as pasta:
            firewall.preparar(rodar, Path(pasta) / "marca")
        textos = [" ".join(c) for c in rodar.comandos]
        self.assertIn("firewall-offline-cmd --set-default-zone=duiaos-publica", textos)
        self.assertFalse(any("nmcli" in t for t in textos))


class TesteConfigurar(unittest.TestCase):
    def test_ligar_com_e_sem_ssh_e_desligar(self):
        rodar = Mentira()
        firewall.configurar(True, False, rodar)
        textos = [" ".join(c) for c in rodar.comandos]
        self.assertIn("systemctl enable --now firewalld.service", textos)
        self.assertIn("firewall-cmd --permanent --zone=duiaos-privada --remove-service=ssh", textos)
        self.assertIn("firewall-cmd --zone=duiaos-privada --remove-service=ssh", textos)
        rodar = Mentira()
        firewall.configurar(False, True, rodar)
        self.assertEqual(rodar.comandos, [["systemctl", "disable", "--now", "firewalld.service"]])


class TesteZonas(unittest.TestCase):
    def test_arquivos_das_zonas(self):
        import xml.etree.ElementTree as ET
        pasta = PASTA.parent / "pacotes/duiaos-agente/raiz/usr/lib/firewalld/zones"
        servicos = {z: {s.get("name") for s in ET.parse(pasta / f"{z}.xml").findall("service")}
                    for z in (firewall.PUBLICA, firewall.PRIVADA)}
        self.assertEqual(servicos[firewall.PUBLICA], {"dhcpv6-client"})          # nada entra
        self.assertEqual(servicos[firewall.PRIVADA], {"ssh", "mdns", "dhcpv6-client"})


if __name__ == "__main__":
    unittest.main()
