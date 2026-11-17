"""Configurações › Armazenamento e os avisos de pouco espaço (ADR 060). Dados inventados.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))

import armazenamento as ar  # noqa: E402

GB = 1000 ** 3
Uso = namedtuple("Uso", "total used free")

LSBLK = json.dumps({"blockdevices": [
    {"name": "nvme0n1", "path": "/dev/nvme0n1", "size": 256 * GB, "fstype": None, "mountpoint": None, "label": None,
     "model": "DISCO EXEMPLO 256", "rm": False, "type": "disk", "tran": "nvme", "children": [
         {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "size": 500 * 1000 ** 2, "fstype": "vfat", "mountpoint": "/boot/efi",
          "label": None, "model": None, "rm": False, "type": "part", "tran": None},
         {"name": "nvme0n1p3", "path": "/dev/nvme0n1p3", "size": 120 * GB, "fstype": "ntfs", "mountpoint": None,
          "label": None, "model": None, "rm": False, "type": "part", "tran": None},
         {"name": "nvme0n1p5", "path": "/dev/nvme0n1p5", "size": 130 * GB, "fstype": "ext4", "mountpoint": "/",
          "label": None, "model": None, "rm": False, "type": "part", "tran": None},
         {"name": "nvme0n1p6", "path": "/dev/nvme0n1p6", "size": 4 * GB, "fstype": "swap", "mountpoint": "[SWAP]",
          "label": None, "model": None, "rm": False, "type": "part", "tran": None}]},
    {"name": "sda", "path": "/dev/sda", "size": 32 * GB, "fstype": None, "mountpoint": None, "label": None,
     "model": "PENDRIVE X", "rm": True, "type": "disk", "tran": "usb", "children": [
         {"name": "sda1", "path": "/dev/sda1", "size": 32 * GB, "fstype": "vfat", "mountpoint": "/media/demo/FOTOS",
          "label": "FOTOS", "model": None, "rm": True, "type": "part", "tran": None}]}]})


class TesteDispositivos(unittest.TestCase):
    def test_le_lsblk(self):
        partes = ar.ler_lsblk(LSBLK)
        self.assertEqual([p["caminho"] for p in partes], ["/dev/nvme0n1p1", "/dev/nvme0n1p3", "/dev/nvme0n1p5", "/dev/sda1"])
        self.assertTrue(partes[-1]["removivel"])
        self.assertEqual(partes[2]["modelo"], "DISCO EXEMPLO 256")
        self.assertEqual(ar.ler_lsblk("não é json"), [])

    def test_ignora_a_midia_do_pendrive(self):
        """No modo live, a ISO e o squashfs (loop) estão sempre cheios: não são discos da pessoa."""
        import json
        texto = json.dumps({"blockdevices": [
            {"name": "loop0", "path": "/dev/loop0", "type": "loop", "fstype": "squashfs", "mountpoint": "/run/live/rootfs/filesystem.squashfs", "size": 1},
            {"name": "sr0", "path": "/dev/sr0", "type": "rom", "fstype": "iso9660", "mountpoint": "/run/live/medium", "size": 1},
            {"name": "sdb", "path": "/dev/sdb", "type": "disk", "rm": True, "children": [
                {"name": "sdb1", "path": "/dev/sdb1", "type": "part", "fstype": "iso9660", "mountpoint": "/run/live/medium", "size": 1}]},
            {"name": "vda", "path": "/dev/vda", "type": "disk", "children": [
                {"name": "vda1", "path": "/dev/vda1", "type": "part", "fstype": "ext4", "mountpoint": "/", "size": 9}]}]})
        self.assertEqual([d["caminho"] for d in ar.ler_lsblk(texto)], ["/dev/vda1"])

    def test_nomes_e_medidas(self):
        usos = {"/": Uso(130 * GB, 120 * GB, 10 * GB), "/media/demo/FOTOS": Uso(32 * GB, 2 * GB, 30 * GB)}
        discos = ar.dispositivos(rodar=lambda _c: LSBLK, uso=lambda m: usos[m])
        self.assertEqual([d["nome"] for d in discos], ["Disco do sistema", "Windows", "FOTOS"])   # sem a partição EFI
        self.assertEqual(discos[0]["livre"], 10 * GB)
        self.assertEqual(discos[1]["nivel"], "")              # não montado: sem medida de livre

    def test_sem_lsblk_usa_a_raiz(self):
        discos = ar.dispositivos(rodar=lambda _c: "", uso=lambda m: Uso(100 * GB, 50 * GB, 50 * GB))
        self.assertEqual(len(discos), 1)
        self.assertEqual((discos[0]["nome"], discos[0]["montado"], discos[0]["nivel"]), ("Disco do sistema", "/", "ok"))


class TesteAvisos(unittest.TestCase):
    def test_nivel(self):
        self.assertEqual(ar.nivel(50 * GB, 256 * GB), "ok")
        self.assertEqual(ar.nivel(4 * GB, 256 * GB), "pouco")     # menos de 10 GB
        self.assertEqual(ar.nivel(20 * GB, 256 * GB), "ok")
        self.assertEqual(ar.nivel(2 * GB, 32 * GB), "pouco")      # disco pequeno: menos de 10%
        self.assertEqual(ar.nivel(int(0.8 * GB), 256 * GB), "cheio")
        self.assertEqual(ar.nivel(3 * GB, 8 * GB), "ok")           # disco pequeno: vale a porcentagem
        self.assertEqual(ar.nivel(0, 0), "ok")

    def test_avisa_uma_vez_e_repete_depois(self):
        disco = [{"nome": "Disco do sistema", "montado": "/", "livre": 4 * GB, "total": 256 * GB}]
        avisos, avisados = ar.avisos_de_espaco(disco, {}, agora=1000)
        self.assertEqual([(a["nivel"], a["urgente"]) for a in avisos], [("pouco", False)])
        self.assertEqual(ar.avisos_de_espaco(disco, avisados, agora=1000 + 3600)[0], [])        # não repete logo
        self.assertEqual(len(ar.avisos_de_espaco(disco, avisados, agora=1000 + 25 * 3600)[0]), 1)  # um dia depois

    def test_piorou_para_cheio_avisa_na_hora(self):
        avisados = {"/": ["pouco", 1000]}
        disco = [{"nome": "Disco do sistema", "montado": "/", "livre": int(0.5 * GB), "total": 256 * GB}]
        avisos, novos = ar.avisos_de_espaco(disco, avisados, agora=1100)
        self.assertTrue(avisos[0]["urgente"])
        self.assertIn("cheio", avisos[0]["titulo"])
        self.assertEqual(novos["/"][0], "cheio")
        self.assertEqual(ar.avisos_de_espaco(disco, novos, agora=1100 + 5 * 3600)[0][0]["nivel"], "cheio")  # 4 h depois

    def test_liberou_espaco_esquece(self):
        disco = [{"nome": "D", "montado": "/", "livre": 100 * GB, "total": 256 * GB}]
        self.assertEqual(ar.avisos_de_espaco(disco, {"/": ["cheio", 1]}, agora=10), ([], {}))

    def test_pendrive_nao_avisa(self):
        disco = [{"nome": "P", "montado": "/media/p", "livre": 0, "total": 32 * GB, "removivel": True}]
        self.assertEqual(ar.avisos_de_espaco(disco, {}, agora=10)[0], [])


def carregar_barra():
    """O main.py da Barra com outro nome (há vários main.py) e sem deixar a plataforma do Qt trocada."""
    import importlib.util
    if "barra_main" in sys.modules:
        return sys.modules["barra_main"]
    antes = os.environ.get("QT_QPA_PLATFORM")
    sys.path.insert(0, str(RAIZ / "shell" / "barra-de-recursos"))
    try:
        spec = importlib.util.spec_from_file_location("barra_main", RAIZ / "shell" / "barra-de-recursos" / "main.py")
        modulo = importlib.util.module_from_spec(spec)
        sys.modules["barra_main"] = modulo
        spec.loader.exec_module(modulo)
        return modulo
    finally:
        sys.path.remove(str(RAIZ / "shell" / "barra-de-recursos"))
        if antes is None:
            os.environ.pop("QT_QPA_PLATFORM", None)
        else:
            os.environ["QT_QPA_PLATFORM"] = antes


class TesteMonitorDaBarra(unittest.TestCase):
    def setUp(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")

    def test_manda_e_guarda(self):
        barra = carregar_barra()
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "espaco-avisado.json"
            mandados = []
            medir = lambda: [{"nome": "Disco do sistema", "montado": "/", "livre": int(0.5 * GB), "total": 256 * GB}]  # noqa: E731
            barra.ver_espaco(arquivo, mandados.append, medir, agora=5000)
            barra.ver_espaco(arquivo, mandados.append, medir, agora=5060)      # 1 minuto depois: não repete
            self.assertEqual(len(mandados), 1)
            self.assertEqual(json.loads(arquivo.read_text())["/"][0], "cheio")

    def test_notificacao_abre_o_armazenamento(self):
        barra = carregar_barra()
        chamadas = []

        class Conexao:
            def call_sync(self, *args):
                chamadas.append(args[4].unpack())
        with mock.patch("gi.repository.Gio.bus_get_sync", return_value=Conexao()):
            barra.notificar("Disco cheio", "texto", origem="Armazenamento", destino="configuracoes:armazenamento",
                            botao="Liberar espaço", urgencia=2)
        nome, _id, _icone, titulo, _texto, acoes, dicas, _t = chamadas[0]
        self.assertEqual((nome, titulo, dicas["x-duiaos-abrir"], dicas["urgency"]),
                         ("Armazenamento", "Disco cheio", "configuracoes:armazenamento", 2))
        self.assertIn("Liberar espaço", acoes)
        sys.path.insert(0, str(RAIZ / "shell" / "notificacoes"))
        import servico
        self.assertTrue(servico.ABRIR_PERMITIDO.match("configuracoes:armazenamento"))


class TesteArquivos(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.inicio = Path(self._pasta.name)

    def tearDown(self):
        self._pasta.cleanup()

    def criar(self, nome, tamanho, conteudo=b"x", mudou=None):
        caminho = self.inicio / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes((conteudo * (tamanho // len(conteudo) + 1))[:tamanho])
        if mudou:
            os.utime(caminho, (mudou, mudou))
        return caminho

    def test_classificar(self):
        self.assertEqual(ar.classificar("Férias.MP4"), "videos")
        self.assertEqual(ar.classificar("contrato.pdf"), "documentos")
        self.assertEqual(ar.classificar("debian.iso"), "instaladores")
        self.assertEqual(ar.classificar("planilha.xlsx.bak"), "copias")
        self.assertEqual(ar.classificar("notas.txt~"), "copias")
        self.assertEqual(ar.classificar("Makefile"), "outros")

    def test_maiores_por_tipo_sem_pastas_escondidas(self):
        mb = 1024 * 1024
        self.criar("Vídeos/grande.mp4", 3 * mb)
        self.criar("Vídeos/pequeno.mp4", 2 * mb)
        self.criar("Vídeos/minusculo.mp4", 10)
        self.criar(".config/escondido.mp4", 5 * mb)
        self.criar("Documentos/livro.pdf", 4 * mb)
        videos = ar.maiores_por_categoria(self.inicio, "videos")
        self.assertEqual([v["nome"] for v in videos], ["grande.mp4", "pequeno.mp4"])
        self.assertEqual(ar.maiores_por_categoria(self.inicio, "grandes")[0]["nome"], "livro.pdf")

    def test_antigos(self):
        agora = time.time()
        self.criar("Downloads/velho.zip", 100, mudou=agora - 200 * 86400)
        self.criar("Downloads/novo.zip", 100, mudou=agora - 2 * 86400)
        self.assertEqual([a["nome"] for a in ar.antigos(self.inicio / "Downloads", agora=agora)], ["velho.zip"])

    def test_duplicados(self):
        mb = 1024 * 1024
        self.criar("a/foto.jpg", 2 * mb, b"abc")
        self.criar("b/copia da foto.jpg", 2 * mb, b"abc")
        self.criar("c/outra.jpg", 2 * mb, b"abd")                # mesmo tamanho, outro conteúdo
        grupos = ar.duplicados(self.inicio)
        self.assertEqual(len(grupos), 1)
        self.assertEqual(sorted(Path(c).name for c in grupos[0]["arquivos"]), ["copia da foto.jpg", "foto.jpg"])

    def test_caches_so_dentro_da_pasta(self):
        cache = self.inicio / ".cache"
        self.criar(".cache/navegador/a.bin", 50000)
        self.criar(".cache/duiaos/avisos.json", 10)
        fora = self.criar("Documentos/importante.txt", 100)
        (cache / "atalho").symlink_to(self.inicio / "Documentos")
        lista = ar.caches(cache)
        self.assertNotIn("duiaos", [Path(c["caminho"]).name for c in lista])
        liberado = ar.apagar_caches([str(cache / "navegador"), str(cache / "duiaos"), str(fora), str(cache / "atalho"),
                                     str(cache / ".." / "Documentos")], cache)
        self.assertGreater(liberado, 0)
        self.assertFalse((cache / "navegador").exists())
        self.assertTrue((cache / "duiaos" / "avisos.json").exists())
        self.assertTrue(fora.exists())

    def test_flathub_da_pessoa_nao_conta_duas_vezes(self):
        """Os aplicativos do Flathub da pessoa ficam em ~/.local/share/flatpak: entram em "Aplicativos" e não
        podem entrar de novo em "Outros arquivos seus" (a soma passava do usado e a barra cortava partes, 16/11)."""
        self.criar(".local/share/flatpak/app/x/arquivo", 300000)
        self.criar("notas.txt", 1000)
        with mock.patch.object(ar, "pastas_do_flathub", return_value=(self.inicio / ".local/share/flatpak", Path("/nao/existe"))):
            uso = ar.uso_por_categoria(self.inicio, {}, None, None, aplicativos=0, ia=False)
        pessoal = next(u for u in uso if u["id"] == "pessoal")["tamanho"]
        self.assertLess(pessoal, 300000)

    def test_arquivo_com_varios_nomes_conta_uma_vez(self):
        original = self.criar("a/grande.bin", 200000)
        (self.inicio / "b").mkdir()
        os.link(original, self.inicio / "b" / "mesmo.bin")
        self.assertLess(ar.tamanho_da_pasta(self.inicio), 2 * original.stat().st_blocks * 512)

    def test_uso_por_categoria(self):
        medidas = {"Documentos": 5 * GB, "Vídeos": 20 * GB, ".cache": GB}
        (self.inicio / "Documentos").mkdir()
        (self.inicio / "Vídeos").mkdir()
        (self.inicio / ".cache").mkdir()
        uso = ar.uso_por_categoria(self.inicio, {"DOCUMENTS": self.inicio / "Documentos", "VIDEOS": self.inicio / "Vídeos"},
                                   None, self.inicio / ".cache", medir=lambda p: medidas[Path(p).name], aplicativos=10 * GB,
                                   ia=False, disco={"usado": 50 * GB})
        self.assertEqual([u["id"] for u in uso], ["videos", "sistema", "aplicativos", "documents", "cache"])
        self.assertEqual(next(u for u in uso if u["id"] == "sistema")["tamanho"], 14 * GB)


class TesteTela(unittest.TestCase):
    def test_pagina_e_listas_em_demonstracao(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")
        with tempfile.TemporaryDirectory() as pasta:
            for lista in ("", "videos", "programas"):
                arquivo = Path(pasta) / f"armazenamento{lista}.png"
                comando = [sys.executable, str(RAIZ / "apps" / "configuracoes" / "main.py"), "--demonstracao",
                           "--secao", "armazenamento", "--captura", str(arquivo)] + (["--lista", lista] if lista else [])
                saida = subprocess.run(comando, capture_output=True, text=True, timeout=60,
                                       env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
                self.assertTrue(arquivo.exists(), saida.stderr[-2000:])
                self.assertNotIn("TypeError", saida.stderr)
                self.assertNotIn("ReferenceError", saida.stderr)


if __name__ == "__main__":
    unittest.main()
