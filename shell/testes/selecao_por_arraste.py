"""Auxiliar do test_selecao_por_arraste.py: abre o Explorador de Arquivos (ou a demonstração da Área de
Trabalho) e arrasta o mouse no espaço vazio. Confere o retângulo de seleção (selecionar vários arquivos
segurando o botão esquerdo, como no Windows e no macOS), a rolagem automática na borda, o Ctrl que
inverte, a roda do mouse com as vistas sem arraste-rolagem e o Descompactar. Imprime SELECAO-OK ou o
problema.

Uso: python3 selecao_por_arraste.py explorador CAMINHO/apps/explorador-de-arquivos/main.py PASTA
     python3 selecao_por_arraste.py area CAMINHO/shell/area-de-trabalho/main.py
"""
import importlib.util
import os
import sys
from pathlib import Path

modo, principal = sys.argv[1], sys.argv[2]
pasta = sys.argv[3] if len(sys.argv) > 3 else ""
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = [principal, pasta] if modo == "explorador" else [principal, "--demonstracao"]
sys.path.insert(0, os.path.dirname(principal))
especificacao = importlib.util.spec_from_file_location("componente", principal)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)

from PySide6.QtCore import QPoint, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def descendentes(item):
    for filho in item.childItems():
        yield filho
        yield from descendentes(filho)


def falhar(texto):
    print(texto, flush=True)
    os._exit(1)


def arrastar(janela, de, ate, passos=12, modificadores=Qt.NoModifier, segurar=0):
    QTest.mouseMove(janela, de)
    QTest.mousePress(janela, Qt.LeftButton, modificadores, de)
    for k in range(1, passos + 1):
        QTest.mouseMove(janela, de + (ate - de) * k / passos)
        QTest.qWait(10)
    if segurar:
        QTest.qWait(segurar)
    QTest.mouseRelease(janela, Qt.LeftButton, modificadores, ate)
    QTest.qWait(80)


def selecao(objeto):
    """A propriedade "selecao" (objeto do JavaScript: caminho → true) como dicionário."""
    valor = objeto.property("selecao")
    if hasattr(valor, "toVariant"):
        valor = valor.toVariant()
    return {k: v for k, v in (valor or {}).items() if v}


def quantos(objeto):
    return len(selecao(objeto))


def conferir_explorador():
    app = QGuiApplication.instance()
    QTest.qWait(600)
    janela = app.topLevelWindows()[0]
    raiz = janela.contentItem()
    itens = list(descendentes(raiz))
    grade = next(i for i in itens if i.property("colunas") is not None)
    area = next(i for i in itens if i.property("bordaRolagem") is not None)   # fundoArea
    if grade.property("interactive"):
        falhar("a grade ainda rola ao arrastar (o arraste no vazio precisa selecionar)")
    colunas = grade.property("colunas")
    largura, altura = grade.property("cellWidth"), grade.property("cellHeight")
    origem = grade.mapToScene(QPointF(0, 0))
    # Começa na margem da área, à esquerda do 1º ícone, e cobre 3 colunas × 2 linhas
    de = area.mapToScene(QPointF(4, 6)).toPoint()
    ate = QPoint(int(origem.x() + largura * 2.5), int(origem.y() + altura * 1.5))
    arrastar(janela, de, ate)
    n = quantos(janela)
    if n != 6:
        falhar(f"o retângulo de 3 colunas × 2 linhas selecionou {n} itens (esperado 6; {colunas} colunas)")
    # A pasta recarregar (um arquivo novo nela, o fim de uma cópia) não apaga a seleção — apagava (17/11)
    modulo_explorador().recarregar()
    QTest.qWait(80)
    if quantos(janela) != 6:
        falhar(f"recarregar a pasta apagou a seleção (ficaram {quantos(janela)})")
    # Ctrl + arrastar sobre a 1ª linha inverte: os 3 da 1ª linha saem, os 3 da 2ª ficam
    de2 = area.mapToScene(QPointF(4, 6)).toPoint()
    ate2 = QPoint(int(origem.x() + largura * 2.5), int(origem.y() + altura * 0.5))
    arrastar(janela, de2, ate2, modificadores=Qt.ControlModifier)
    n = quantos(janela)
    if n != 3:
        falhar(f"Ctrl + arrastar não inverteu a seleção (ficaram {n}, esperado 3)")
    # Clique simples no vazio limpa
    QTest.mouseClick(janela, Qt.LeftButton, Qt.NoModifier, de)
    QTest.qWait(80)
    if selecao(janela):
        falhar("o clique no vazio não limpou a seleção")
    # Roda do mouse rola a grade (que não é mais "interactive")
    area_y = area.mapToScene(QPointF(4, 200)).toPoint()
    QTest.mouseMove(janela, area_y)
    from PySide6.QtGui import QWheelEvent
    evento = QWheelEvent(QPointF(area_y), QPointF(area_y), QPoint(0, 0), QPoint(0, -240), Qt.NoButton,
                         Qt.NoModifier, Qt.NoScrollPhase, False)
    QGuiApplication.sendEvent(janela, evento)
    QTest.qWait(80)
    if grade.property("contentY") <= 0:
        falhar("a roda do mouse não rolou a grade")
    grade.setProperty("contentY", 0)
    QTest.qWait(50)
    # Arrastar até a borda de baixo e segurar: a grade rola sozinha e o retângulo continua crescendo
    baixo = area.mapToScene(QPointF(area.width() / 2, area.height() - 4)).toPoint()
    arrastar(janela, de, baixo, segurar=900)
    total = len(modulo_explorador()._itens)
    n = quantos(janela)
    if grade.property("contentY") <= 0:
        falhar("o retângulo encostou na borda e a grade não rolou")
    if n <= colunas * 4 or n > total:
        falhar(f"a rolagem automática não estendeu a seleção ({n} de {total})")
    # Arrastar a partir de um ícone continua sendo arrastar o arquivo (não desenha retângulo)
    if area.property("arrastando"):
        falhar("o retângulo ficou preso depois de soltar")
    # Descompactar: o .zip vira uma pasta ao lado e ela fica selecionada
    zip_ = next(i for i in modulo_explorador()._itens if i["nome"].endswith(".zip"))
    if not zip_.get("compactado"):
        falhar("o .zip não veio marcado como compactado")
    modulo_explorador().abrirItem(zip_["caminho"])            # duplo clique
    for _ in range(50):
        QTest.qWait(100)
        if (Path(pasta) / "Pacote").is_dir() and not modulo_explorador()._tarefa["ativa"]:
            break
    if not (Path(pasta) / "Pacote" / "dentro" / "b.txt").is_file():
        falhar("abrir o .zip não descompactou ao lado")
    QTest.qWait(300)
    if list(selecao(janela)) != [str(Path(pasta) / "Pacote")]:
        falhar(f"a pasta descompactada não ficou selecionada: {selecao(janela)}")
    print("SELECAO-OK", flush=True)
    os._exit(0)


def conferir_area():
    app = QGuiApplication.instance()
    QTest.qWait(600)
    janela = app.topLevelWindows()[0]
    itens = list(descendentes(janela.contentItem()))
    conteudo = next(i for i in itens if i.property("renomeando") is not None and i.property("nomeTela") is not None)
    icones = sorted([i for i in itens if i.property("sel") is not None and i.property("modelData") is not None],
                    key=lambda i: i.mapToScene(QPointF(0, 0)).y())
    coluna = [i for i in icones if abs(i.mapToScene(QPointF(0, 0)).x() - icones[0].mapToScene(QPointF(0, 0)).x()) < 2]
    if len(coluna) < 3:
        falhar(f"a demonstração tem só {len(coluna)} ícones na primeira coluna")
    a, b = coluna[0], coluna[1]
    topo = a.mapToScene(QPointF(0, 0))
    fim = b.mapToScene(QPointF(b.width() / 2, b.height() / 2))
    de = QPoint(int(topo.x() - 30), max(2, int(topo.y() - 4)))
    arrastar(janela, de, fim.toPoint())
    marcados = sorted(selecao(conteudo))
    esperados = sorted([a.property("modelData")["caminho"], b.property("modelData")["caminho"]])
    if marcados != esperados:
        falhar(f"o retângulo na Área de Trabalho selecionou {marcados} (esperado {esperados})")
    QTest.mouseClick(janela, Qt.LeftButton, Qt.NoModifier, de)
    QTest.qWait(80)
    if selecao(conteudo):
        falhar("o clique no vazio da Área de Trabalho não limpou a seleção")
    print("SELECAO-OK", flush=True)
    os._exit(0)


_instancia = {}


def modulo_explorador():
    return _instancia["explorador"]


if modo == "explorador":
    _Explorador = modulo.Explorador

    class ExploradorParaTeste(_Explorador):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            _instancia["explorador"] = self

    modulo.Explorador = ExploradorParaTeste
    modulo.QGuiApplication.exec = staticmethod(conferir_explorador)
else:
    modulo.QGuiApplication.exec = staticmethod(conferir_area)
modulo.main()
