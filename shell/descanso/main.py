#!/usr/bin/env python3
"""DuiaOS — Tela de Descanso: depois de alguns minutos sem uso, cobre as telas com uma imagem,
uma imagem com movimento (GIF/WebP), um vídeo ou o papel de parede, com o relógio por cima.
Qualquer tecla ou movimento do mouse volta para onde a pessoa estava (não pede senha: quem
pede é a Tela de Bloqueio, no tempo dela).

Aberta pelo swayidle (comum/sessao.py) e fechada por ele quando a pessoa volta. Escolhas em
Configurações › Tela de Descanso (~/.config/duiaos/preferencias.conf, seção [descanso]).

Uso:
  main.py                         mostra agora (uma por vez)
  main.py --demonstracao [--captura ARQUIVO]
"""
import fcntl
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))
DEMONSTRACAO = "--demonstracao" in sys.argv

if not DEMONSTRACAO:
    _trava = open(os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "duiaos-descanso.lock"), "w")
    try:
        fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(0)
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import interface  # noqa: E402
import pastas  # noqa: E402
import sessao  # noqa: E402


def escolha():
    """(arquivo, cor, relógio): a imagem da Tela de Descanso ou, sem ela, o papel de parede."""
    arquivo = pastas.ler_preferencia("descanso", "arquivo", "")
    if not arquivo or not Path(arquivo).is_file():
        arquivo = pastas.ler_preferencia("papel-de-parede", "arquivo", str(sessao.PAPEL_PADRAO))
        if arquivo and not Path(arquivo).is_file():
            arquivo = ""
    cor = pastas.ler_preferencia("papel-de-parede", "cor", sessao.COR_PADRAO)
    return arquivo, cor, pastas.ler_preferencia("descanso", "relogio", "sim") == "sim"


def main():
    if DEMONSTRACAO and "--captura" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    interface.ligar_registro("duiaos-descanso")
    app.setApplicationName("duiaos-descanso")
    arquivo, cor, relogio = escolha()
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    contexto = engine.rootContext()
    contexto.setContextProperty("arquivoDescanso", arquivo)
    contexto.setContextProperty("corDescanso", cor)
    contexto.setContextProperty("mostrarRelogio", relogio)
    captura = sys.argv[sys.argv.index("--captura") + 1] if "--captura" in sys.argv else ""
    contexto.setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "Descanso.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
