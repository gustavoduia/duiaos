# DuiaOS — aplicativo Qt de teste para o leitor de menus (test_menus.py): imprime ACIONADO <item>.
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PySide6.QtGui import QAction, QKeySequence
app = QApplication(sys.argv); w = QMainWindow(); w.setWindowTitle("Editor Qt de teste"); w.setCentralWidget(QTextEdit())
def acao(menu, nome, tecla=None, ativo=True, marcavel=False, marcado=False):
    a = QAction(nome, w); a.setEnabled(ativo)
    if tecla: a.setShortcut(QKeySequence(tecla))
    if marcavel: a.setCheckable(True); a.setChecked(marcado)
    a.triggered.connect(lambda *_: print("ACIONADO", nome.replace("&", ""), flush=True)); menu.addAction(a); return a
arq = w.menuBar().addMenu("&Arquivo"); acao(arq, "&Novo", "Ctrl+N"); acao(arq, "&Salvar", "Ctrl+S")
rec = arq.addMenu("&Recentes"); acao(rec, "plano.odt"); arq.addSeparator(); acao(arq, "Sai&r", "Ctrl+Q")
ed = w.menuBar().addMenu("&Editar"); acao(ed, "&Desfazer", "Ctrl+Z", ativo=False); acao(ed, "&Copiar", "Ctrl+C")
inv = acao(ed, "Invisível"); inv.setVisible(False)
ex = w.menuBar().addMenu("E&xibir"); acao(ex, "&Barra de status", marcavel=True, marcado=True)
w.resize(500, 300); w.show(); w.activateWindow(); sys.exit(app.exec())
