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
