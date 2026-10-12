"""Testes da biblioteca duiaos_registro e do coletor duiaos-relatorios (ADR 040)."""
import io
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import duiaos_registro as registro
from duiaos_registro import journal, privacidade
from relatorios import coleta, config as cfg, envio, perfil


def ler_datagrama(dados):
    """Desmonta o protocolo nativo do journal (o mesmo que o systemd-journald lê)."""
    campos, i = {}, 0
    while i < len(dados):
        fim = dados.index(b"\n", i)
        linha = dados[i:fim]
        if b"=" in linha:
            nome, valor = linha.split(b"=", 1)
            campos[nome.decode()] = valor.decode()
            i = fim + 1
        else:
            tamanho = struct.unpack("<Q", dados[fim + 1:fim + 9])[0]
            campos[linha.decode()] = dados[fim + 9:fim + 9 + tamanho].decode()
            i = fim + 9 + tamanho + 1
    return campos


class JournalFalso:
    def __init__(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = os.path.join(self.pasta.name, "socket")
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(self.caminho)
        self.socket.settimeout(2)
        self._antes = journal.SOCKET
        journal.SOCKET = self.caminho

    def receber(self):
        return ler_datagrama(self.socket.recv(1 << 20))

    def fechar(self):
        journal.SOCKET = self._antes
        self.socket.close()
        self.pasta.cleanup()


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self.journal = JournalFalso()

    def tearDown(self):
        self.journal.fechar()

    def test_campos_padronizados(self):
        registro.info("ia.modelo_carregado", "Modelo carregado", componente="duiaos-ia", modelo="qwen3.5:4b",
                      chave_api="segredo123")
        campos = self.journal.receber()
        self.assertEqual(campos["SYSLOG_IDENTIFIER"], "duiaos-ia")
        self.assertEqual(campos["DUIAOS_EVENTO"], "ia.modelo_carregado")
        self.assertEqual(campos["PRIORITY"], "6")
        dados = json.loads(campos["DUIAOS_DADOS"])
        self.assertEqual(dados["modelo"], "qwen3.5:4b")
        self.assertEqual(dados["chave_api"], privacidade.OCULTO)
        self.assertTrue(campos["CODE_FILE"].endswith("test_relatorios.py"))

    def test_falha_com_rastro_e_assinatura_estavel(self):
        assinaturas = []
        for valor in ("a", "b"):            # mensagens diferentes, mesma falha
            try:
                {}[valor]
            except KeyError:
                registro.falha("ao ler", componente="duiaos-teste")
            campos = self.journal.receber()
            assinaturas.append(campos["DUIAOS_ASSINATURA"])
        self.assertEqual(campos["DUIAOS_EVENTO"], "falha")
        self.assertEqual(campos["MESSAGE_ID"], registro.ID_FALHA)
        self.assertIn("KeyError", campos["DUIAOS_RASTRO"])
        self.assertIn("\n", campos["DUIAOS_RASTRO"])                 # campo binário (várias linhas)
        self.assertEqual(assinaturas[0], assinaturas[1])

    def test_falha_nao_tratada_em_thread(self):
        anteriores = (sys.excepthook, threading.excepthook)
        try:
            registro.instalar_ganchos("duiaos-teste")
            with mock.patch("sys.stderr", io.StringIO()):
                t = threading.Thread(target=lambda: 1 / 0, name="trabalho")
                t.start()
                t.join()
            campos = self.journal.receber()
            self.assertEqual(campos["PRIORITY"], str(registro.CRITICO))
            self.assertIn("ZeroDivisionError", campos["MESSAGE"])
        finally:
            sys.excepthook, threading.excepthook = anteriores

    def test_sem_journal_nao_quebra(self):
        journal.SOCKET = "/nao/existe"
        with mock.patch("sys.stderr", io.StringIO()) as saida:
            registro.erro("teste", "algo deu errado")
        self.assertIn("algo deu errado", saida.getvalue())

    def test_nivel(self):
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as arquivo:
            arquivo.write("[relatorios]\nnivel = desenvolvimento\n")
        with mock.patch.object(registro, "ARQUIVO_CONFIG", arquivo.name):
            self.assertEqual(registro.nivel(), "desenvolvimento")
        with mock.patch.object(registro, "ARQUIVO_CONFIG", "/nao/existe"):
            self.assertEqual(registro.nivel(), "nao_escolhido")
        os.unlink(arquivo.name)


class TestPrivacidade(unittest.TestCase):
    def test_segredos(self):
        limpo = privacidade.limpar_segredos({"senha": "x", "tokens_por_segundo": 8.1,
                                             "texto": "chave AIzaSyA1234567890abcdefghijklmnopqrstu",
                                             "url": "https://ana:segredo@caldav.exemplo.com/"})
        self.assertEqual(limpo["senha"], privacidade.OCULTO)
        self.assertEqual(limpo["tokens_por_segundo"], 8.1)
        self.assertNotIn("AIza", limpo["texto"])
        self.assertNotIn("segredo", limpo["url"])

    def test_anonimizar(self):
        texto = ("gustavo@duiaos abriu /home/gustavo/Projetos de 192.168.15.27 e fe80::4263:e3e9:21c7:7930 "
                 "(mac 40:63:e3:e9:21:c7), e-mail gustavo.d@exemplo.com às 12:34:56 em 127.0.0.1")
        r = privacidade.anonimizar(texto, {"gustavo", "duiaos"})
        for proibido in ("gustavo", "duiaos", "192.168", "fe80", "40:63", "exemplo.com"):
            self.assertNotIn(proibido, r)
        self.assertIn("12:34:56", r)                                   # hora não é endereço
        self.assertIn("127.0.0.1", r)


def entrada(mensagem, prioridade=6, **campos):
    return {"MESSAGE": mensagem, "PRIORITY": str(prioridade), "__REALTIME_TIMESTAMP": str(int(time.time() * 1e6)),
            "_BOOT_ID": "abcdef0123456789", **campos}


COREDUMP = entrada("Process 1234 (labwc) of user 1000 dumped core.\n\nStack trace of thread 1234:\n"
                   "#0  0x00007f1 wlr_scene_node_destroy (libwlroots.so + 0x1)\n#1  0x00007f2 view_destroy (labwc + 0x2)\n"
                   "\nStack trace of thread 1235:\n#0  0x00007f3 poll (libc.so.6 + 0x3)\n", 2,
                   MESSAGE_ID=coleta.ID_COREDUMP, COREDUMP_EXE="/usr/bin/labwc", COREDUMP_SIGNAL_NAME="SIGSEGV",
                   SYSLOG_IDENTIFIER="systemd-coredump")


class TestColeta(unittest.TestCase):
    def test_classificar_por_nivel(self):
        info_duiaos = entrada("Modelo carregado", 6, SYSLOG_IDENTIFIER="duiaos-ia", DUIAOS_COMPONENTE="duiaos-ia")
        info_outro = entrada("Started foo", 6, SYSLOG_IDENTIFIER="systemd")
        aviso_outro = entrada("algo", 4, SYSLOG_IDENTIFIER="NetworkManager")
        self.assertIsNone(coleta.classificar(info_duiaos, "erros"))
        self.assertEqual(coleta.classificar(info_duiaos, "desenvolvimento"), "registro")
        self.assertIsNone(coleta.classificar(info_outro, "desenvolvimento"))
        self.assertIsNone(coleta.classificar(aviso_outro, "erros"))
        self.assertEqual(coleta.classificar(aviso_outro, "desenvolvimento"), "registro")
        self.assertEqual(coleta.classificar(entrada("x", 3, SYSLOG_IDENTIFIER="kernel"), "erros"), "erro")
        self.assertEqual(coleta.classificar(entrada("Failed with result 'exit-code'.", 4, UNIT_RESULT="exit-code"),
                                            "erros"), "servico_falhou")
        self.assertEqual(coleta.classificar(COREDUMP, "erros"), "falha_nativa")

    def test_falhas_agrupadas_e_repeticoes(self):
        falha = entrada("Falha: KeyError", 3, SYSLOG_IDENTIFIER="duiaos-wise", DUIAOS_EVENTO="falha",
                        DUIAOS_ASSINATURA="abc123", DUIAOS_RASTRO="Traceback…")
        erro = entrada("i915: GPU hang on rcs0 at 1234", 3, SYSLOG_IDENTIFIER="kernel")
        erro2 = entrada("i915: GPU hang on rcs0 at 9876", 3, SYSLOG_IDENTIFIER="kernel")
        eventos, falhas = coleta.montar([falha, falha, COREDUMP, COREDUMP, erro, erro2], "erros", ())
        self.assertEqual(len(falhas), 2)
        self.assertEqual(falhas[0]["contagem"], 2)
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["repeticoes"], 2)
        nativa = next(f for f in falhas if f["tipo"] == "falha_nativa")
        self.assertEqual(nativa["programa"], "/usr/bin/labwc")
        self.assertEqual(nativa["assinatura"], coleta.assinatura_nativa(COREDUMP))
        outra = dict(COREDUMP, MESSAGE=COREDUMP["MESSAGE"].replace("view_destroy", "outra_funcao"))
        self.assertNotEqual(coleta.assinatura_nativa(outra), nativa["assinatura"])

    def test_bytes_do_journal(self):
        e = entrada([104, 105, 255], 3, SYSLOG_IDENTIFIER="x")
        self.assertTrue(coleta.compactar(e, "erro")["mensagem"].startswith("hi"))

    def test_anonimiza_fora_do_desenvolvimento(self):
        e = entrada("falhou ao abrir /home/gustavo/a.txt", 3, SYSLOG_IDENTIFIER="duiaos-wise")
        eventos, _ = coleta.montar([e], "erros", {"gustavo"})
        self.assertNotIn("gustavo", json.dumps(eventos))
        eventos, _ = coleta.montar([e], "desenvolvimento", {"gustavo"})
        self.assertIn("gustavo", json.dumps(eventos))


class ComPasta(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        self.perfil = {"sistema": {"version_id": "0.3.0"}, "processador": {"modelo": "i5"}, "inicio_segundos": 9}

    def tearDown(self):
        self.temp.cleanup()

    def coletar(self, nivel, entradas, **k):
        lidos = []

        def journal(cursor, desde):
            lidos.append(cursor)
            return entradas, "cursor-" + str(len(lidos))
        caminho = coleta.coletar(cfg.Config(nivel, maquina="dell"), self.pasta, journal=journal,
                                 coletar_perfil=lambda: dict(self.perfil), nomes=set(), **k)
        return caminho, lidos


class TestColetar(ComPasta):
    def test_nada_sem_escolha(self):
        caminho, lidos = self.coletar("nao_escolhido", [entrada("x", 2)])
        self.assertIsNone(caminho)
        self.assertEqual(lidos, [])                                    # nem lê o journal

    def test_relatorio_e_cursor(self):
        caminho, _ = self.coletar("erros", [entrada("erro do kernel", 3, SYSLOG_IDENTIFIER="kernel")])
        relatorio = json.loads(caminho.read_text())
        self.assertEqual(relatorio["resumo"]["erros"], 1)
        self.assertIn("perfil", relatorio)
        self.assertEqual(relatorio["maquina"], "")                    # nome da máquina só em desenvolvimento
        self.assertEqual(oct(caminho.stat().st_mode & 0o777), "0o600")
        # 2ª coleta: continua do cursor; perfil igual não vai de novo; sem novidade não gera relatório
        caminho2, lidos = self.coletar("erros", [])
        self.assertIsNone(caminho2)
        self.assertEqual(lidos, ["cursor-1"])

    def test_perfil_mudou(self):
        self.coletar("erros", [])
        self.perfil["pacotes"] = {"duiaos-shell": "0.3.1"}
        caminho, _ = self.coletar("erros", [])
        self.assertIn("perfil", json.loads(caminho.read_text()))

    def test_config_salvar_e_carregar(self):
        arquivo = self.pasta / "r.conf"
        cfg.Config("desenvolvimento", "git", "git@github.com:x/y.git", maquina="dell").salvar(arquivo)
        lido = cfg.Config.carregar(arquivo)
        self.assertEqual((lido.nivel, lido.repositorio, lido.maquina), ("desenvolvimento", "git@github.com:x/y.git", "dell"))
        self.assertEqual(len(cfg.identificador(self.pasta)), 32)
        self.assertEqual(cfg.identificador(self.pasta), cfg.identificador(self.pasta))


class TestEnvio(ComPasta):
    def setUp(self):
        super().setUp()
        self.remoto = self.pasta / "remoto.git"
        semente = self.pasta / "semente"
        rodar = lambda *a: subprocess.run(a, check=True, capture_output=True)  # noqa: E731
        rodar("git", "init", "-q", "--bare", "-b", "main", str(self.remoto))
        rodar("git", "init", "-q", "-b", "main", str(semente))
        (semente / "README.md").write_text("relatórios\n")
        rodar("git", "-C", str(semente), "add", ".")
        rodar("git", "-C", str(semente), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "início")
        rodar("git", "-C", str(semente), "push", "-q", str(self.remoto), "main")
        chave = self.pasta / "chave"
        chave.write_text("x")
        self.trocas = [mock.patch.object(cfg, "CHAVE_GIT", chave), mock.patch.object(cfg, "PASTA_ESTADO", self.pasta)]
        for t in self.trocas:
            t.start()

    def tearDown(self):
        for t in self.trocas:
            t.stop()
        super().tearDown()

    def arquivos(self):
        return subprocess.run(["git", "--git-dir", str(self.remoto), "ls-tree", "-r", "--name-only", "main"],
                              capture_output=True, text=True, check=True).stdout.split()

    def test_envia_e_move_para_enviados(self):
        self.coletar("desenvolvimento", [COREDUMP])
        config = cfg.Config("desenvolvimento", "git", str(self.remoto), maquina="dell")
        resultado = envio.enviar_pendentes(config, self.pasta)
        self.assertEqual(resultado, {"enviados": 1})
        arquivos = self.arquivos()
        self.assertIn("maquinas/dell/perfil.json", arquivos)
        self.assertTrue(any(a.startswith("maquinas/dell/20") and a.endswith(".json") for a in arquivos))
        self.assertEqual(len(list((self.pasta / "enviados").glob("*.json"))), 1)
        self.assertEqual(list((self.pasta / "pendentes").glob("*.json")), [])

    def test_nivel_desligado_na_hora_de_enviar(self):
        self.coletar("erros", [entrada("x", 3)])
        resultado = envio.enviar_pendentes(cfg.Config("desligado"), self.pasta)
        self.assertEqual(resultado["enviados"], 0)
        self.assertEqual(len(list((self.pasta / "pendentes").glob("*.json"))), 1)

    def test_falha_mantem_pendente(self):
        self.coletar("erros", [entrada("x", 3)])
        resultado = envio.enviar_pendentes(cfg.Config("erros", "git", str(self.pasta / "nao-existe.git")),
                                           self.pasta)
        self.assertIn("erro", resultado)
        self.assertEqual(len(list((self.pasta / "pendentes").glob("*.json"))), 1)


class TestCorrecoesDoDell(ComPasta):
    """O que o primeiro relatório do Dell (12/10) mostrou."""

    def test_servico_que_falhou_leva_as_ultimas_linhas(self):
        falhou = entrada("zramswap.service: Failed with result 'exit-code'.", 4, UNIT="zramswap.service",
                         UNIT_RESULT="exit-code", SYSLOG_IDENTIFIER="systemd", _SYSTEMD_UNIT="init.scope")
        pedidos = []

        def contexto(unidade, boot):
            pedidos.append((unidade, boot))
            return ["zramswap: motivo da falha"]
        eventos, _ = coleta.montar([falhou], "erros", (), contexto)
        self.assertEqual(pedidos, [("zramswap.service", "abcdef0123456789")])
        self.assertEqual(eventos[0]["contexto"], ["zramswap: motivo da falha"])
        self.assertEqual(eventos[0]["unidade_afetada"], "zramswap.service")

    def test_limite_nao_pula_registros(self):
        linhas = [json.dumps({"MESSAGE": f"m{i}", "__CURSOR": f"c{i}"}) + "\n" for i in range(10)]

        class Processo:
            def __init__(self, *a, **k):
                self.stdout = iter(linhas + ["-- cursor: c9\n"])

            def kill(self):
                pass

            def wait(self):
                return 0
        with mock.patch.object(coleta, "LIMITE_ENTRADAS", 4):
            entradas, cursor = coleta.ler_journal(None, 0, executar=Processo)
        self.assertEqual(len(entradas), 4)
        self.assertEqual(cursor, "c3")                      # a próxima coleta continua do 5º

    def test_estado_sem_sudo(self):
        (self.pasta / "pendentes").mkdir(mode=0o700)
        (self.pasta / "pendentes" / "x.json").write_text("{}")
        coleta.publicar_situacao(self.pasta, coleta=time.time(), envio={"t": time.time(), "enviados": 1})
        situacao = self.pasta / "situacao.json"
        self.assertEqual(oct(situacao.stat().st_mode & 0o777), "0o644")
        self.assertEqual(json.loads(situacao.read_text())["pendentes"], 1)
        from relatorios import principal
        saida = io.StringIO()
        with mock.patch.object(cfg, "PASTA_ESTADO", self.pasta), mock.patch("sys.stdout", saida), \
                mock.patch.object(cfg.Config, "carregar", return_value=cfg.Config("desenvolvimento")), \
                mock.patch.object(Path, "is_dir", side_effect=PermissionError("sem permissão")):
            self.assertEqual(principal.estado(), 0)
            self.assertEqual(principal._arquivos("pendentes"), [])
        self.assertIn("Pendentes: 1", saida.getvalue())
        self.assertIn("relatório(s)", saida.getvalue())


class TestPerfil(unittest.TestCase):
    def test_perfil_real_sem_dados_pessoais(self):
        dados = perfil.coletar()
        self.assertIn("processador", dados)
        texto = json.dumps(dados)
        self.assertNotIn(socket.gethostname(), texto)
        self.assertEqual(perfil.resumo(dados), perfil.resumo(dict(dados, inicio_segundos=99)))


if __name__ == "__main__":
    unittest.main()
