"""Menu do aplicativo em foco na Barra de Recursos (menus.py, ADR 057).

A parte de leitura é testada com uma árvore de mentira, nos formatos que o GTK e o Qt usam; a de
integração abre aplicativos GTK e Qt de verdade num X virtual com o AT-SPI ligado (pula se faltar
o Xvfb, o dbus-run-session ou o AT-SPI).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import json
import shutil
import unittest.mock
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "barra-de-recursos"))
import menus  # noqa: E402


class No:
    def __init__(self, papel, nome="", filhos=(), estados=("ENABLED", "SENSITIVE", "VISIBLE"), tecla=""):
        self.papel, self.nome, self.filhos, self.estados, self.tecla = papel, nome, list(filhos), set(estados), tecla


class ArvoreDeMentira:
    def papel(self, n):
        return n.papel

    def nome(self, n):
        return n.nome

    def filhos(self, n, limite=400):
        return n.filhos[:limite]

    def quantos_filhos(self, n):
        return len(n.filhos)

    def estados(self, n):
        return n.estados

    def tecla(self, n):
        return n.tecla


def janela_gtk():
    arquivo = No("menu", "_Arquivo", [
        No("menu item", "_Novo", tecla="n;<Alt>a:n;<Primary>n"),
        No("menu", "_Recentes", [No("menu item", "a.txt")]),
        No("separator"), No("separator"),
        No("menu item", "Oculto", estados=("ENABLED", "SENSITIVE")),
        No("menu item", "Des_fazer", estados=("VISIBLE",), tecla="f;<Alt>e:f;<Primary><Shift>z"),
        No("check menu item", "_Quebrar linhas", estados=("ENABLED", "VISIBLE", "CHECKED")),
        No("separator")])
    vazio = No("menu", "_Vazio", [])
    barra = No("menu bar", "", [arquivo, vazio])
    return No("frame", "Editor", [No("filler", "", [barra, No("text")])])


def janela_qt():
    popup = No("popup menu", "", [
        No("menu item", "&Salvar", estados=("ENABLED",), tecla="Ctrl+S"),
        No("menu item", "&Barra de status", estados=("ENABLED", "CHECKABLE", "CHECKED"), tecla="Alt+B"),
        No("menu item", "&Recentes", [No("popup menu", "", [No("menu item", "plano.odt", estados=("ENABLED",))])],
           estados=("ENABLED",)),
        No("menu item", "&Desfazer", estados=(), tecla="Ctrl+Z")])
    barra = No("menu bar", "", [No("menu item", "&Arquivo", [popup], tecla="Alt+A"),
                                No("menu item", "Sem menu", [])])
    return No("frame", "Editor Qt", [barra])


class TesteTexto(unittest.TestCase):
    def test_atalhos(self):
        casos = {"n;<Alt>a:n;<Primary>n": "Ctrl+N", "f;<Alt>e:f;<Primary><Shift>z": "Ctrl+Shift+Z",
                 "<Alt>a;<Alt>a;": "", "Ctrl+S": "Ctrl+S", "Alt+B": "", "Ctrl+Shift+Del": "Ctrl+Shift+Del",
                 "Ctrl++": "Ctrl++", "": "", ";;<Control>Return": "Ctrl+Enter", "F1": "F1", "x;;<Primary>plus": "Ctrl++"}
        for entrada, esperado in casos.items():
            self.assertEqual(menus.atalho(entrada), esperado, entrada)

    def test_rotulos(self):
        self.assertEqual(menus.rotulo("_Arquivo"), "Arquivo")
        self.assertEqual(menus.rotulo("Sai&r"), "Sair")
        self.assertEqual(menus.rotulo("Salvar && sair"), "Salvar & sair")


class TesteLeitura(unittest.TestCase):
    def setUp(self):
        self.arvore = ArvoreDeMentira()
        self.nos = {}

    def registrar(self, no):
        self.nos[len(self.nos) + 1] = no
        return len(self.nos)

    def test_gtk(self):
        barra = menus.achar_barra(self.arvore, janela_gtk())
        titulos = menus.titulos(self.arvore, barra)
        self.assertEqual([nome for _no, nome in titulos], ["Arquivo"])            # o menu vazio fica de fora
        itens = menus.ler_itens(self.arvore, titulos[0][0], self.registrar, filtrar_invisiveis=True)
        resumo = [(i["rotulo"], i["tipo"], i["ativo"], i["marcado"], i["atalho"]) for i in itens]
        self.assertEqual(resumo, [("Novo", "item", True, False, "Ctrl+N"), ("Recentes", "submenu", True, False, ""),
                                  ("", "separador", False, False, ""),                       # dois seguidos viram um
                                  ("Desfazer", "item", False, False, "Ctrl+Shift+Z"),       # desativado; "Oculto" sumiu
                                  ("Quebrar linhas", "marcavel", True, True, "")])           # separador do fim sai
        self.assertEqual(itens[1]["itens"][0]["rotulo"], "a.txt")
        self.assertIs(self.nos[itens[0]["id"]].nome, "_Novo")

    def test_qt(self):
        barra = menus.achar_barra(self.arvore, janela_qt())
        titulos = menus.titulos(self.arvore, barra)
        self.assertEqual([nome for _no, nome in titulos], ["Arquivo"])
        itens = menus.ler_itens(self.arvore, titulos[0][0], self.registrar, filtrar_invisiveis=False)
        resumo = [(i["rotulo"], i["tipo"], i["ativo"], i["marcado"], i["atalho"]) for i in itens]
        self.assertEqual(resumo, [("Salvar", "item", True, False, "Ctrl+S"), ("Barra de status", "marcavel", True, True, ""),
                                  ("Recentes", "submenu", True, False, ""), ("Desfazer", "item", False, False, "Ctrl+Z")])
        self.assertEqual(itens[2]["itens"][0]["rotulo"], "plano.odt")

    def test_sem_barra_e_limites(self):
        self.assertIsNone(menus.achar_barra(self.arvore, No("frame", "Firefox", [No("document web")])))
        enorme = No("menu", "Muitos", [No("menu item", f"item {i}") for i in range(2000)])
        itens = menus.ler_itens(self.arvore, enorme, self.registrar, filtrar_invisiveis=True)
        self.assertLessEqual(len(itens), 200)

    def test_menu_da_janela(self):
        itens = menus.menu_da_janela("Firefox")
        self.assertEqual([i["id"] for i in itens if i["tipo"] != "separador"],
                         ["janela:minimizar", "janela:expandir", "janela:fechar", "janela:encerrar"])
        self.assertEqual(itens[-1]["rotulo"], "Encerrar Firefox")


class TesteServico(unittest.TestCase):
    def test_sem_barramento_de_acessibilidade_sai_sem_derrubar_ninguem(self):
        """Sem o barramento, o Atspi.init() encerraria o processo: o serviço confere antes e sai com 3."""
        import io
        with unittest.mock.patch.object(menus, "barramento_de_acessibilidade", return_value=False):
            saida = io.StringIO()
            self.assertEqual(menus.servico(io.StringIO(""), saida), 3)
        self.assertEqual(json.loads(saida.getvalue()), {"evento": "sem_atspi"})

    def test_processo_que_cai_volta_e_a_barra_fica_com_o_menu_da_janela(self):
        import tempfile
        import threading
        with tempfile.TemporaryDirectory() as pasta:
            falso = Path(pasta) / "servico.py"
            contagem = Path(pasta) / "vezes"
            falso.write_text("import json, sys, pathlib\n"
                             f"p = pathlib.Path({str(contagem)!r}); p.write_text(str(int(p.read_text() or 0) + 1) if p.exists() else '1')\n"
                             "print(json.dumps({'evento': 'menus', 'app_id': 'x', 'titulos': ['Arquivo']}), flush=True)\n")
            recebidos, chegou = [], threading.Event()

            def ao_menus(app, titulos):
                recebidos.append((app, list(titulos)))
                chegou.set()
            with unittest.mock.patch.object(menus.time, "sleep", lambda _s: None):
                processo = menus.ProcessoDeMenus(ao_menus, lambda *_a: None, comando=[sys.executable, str(falso)])
                for _ in range(60):
                    if len(recebidos) >= 4:
                        break
                    chegou.wait(1)
                    chegou.clear()
                processo.parar()
            self.assertIn(("x", ["Arquivo"]), recebidos)
            self.assertIn(("", []), recebidos)                 # caiu: sem menus até voltar
            self.assertGreaterEqual(int(contagem.read_text()), 2)  # e voltou


def _tem_atspi():
    try:
        import gi
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi  # noqa: F401
        return True
    except (ImportError, ValueError):
        return False


@unittest.skipUnless(shutil.which("Xvfb") and shutil.which("dbus-run-session") and _tem_atspi(),
                     "sem Xvfb, dbus-run-session ou AT-SPI")
class TesteAplicativosDeVerdade(unittest.TestCase):
    def rodar(self, qual):
        processo = subprocess.run(["dbus-run-session", "--", sys.executable, str(RAIZ / "shell/testes/menus/sessao.py"), qual],
                                  capture_output=True, text=True, timeout=120, check=False)
        linha = next((l for l in processo.stdout.splitlines() if l.startswith("RESULTADO ")), "")
        self.assertTrue(linha, processo.stdout[-1500:] + processo.stderr[-1500:])
        return json.loads(linha[len("RESULTADO "):])

    def test_gtk(self):
        if subprocess.run([sys.executable, "-c", "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"],
                          capture_output=True, check=False).returncode != 0:
            self.skipTest("sem GTK 3")
        r = self.rodar("gtk")
        self.assertEqual(r["titulos"], ["Arquivo", "Editar", "Exibir"])
        editar = {i["rotulo"]: i for i in r["itens"]["1"]}
        self.assertEqual(list(editar), ["Desfazer", "Copiar", "Colar"])                 # "Oculto" não aparece
        self.assertFalse(editar["Desfazer"]["ativo"])
        self.assertEqual(editar["Copiar"]["atalho"], "Ctrl+C")
        self.assertTrue(r["itens"]["2"][0]["marcado"])
        self.assertIn("ACIONADO Novo", r["saida"])
        self.assertIn("ACIONADO relatorio.txt", r["saida"])                            # dentro do submenu

    def test_qt(self):
        try:
            import PySide6.QtWidgets  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")
        r = self.rodar("qt")
        self.assertEqual(r["titulos"], ["Arquivo", "Editar", "Exibir"])
        arquivo = {i["rotulo"]: i for i in r["itens"]["0"]}
        self.assertEqual(arquivo["Salvar"]["atalho"], "Ctrl+S")
        self.assertEqual(arquivo["Recentes"]["tipo"], "submenu")
        self.assertTrue(r["itens"]["2"][0]["marcado"])
        self.assertIn("ACIONADO Novo", r["saida"])
        self.assertIn("ACIONADO plano.odt", r["saida"])


if __name__ == "__main__":
    unittest.main()
