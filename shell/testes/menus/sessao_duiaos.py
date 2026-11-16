"""DuiaOS — roda dentro de "dbus-run-session" para o test_menu_do_app.py: abre um aplicativo do DuiaOS
(argumento: explorador, configuracoes ou loja), lê os menus dele como a Barra lê (menu_do_app.py) e
aciona um item. Imprime um JSON com os títulos, os menus antes e depois e se o item fez efeito."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "shell" / "comum"))
import menu_do_app  # noqa: E402

qual = sys.argv[1]
inicio = tempfile.mkdtemp()
(Path(inicio) / "Documentos").mkdir()
ambiente = {**os.environ, "HOME": inicio, "XDG_CONFIG_HOME": inicio + "/.config", "XDG_RUNTIME_DIR": inicio,
            "QT_QPA_PLATFORM": "offscreen"}
comandos = {"explorador": ([sys.executable, str(RAIZ / "apps/explorador-de-arquivos/main.py"), inicio], "duiaos-explorador-de-arquivos"),
            "configuracoes": ([sys.executable, str(RAIZ / "apps/configuracoes/main.py"), "--demonstracao"], "duiaos-configuracoes"),
            "loja": ([sys.executable, str(RAIZ / "apps/loja/main.py"), "--demonstracao"], "duiaos-loja")}
comando, app_id = comandos[qual]
processo = subprocess.Popen(comando, env=ambiente, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
nome, menus = "", []
for _ in range(60):
    time.sleep(0.25)
    nome, menus = menu_do_app.ler_da_sessao(app_id)
    if menus:
        break
resultado = {"nome": nome, "titulos": [m["rotulo"] for m in menus], "antes": menus}
acao = {"explorador": "lista", "configuracoes": "secao:som", "loja": "pagina:instalados"}[qual]
resultado["acionou"] = menu_do_app.acionar_na_sessao(nome, acao) if nome else False
time.sleep(1.0)
resultado["depois"] = menu_do_app.ler_da_sessao(app_id)[1]
resultado["recusou_id_falso"] = menu_do_app.acionar_na_sessao(nome, "rm -rf /") if nome else False
processo.terminate()
print("RESULTADO " + json.dumps(resultado, ensure_ascii=False), flush=True)
