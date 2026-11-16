"""DuiaOS — roda dentro de "dbus-run-session" para o test_menus.py: abre o Gedit (aplicativo do GNOME,
sem barra de menus, com o botão ☰) num X virtual e confere, pelo mesmo leitor da Barra, que o menu do ☰
vira o menu "Menu", que um item abre uma janela e que a página interna "View/Exibir" vira submenu depois
de usada uma vez (ADR 061). Imprime um JSON com o resultado."""
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

leitor_fd, escritor_fd = os.pipe()
xvfb = subprocess.Popen(["Xvfb", "-displayfd", str(escritor_fd), "-screen", "0", "1024x700x24"], pass_fds=(escritor_fd,),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.close(escritor_fd)
os.environ.update({"DISPLAY": ":" + os.read(leitor_fd, 16).decode().strip(), "LANGUAGE": "en", "LC_ALL": "C.UTF-8"})
subprocess.run(["dbus-send", "--session", "--print-reply", "--dest=org.a11y.Bus", "/org/a11y/bus",
                "org.freedesktop.DBus.Properties.Set", "string:org.a11y.Status", "string:IsEnabled", "variant:boolean:true"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
app = subprocess.Popen(["gedit", "--new-window"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

resultado, pronto = {}, threading.Event()
leitor = menus.ProcessoDeMenus(lambda a, t: (resultado.__setitem__("titulos", t), pronto.set()),
                               lambda i, itens: (resultado.setdefault("leituras", []).append(itens), pronto.set()))


def esperar():
    pronto.wait(10)
    pronto.clear()


def janelas_do_gedit():
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    mesa = Atspi.get_desktop(0)
    for i in range(mesa.get_child_count()):
        a = mesa.get_child_at_index(i)
        if a is not None and (a.get_name() or "") == "gedit":
            return a.get_child_count()
    return 0


for _ in range(60):
    leitor.foco("org.gnome.gedit", "Untitled Document 1 - gedit")
    esperar()
    if resultado.get("titulos"):
        break
    time.sleep(0.25)
leitor.itens(0)
esperar()
primeira = resultado.get("leituras", [[]])[-1]
por_nome = {i["rotulo"]: i for i in primeira}
import gi  # noqa: E402
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402
Atspi.init()
antes = janelas_do_gedit()
if "Keyboard Shortcuts" in por_nome:
    leitor.acionar(por_nome["Keyboard Shortcuts"]["id"])
    for _ in range(40):
        time.sleep(0.1)
        if janelas_do_gedit() > antes:
            break
resultado["abriu_janela"] = janelas_do_gedit() > antes
if "View" in por_nome:
    leitor.acionar(por_nome["View"]["id"])              # 1ª vez: aprende a página interna
    time.sleep(1)
leitor.itens(0)
esperar()
resultado["segunda"] = resultado.get("leituras", [[]])[-1]
print("RESULTADO " + json.dumps(resultado, ensure_ascii=False), flush=True)
leitor.parar()
app.terminate()
xvfb.terminate()
