"""Conferências dos arquivos de sistema do pacote duiaos-ia (D-Bus, polkit, systemd)."""
import configparser
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] / "pacotes/duiaos-ia/raiz"


class TestArquivosDoSistema(unittest.TestCase):
    def usuario_do_servico(self):
        unidade = configparser.ConfigParser(strict=False)
        unidade.read(RAIZ / "usr/lib/systemd/system/duiaos-ia.service")
        return unidade["Service"]["User"]

    def test_polkit_declara_o_servico_como_dono(self):
        # Sem isto o polkit recusa toda consulta feita pelo serviço em nome de
        # outra pessoa ("Only trusted callers ... can use CheckAuthorization()")
        acao = ET.parse(RAIZ / "usr/share/polkit-1/actions/org.duiaos.ia.policy").find(
            "action[@id='org.duiaos.ia.gerenciar']")
        anotacoes = {a.get("key"): a.text for a in acao.findall("annotate")}
        self.assertEqual(anotacoes.get("org.freedesktop.policykit.owner"),
                         f"unix-user:{self.usuario_do_servico()}")
        self.assertEqual(acao.find("defaults/allow_active").text, "yes")

    def test_dbus_deixa_o_usuario_do_servico_ter_o_nome(self):
        conf = ET.parse(RAIZ / "usr/share/dbus-1/system.d/org.duiaos.IA1.conf")
        donos = [p.get("user") for p in conf.findall("policy") if p.find("allow[@own='org.duiaos.IA1']") is not None]
        self.assertEqual(donos, [self.usuario_do_servico()])
        ativacao = configparser.ConfigParser()
        ativacao.read(RAIZ / "usr/share/dbus-1/system-services/org.duiaos.IA1.service")
        self.assertEqual(ativacao["D-BUS Service"]["User"], self.usuario_do_servico())


if __name__ == "__main__":
    unittest.main()
