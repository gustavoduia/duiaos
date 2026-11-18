"""Atualização automática (agente/automatica.py, ADR 058): configuração, estado e o ciclo do temporizador.

Rodar: python3 -m unittest discover -s agente/testes -t .
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PASTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA))
import automatica as au  # noqa: E402


class TesteConfiguracao(unittest.TestCase):
    def test_modos(self):
        with tempfile.TemporaryDirectory() as pasta:
            conf = Path(pasta) / "duiaos" / "atualizacoes.conf"
            self.assertEqual(au.ler_modo(conf), "baixar")                  # sem arquivo: o padrão
            for modo in au.MODOS:
                au.gravar_modo(modo, conf)
                self.assertEqual(au.ler_modo(conf), modo)
            self.assertEqual(conf.stat().st_mode & 0o777, 0o644)            # a sessão lê
            with self.assertRaises(ValueError):
                au.gravar_modo("sempre", conf)
            conf.write_text("[automatica]\nmodo = qualquer\n")
            self.assertEqual(au.ler_modo(conf), "baixar")


class TesteEstado(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.estado = Path(self.pasta.name) / "atualizacoes" / "estado.json"

    def tearDown(self):
        self.pasta.cleanup()

    def test_verificacao_download_e_instalacao(self):
        mudancas = {"atualizar": [{"pacote": "duiaos-shell", "para": "0.3"}, {"pacote": "linux-image-amd64", "para": "6.12.120"}],
                    "instalar": [], "remover": []}
        dados = au.registrar_verificacao(mudancas, self.estado, agora=100)
        self.assertEqual((dados["disponiveis"], dados["duiaos"], dados["reiniciar_previsto"]), (2, 1, "computador"))
        assinatura = dados["assinatura"]
        au.registrar_download(self.estado)
        self.assertTrue(au.ler_estado(self.estado)["baixadas"])
        self.assertTrue(au.registrar_verificacao(mudancas, self.estado)["baixadas"])        # mesmo conjunto: continua baixado
        outro = {"atualizar": mudancas["atualizar"] + [{"pacote": "vim", "para": "9.2"}]}
        dados = au.registrar_verificacao(outro, self.estado)
        self.assertNotEqual(dados["assinatura"], assinatura)
        self.assertFalse(dados["baixadas"])                                                  # outro conjunto: baixar de novo
        dados = au.registrar_instalacao("ok", ["duiaos-shell 0.3", "linux-image-amd64 6.12.120"], self.estado, agora=200)
        self.assertEqual((dados["disponiveis"], dados["instalacao"]["reiniciar"], dados["instalacao"]["quantidade"]), (0, "computador", 2))
        self.assertEqual(self.estado.stat().st_mode & 0o777, 0o644)

    def test_rede_limitada_pelo_networkmanager(self):
        class Saida:
            def __init__(self, texto):
                self.stdout = texto
        self.assertTrue(au.rede_limitada(lambda c: Saida("u 1\n")))
        self.assertTrue(au.rede_limitada(lambda c: Saida("u 3\n")))                 # provavelmente (celular)
        self.assertFalse(au.rede_limitada(lambda c: Saida("u 4\n")))
        self.assertFalse(au.rede_limitada(lambda c: Saida("")))                       # sem NetworkManager

    def test_reinicio(self):
        self.assertEqual(au.reinicio(["vim", "curl"]), "nao")
        self.assertEqual(au.reinicio(["vim", "duiaos-shell"]), "sessao")
        self.assertEqual(au.reinicio(["duiaos-shell", "systemd"]), "computador")

    def test_ciclo_conforme_o_modo(self):
        pacotes = ["vim 9.2"]
        chamadas = []

        def preparar(forcar):
            chamadas.append(("preparar", forcar))
            return {}, pacotes

        def baixar():
            chamadas.append(("baixar",))

        def instalar():
            chamadas.append(("instalar",))
            return "ok", pacotes
        with mock.patch.object(au, "ESTADO", self.estado):
            funcoes = {"ao_preparar": preparar, "ao_baixar": baixar, "ao_instalar": instalar, "limitada": lambda: False}
            esperado = {"desativado": ("desativado", []), "avisar": ("avisado", [("preparar", True)]),
                        "baixar": ("baixado", [("preparar", True), ("baixar",)]),
                        "instalar-avisando": ("instalado", [("preparar", True), ("baixar",), ("instalar",)]),
                        "instalar": ("instalado", [("preparar", True), ("baixar",), ("instalar",)])}
            for modo, (resultado, passos) in esperado.items():
                chamadas.clear()
                au.gravar_estado({"baixadas": False}, self.estado)
                self.assertEqual(au.ciclo(modo, **funcoes), resultado, modo)
                self.assertEqual(chamadas, passos, modo)
            # Já baixado: não baixa de novo
            chamadas.clear()
            au.gravar_estado({"baixadas": True}, self.estado)
            au.ciclo("baixar", **funcoes)
            self.assertNotIn(("baixar",), chamadas)
            # Rede limitada (celular, franquia): só procura e avisa, não baixa nem instala (ADR 069)
            chamadas.clear()
            au.gravar_estado({"baixadas": False}, self.estado)
            self.assertEqual(au.ciclo("instalar", **{**funcoes, "limitada": lambda: True}), "rede-limitada")
            self.assertEqual(chamadas, [("preparar", True)])
            # Em dia: nada além de procurar
            chamadas.clear()
            pacotes.clear()
            self.assertEqual(au.ciclo("instalar", **funcoes), "em-dia")
            self.assertEqual(chamadas, [("preparar", True)])


try:
    import importlib.util
    _espec = importlib.util.spec_from_file_location("agente_servico", PASTA / "agente.py")
    ag = importlib.util.module_from_spec(_espec)
    _espec.loader.exec_module(ag)
    TEM_GI = True
except (ImportError, ValueError):
    TEM_GI = False


@unittest.skipUnless(TEM_GI, "sem python3-gi")
class TesteAgente(unittest.TestCase):
    def test_agente_grava_estado_e_configura(self):
        with tempfile.TemporaryDirectory() as pasta:
            agente = ag.Agente(ag.AptDeMentira(), usar_polkit=False, registro=Path(pasta) / "acoes.jsonl")
            plano = agente.preparar("atualizar_sistema", {"forcar": True}, 1000)
            estado = json.loads((Path(pasta) / "atualizacoes.json").read_text())
            self.assertEqual(estado["disponiveis"], sum(len(v) for k, v in plano["mudancas"].items() if k != "remover"))
            with self.assertRaises(ag.Recusa):
                agente.configurar('{"modo": "sempre"}', 1000, lambda _acao: True)
            with self.assertRaises(ag.Recusa):
                agente.configurar('{"modo": "instalar"}', 1000, lambda _acao: False)        # sem autorização
            agente.configurar('{"modo": "instalar"}', 1000, lambda acao: acao == "org.duiaos.agente.configurar_atualizacoes")
            self.assertEqual(au.ler_modo(Path(pasta) / "atualizacoes.conf"), "instalar")


    def test_proxy_do_apt(self):
        """ConfigurarProxy (ADR 070): grava o proxy HTTP do apt, recusa dados ruins e sem autorização, e tira com {}."""
        with tempfile.TemporaryDirectory() as pasta:
            agente = ag.Agente(ag.AptDeMentira(), usar_polkit=False, registro=Path(pasta) / "acoes.jsonl")
            arquivo = Path(pasta) / "95duiaos-proxy"
            sim = lambda acao: acao == "org.duiaos.agente.configurar_proxy"  # noqa: E731
            for ruim in ('{"servidor": "proxy;rm -rf /", "porta": 3128}', '{"servidor": "proxy", "porta": 70000}', "não é json"):
                with self.assertRaises(ag.Recusa):
                    agente.configurar_proxy(ruim, 1000, sim, arquivo)
            with self.assertRaises(ag.Recusa):
                agente.configurar_proxy('{"servidor": "proxy.exemplo.com", "porta": 3128}', 1000, lambda _a: False, arquivo)
            agente.configurar_proxy('{"servidor": "proxy.exemplo.com", "porta": 3128}', 1000, sim, arquivo)
            self.assertIn('Acquire::http::Proxy "http://proxy.exemplo.com:3128/";', arquivo.read_text())
            agente.configurar_proxy("{}", 1000, sim, arquivo)
            self.assertFalse(arquivo.exists())


    def test_firewall(self):
        """ConfigurarFirewall (ADR 071): valida o pedido e a autorização antes de mexer no serviço."""
        with tempfile.TemporaryDirectory() as pasta:
            agente = ag.Agente(ag.AptDeMentira(), usar_polkit=False, registro=Path(pasta) / "acoes.jsonl")
            comandos = []
            rodar = lambda c, tempo=30: (comandos.append(c), (0, "running\n", ""))[1]  # noqa: E731
            sim = lambda acao: acao == "org.duiaos.agente.configurar_firewall"  # noqa: E731
            for ruim in ('{"ligado": "sim"}', "[]", "x"):
                with self.assertRaises(ag.Recusa):
                    agente.configurar_firewall(ruim, 1000, sim, rodar)
            with self.assertRaises(ag.Recusa):
                agente.configurar_firewall('{"ligado": false}', 1000, lambda _a: False, rodar)
            self.assertEqual(comandos, [])
            agente.configurar_firewall('{"ligado": true, "ssh": false}', 1000, sim, rodar)
            self.assertIn(["systemctl", "enable", "--now", "firewalld.service"], comandos)


@unittest.skipUnless(TEM_GI, "sem python3-gi")
class TesteLimpeza(unittest.TestCase):
    """Limpar pacotes baixados e registros antigos (ADR 060), com autorização."""

    def test_limpa_so_com_autorizacao_e_mede_o_liberado(self):
        with tempfile.TemporaryDirectory() as pasta:
            apt_pasta, registros = Path(pasta) / "apt", Path(pasta) / "journal"
            apt_pasta.mkdir()
            registros.mkdir()
            (apt_pasta / "a.deb").write_bytes(b"x" * 300000)
            (apt_pasta / "lock").write_bytes(b"")
            comandos = []

            class AptConta(ag.AptDeMentira):
                def rodar(self, argumentos, tempo=300):
                    comandos.append(argumentos)
                    if "clean" in argumentos:
                        (apt_pasta / "a.deb").unlink()
                    return 0, "", ""
            agente = ag.Agente(AptConta(), usar_polkit=False, registro=Path(pasta) / "acoes.jsonl")
            agente.PASTA_APT, agente.PASTA_REGISTROS = apt_pasta, registros
            self.assertGreater(agente.espaco_do_sistema()["apt"], 290000)
            with self.assertRaises(ag.Recusa):
                agente.limpar_sistema('{"apt": true}', 1000, lambda _a: False)
            with self.assertRaises(ag.Recusa):
                agente.limpar_sistema('{}', 1000, lambda _a: True)
            resultado = agente.limpar_sistema('{"apt": true}', 1000, lambda a: a == "org.duiaos.agente.limpar_sistema")
            self.assertGreater(resultado["liberado"], 290000)
            self.assertEqual([c for c in comandos if "clean" in c][0][-1], "clean")
            self.assertFalse(any("journalctl" in c for c in comandos))       # só o que foi pedido


if __name__ == "__main__":
    unittest.main()
