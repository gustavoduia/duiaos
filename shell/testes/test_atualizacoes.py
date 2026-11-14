"""Fichas de atualização (DUIA-AAAA-NNNN) e o que a Central de Atualizações mostra (ADR 046).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "ferramentas"))
sys.path.insert(0, str(RAIZ / "apps" / "configuracoes"))

import atualizacoes as fichas  # noqa: E402
import atualizacoes_sistema as at  # noqa: E402

FICHA = """---
codigo: DUIA-2026-0009
titulo: Teste
data: 2026-11-14
tipo: correcao
importancia: importante
pacotes: duiaos-shell, duiaos-wise
reiniciar: sessao
resumo: Uma frase.
---

## O que muda
Primeiro parágrafo
em duas linhas.

Segundo parágrafo.

## Detalhes
- Item um
- Item dois
"""


class TesteFichas(unittest.TestCase):
    def test_fichas_do_repositorio_estao_certas(self):
        self.assertEqual(fichas.conferir(), [])

    def test_ler_ficha(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta, "DUIA-2026-0009.md")
            caminho.write_text(FICHA)
            ficha = fichas.ler_ficha(caminho)
            self.assertEqual(ficha["tipoNome"], "Correção")
            self.assertEqual(ficha["pacotes"], ["duiaos-shell", "duiaos-wise"])
            self.assertEqual(ficha["descricao"], "Primeiro parágrafo em duas linhas.\n\nSegundo parágrafo.")
            self.assertEqual(ficha["detalhes"], ["Item um", "Item dois"])
            self.assertEqual(ficha["reiniciarNome"], "Saia e entre de novo na sessão")

    def test_fichas_erradas_sao_recusadas(self):
        casos = {
            "tipo: correcao": "tipo: conserto",
            "pacotes: duiaos-shell, duiaos-wise": "pacotes: firefox",
            "## Detalhes\n- Item um\n- Item dois\n": "",
            "codigo: DUIA-2026-0009": "codigo: DUIA-26-9",
        }
        with tempfile.TemporaryDirectory() as pasta:
            for certo, errado in casos.items():
                with self.subTest(errado=errado):
                    caminho = Path(pasta, "DUIA-2026-0009.md")
                    caminho.write_text(FICHA.replace(certo, errado))
                    with self.assertRaises(fichas.FichaErrada):
                        fichas.ler_ficha(caminho)


class TesteCentralDeAtualizacoes(unittest.TestCase):
    def test_simulacao_com_origem(self):
        saida = "\n".join([
            "NOTE: This is only a simulation!",
            "Inst libc6 [2.41-11] (2.41-12 Debian:13.2/stable [amd64])",
            "Inst firefox-esr [128.5.0esr-1~deb13u1] (128.6.0esr-1~deb13u1 Debian-Security:13/stable-security [amd64])",
            "Inst duiaos-shell [0.2.0+git20261114153434.0f97c71] (0.2.0+git20261114161951.4920161 DuiaOS:teste [all])",
            "Conf libc6 (2.41-12 Debian:13.2/stable [amd64])",
        ])
        pacotes = at.interpretar_simulacao(saida)
        self.assertEqual([p["pacote"] for p in pacotes], ["libc6", "firefox-esr", "duiaos-shell"])
        self.assertFalse(pacotes[0]["seguranca"])
        self.assertTrue(pacotes[1]["seguranca"])
        self.assertEqual(pacotes[1]["origem"], "Debian-Security:13/stable-security")

    def test_descricoes(self):
        saida = ("Package: libc6\nDescription: GNU C Library: Shared libraries\n\n"
                 "Package: tzdata\nDescription-en: time zone data\nDescription-pt_BR: dados de fuso horário\n")
        self.assertEqual(at.interpretar_apt_cache(saida), {"libc6": "GNU C Library: Shared libraries",
                                                          "tzdata": "dados de fuso horário"})

    def test_data_da_versao_e_endereco(self):
        self.assertEqual(at.data_da_versao("0.2.0+git20261114161951.4920161"), "20261114161951")
        self.assertEqual(at.data_da_versao("0.3.0"), "")
        with tempfile.TemporaryDirectory() as pasta:
            fontes = Path(pasta, "duiaos.sources")
            fontes.write_text("Types: deb\nURIs: https://exemplo.github.io/apt/\nSuites: teste\n")
            self.assertEqual(at.endereco_do_catalogo(fontes), "https://exemplo.github.io/apt/atualizacoes.json")
        self.assertEqual(at.endereco_do_catalogo("/nao/existe"), "")

    def test_fichas_pendentes(self):
        publicado = [
            {"codigo": "DUIA-2026-0004", "publicada": "20261114213926", "pacotes": ["duiaos-shell"], "reiniciar": "nao"},
            {"codigo": "DUIA-2026-0003", "publicada": "20261114161951", "pacotes": ["duiaos-wise"], "reiniciar": "sessao"},
            {"codigo": "DUIA-2026-0002", "publicada": "20261114161951", "pacotes": ["duiaos-shell"], "reiniciar": "computador"},
            {"codigo": "DUIA-2026-0001", "publicada": "20261114153434", "pacotes": ["duiaos-shell"], "reiniciar": "computador"},
            {"codigo": "DUIA-2026-0005", "publicada": "20261115100000", "pacotes": ["duiaos-shell"], "reiniciar": "nao"},
        ]
        instalado = [{"codigo": "DUIA-2026-0001"}]
        mudancas = [{"pacote": "duiaos-shell", "de": "0.2.0+git20261114153434.0f97c71", "para": "0.2.0+git20261114213926.abcdef0"},
                    {"pacote": "duiaos-wise", "de": "", "para": "0.2.0+git20261114213926.abcdef0"}]
        pendentes = at.fichas_pendentes(publicado, instalado, mudancas)
        # 0005 é de uma versão mais nova que a que chega; 0001 já está instalada
        self.assertEqual([f["codigo"] for f in pendentes], ["DUIA-2026-0004", "DUIA-2026-0003", "DUIA-2026-0002"])
        self.assertEqual(at.maior_reinicio(pendentes), "computador")
        self.assertEqual(at.fichas_pendentes(publicado, instalado, []), [])


if __name__ == "__main__":
    unittest.main()
