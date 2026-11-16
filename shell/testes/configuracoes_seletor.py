"""Auxiliar do test_armazenamento.py: abre Configurações › Atualizações (demonstração), clica na lista
"Quando houver atualizações" e escolhe outra opção. A lista não abria no Dell (16/11): a propriedade
"busca" da lista de opções tinha o mesmo nome do campo de busca da lateral, e o QML usava o campo.
Imprime SELETOR-OK ou o problema.
"""
import importlib.util
import os
import sys

principal = sys.argv[1]
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = [principal, "--demonstracao", "--secao", "atualizacoes"]
sys.path.insert(0, os.path.dirname(principal))
especificacao = importlib.util.spec_from_file_location("componente", principal)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)

from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def descendentes(item):
    for filho in item.childItems():
        yield filho
        yield from descendentes(filho)


def conferir():
    app = QGuiApplication.instance()
    QTest.qWait(600)
    janela = app.topLevelWindows()[0]
    itens = list(descendentes(janela.contentItem()))
    seletor = next((i for i in itens if i.property("rotulo") is not None and i.property("opcoes") is not None
                    and i.property("valor") in ("baixar", "avisar", "desativado", "instalar", "instalar-avisando")), None)
    escolha = next((i for i in itens if i.property("aoEscolher") is not None or i.property("filtradas") is not None), None)
    if seletor is None or escolha is None:
        print("não achei a lista ou a escolha", flush=True)
        os._exit(1)
    centro = seletor.mapToScene(QPointF(seletor.width() / 2, seletor.height() / 2)).toPoint()
    QTest.mouseClick(janela, Qt.LeftButton, Qt.NoModifier, centro)
    QTest.qWait(200)
    if not escolha.property("visible"):
        print("a lista de opções não abriu", flush=True)
        os._exit(1)
    if len(escolha.property("filtradas").toVariant() if hasattr(escolha.property("filtradas"), "toVariant") else escolha.property("filtradas")) != 5:
        print("a lista não mostra as 5 opções", flush=True)
        os._exit(1)
    print("SELETOR-OK", flush=True)
    os._exit(0)


modulo.QGuiApplication.exec = staticmethod(conferir)
modulo.main()
