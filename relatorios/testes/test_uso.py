"""Uso agregado e escolha pela tela de "Ajude a melhorar o DuiaOS" (ADR 040, fase 2)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from relatorios import coleta, principal, uso

RAIZ = Path(__file__).resolve().parents[2]


def entrada(evento, prioridade=6, **dados):
    """Entrada do journal como o journalctl -o json a entrega."""
    return {"PRIORITY": str(prioridade), "SYSLOG_IDENTIFIER": "duiaos-ilha-de-aplicativos",
            "DUIAOS_COMPONENTE": "duiaos-ilha-de-aplicativos", "DUIAOS_EVENTO": evento,
            "DUIAOS_DADOS": json.dumps(dados), "MESSAGE": evento, "__REALTIME_TIMESTAMP": "1791840000000000",
            "_BOOT_ID": "abcdef0123456789"}


class TestUsoAgregado(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        (Path(self.pasta.name) / "firefox-esr.desktop").write_text("[Desktop Entry]\n")
        self.patch = mock.patch.object(uso, "PASTA_APLICATIVOS", Path(self.pasta.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.pasta.cleanup()

    def test_soma_por_valor_e_descarta_o_desconhecido(self):
        r = uso.agregar([
            ("uso.aplicativo_aberto", {"aplicativo": "firefox-esr.desktop", "por": "ilha"}),
            ("uso.aplicativo_aberto", {"aplicativo": "firefox-esr.desktop", "por": "central"}),
            ("uso.aplicativo_aberto", {"aplicativo": "atalho-da-maria.desktop", "por": "ilha"}),
            ("uso.qualquer_coisa", {"texto": "conteúdo pessoal"}),
        ])
        soma = r["eventos"]["uso.aplicativo_aberto"]
        self.assertEqual(soma["total"], 3)
        self.assertEqual(soma["por"]["aplicativo"], {"firefox-esr.desktop": 2, "outro": 1})
        self.assertEqual(soma["por"]["por"], {"ilha": 2, "central": 1})
        self.assertEqual(r["descartados"], 1)

    def test_campo_livre_nunca_entra(self):
        r = uso.agregar([("uso.wise_pedido", {"provedor": "local", "texto": "minha senha é 1234"})])
        self.assertEqual(r["eventos"]["uso.wise_pedido"]["por"], {"provedor": {"local": 1}})
        self.assertNotIn("1234", json.dumps(r))

    def test_valor_fora_do_formato_fica_de_fora(self):
        r = uso.agregar([("uso.wise_ferramenta", {"ferramenta": "rm -rf /"})])
        self.assertEqual(r["eventos"]["uso.wise_ferramenta"], {"total": 1, "por": {}})

    def test_so_a_partir_de_erros_e_uso(self):
        entradas = [entrada("uso.menu_de_energia", acao="bloquear")] * 3
        self.assertEqual(coleta.agregar_uso(entradas, "erros"), {})
        r = coleta.agregar_uso(entradas, "erros_e_uso")
        self.assertEqual(r["eventos"]["uso.menu_de_energia"]["por"]["acao"], {"bloquear": 3})

    def test_uso_nunca_sai_um_a_um(self):
        eventos, _ = coleta.montar([entrada("uso.menu_de_energia", acao="desligar")], "desenvolvimento")
        self.assertEqual(eventos, [])

    def test_relatorio_leva_o_uso(self):
        from relatorios import config as cfg
        with tempfile.TemporaryDirectory() as pasta:
            caminho = coleta.coletar(cfg.Config("erros_e_uso"), pasta,
                                     journal=lambda cursor, desde: ([entrada("uso.central_de_aplicativos",
                                                                             por="atalho")], "c1"),
                                     coletar_perfil=lambda: {}, nomes=set(), contexto=None)
            relatorio = json.loads(Path(caminho).read_text())
        self.assertEqual(relatorio["uso"]["eventos"]["uso.central_de_aplicativos"]["por"]["por"], {"atalho": 1})


class TestEscolhaPelaTela(unittest.TestCase):
    def test_desenvolvimento_nao_pela_tela(self):
        with mock.patch("os.geteuid", return_value=0), mock.patch.object(principal, "nivel") as nivel:
            self.assertEqual(principal.escolher(["desenvolvimento"]), 2)
            nivel.assert_not_called()

    def test_grava_a_escolha(self):
        with mock.patch("os.geteuid", return_value=0), \
                mock.patch.object(principal, "nivel", return_value=0) as nivel:
            self.assertEqual(principal.escolher(["erros_e_uso"]), 0)
            nivel.assert_called_once_with(["erros_e_uso"])

    def test_tela_so_abre_na_primeira_entrada_sem_escolha(self):
        especificacao = importlib.util.spec_from_file_location("ajude", RAIZ / "apps/ajude-a-melhorar/main.py")
        ajude = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(ajude)
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "relatorios.conf"
            with mock.patch.object(ajude, "ARQUIVO_CONFIG", arquivo):
                self.assertTrue(ajude.precisa_perguntar(["--primeira-entrada"]))       # sem arquivo
                arquivo.write_text("[relatorios]\nnivel = desligado\n")
                self.assertFalse(ajude.precisa_perguntar(["--primeira-entrada"]))
                self.assertTrue(ajude.precisa_perguntar([]))                          # pela Central

    def test_polkit_so_libera_o_helper_ao_administrador(self):
        regras = (RAIZ / "pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/rules.d/"
                  "50-duiaos-relatorios.rules").read_text()
        self.assertIn('action.id == "org.duiaos.relatorios.escolher"', regras)
        self.assertIn('subject.isInGroup("sudo")', regras)
        politica = (RAIZ / "pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/actions/"
                    "org.duiaos.relatorios.policy").read_text()
        self.assertIn("<allow_active>auth_admin_keep</allow_active>", politica)
        self.assertIn("/usr/lib/duiaos/relatorios/escolher-nivel", politica)


class TestEnvioPeloSite(unittest.TestCase):
    """Fase 3: POST ao Worker do site, sem credencial; o que não foi aceito fica pendente."""

    def preparar(self, quantidade):
        from relatorios import config as cfg, envio
        self.cfg, self.envio = cfg, envio
        self.pasta = Path(tempfile.mkdtemp())
        (self.pasta / "pendentes").mkdir()
        for i in range(quantidade):
            (self.pasta / "pendentes" / f"20261013-09000{i}.json").write_text(json.dumps({"formato": 1, "i": i}))
        return cfg.Config("erros")

    def abrir_com(self, respostas, recebidos):
        import urllib.error

        class Resposta:
            def __init__(self, status):
                self.status = status

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def abrir(pedido, timeout):
            recebidos.append((pedido.full_url, json.loads(pedido.data)))
            status = respostas.pop(0)
            if isinstance(status, Exception):
                raise status
            if status >= 400:
                raise urllib.error.HTTPError(pedido.full_url, status, "erro", {}, None)
            return Resposta(status)
        return abrir

    def test_padrao_e_o_site(self):
        config = self.preparar(0)
        self.assertEqual(config.transporte, "https")
        self.assertTrue(self.cfg.ENDERECO_PADRAO.startswith("https://"))
        self.assertTrue(self.cfg.ENDERECO_PADRAO.endswith("/api/relatorios"))

    def test_todos_aceitos(self):
        config, recebidos = self.preparar(2), []
        abrir = self.abrir_com([202, 202], recebidos)
        resultado = self.envio.enviar_pendentes(
            config, self.pasta, transporte=lambda c, r, p: self.envio.enviar_https(c, r, p, abrir=abrir))
        self.assertEqual(resultado, {"enviados": 2})
        self.assertEqual(recebidos[0][0], self.cfg.ENDERECO_PADRAO)
        self.assertEqual(len(list((self.pasta / "enviados").glob("*.json"))), 2)

    def test_site_pede_para_esperar_o_resto_fica(self):
        config, recebidos = self.preparar(3), []
        abrir = self.abrir_com([202, 429], recebidos)
        resultado = self.envio.enviar_pendentes(
            config, self.pasta, transporte=lambda c, r, p: self.envio.enviar_https(c, r, p, abrir=abrir))
        self.assertEqual(resultado, {"enviados": 1})
        self.assertEqual(len(list((self.pasta / "pendentes").glob("*.json"))), 2)

    def test_recusado_pelo_site_e_descartado(self):
        config, recebidos = self.preparar(2), []
        abrir = self.abrir_com([400, 202], recebidos)
        self.envio.enviar_pendentes(
            config, self.pasta, transporte=lambda c, r, p: self.envio.enviar_https(c, r, p, abrir=abrir))
        self.assertEqual(list((self.pasta / "pendentes").glob("*.json")), [])

    def test_sem_internet_nada_sai(self):
        config = self.preparar(1)
        abrir = self.abrir_com([OSError("sem rede")], [])
        resultado = self.envio.enviar_pendentes(
            config, self.pasta, transporte=lambda c, r, p: self.envio.enviar_https(c, r, p, abrir=abrir))
        self.assertIn("sem conexão", resultado["erro"])
        self.assertEqual(len(list((self.pasta / "pendentes").glob("*.json"))), 1)

    def test_desenvolvimento_nao_vai_pelo_site(self):
        self.preparar(1)
        config = self.cfg.Config("desenvolvimento", transporte="https")
        self.assertIn("Git", self.envio.enviar_pendentes(config, self.pasta)["erro"])


if __name__ == "__main__":
    unittest.main()
