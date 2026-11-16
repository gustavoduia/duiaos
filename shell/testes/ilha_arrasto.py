"""Auxiliar do test_ilha.py: arrasta um fixado na demonstração da Ilha. Confere que (1) durante o arrasto
os vizinhos abrem espaço (reorganização em tempo real, como no Dock do macOS), (2) ao soltar a ordem muda
e (3) a Ilha não fica presa em "arrastando" — ficava, porque a lista nova recriava o ícone no meio do
próprio clique (16/11). Imprime ARRASTO-OK ou o problema.

Uso: python3 ilha_arrasto.py CAMINHO/shell/ilha-de-aplicativos/main.py
"""
import importlib.util
import os
import sys

principal = sys.argv[1]
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = [principal, "--demonstracao"]
sys.path.insert(0, os.path.dirname(principal))
especificacao = importlib.util.spec_from_file_location("componente", principal)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)

from PySide6.QtCore import QPoint, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def descendentes(item):
    for filho in item.childItems():
        yield filho
        yield from descendentes(filho)


def falhar(texto):
    print(texto, flush=True)
    os._exit(1)


def conferir():
    app = QGuiApplication.instance()
    QTest.qWait(500)
    janela = next(j for j in app.topLevelWindows() if j.property("posicao") is not None)
    ilha = next(f for f in janela.contentItem().childItems() if isinstance(f, QQuickItem) and f.property("raioAmpliacao"))
    dados = modulo._ilha_para_teste
    itens = dados._itens
    moveis = [i for i, it in enumerate(itens) if it.get("fixado") and it["id"] not in (modulo.WISE_DESKTOP, modulo.EXPLORADOR_DESKTOP)]
    if len(moveis) < 3:
        falhar(f"a demonstração tem só {len(moveis)} fixados móveis")
    origem = moveis[0]
    id_arrastado, id_vizinho = itens[origem]["id"], itens[origem + 1]["id"]
    vagas = {i.property("indice"): i for i in descendentes(ilha) if i.property("indice") is not None and i.property("indice") >= 0}
    vaga = vagas[origem]
    passo = ilha.property("passoArrasto")
    inicio = vaga.mapToScene(QPointF(vaga.width() / 2, vaga.height() / 2)).toPoint()
    QTest.mouseMove(janela, inicio)
    QTest.mousePress(janela, Qt.LeftButton, Qt.NoModifier, inicio)
    for k in range(1, 21):                                   # 2 vagas para a direita, aos poucos
        QTest.mouseMove(janela, inicio + QPoint(int(2 * passo * k / 20), 0))
        QTest.qWait(10)
    QTest.qWait(300)                                         # a animação do vizinho termina
    if not ilha.property("arrastando"):
        falhar("o arrasto não começou")
    desvio = vagas[origem + 1].property("desvio")
    if abs(desvio + passo) > 0.5:
        falhar(f"o vizinho não abriu espaço durante o arrasto (desvio {desvio:.1f}, esperado {-passo:.1f})")
    QTest.mouseRelease(janela, Qt.LeftButton, Qt.NoModifier, inicio + QPoint(int(2 * passo), 0))
    QTest.qWait(900)
    if ilha.property("arrastando"):
        falhar("a Ilha ficou presa em \"arrastando\" depois de soltar")
    if ilha.property("origem") != -1:
        falhar("o estado do arrasto não voltou ao normal")
    novos = [it["id"] for it in dados._itens]
    if novos.index(id_arrastado) != origem + 2 or novos.index(id_vizinho) != origem:
        falhar(f"a ordem não mudou como esperado: {novos}")
    # Depois de soltar, a Ilha responde de novo: um segundo arrasto também funciona
    vagas = {i.property("indice"): i for i in descendentes(ilha) if i.property("indice") is not None and i.property("indice") >= 0}
    vaga = vagas[origem + 2]
    inicio = vaga.mapToScene(QPointF(vaga.width() / 2, vaga.height() / 2)).toPoint()
    QTest.mousePress(janela, Qt.LeftButton, Qt.NoModifier, inicio)
    for k in range(1, 21):
        QTest.mouseMove(janela, inicio - QPoint(int(2 * passo * k / 20), 0))
        QTest.qWait(10)
    QTest.mouseRelease(janela, Qt.LeftButton, Qt.NoModifier, inicio - QPoint(int(2 * passo), 0))
    QTest.qWait(900)
    if [it["id"] for it in dados._itens].index(id_arrastado) != origem or ilha.property("arrastando"):
        falhar("o segundo arrasto não funcionou")
    print("ARRASTO-OK", flush=True)
    os._exit(0)


_Ilha = modulo.Ilha


class IlhaParaTeste(_Ilha):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        modulo._ilha_para_teste = self


modulo.Ilha = IlhaParaTeste
modulo.QGuiApplication.exec = staticmethod(conferir)
modulo.main()
