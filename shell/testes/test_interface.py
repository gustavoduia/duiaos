"""Testes da interface: leitura dos controles do sistema, pastas, aplicativos, tipos de arquivo,
preferências da sessão e operações do Explorador de Arquivos (Lixeira, copiar, mover, renomear).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import datetime
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
sys.path.insert(0, str(RAIZ / "apps" / "explorador-de-arquivos"))

import aplicativos  # noqa: E402
import controles  # noqa: E402
import operacoes  # noqa: E402
import pastas  # noqa: E402
import sessao  # noqa: E402
import tipos  # noqa: E402


class TesteControles(unittest.TestCase):
    def test_redes_unicas_com_conectada_primeiro(self):
        saida = "\n".join([
            " :Casa:64:WPA2",
            "*:Casa 5G:82:WPA2 WPA3",
            " :Casa:70:WPA2",
            " :Café\\:Aberto:22:",
            " ::50:WPA2",
        ])
        redes = controles.interpretar_redes(saida)
        self.assertEqual([r["ssid"] for r in redes], ["Casa 5G", "Casa", "Café:Aberto"])
        self.assertTrue(redes[0]["conectada"])
        self.assertEqual(redes[1]["sinal"], 70)
        self.assertFalse(redes[2]["segura"])

    def test_nivel_wifi(self):
        self.assertEqual([controles.nivel_wifi(s) for s in (10, 40, 90)], [1, 2, 3])

    def test_redes_salvas_e_cabo(self):
        self.assertEqual(controles.ler_redes_salvas("Casa:802-11-wireless\nCabo:802-3-ethernet\n"), ["Casa"])
        self.assertTrue(controles.ler_ethernet("ethernet:connected:Cabo\nwifi:disconnected:\n"))
        self.assertFalse(controles.ler_ethernet("ethernet:unavailable:\n"))

    def test_bluetooth(self):
        self.assertEqual(controles.interpretar_bluetooth_show("Controller AA\n\tPowered: yes\n"), (True, True))
        self.assertEqual(controles.interpretar_bluetooth_show("No default controller available"), (False, False))
        dispositivos = controles.interpretar_dispositivos("Device AA:BB:CC:DD:EE:01 Fone Duia\nlixo\n")
        self.assertEqual(dispositivos, [{"endereco": "AA:BB:CC:DD:EE:01", "nome": "Fone Duia"}])

    def test_volume(self):
        self.assertEqual(controles.interpretar_volume("Volume: 0.45"), (45, False))
        self.assertEqual(controles.interpretar_volume("Volume: 0.80 [MUTED]"), (80, True))
        self.assertEqual(controles.interpretar_volume(""), (-1, False))

    def test_saidas_do_wpctl(self):
        status = "\n".join([
            "PipeWire 'pipewire-0' [1.2.7]",
            " └─ Clients:",
            "Audio",
            " ├─ Devices:",
            " │      42. Áudio interno                      [alsa]",
            " ├─ Sinks:",
            " │  *   46. Alto-falantes internos              [vol: 0.40]",
            " │      51. Fone Duia                           [vol: 0.70]",
            " ├─ Sources:",
            " │  *   47. Microfone interno                   [vol: 1.00]",
            " └─ Streams:",
            "Video",
            " ├─ Sinks:",
            " │      90. Câmera",
        ])
        saidas = controles.interpretar_saidas(status, "Sinks")
        self.assertEqual([(s["id"], s["nome"], s["padrao"]) for s in saidas],
                         [(46, "Alto-falantes internos", True), (51, "Fone Duia", False)])
        self.assertEqual(controles.interpretar_saidas(status, "Sources")[0]["nome"], "Microfone interno")

    def test_brilho(self):
        self.assertEqual(controles.interpretar_brilho("intel_backlight,backlight,400,40%,1000"), 40)
        self.assertEqual(controles.interpretar_brilho("input0::capslock,leds,0,0%,1"), -1)

    def test_bateria(self):
        with tempfile.TemporaryDirectory() as raiz:
            bat = Path(raiz, "BAT0")
            bat.mkdir()
            for nome, valor in {"capacity": "73", "status": "Discharging", "energy_now": "30000000",
                                "energy_full": "50000000", "power_now": "10000000"}.items():
                (bat / nome).write_text(valor)
            ac = Path(raiz, "AC")
            ac.mkdir()
            (ac / "type").write_text("Mains")
            (ac / "online").write_text("0")
            estado = controles.ler_bateria(raiz)
            self.assertEqual((estado["nivel"], estado["carregando"], estado["minutos"]), (73, False, 180))
            self.assertEqual(controles.descrever_tempo(estado["minutos"]), "3 h")
            self.assertEqual(controles.descrever_tempo(95), "1 h 35 min")
        self.assertEqual(controles.ler_bateria("/nao/existe")["nivel"], -1)

    def test_perfis_de_energia(self):
        saida = "  performance:\n    Driver: intel\n\n* balanced:\n    Driver: intel\n\n  power-saver:\n"
        self.assertEqual(controles.interpretar_perfis(saida), ["power-saver", "balanced", "performance"])

    def test_luz_noturna(self):
        self.assertEqual(controles.luz_noturna_comando("desligada"), [])
        programada = controles.luz_noturna_comando("programada", "19:00", "06:30", 3800)
        self.assertEqual(programada, ["wlsunset", "-t", "3800", "-T", "6500", "-s", "19:00", "-S", "06:30", "-d", "600"])
        agora = datetime.datetime(2026, 11, 14, 10, 0)
        ligada = controles.luz_noturna_comando("ligada", agora=agora)
        self.assertIn("09:58", ligada)        # a "noite" começou há 2 minutos
        self.assertIn("09:57", ligada)        # e o "dia" só volta daqui a quase 24 h

    def test_teclado(self):
        self.assertEqual(controles.interpretar_localectl("   X11 Layout: br\n    X11 Model: abnt2\n"), "br")
        self.assertEqual(controles.interpretar_localectl("X11 Layout: us\nX11 Variant: intl\n"), "us:intl")


class TestePastasEPreferencias(unittest.TestCase):
    def test_user_dirs(self):
        with tempfile.TemporaryDirectory() as inicio:
            arquivo = Path(inicio, "user-dirs.dirs")
            arquivo.write_text('XDG_DOWNLOAD_DIR="$HOME/Baixados"\nXDG_DESKTOP_DIR="$HOME/"\n# comentário\n')
            self.assertEqual(pastas.pasta("DOWNLOAD", arquivo, inicio), Path(inicio, "Baixados"))
            self.assertEqual(pastas.pasta("DESKTOP", arquivo, inicio), Path(inicio, "Área de Trabalho"))
            nomes = [f["nome"] for f in pastas.favoritos(arquivo, inicio)]
            self.assertEqual(nomes, ["Início", "Área de Trabalho", "Documentos", "Downloads", "Imagens", "Música", "Vídeos"])
            pastas.criar_pastas_padrao(arquivo, inicio)
            self.assertTrue(Path(inicio, "Baixados").is_dir())

    def test_preferencias(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta, "sub", "preferencias.conf")
            self.assertEqual(pastas.ler_preferencia("energia", "bloquear", "10", arquivo), "10")
            pastas.gravar_preferencia("energia", "bloquear", 5, arquivo)
            pastas.gravar_preferencia("luz-noturna", "modo", "ligada", arquivo)
            self.assertEqual(pastas.ler_preferencia("energia", "bloquear", "10", arquivo), "5")
            self.assertEqual(pastas.ler_preferencia("luz-noturna", "modo", "", arquivo), "ligada")


class TesteAplicativosETipos(unittest.TestCase):
    def test_ler_desktop_em_portugues(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta, "editor.desktop")
            arquivo.write_text("[Desktop Entry]\nType=Application\nName=Text Editor\nName[pt_BR]=Editor de Texto\n"
                               "Exec=editor %F\nIcon=editor\nMimeType=text/plain;text/markdown;\n"
                               "[Desktop Action nova]\nName=Nova janela\n")
            app = aplicativos.ler_entrada(arquivo)
            self.assertEqual(app["nome"], "Editor de Texto")
            self.assertEqual(app["tipos"], ["text/plain", "text/markdown"])
            oculto = Path(pasta, "oculto.desktop")
            oculto.write_text("[Desktop Entry]\nType=Application\nName=X\nNoDisplay=true\n")
            self.assertIsNone(aplicativos.ler_entrada(oculto))

    def test_comando_de_exec_com_arquivos(self):
        app = {"exec": "editor --nova %F", "terminal": False}
        self.assertEqual(aplicativos.comando_de_exec(app, ["/a b.txt", "/c.txt"]), ["editor", "--nova", "/a b.txt", "/c.txt"])
        self.assertEqual(aplicativos.comando_de_exec({"exec": "vlc %U", "terminal": False}), ["vlc"])
        self.assertEqual(aplicativos.comando_de_exec({"exec": "visualizador", "terminal": False}, ["/x.pdf"]), ["visualizador", "/x.pdf"])
        self.assertEqual(aplicativos.comando_de_exec({"exec": "htop", "terminal": True}), ["foot", "--", "htop"])

    def test_tipos(self):
        self.assertEqual(tipos.tipo("/x/Contrato.PDF")[:2], ("pdf", "Documento PDF"))
        self.assertEqual(tipos.tipo("/x/foto.jpg")[0], "imagem")
        self.assertTrue(tipos.tipo("/x/foto.jpg")[2])
        self.assertEqual(tipos.tipo("/x/pasta", eh_pasta=True)[0], "pasta")
        self.assertEqual(tipos.tipo("/x/sem-extensao")[1], "Arquivo")
        self.assertEqual(tipos.tamanho_legivel(1), "1 byte")
        self.assertEqual(tipos.tamanho_legivel(1_500_000), "1,5 MB")


class TesteSessao(unittest.TestCase):
    def test_wlr_randr(self):
        saida = "\n".join([
            'eDP-1 "Chimei Innolux Corporation 0x14C9 (eDP-1)"',
            "  Physical size: 310x170 mm",
            "  Enabled: yes",
            "  Modes:",
            "    1920x1080 px, 60.006001 Hz (preferred, current)",
            "    1920x1080 px, 48.004002 Hz",
            "    1280x720 px, 59.855000 Hz",
            "  Position: 0,0",
            "  Transform: normal",
            "  Scale: 1.250000",
            'HDMI-A-1 "Samsung"',
            "  Enabled: no",
            "  Modes:",
            "    3840x2160 px, 30.000000 Hz (preferred)",
        ])
        telas = sessao.interpretar_wlr_randr(saida)
        self.assertEqual([t["nome"] for t in telas], ["eDP-1", "HDMI-A-1"])
        self.assertEqual(telas[0]["modo"], "1920x1080@60.006")
        self.assertEqual(telas[0]["escala"], 1.25)
        self.assertEqual(len(telas[0]["modos"]), 3)
        self.assertFalse(telas[1]["ligada"])
        self.assertEqual(sessao.comando_tela("eDP-1", "1280x720@59.855", 1.5),
                         ["wlr-randr", "--output", "eDP-1", "--mode", "1280x720@59.855", "--scale", "1.5"])

    def test_papel_e_bloqueio(self):
        self.assertEqual(sessao.comando_papel("/nao/existe.jpg", "#123456"), ["swaybg", "-c", "#123456"])
        self.assertEqual(sessao.comando_papel("", "vermelho"), ["swaybg", "-c", sessao.COR_PADRAO])
        comando = sessao.comando_swayidle(10, 0, "/b")
        self.assertEqual(comando, ["swayidle", "-w", "timeout", "600", "/b", "before-sleep", "/b", "lock", "/b"])
        self.assertIn("systemctl suspend", sessao.comando_swayidle(0, 30, "/b"))
        self.assertNotIn("600", sessao.comando_swayidle(0, 30, "/b"))

    def test_sem_bloqueio_no_pendrive(self):
        self.assertTrue(sessao.sessao_do_pendrive("BOOT_IMAGE=/live/vmlinuz boot=live components quiet"))
        self.assertFalse(sessao.sessao_do_pendrive("BOOT_IMAGE=/boot/vmlinuz root=UUID=1 ro quiet"))
        self.assertFalse(sessao.sessao_do_pendrive("boot=liveish"))
        iniciados = []
        with mock.patch.object(sessao, "sessao_do_pendrive", return_value=True), \
                mock.patch.object(sessao, "_parar"), mock.patch.object(sessao, "_iniciar", iniciados.append):
            sessao.aplicar_bloqueio()
        self.assertEqual(iniciados, [])


class TesteOperacoesDeArquivo(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.raiz = Path(self._pasta.name)
        self.lixeira = self.raiz / "Lixeira"
        (self.raiz / "docs").mkdir()
        (self.raiz / "docs" / "a.txt").write_text("um")
        (self.raiz / "docs" / ".oculto").write_text("x")
        (self.raiz / "docs" / "Sub").mkdir()
        (self.raiz / "docs" / "Sub" / "b.pdf").write_text("dois")

    def tearDown(self):
        self._pasta.cleanup()

    def test_listar_pastas_primeiro_e_ocultos(self):
        itens = operacoes.listar(self.raiz / "docs")
        self.assertEqual([i["nome"] for i in itens], ["Sub", "a.txt"])
        self.assertEqual(len(operacoes.listar(self.raiz / "docs", ocultos=True)), 3)
        with self.assertRaises(operacoes.ErroDeArquivo):
            operacoes.listar(self.raiz / "nao-existe")

    def test_nome_livre_e_nova_pasta(self):
        self.assertEqual(operacoes.nome_livre(self.raiz / "docs", "a.txt"), "a (2).txt")
        self.assertEqual(operacoes.nome_livre(self.raiz / "docs", "novo.txt"), "novo.txt")
        primeira = operacoes.nova_pasta(self.raiz / "docs")
        segunda = operacoes.nova_pasta(self.raiz / "docs")
        self.assertEqual(Path(primeira).name, "Nova pasta")
        self.assertEqual(Path(segunda).name, "Nova pasta (2)")

    def test_renomear(self):
        novo = operacoes.renomear(self.raiz / "docs" / "a.txt", "Notas.txt")
        self.assertTrue(Path(novo).is_file())
        for nome in ("", "x/y", "Sub"):
            with self.assertRaises(operacoes.ErroDeArquivo):
                operacoes.renomear(novo, nome)

    def test_copiar_e_mover_sem_sobrescrever(self):
        destino = self.raiz / "destino"
        destino.mkdir()
        (destino / "a.txt").write_text("já existia")
        progresso = []
        novos = operacoes.transferir([self.raiz / "docs" / "a.txt", self.raiz / "docs" / "Sub"], destino,
                                     progresso=lambda f, _n: progresso.append(f))
        self.assertEqual(sorted(Path(n).name for n in novos), ["Sub", "a (2).txt"])
        self.assertEqual((destino / "a.txt").read_text(), "já existia")
        self.assertEqual((destino / "Sub" / "b.pdf").read_text(), "dois")
        self.assertEqual(progresso[-1], 1.0)
        operacoes.transferir([self.raiz / "docs" / "Sub"], destino, mover=True)
        self.assertFalse((self.raiz / "docs" / "Sub").exists())
        self.assertTrue((destino / "Sub (2)" / "b.pdf").exists())

    def test_nao_coloca_pasta_dentro_dela_mesma(self):
        with self.assertRaises(operacoes.ErroDeArquivo):
            operacoes.transferir([self.raiz / "docs"], self.raiz / "docs" / "Sub")

    def test_cancelar_copia(self):
        grande = self.raiz / "grande.bin"
        grande.write_bytes(os.urandom(3 * 1024 * 1024))
        destino = self.raiz / "destino"
        destino.mkdir()
        with self.assertRaises(operacoes.ErroDeArquivo):
            operacoes.transferir([grande], destino, cancelado=lambda: True)

    def test_lixeira_ida_e_volta(self):
        quando = datetime.datetime(2026, 11, 14, 9, 30)
        nomes = operacoes.mover_para_lixeira([self.raiz / "docs" / "a.txt"], self.lixeira, quando)
        self.assertFalse((self.raiz / "docs" / "a.txt").exists())
        info = (self.lixeira / "info" / (nomes[0] + ".trashinfo")).read_text()
        self.assertIn("DeletionDate=2026-11-14T09:30:00", info)
        itens = operacoes.listar_lixeira(self.lixeira)
        self.assertEqual(itens[0]["nome"], "a.txt")
        self.assertEqual(itens[0]["original"], str(self.raiz / "docs" / "a.txt"))
        # Mesmo nome de novo: a Lixeira guarda os dois
        (self.raiz / "docs" / "a.txt").write_text("outro")
        operacoes.mover_para_lixeira([self.raiz / "docs" / "a.txt"], self.lixeira)
        self.assertEqual(len(operacoes.listar_lixeira(self.lixeira)), 2)
        # Restaurar com o original já de volta: ganha outro nome, nada é sobrescrito
        (self.raiz / "docs" / "a.txt").write_text("novo")
        restaurados = operacoes.restaurar([nomes[0]], self.lixeira)
        self.assertEqual(Path(restaurados[0]).name, "a (2).txt")
        self.assertEqual(Path(restaurados[0]).read_text(), "um")
        operacoes.esvaziar_lixeira(self.lixeira)
        self.assertEqual(operacoes.listar_lixeira(self.lixeira), [])

    def test_lixeira_sem_permissao_na_pasta_diz_de_quem_e_e_segue_com_os_outros(self):
        """Pasta de outro usuário (ex.: criada como root por um build): os outros itens vão, e o erro traz os
        que ficaram, para o agente movê-los com autorização (ADR 068)."""
        bloqueado = str((self.raiz / "docs" / "Sub").absolute())
        renomear = os.rename

        def rename(origem, destino):
            if str(origem) == bloqueado:
                raise PermissionError(13, "Permission denied")
            return renomear(origem, destino)
        with mock.patch("os.rename", rename), mock.patch.object(operacoes, "_dono", lambda c: "root" if Path(c).name == "docs" else "eu"):
            with self.assertRaises(operacoes.SemPermissao) as contexto:
                operacoes.mover_para_lixeira([self.raiz / "docs" / "a.txt", self.raiz / "docs" / "Sub"], self.lixeira)
        self.assertEqual(contexto.exception.caminhos, [bloqueado])
        self.assertEqual(contexto.exception.movidos, ["a.txt"])
        self.assertIn("administrador do sistema (root)", str(contexto.exception))
        self.assertEqual(len(operacoes.listar_lixeira(self.lixeira)), 1)        # o a.txt foi; o Sub ficou
        self.assertTrue((self.raiz / "docs" / "Sub").is_dir())

    def test_restaurar_recria_a_pasta(self):
        nomes = operacoes.mover_para_lixeira([self.raiz / "docs" / "Sub"], self.lixeira)
        operacoes.transferir([self.raiz / "docs"], self.raiz, mover=True)  # nada muda (mesma pasta)
        import shutil
        shutil.rmtree(self.raiz / "docs")
        restaurados = operacoes.restaurar(nomes, self.lixeira)
        self.assertTrue(Path(restaurados[0], "b.pdf").is_file())

    def test_buscar(self):
        achados = operacoes.buscar(self.raiz, "B.PDF")
        self.assertEqual([a["nome"] for a in achados], ["b.pdf"])
        self.assertEqual(operacoes.buscar(self.raiz, "oculto"), [])
        self.assertEqual(len(operacoes.buscar(self.raiz, "oculto", ocultos=True)), 1)

    def test_discos(self):
        mounts = self.raiz / "mounts"
        mounts.write_text("/dev/nvme0n1p2 / ext4 rw 0 0\n/dev/sdb1 /media/gustavo/PENDRIVE\\040AZUL vfat rw 0 0\n")
        discos = operacoes.discos_montados(mounts)
        self.assertEqual([d["nome"] for d in discos], ["PENDRIVE AZUL"])
        lsblk = ('{"blockdevices": [{"path": "/dev/nvme0n1", "hotplug": false, "type": "disk", "children": ['
                 '{"path": "/dev/nvme0n1p2", "fstype": "ext4", "type": "part", "mountpoint": "/", "hotplug": false}]},'
                 '{"path": "/dev/sdb", "hotplug": true, "type": "disk", "size": "28.9G", "children": ['
                 '{"path": "/dev/sdb1", "fstype": "vfat", "type": "part", "label": null, "mountpoint": null, "size": "28.9G"}]}]}')
        externos = operacoes.interpretar_lsblk(lsblk)
        self.assertEqual(externos, [{"nome": "Disco de 28,9G", "dispositivo": "/dev/sdb1", "caminho": "",
                                     "montado": False, "removivel": True}])


if __name__ == "__main__":
    unittest.main()
