"""Testes de agente/lixeira.py: mover para a Lixeira da pessoa o que está numa pasta que ela não pode mudar.

Roda sem root: o chown é trocado por um que só anota, e a "pasta pessoal" é uma pasta temporária.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA))
import lixeira  # noqa: E402


class TesteLixeiraDoAgente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.casa = Path(self.tmp.name) / "gustavo"
        (self.casa / "Projetos" / "duiaos-isos").mkdir(parents=True)
        self.iso = self.casa / "Projetos" / "duiaos-isos" / "duiaos-dev-333dd41-amd64.iso"
        self.iso.write_bytes(b"iso")
        self.donos = {}

    def tearDown(self):
        self.tmp.cleanup()

    def chown(self, caminho, uid, gid):
        self.donos[caminho] = (uid, gid)

    def mover(self, caminhos):
        return lixeira.mover(caminhos, os.getuid(), chown=self.chown, casa=str(self.casa))

    def test_move_para_a_lixeira_da_pessoa_e_passa_a_ser_dela(self):
        sub = self.casa / "Projetos" / "duiaos-isos" / "build"
        (sub / "dentro").mkdir(parents=True)
        (sub / "dentro" / "a.bin").write_bytes(b"x")
        resultado = self.mover([str(self.iso), str(sub)])
        self.assertEqual(resultado["recusados"], [])
        self.assertEqual(sorted(resultado["movidos"]), ["build", "duiaos-dev-333dd41-amd64.iso"])
        arquivos = self.casa / ".local/share/Trash/files"
        self.assertTrue((arquivos / "duiaos-dev-333dd41-amd64.iso").is_file())
        self.assertFalse(self.iso.exists())
        info = (self.casa / ".local/share/Trash/info/duiaos-dev-333dd41-amd64.iso.trashinfo").read_text()
        self.assertIn("Path=" + str(self.iso).replace(" ", "%20"), info)
        # A Lixeira, o que foi movido (inclusive o de dentro) e o .trashinfo ficam com a pessoa
        for caminho in (arquivos, arquivos / "build" / "dentro" / "a.bin",
                        self.casa / ".local/share/Trash/info/build.trashinfo"):
            self.assertIn(str(caminho), self.donos)

    def test_nome_repetido_na_lixeira(self):
        self.mover([str(self.iso)])
        self.iso.write_bytes(b"de novo")
        resultado = self.mover([str(self.iso)])
        self.assertEqual(resultado["movidos"], ["duiaos-dev-333dd41-amd64 (2).iso"])

    def test_recusa_fora_da_pasta_pessoal_escondidos_e_atalhos_de_pasta(self):
        fora = Path(self.tmp.name) / "outro" / "segredo.txt"
        fora.parent.mkdir()
        fora.write_text("x")
        config = self.casa / ".config" / "app.conf"
        config.parent.mkdir()
        config.write_text("x")
        # Um atalho dentro da pasta pessoal que aponta para fora: o que está "dentro" dele é de fora
        (self.casa / "atalho").symlink_to(fora.parent)
        pedidos = [str(fora), str(config), str(self.casa / "atalho" / "segredo.txt"), "relativo.txt",
                   str(self.casa), str(self.casa / ".local/share/Trash/files"), str(self.casa / "nao-existe.iso")]
        resultado = self.mover(pedidos)
        self.assertEqual(resultado["movidos"], [])
        self.assertEqual(len(resultado["recusados"]), len(pedidos))
        self.assertTrue(fora.exists() and config.exists())

    def test_atalho_vai_como_atalho(self):
        (self.casa / "Projetos" / "link.iso").symlink_to(self.iso)
        resultado = self.mover([str(self.casa / "Projetos" / "link.iso")])
        self.assertEqual(resultado["movidos"], ["link.iso"])
        self.assertTrue((self.casa / ".local/share/Trash/files/link.iso").is_symlink())
        self.assertTrue(self.iso.exists())                       # o original continua lá

    def test_pedido_invalido(self):
        for pedido in ([], "texto", ["x"] * (lixeira.LIMITE_ITENS + 1)):
            with self.assertRaises(lixeira.Recusado):
                self.mover(pedido)


if __name__ == "__main__":
    unittest.main()
