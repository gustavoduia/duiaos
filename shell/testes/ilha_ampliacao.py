"""Auxiliar do test_ilha.py: abre a demonstração da Ilha, passa o mouse por cima e confere que a
ampliação é estável (o foco não muda com o mouse parado) e que nenhuma imagem é refeita por causa
da ampliação (era o que fazia os ícones piscarem). Imprime AMPLIACAO-OK ou os problemas.

Uso: python3 ilha_ampliacao.py CAMINHO/shell/ilha-de-aplicativos/main.py
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

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlEngine, QQmlExpression  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def imagens(item):
    achadas = []
    for filho in item.childItems():
        if filho.inherits("QQuickImage") and filho.property("source").toString():
            achadas.append(filho)
        achadas += imagens(filho)
    return achadas


def pronta(imagem):
    """Image.Ready? (o PySide6 não converte o enum "status"; a expressão QML devolve o número)"""
    valor, _ = QQmlExpression(QQmlEngine.contextForObject(imagem), imagem, "status === 1").evaluate()
    return bool(valor)


def conferir():
    app = QGuiApplication.instance()
    problemas = []
    for _ in range(40):
        app.processEvents()
        QTest.qWait(10)
    janela = next(j for j in app.topLevelWindows() if j.property("posicao") is not None)
    ilha = next(f for f in janela.contentItem().childItems() if isinstance(f, QQuickItem) and f.property("raioAmpliacao"))
    antes = [(i.property("source").toString(), i.property("sourceSize")) for i in imagens(ilha)]
    if len(antes) < 8:
        problemas.append(f"poucas imagens na Ilha: {len(antes)}")

    base, maximo = ilha.property("base"), ilha.property("maximo")
    if maximo <= base:
        problemas.append("a demonstração está sem ampliação")
    y = int(ilha.y() + ilha.height() - base / 2 - 11)
    centro = int(ilha.x() + ilha.width() / 2)
    maior = 0.0
    for dx in (-150, -97, -41, 0, 13, 58, 131):
        QTest.mouseMove(janela, QPoint(centro + dx, y))
        focos, estados = [], []
        for _ in range(30):                       # o mouse fica parado enquanto a onda se forma
            app.processEvents()
            QTest.qWait(10)
            focos.append(round(ilha.property("foco"), 4))
            estados += [pronta(i) for i in imagens(ilha)]
        if len(set(focos)) != 1:
            problemas.append(f"com o mouse parado em {dx}, o foco variou: {sorted(set(focos))}")
        if not all(estados):
            problemas.append(f"com o mouse em {dx}, alguma imagem foi recarregada (o ícone pisca)")
        maior = max(maior, max(i.width() for i in imagens(ilha)))
    if maior < base + (maximo - base) * 0.3:
        problemas.append(f"os ícones não cresceram com o mouse em cima (maior: {maior})")
    if ilha.property("forca") < 0.99:
        problemas.append("a ampliação não entrou com o mouse sobre a Ilha")
    depois = [(i.property("source").toString(), i.property("sourceSize")) for i in imagens(ilha)]
    if antes != depois:
        problemas.append("a ampliação mudou o tamanho com que as imagens são geradas")
    print("\n".join(problemas) if problemas else "AMPLIACAO-OK", flush=True)
    os._exit(1 if problemas else 0)


modulo.QGuiApplication.exec = staticmethod(conferir)
modulo.main()
