#!/usr/bin/env python3
"""DuiaOS — painel superior (relógio, Wi-Fi, volume e bateria).

A interface fica em Painel.qml; este arquivo inicia o Qt e fornece ao QML
as informações do sistema, atualizadas a cada 5 segundos.
"""
import glob
import os
import subprocess
import sys
from pathlib import Path

# O painel é uma "camada" do Wayland presa à borda da tela (layer-shell).
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QObject, Property, QTimer, Signal  # noqa: E402
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


class Sistema(QObject):
    """Estado do sistema exibido no painel."""

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
    app.setApplicationName("duiaos-painel")

    sistema = Sistema()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("sistema", sistema)
    engine.load(Path(__file__).with_name("Painel.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
