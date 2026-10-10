#!/usr/bin/env python3
"""DuiaOS — Barra de Recursos (relógio, Wi-Fi, volume e bateria).

A interface fica em BarraDeRecursos.qml; este arquivo inicia o Qt e fornece
ao QML as informações do sistema e a posição escolhida pelo usuário.

Uso:
  main.py                     inicia a Barra de Recursos
  main.py --posicao LUGAR     muda a posição: topo, base, esquerda ou direita
                              (a barra em execução se move na hora)
"""
import configparser
import glob
import os
import subprocess
import sys
from pathlib import Path

POSICOES = ("topo", "base", "esquerda", "direita")
PASTA_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos"
ARQUIVO_CONFIG = PASTA_CONFIG / "barra-de-recursos.conf"


def ler_posicao():
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    posicao = config.get("barra", "posicao", fallback="topo").strip().lower()
    return posicao if posicao in POSICOES else "topo"


def gravar_posicao(posicao):
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    if not config.has_section("barra"):
        config.add_section("barra")
    config.set("barra", "posicao", posicao)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Barra de Recursos. posicao: topo, base, esquerda ou direita\n")
        config.write(arquivo)


# Comando para mudar a posição, sem abrir a barra
if len(sys.argv) == 3 and sys.argv[1] == "--posicao":
    if sys.argv[2] not in POSICOES:
        sys.exit("Posição inválida. Use: " + ", ".join(POSICOES))
    gravar_posicao(sys.argv[2])
    print("Barra de Recursos: posição alterada para", sys.argv[2])
    sys.exit(0)

# A barra é uma "camada" do Wayland presa à borda da tela (layer-shell).
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QTimer, Signal  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402


def executar(*comando):
    """Roda um comando e devolve a saída como texto ('' se falhar)."""
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=2, check=False
        )
        return resultado.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


class Configuracao(QObject):
    """Preferências da Barra de Recursos, recarregadas quando o arquivo muda."""

    mudou = Signal()

    def __init__(self):
        super().__init__()
        if not ARQUIVO_CONFIG.exists():
            gravar_posicao("topo")
        self._posicao = ler_posicao()
        # Vigia a pasta (editores e o --posicao recriam o arquivo)
        self._vigia = QFileSystemWatcher([str(PASTA_CONFIG), str(ARQUIVO_CONFIG)], self)
        self._vigia.directoryChanged.connect(self.recarregar)
        self._vigia.fileChanged.connect(self.recarregar)

    def recarregar(self, _caminho=None):
        if str(ARQUIVO_CONFIG) not in self._vigia.files() and ARQUIVO_CONFIG.exists():
            self._vigia.addPath(str(ARQUIVO_CONFIG))
        posicao = ler_posicao()
        if posicao != self._posicao:
            self._posicao = posicao
            self.mudou.emit()

    posicao = Property(str, lambda self: self._posicao, notify=mudou)


class Sistema(QObject):
    """Estado do sistema exibido na barra."""

    mudou = Signal()

    def __init__(self):
        super().__init__()
        self._wifi = ""
        self._volume = -1
        self._mudo = False
        self._bateria = -1
        self._carregando = False
        self._timer = QTimer(self, interval=5000, timeout=self.atualizar)
        self._timer.start()
        self.atualizar()

    def atualizar(self):
        # Wi-Fi: nome da rede conectada
        wifi = ""
        for linha in executar("nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device").splitlines():
            partes = linha.split(":", 2)
            if len(partes) == 3 and partes[0] == "wifi" and partes[1] == "connected":
                wifi = partes[2]
                break

        # Volume: "Volume: 0.80" ou "Volume: 0.80 [MUTED]"
        volume, mudo = -1, False
        saida = executar("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")
        if saida.startswith("Volume:"):
            try:
                volume = round(float(saida.split()[1]) * 100)
            except (IndexError, ValueError):
                volume = -1
            mudo = "MUTED" in saida

        # Bateria: /sys/class/power_supply/BAT*/
        bateria, carregando = -1, False
        for pasta in sorted(glob.glob("/sys/class/power_supply/BAT*")):
            try:
                bateria = int(Path(pasta, "capacity").read_text().strip())
                carregando = Path(pasta, "status").read_text().strip() in ("Charging", "Full")
            except (OSError, ValueError):
                continue
            break

        self._wifi, self._volume, self._mudo = wifi, volume, mudo
        self._bateria, self._carregando = bateria, carregando
        self.mudou.emit()

    wifi = Property(str, lambda self: self._wifi, notify=mudou)
    volume = Property(int, lambda self: self._volume, notify=mudou)
    mudo = Property(bool, lambda self: self._mudo, notify=mudou)
    bateria = Property(int, lambda self: self._bateria, notify=mudou)
    carregando = Property(bool, lambda self: self._carregando, notify=mudou)


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("duiaos-barra-de-recursos")

    configuracao = Configuracao()
    sistema = Sistema()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("configuracao", configuracao)
    engine.rootContext().setContextProperty("sistema", sistema)
    engine.load(Path(__file__).with_name("BarraDeRecursos.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
