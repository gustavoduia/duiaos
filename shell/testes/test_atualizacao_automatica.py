"""O que a sessão mostra da atualização automática (shell/comum/atualizacao_automatica.py, ADR 058) e a
dica de abrir uma tela do DuiaOS pela notificação (shell/notificacoes/servico.py).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
import atualizacao_automatica as aa  # noqa: E402

LIGOU, SESSAO = 1000, 2000          # o computador ligou em 1000; a sessão começou em 2000


def estado(**mais):
    return {"disponiveis": 3, "assinatura": "abc", "duiaos": 1, "baixadas": False, **mais}


class TesteAvisos(unittest.TestCase):
    def test_modos(self):
        for modo, icone, avisa in (("desativado", False, False), ("avisar", True, True), ("baixar", True, True),
                                   ("instalar-avisando", True, True), ("instalar", False, False)):
            r = aa.avisos(estado(), modo, {}, LIGOU, SESSAO)
            self.assertEqual(r["icone"], icone, modo)
            self.assertEqual(bool(r["notificacoes"]), avisa, modo)

    def test_avisa_uma_vez_por_conjunto(self):
        r = aa.avisos(estado(), "avisar", {}, LIGOU, SESSAO)
        self.assertEqual(r["notificacoes"][0]["chave"], ("disponiveis", "abc"))
        self.assertIn("3 atualizações", r["notificacoes"][0]["texto"])
        self.assertIn("novidades do DuiaOS", r["notificacoes"][0]["texto"])
        self.assertEqual(aa.avisos(estado(), "avisar", {"disponiveis": "abc"}, LIGOU, SESSAO)["notificacoes"], [])
        self.assertTrue(aa.avisos(estado(assinatura="def"), "avisar", {"disponiveis": "abc"}, LIGOU, SESSAO)["notificacoes"])

    def test_baixadas(self):
        r = aa.avisos(estado(baixadas=True, disponiveis=1), "baixar", {}, LIGOU, SESSAO)
        self.assertEqual(r["dica"], "1 atualização baixada, pronta para instalar")
        self.assertIn("Já baixadas", r["notificacoes"][0]["texto"])

    def test_instalada_e_reiniciar(self):
        instalada = {"disponiveis": 0, "instalacao": {"quando": 1500, "resultado": "ok", "reiniciar": "computador",
                                                      "quantidade": 4, "automatica": True}}
        r = aa.avisos(instalada, "instalar-avisando", {}, LIGOU, SESSAO)
        self.assertTrue(r["icone"])
        self.assertIn("Reinicie o computador", r["dica"])
        self.assertEqual(r["notificacoes"][0]["titulo"], "Atualizações instaladas")
        self.assertIn("4 atualizações instaladas", r["notificacoes"][0]["texto"])
        # Já reiniciou depois: nada
        self.assertFalse(aa.avisos(instalada, "instalar-avisando", {"instalacao": 1500}, 1600, 1700)["icone"])
        # No modo sem avisos, só se for preciso reiniciar
        r = aa.avisos(instalada, "instalar", {}, LIGOU, SESSAO)
        self.assertEqual([n["titulo"] for n in r["notificacoes"]], ["Atualização instalada"])
        sem_reinicio = {"instalacao": {**instalada["instalacao"], "reiniciar": "nao"}}
        self.assertEqual(aa.avisos(sem_reinicio, "instalar", {}, LIGOU, SESSAO)["notificacoes"], [])
        # Sessão: conta a partir do início da sessão, não do computador
        sessao = {"instalacao": {**instalada["instalacao"], "reiniciar": "sessao", "quando": 2500}}
        self.assertIn("Saia e entre", aa.avisos(sessao, "avisar", {}, LIGOU, SESSAO)["dica"])
        self.assertFalse(aa.avisos(sessao, "avisar", {}, LIGOU, 3000)["icone"])

    def test_falha_na_instalacao_automatica(self):
        falhou = {"instalacao": {"quando": 1500, "resultado": "erro", "automatica": True}}
        self.assertEqual(aa.avisos(falhou, "instalar", {}, LIGOU, SESSAO)["notificacoes"][0]["titulo"],
                         "A atualização automática não terminou")

    def test_cada_modo_tem_nome_e_explicacao(self):
        self.assertEqual(set(aa.NOMES), set(aa.MODOS))
        self.assertEqual(set(aa.EXPLICACOES), set(aa.MODOS))


class TesteDicaDeAbrir(unittest.TestCase):
    def test_so_telas_do_duiaos(self):
        sys.path.insert(0, str(RAIZ / "shell" / "notificacoes"))
        try:
            import servico
        except (ImportError, ValueError):
            self.skipTest("sem python3-gi")
        for valor, aceito in (("configuracoes:atualizacoes", True), ("loja:atualizacoes", True), ("configuracoes", True),
                              ("sh -c 'rm -rf ~'", False), ("configuracoes:../x", False), ("firefox", False)):
            dados = servico.interpretar("App", 0, "", "t", "", [], {"x-duiaos-abrir": valor}, -1)
            self.assertEqual(dados["abrir"], valor if aceito else "", valor)


if __name__ == "__main__":
    unittest.main()


class TesteListaDoModo(unittest.TestCase):
    def test_lista_quando_houver_atualizacoes_abre(self):
        """A lista não abria (16/11): a propriedade "busca" da lista de opções tinha o nome do campo de busca."""
        import os
        import subprocess
        try:
            import PySide6  # noqa: F401
        except ImportError:
            self.skipTest("sem PySide6")
        resultado = subprocess.run([sys.executable, str(RAIZ / "shell/testes/configuracoes_seletor.py"),
                                    str(RAIZ / "apps/configuracoes/main.py")], capture_output=True, text=True, timeout=90,
                                   env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}, cwd=RAIZ)
        self.assertIn("SELETOR-OK", resultado.stdout, resultado.stdout[-1500:] + resultado.stderr[-1500:])

    def test_nenhuma_propriedade_com_o_nome_de_um_id(self):
        """No QML, um id do arquivo ganha de uma propriedade de mesmo nome usada sem o objeto na frente.
        Propriedade e id com o mesmo nome só onde todo uso é qualificado (lista abaixo, conferida à mão)."""
        import re
        conferidos = {("shell/ilha-de-aplicativos/Ilha.qml", "vaga"), 
                      ("apps/ajude-a-melhorar/AjudeAMelhorar.qml", "cartao")}
        problemas = []
        for arquivo in sorted(list(RAIZ.glob("apps/**/*.qml")) + list(RAIZ.glob("shell/**/*.qml"))):
            texto = arquivo.read_text(encoding="utf-8")
            ids = set(re.findall(r"\bid:\s*(\w+)", texto))
            # "property alias x: x" é o jeito certo de expor um filho: não conta
            nomes = {n for t, n in re.findall(r"property\s+([\w<>.]+)\s+(\w+)", texto) if not re.search(rf"property\s+alias\s+{n}\s*:\s*{n}\b", texto)}
            for nome in ids & nomes:
                if (str(arquivo.relative_to(RAIZ)), nome) not in conferidos:
                    problemas.append(f"{arquivo.relative_to(RAIZ)}: {nome}")
        self.assertEqual(problemas, [])
