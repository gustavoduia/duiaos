"""DuiaOS — roda dentro de "dbus-run-session" para o test_menus.py: um X virtual, o AT-SPI ligado, um
aplicativo de teste (GTK ou Qt, o argumento) e o leitor de menus da Barra. Imprime um JSON com o
que leu e o que o aplicativo disse ao ser acionado."""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parents[1] / "barra-de-recursos"))
import menus  # noqa: E402

qual = sys.argv[1]
leitor_fd, escritor_fd = os.pipe()
xvfb = subprocess.Popen(["Xvfb", "-displayfd", str(escritor_fd), "-screen", "0", "1024x700x24"], pass_fds=(escritor_fd,),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.close(escritor_fd)
numero = os.read(leitor_fd, 16).decode().strip()
os.environ.update({"DISPLAY": ":" + numero, "QT_QPA_PLATFORM": "xcb", "QT_LINUX_ACCESSIBILITY_ALWAYS_ON": "1"})
subprocess.run(["dbus-send", "--session", "--print-reply", "--dest=org.a11y.Bus", "/org/a11y/bus",
                "org.freedesktop.DBus.Properties.Set", "string:org.a11y.Status", "string:IsEnabled", "variant:boolean:true"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
app = subprocess.Popen([sys.executable, str(PASTA / f"app_{qual}.py")], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
saida = []
threading.Thread(target=lambda: saida.extend(app.stdout), daemon=True).start()

resultado, pronto = {}, threading.Event()
# O mesmo caminho da Barra: o leitor num processo à parte
leitor = menus.ProcessoDeMenus(lambda a, t: (resultado.__setitem__("titulos", t), pronto.set()),
                               lambda i, itens: (resultado.setdefault("itens", {}).__setitem__(i, itens), pronto.set()))


def esperar():
    pronto.wait(8)
    pronto.clear()


# O aplicativo leva um instante para abrir e se descrever
for _ in range(40):
    leitor.foco(f"app_{qual}")
    esperar()
    if resultado.get("titulos"):
        break
    time.sleep(0.25)
for indice in range(len(resultado.get("titulos", []))):
    leitor.itens(indice)
    esperar()
# Aciona "Novo" (Arquivo) e o primeiro item do submenu Recentes
arquivo = resultado.get("itens", {}).get(0, [])
for item in arquivo:
    if item["rotulo"] == "Novo":
        leitor.acionar(item["id"])
    if item["tipo"] == "submenu" and item["itens"]:
        leitor.acionar(item["itens"][0]["id"])
for _ in range(40):                                  # espera o aplicativo dizer que foi acionado
    if len(saida) >= 2:
        break
    time.sleep(0.1)
resultado["saida"] = [linha.strip() for linha in saida]
print("RESULTADO " + json.dumps(resultado, ensure_ascii=False), flush=True)
leitor.parar()
app.terminate()
xvfb.terminate()
