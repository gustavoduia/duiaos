"""Menus dos aplicativos do DuiaOS na Barra (shell/comum/menu_do_app.py, ADR 059): o Explorador, as
Configurações e a Duia App Store publicam os menus no D-Bus da sessão, e a Barra lê e aciona.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
import menu_do_app  # noqa: E402

try:
    import PySide6  # noqa: F401
    import gi  # noqa: F401
    TEM_TUDO = bool(shutil.which("dbus-run-session"))
except ImportError:
    TEM_TUDO = False


def achar(menus, rotulo_menu, rotulo_item):
    for menu in menus:
        if menu["rotulo"] == rotulo_menu:
            for item in menu["itens"]:
                if item["rotulo"] == rotulo_item:
                    return item
    return None


class TesteFormato(unittest.TestCase):
    def test_chave_e_ids(self):
        self.assertEqual(menu_do_app.chave_do_app("duiaos-explorador-de-arquivos"), "explorador_de_arquivos")
        menus = [{"rotulo": "Arquivo", "itens": [menu_do_app.item("a", "A"), menu_do_app.SEPARADOR,
                                                  menu_do_app.item("b", "B", ativo=False),
                                                  menu_do_app.item("s", "Sub", itens=[menu_do_app.item("c", "C")])]}]
        self.assertEqual(menu_do_app.ids_validos(menus), {"a", "c"})        # desativado e submenu não acionam


@unittest.skipUnless(TEM_TUDO, "sem PySide6, python3-gi ou dbus-run-session")
class TesteAplicativosDoDuiaOS(unittest.TestCase):
    def rodar(self, qual):
        processo = subprocess.run(["dbus-run-session", "--", sys.executable, str(RAIZ / "shell/testes/menus/sessao_duiaos.py"), qual],
                                  capture_output=True, text=True, timeout=120, check=False)
        linha = next((l for l in processo.stdout.splitlines() if l.startswith("RESULTADO ")), "")
        self.assertTrue(linha, processo.stdout[-1500:] + processo.stderr[-1500:])
        return json.loads(linha[len("RESULTADO "):])

    def test_explorador(self):
        r = self.rodar("explorador")
        self.assertEqual(r["titulos"], ["Arquivo", "Editar", "Exibir", "Ir"])
        self.assertFalse(achar(r["antes"], "Exibir", "Lista")["marcado"])
        self.assertFalse(achar(r["antes"], "Arquivo", "Renomear")["ativo"])           # nada selecionado
        self.assertEqual(achar(r["antes"], "Editar", "Copiar")["atalho"], "Ctrl+C")
        self.assertTrue(r["acionou"])
        self.assertTrue(achar(r["depois"], "Exibir", "Lista")["marcado"])             # o item fez efeito

    def test_configuracoes(self):
        r = self.rodar("configuracoes")
        self.assertEqual(r["titulos"], ["Configurações", "Exibir"])
        self.assertTrue(achar(r["depois"], "Exibir", "Som")["marcado"])

    def test_loja(self):
        r = self.rodar("loja")
        self.assertEqual(r["titulos"], ["Loja", "Editar", "Categorias"])
        self.assertTrue(achar(r["depois"], "Loja", "Instalados")["marcado"])


if __name__ == "__main__":
    unittest.main()


class TesteMenuDoWise(unittest.TestCase):
    """Botão direito no Wise, na Barra (ADR 063): abrir, as páginas das Configurações e desligar."""

    def test_itens_e_acoes(self):
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")
        import os
        import tempfile
        from unittest import mock
        from shell.testes.test_armazenamento import carregar_barra      # a Barra só carrega uma vez por processo
        barra = carregar_barra()
        self.assertNotIn("wise", barra.INDICADORES_PADRAO.split(",")[:barra.MAXIMO_VISIVEIS])   # atrás da seta, por padrão
        Sistema = next(v for v in vars(barra).values() if isinstance(v, type) and hasattr(v, "abrirMenuDoWise"))
        falso = mock.Mock()
        falso._painel = ""
        with tempfile.TemporaryDirectory() as pasta, mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": pasta}):
            Sistema.abrirMenuDoWise(falso, 100.0)
            ids = [i["id"] for i in falso._itens_menu if i["tipo"] == "item"]
            self.assertEqual(ids, ["wise:abrir", "wise:configuracoes", "wise:ia", "wise:desligar"])
            Path(pasta, "duiaos-wise-desligado").write_text("x")
            falso._painel = ""
            Sistema.abrirMenuDoWise(falso, 100.0)
            self.assertNotIn("wise:desligar", [i["id"] for i in falso._itens_menu])
            self.assertIn("Ligar", falso._itens_menu[0]["rotulo"])
        with mock.patch.object(barra, "DEMONSTRACAO", False), mock.patch.object(barra.aplicativos, "iniciar") as iniciar, \
                mock.patch.object(barra.comum, "abrir_app_duiaos") as abrir:
            Sistema.acionarMenu(falso, "wise:desligar")
            Sistema.acionarMenu(falso, "wise:ia")
        iniciar.assert_called_once_with(["/usr/bin/duiaos-wise", "--desligar"])
        abrir.assert_called_once_with("configuracoes", "--secao", "ia")
