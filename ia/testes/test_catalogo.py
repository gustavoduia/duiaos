"""Testes do catálogo de modelos e das regras de memória."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalogo as cat  # noqa: E402


class TesteCatalogo(unittest.TestCase):
    def setUp(self):
        self.catalogo = cat.carregar()

    def test_ids_unicos_e_padrao_no_catalogo(self):
        ids = [m["id"] for _f, m, _l in cat.modelos(self.catalogo)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(self.catalogo["padrao"], ids)
        self.assertEqual(self.catalogo["padrao"], "qwen3.5:4b")
        for alternativa in self.catalogo["padrao_alternativas"]:
            self.assertIn(alternativa, ids)

    def test_licencas_conhecidas_e_llama_nao_livre(self):
        licencas = self.catalogo["licencas"]
        for familia, modelo, licenca in cat.modelos(self.catalogo):
            self.assertIn(licenca, licencas, modelo["id"])
            livre = licencas[licenca]["livre"]
            self.assertEqual(livre, not modelo["id"].startswith("llama"), modelo["id"])
            # O padrão e as alternativas precisam ter licença livre (ADR 019)
            if modelo["id"] == self.catalogo["padrao"]:
                self.assertTrue(livre)

    def test_familias_pedidas(self):
        nomes = {f["nome"] for f in self.catalogo["familias"]}
        self.assertEqual(nomes, {"Qwen3.5", "Qwen3", "Gemma 4", "Llama", "Phi"})

    def test_memoria(self):
        # 16 GB (Dell): 4B cabe sem aviso; 14B cabe com aviso; 70B não cabe
        self.assertEqual(cat.avaliar(4.0, 15.5), (True, ""))
        cabe, aviso = cat.avaliar(9.3, 15.5)
        self.assertTrue(cabe)
        self.assertIn("lento", aviso)
        cabe, aviso = cat.avaliar(43.0, 15.5)
        self.assertFalse(cabe)
        self.assertIn("46 GB", aviso)
        self.assertIn("16 GB", aviso)

    def test_manter_na_memoria(self):
        # 4B (6,5 GB) num computador de 15,5 GB fica sempre carregado; 9B (10,1 GB) não
        self.assertLessEqual(cat.memoria_necessaria_gb(4.0), 15.5 * cat.LIMITE_MANTER)
        self.assertGreater(cat.memoria_necessaria_gb(7.6), 15.5 * cat.LIMITE_MANTER)

    def test_memoria_total(self):
        with tempfile.NamedTemporaryFile("w", suffix="meminfo") as arquivo:
            arquivo.write("MemTotal:       16252928 kB\nMemFree: 1 kB\n")
            arquivo.flush()
            self.assertEqual(cat.memoria_total_gb(arquivo.name), 15.5)
        self.assertEqual(cat.memoria_total_gb("/nao/existe"), 0.0)

    def test_montar(self):
        familias = cat.montar(self.catalogo, {"qwen3.5:4b", "phi4:14b"}, "qwen3.5:4b", 15.5)
        modelos = {m["id"]: m for f in familias for m in f["modelos"]}
        self.assertTrue(modelos["qwen3.5:4b"]["ativo"])
        self.assertTrue(modelos["qwen3.5:4b"]["padrao"])
        self.assertTrue(modelos["phi4:14b"]["instalado"])
        self.assertFalse(modelos["phi4:14b"]["ativo"])
        self.assertFalse(modelos["llama3.3:70b"]["cabe"])
        self.assertFalse(modelos["llama3.3:70b"]["licenca"]["livre"])
        self.assertTrue(modelos["gemma4:e4b"]["cabe"])

    def test_procurar_so_aceita_catalogo(self):
        self.assertIsNotNone(cat.procurar(self.catalogo, "gemma4:e4b"))
        self.assertIsNone(cat.procurar(self.catalogo, "qualquer-coisa:latest"))


if __name__ == "__main__":
    unittest.main()
