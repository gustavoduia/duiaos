"""Testes do plano do duiaos-agente: validação, leitura do apt e recusas."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plano as pl  # noqa: E402

SIMULACAO = """NOTE: This is only a simulation!
Inst libc6 [2.41-11] (2.41-12 Debian:13.2/stable [amd64])
Inst vlc (3.0.21-1 Debian:13.1/stable [amd64]) []
Conf vlc (3.0.21-1 Debian:13.1/stable [amd64])
Remv velho:amd64 [1.0-1]
"""
DPKG = "libc6\tyes\trequired\nvlc\tno\toptional\nduiaos-shell\tno\toptional\nopcional\tno\toptional\n"


class TestValidar(unittest.TestCase):
    def test_acoes_e_pacotes(self):
        self.assertEqual(pl.validar("atualizar_sistema", {"x": 1}), {})
        self.assertEqual(pl.validar("instalar_aplicativo", {"pacote": "vlc", "outro": 2}), {"pacote": "vlc"})
        for ruim in ("VLC", "vlc; rm -rf /", "-y", "a", "../x", "", None, 3):
            with self.assertRaises(pl.Recusa, msg=ruim):
                pl.validar("instalar_aplicativo", {"pacote": ruim})
        with self.assertRaises(pl.Recusa):
            pl.validar("rodar_comando", {})

    def test_comando_nunca_remove_ao_instalar(self):
        self.assertIn("--no-remove", pl.comando_apt("instalar_aplicativo", {"pacote": "vlc"}))
        self.assertEqual(pl.comando_apt("atualizar_sistema", {}), ["full-upgrade"])


class TestLeituras(unittest.TestCase):
    def test_simulacao(self):
        m = pl.ler_simulacao(SIMULACAO)
        self.assertEqual(m["atualizar"], [{"pacote": "libc6", "de": "2.41-11", "para": "2.41-12"}])
        self.assertEqual(m["instalar"], [{"pacote": "vlc", "de": "", "para": "3.0.21-1"}])
        self.assertEqual(m["remover"], [{"pacote": "velho", "de": "1.0-1", "para": ""}])

    def test_politica_em_ingles_e_portugues(self):
        self.assertEqual(pl.ler_politica("vlc:\n  Installed: (none)\n  Candidate: 3.0.21-1\n"), ("", "3.0.21-1"))
        self.assertEqual(pl.ler_politica("vlc:\n  Instalado: 3.0\n  Candidato: (nenhum)\n"), ("3.0", ""))

    def test_progresso(self):
        self.assertEqual(pl.ler_progresso("dlstatus:1:50.0:Baixando vlc")[0], 0.25)
        self.assertEqual(pl.ler_progresso("pmstatus:vlc:100:Instalado")[0], 1.0)
        self.assertEqual(pl.ler_progresso("lixo"), (None, ""))

    def test_tamanhos(self):
        self.assertEqual(pl.tamanhos("Size: 100\nInstalled-Size: 2\n\nSize: 50\n"), (150, 2048))


class TestAvaliar(unittest.TestCase):
    def setUp(self):
        self.protegidos = pl.ler_protegidos(DPKG)

    def test_protegidos(self):
        self.assertIn("libc6", self.protegidos)
        self.assertIn("duiaos-shell", self.protegidos)
        self.assertIn("systemd", self.protegidos)
        self.assertNotIn("opcional", self.protegidos)

    def test_nunca_remove_essencial(self):
        _r, recusa = pl.avaliar("remover_aplicativo", {"pacote": "duiaos-shell"},
                                {"instalar": [], "atualizar": [], "remover": []}, self.protegidos, "1.0", "1.0")
        self.assertEqual(recusa.codigo, "Protegido")
        # Remover um pacote comum que arrastaria um essencial também é recusado
        mud = {"instalar": [], "atualizar": [], "remover": [{"pacote": "opcional", "de": "1", "para": ""},
                                                            {"pacote": "libc6", "de": "2", "para": ""}]}
        _r, recusa = pl.avaliar("remover_aplicativo", {"pacote": "opcional"}, mud, self.protegidos, "1", "1")
        self.assertEqual(recusa.codigo, "Protegido")

    def test_resumos(self):
        mud = pl.ler_simulacao(SIMULACAO)
        mud["remover"] = []
        resumo, recusa = pl.avaliar("instalar_aplicativo", {"pacote": "vlc"}, mud, self.protegidos, "", "3.0.21-1")
        self.assertIsNone(recusa)
        self.assertTrue(resumo.startswith("Instalar vlc (3.0.21-1)"))
        resumo, recusa = pl.avaliar("atualizar_sistema", {}, mud, self.protegidos, "", "")
        self.assertIsNone(recusa)
        self.assertIn("Atualizar 1 pacote", resumo)
        _r, recusa = pl.avaliar("atualizar_sistema", {}, {"instalar": [], "atualizar": [], "remover": []},
                                self.protegidos, "", "")
        self.assertEqual(recusa.codigo, "NadaAFazer")
        _r, recusa = pl.avaliar("instalar_aplicativo", {"pacote": "vlc"}, mud, self.protegidos, "3.0", "3.0")
        self.assertEqual(recusa.codigo, "JaInstalado")
        _r, recusa = pl.avaliar("instalar_aplicativo", {"pacote": "nada"}, mud, self.protegidos, "", "")
        self.assertEqual(recusa.codigo, "NaoEncontrado")


if __name__ == "__main__":
    unittest.main()
