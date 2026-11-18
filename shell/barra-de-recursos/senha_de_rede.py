#!/usr/bin/env python3
"""DuiaOS — janela "Senha da rede" (ADR 070), aberta pelo agente de senhas (shell/comum/agente_de_senhas.py).

Recebe o pedido em JSON pela entrada padrão ({titulo, texto, campos:[{chave, rotulo, senha}], lembrar}) e
escreve a resposta em JSON na saída ({valores, lembrar}). Cancelar (ou fechar) termina com código 1.
É uma janela comum (não um painel da Barra), para a pessoa poder alternar para ela e digitar.

Uso: echo '{...}' | senha_de_rede.py        ·   senha_de_rede.py --demonstracao [--captura ARQUIVO]
"""
import json
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))

DEMONSTRACAO = "--demonstracao" in sys.argv
EXEMPLO = {"titulo": "Entrar na rede", "texto": "A rede “eduroam” pede usuário e senha (rede corporativa ou da faculdade).",
           "campos": [{"chave": "identity", "rotulo": "Usuário", "senha": False}, {"chave": "password", "rotulo": "Senha", "senha": True}],
           "lembrar": True}


def main():
    captura = sys.argv[sys.argv.index("--captura") + 1] if "--captura" in sys.argv else ""
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    dados = EXEMPLO if DEMONSTRACAO else json.loads(sys.stdin.read() or "{}")
    from PySide6.QtCore import QObject, Slot
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import interface
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Senha da rede")
    app.setDesktopFileName("duiaos-senha-de-rede")
    interface.ligar_registro("duiaos-senha-de-rede")

    class Resposta(QObject):
        @Slot("QVariantMap", bool)
        def confirmar(self, valores, lembrar):
            print(json.dumps({"valores": dict(valores), "lembrar": bool(lembrar)}), flush=True)
            app.exit(0)

        @Slot()
        def cancelar(self):
            app.exit(1)

    resposta = Resposta()
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    engine.rootContext().setContextProperty("pedido", dados)
    engine.rootContext().setContextProperty("resposta", resposta)
    engine.rootContext().setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / "SenhaDeRede.qml")
    if not engine.rootObjects():
        sys.exit(2)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
