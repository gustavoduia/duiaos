#!/usr/bin/env python3
"""DuiaOS — Notificações: o serviço org.freedesktop.Notifications da sessão e os balões no canto
de cima, à direita. Clique no balão abre o aplicativo (ação padrão); o X fecha; somem sozinhos
depois de alguns segundos (os urgentes ficam até a pessoa fechar).

Com "Não perturbe" ligado (Central de Controle; ~/.config/duiaos/preferencias.conf, seção
[notificacoes]), os balões não aparecem — só as urgentes —, mas tudo vai para o histórico.
O histórico da sessão fica em $XDG_RUNTIME_DIR/duiaos-notificacoes.json e aparece no balão do
relógio da Barra de Recursos.

Uso:
  main.py                                    serviço da sessão (um só)
  main.py --demonstracao [--captura ARQUIVO] balões de exemplo
  main.py --sem-janela                       só o serviço, sem balões (testes)
"""
import json
import os
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))
DEMONSTRACAO = "--demonstracao" in sys.argv
HISTORICO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-notificacoes.json"
LIMITE_HISTORICO = 50
TEMPO_PADRAO = 6000
MAXIMO_NA_TELA = 4

if not DEMONSTRACAO:
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import aplicativos  # noqa: E402
import interface  # noqa: E402
import pastas  # noqa: E402


def nao_perturbe():
    return pastas.ler_preferencia("notificacoes", "nao_perturbe", "nao") == "sim"


def icone_para(dados):
    """(tipo, valor): 'arquivo' para imagem em disco, 'tema' para ícone do tema, ou ('', '')."""
    icone = dados.get("icone", "")
    if icone.startswith("file://"):
        icone = icone[7:]
    if icone.startswith("/"):
        return ("arquivo", "file://" + icone) if Path(icone).is_file() else ("", "")
    if icone:
        app = aplicativos.ler_desktop(icone if icone.endswith(".desktop") else icone + ".desktop")
        return "tema", (app["icone"] if app and app.get("icone") else icone)
    return "", ""


class Notificacoes(QObject):
    mudou = Signal()
    _chegou = Signal(int, "QVariantMap")
    _fechar = Signal(int)
    _limpar = Signal()
    _remover = Signal(int)

    def __init__(self):
        super().__init__()
        self._visiveis, self._historico, self._timers = [], [], {}
        self.servico = None
        self._chegou.connect(self._ao_chegar)
        self._fechar.connect(lambda i: self._tirar(i))
        self._limpar.connect(self._ao_limpar)
        self._remover.connect(self._ao_remover)

    def ligar(self):
        import servico
        self.servico = servico.Servico(self._chegou.emit, self._fechar.emit, self._limpar.emit, self._remover.emit)
        if not self.servico.iniciar():
            print("Notificações:", self.servico.erro, file=sys.stderr)
            return False
        self._gravar()
        return True

    # ------------------------------------------------------------ chegada
    def _ao_chegar(self, identificador, dados):
        tipo, valor = icone_para(dados)
        item = {**dados, "id": identificador, "tipoIcone": tipo, "valorIcone": valor,
                "quando": time.strftime("%H:%M")}
        self._historico = [h for h in self._historico if h["id"] != identificador]
        self._historico.insert(0, item)
        del self._historico[LIMITE_HISTORICO:]
        self._gravar()
        if nao_perturbe() and item["urgencia"] < 2:
            self.mudou.emit()
            return
        self._visiveis = [v for v in self._visiveis if v["id"] != identificador]
        self._visiveis.insert(0, item)
        for sobrando in self._visiveis[MAXIMO_NA_TELA:]:
            self._tirar(sobrando["id"])
        self._visiveis = self._visiveis[:MAXIMO_NA_TELA]
        tempo = item["tempo"] if item["tempo"] > 0 else TEMPO_PADRAO
        if item["urgencia"] < 2 and item["tempo"] != 0 or item["tempo"] > 0:
            timer = self._timers.pop(identificador, None)
            if timer:
                timer.stop()
            timer = QTimer(self, singleShot=True, interval=tempo)
            timer.timeout.connect(lambda i=identificador: self._vencer(i))
            timer.start()
            self._timers[identificador] = timer
        self.mudou.emit()

    def _vencer(self, identificador):
        self._tirar(identificador)
        if self.servico:
            self.servico.fechada(identificador, 1)

    def _tirar(self, identificador):
        timer = self._timers.pop(identificador, None)
        if timer:
            timer.stop()
        antes = len(self._visiveis)
        self._visiveis = [v for v in self._visiveis if v["id"] != identificador]
        if len(self._visiveis) != antes:
            self.mudou.emit()

    def _ao_limpar(self):
        self._historico = []
        self._gravar()

    def _ao_remover(self, identificador):
        self._historico = [h for h in self._historico if h["id"] != identificador]
        self._gravar()

    def _gravar(self):
        if DEMONSTRACAO:
            return
        try:
            temporario = HISTORICO.with_suffix(".tmp")
            temporario.write_text(json.dumps(self._historico, ensure_ascii=False), encoding="utf-8")
            os.replace(temporario, HISTORICO)
        except OSError:
            pass

    # -------------------------------------------------------- da interface
    @Slot(int)
    def fechar(self, identificador):
        self._tirar(identificador)
        if self.servico:
            self.servico.fechada(identificador, 2)

    @Slot(int)
    def clicar(self, identificador):
        item = next((v for v in self._visiveis if v["id"] == identificador), None)
        if item and item.get("temPadrao") and self.servico:
            self.servico.acao(identificador, "default")
        self.fechar(identificador)

    @Slot(int, str)
    def acionar(self, identificador, chave):
        if self.servico:
            self.servico.acao(identificador, chave)
        self.fechar(identificador)

    visiveis = Property("QVariantList", lambda self: self._visiveis, notify=mudou)

    def demonstracao(self):
        exemplos = [
            {"app": "Wise", "icone": "", "titulo": "Sua agenda de amanhã", "texto": "Reunião com a equipe às 9h e dentista às 15h.",
             "acoes": [{"chave": "abrir", "rotulo": "Ver agenda"}], "temPadrao": True, "urgencia": 1, "tempo": -1},
            {"app": "Explorador de Arquivos", "icone": "", "titulo": "Cópia concluída", "texto": "12 itens copiados para Documentos.",
             "acoes": [], "temPadrao": False, "urgencia": 1, "tempo": -1},
            {"app": "Atualizações", "icone": "", "titulo": "Sistema atualizado", "texto": "Reinicie quando puder para terminar.",
             "acoes": [{"chave": "reiniciar", "rotulo": "Reiniciar"}], "temPadrao": False, "urgencia": 2, "tempo": 0},
        ]
        self._visiveis = [{**e, "id": n + 1, "tipoIcone": "", "valorIcone": "", "quando": "12:4" + str(n)} for n, e in enumerate(exemplos)]
        self.mudou.emit()


def main():
    captura = sys.argv[sys.argv.index("--captura") + 1] if "--captura" in sys.argv else ""
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    interface.ligar_registro("duiaos-notificacoes")
    os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)
    app.setApplicationName("duiaos-notificacoes")
    notificacoes = Notificacoes()
    if DEMONSTRACAO:
        notificacoes.demonstracao()
    elif not notificacoes.ligar():
        sys.exit(1)
    if "--sem-janela" in sys.argv:
        sys.exit(app.exec())
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    engine.rootContext().setContextProperty("notificacoes", notificacoes)
    engine.rootContext().setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "Notificacoes.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
