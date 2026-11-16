"""Auxiliar do test_ilha.py: abre a demonstração da Ilha, põe o mouse sobre um ícone (que amplia) e o
faz pular, como ao abrir um aplicativo. Confere que, durante todo o pulo, nenhum ícone sai da área
da Ilha (que é a janela dela no sistema) — saía e era cortado (16/11). Imprime PULO-OK ou o problema.

Uso: python3 ilha_pulo.py CAMINHO/shell/ilha-de-aplicativos/main.py
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

from PySide6.QtCore import QPointF  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def descendentes(item):
    for filho in item.childItems():
        yield filho
        yield from descendentes(filho)


def conferir():
    app = QGuiApplication.instance()
    QTest.qWait(500)
    janela = next(j for j in app.topLevelWindows() if j.property("posicao") is not None)
    ilha = next(f for f in janela.contentItem().childItems() if isinstance(f, QQuickItem) and f.property("raioAmpliacao"))
    vaga = next(i for i in descendentes(ilha) if i.property("idDesktop") == "foot.desktop")
    centro = vaga.mapToScene(QPointF(vaga.width() / 2, vaga.height() - 30))
    QTest.mouseMove(janela, centro.toPoint())
    QTest.qWait(300)
    ilha_obj = modulo.__dict__.get("_ilha_para_teste")
    ilha_obj.pulando.emit("foot.desktop")
    menor = 1e9
    for _ in range(90):                                  # o pulo dura cerca de 1,5 s
        QTest.qWait(16)
        # O desenho do ícone (o Item "dentro" da vaga, do tamanho do ícone), seja imagem ou a inicial
        desenho = next(i for i in vaga.childItems() if abs(i.width() - vaga.property("tam")) < 0.5 and i.height() > 10)
        menor = min(menor, desenho.mapToItem(ilha, QPointF(0, 0)).y())
    print("PULO-OK" if menor >= 0 else f"o ícone saiu {-menor:.1f} px pelo alto da Ilha", flush=True)
    os._exit(0 if menor >= 0 else 1)


_Ilha = modulo.Ilha


class IlhaParaTeste(_Ilha):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        modulo._ilha_para_teste = self


modulo.Ilha = IlhaParaTeste
modulo.QGuiApplication.exec = staticmethod(conferir)
modulo.main()
