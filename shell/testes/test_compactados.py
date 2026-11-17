"""Testes do Descompactar do Explorador de Arquivos e da Área de Trabalho (compactados.py).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import gzip
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
sys.path.insert(0, str(RAIZ / "apps" / "explorador-de-arquivos"))

import compactados  # noqa: E402
import operacoes  # noqa: E402


class TesteDescompactar(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def zip(self, nome, itens, **kw):
        caminho = self.pasta / nome
        with zipfile.ZipFile(caminho, "w", **kw) as z:
            for nome_item, conteudo in itens:
                z.writestr(nome_item, conteudo)
        return caminho

    def test_reconhece_as_extensoes(self):
        for nome in ("a.zip", "A.ZIP", "b.tar.gz", "c.tgz", "d.tar.xz", "e.gz", "f.7z", "g.rar", "h.tar.bz2"):
            self.assertTrue(compactados.eh_compactado(nome), nome)
        for nome in ("a.txt", "pacote.deb", "disco.iso", ".zip", "zip"):
            self.assertFalse(compactados.eh_compactado(nome), nome)
        self.assertEqual(compactados.nome_sem_extensao("Fotos de 2026.tar.gz"), "Fotos de 2026")
        self.assertTrue(operacoes.item_de(self.zip("x.zip", [("a.txt", "1")]))["compactado"])

    def test_varios_itens_vao_para_uma_pasta_com_o_nome_do_arquivo(self):
        arquivo = self.zip("Viagem.zip", [("foto1.jpg", "a"), ("foto2.jpg", "b"), ("roteiro/dia1.txt", "praia")])
        resultado = compactados.descompactar(arquivo)
        self.assertEqual(Path(resultado), self.pasta / "Viagem")
        self.assertEqual((self.pasta / "Viagem" / "roteiro" / "dia1.txt").read_text(), "praia")
        self.assertTrue(arquivo.exists())                       # o original fica
        self.assertEqual([p.name for p in self.pasta.iterdir() if p.name.startswith(".")], [])  # sem sobras

    def test_um_item_so_aparece_direto_e_sem_sobrescrever(self):
        arquivo = self.zip("projeto.zip", [("projeto/", ""), ("projeto/leia.txt", "oi")])
        primeiro = compactados.descompactar(arquivo)
        segundo = compactados.descompactar(arquivo)
        self.assertEqual(Path(primeiro), self.pasta / "projeto")
        self.assertEqual(Path(segundo), self.pasta / "projeto (2)")
        self.assertEqual((self.pasta / "projeto (2)" / "leia.txt").read_text(), "oi")

    def test_nomes_com_acento_de_zip_feito_no_windows(self):
        # O Windows em português grava os nomes na página 850, sem a marca de UTF-8
        arquivo = self.zip("windows.zip", [("Informacoes.txt", "conteúdo")])
        nome_850 = "Informações.txt".encode("cp850")
        self.assertEqual(len(nome_850), len("Informacoes.txt"))
        arquivo.write_bytes(arquivo.read_bytes().replace(b"Informacoes.txt", nome_850))
        resultado = compactados.descompactar(arquivo)
        self.assertEqual(Path(resultado).name, "Informações.txt")

    def test_recusa_caminhos_que_saem_da_pasta(self):
        for nome_ruim in ("../fora.txt", "/etc/passwd2", "a/../../fora.txt"):
            arquivo = self.zip("ruim.zip", [("ok.txt", "1"), (nome_ruim, "2")])
            with self.assertRaises(operacoes.ErroDeArquivo):
                compactados.descompactar(arquivo)
            self.assertFalse((self.pasta.parent / "fora.txt").exists())
            self.assertFalse((self.pasta / "ruim").exists())
            self.assertEqual([p.name for p in self.pasta.iterdir() if p.name.startswith(".")], [])

    def test_tar_gz_com_link_para_fora_e_executavel(self):
        arquivo = self.pasta / "app.tar.gz"
        with tarfile.open(arquivo, "w:gz") as t:
            dados = b"#!/bin/sh\necho oi\n"
            info = tarfile.TarInfo("app/rodar.sh")
            info.size, info.mode = len(dados), 0o755
            t.addfile(info, io.BytesIO(dados))
            link = tarfile.TarInfo("app/senhas")
            link.type, link.linkname = tarfile.SYMTYPE, "/etc/shadow"
            t.addfile(link)
        resultado = Path(compactados.descompactar(arquivo))
        self.assertEqual(resultado, self.pasta / "app")
        self.assertTrue(os.access(resultado / "rodar.sh", os.X_OK))
        self.assertFalse((resultado / "senhas").is_symlink())

    def test_gz_de_um_arquivo_so(self):
        arquivo = self.pasta / "notas.txt.gz"
        with gzip.open(arquivo, "wb") as g:
            g.write(b"texto")
        self.assertEqual(Path(compactados.descompactar(arquivo)).read_bytes(), b"texto")
        self.assertTrue((self.pasta / "notas.txt").exists())

    def test_danificado_vazio_senha_e_cancelar(self):
        falso = self.pasta / "falso.zip"
        falso.write_text("não sou zip")
        with self.assertRaisesRegex(operacoes.ErroDeArquivo, "danificado"):
            compactados.descompactar(falso)
        vazio = self.zip("vazio.zip", [])
        with self.assertRaisesRegex(operacoes.ErroDeArquivo, "vazio"):
            compactados.descompactar(vazio)
        com_senha = self.zip("senha.zip", [("a.txt", "1")])
        dados = bytearray(com_senha.read_bytes())
        dados[6] |= 0x1                                       # marca de "criptografado" no cabeçalho local
        central = dados.find(b"PK\x01\x02")
        dados[central + 8] |= 0x1                             # e no diretório central
        com_senha.write_bytes(bytes(dados))
        with self.assertRaisesRegex(operacoes.ErroDeArquivo, "senha"):
            compactados.descompactar(com_senha)
        grande = self.zip("grande.zip", [("a.bin", os.urandom(3 * 1024 * 1024))])
        with self.assertRaisesRegex(operacoes.ErroDeArquivo, "cancelada"):
            compactados.descompactar(grande, cancelado=lambda: True)
        self.assertEqual([p.name for p in self.pasta.iterdir() if p.name.startswith(".")], [])

    def test_progresso_chega_ao_fim(self):
        arquivo = self.zip("p.zip", [("a.bin", b"x" * 3_000_000), ("b.bin", b"y" * 10)])
        visto = []
        compactados.descompactar(arquivo, progresso=visto.append)
        self.assertEqual(visto[-1], 1.0)
        self.assertEqual(visto, sorted(visto))

    @unittest.skipUnless(compactados._7z(), "7-Zip não instalado")
    def test_7z(self):
        origem = self.pasta / "origem"
        (origem / "sub").mkdir(parents=True)
        (origem / "sub" / "a.txt").write_text("sete")
        (origem / "b.txt").write_text("zip")
        arquivo = self.pasta / "Coisas.7z"
        subprocess.run([compactados._7z(), "a", str(arquivo), "sub", "b.txt"], cwd=origem, check=True,
                       capture_output=True)
        resultado = Path(compactados.descompactar(arquivo))
        self.assertEqual(resultado, self.pasta / "Coisas")
        self.assertEqual((resultado / "sub" / "a.txt").read_text(), "sete")


if __name__ == "__main__":
    unittest.main()
