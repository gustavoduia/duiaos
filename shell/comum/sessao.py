#!/usr/bin/env python3
"""DuiaOS — aplica as escolhas das Configurações na sessão (modo escuro, telas, luz noturna,
Tela de Descanso e bloqueio automático; o papel de parede é da Área de Trabalho).

Chamado por sessao/autostart ao entrar e pelas Configurações quando algo muda:
  sessao.py aplicar                  tudo (início da sessão)
  sessao.py aparencia                modo claro ou escuro nas janelas e nos aplicativos GTK
  sessao.py papel-de-parede          papel de parede pelo swaybg (reserva, sem a Área de Trabalho)
  sessao.py telas                    só resolução e escala
  sessao.py bloqueio                 só o bloqueio automático e o repouso
As preferências ficam em ~/.config/duiaos/preferencias.conf (pastas.py).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pastas  # noqa: E402

PASTA_SHELL = Path(os.environ.get("DUIAOS_SHELL", Path(__file__).resolve().parents[1]))
PAPEIS_DO_SISTEMA = Path("/usr/share/duiaos/papel-de-parede")
PAPEL_PADRAO = PAPEIS_DO_SISTEMA / "paisagem.jpg"
COR_PADRAO = "#E8F0FE"
BLOQUEIO_PADRAO = 10          # minutos
EXTENSOES_DE_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")


def _iniciar(comando):
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def _rodar(*comando):
    """Roda e espera, sem falhar se o programa não existir."""
    try:
        subprocess.run(comando, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _parar(programa):
    _rodar("pkill", "-u", str(os.getuid()), "-x", programa)


# ------------------------------------------------------------ papel de parede

def papeis_do_sistema(pasta=PAPEIS_DO_SISTEMA):
    try:
        return sorted(str(p) for p in Path(pasta).iterdir() if p.suffix.lower() in EXTENSOES_DE_IMAGEM)
    except OSError:
        return []


def comando_papel(arquivo, cor):
    """swaybg com a imagem escolhida (que exista) ou, sem ela, com a cor."""
    if arquivo and Path(arquivo).is_file():
        return ["swaybg", "-i", arquivo, "-m", "fill"]
    if not re.match(r"^#[0-9A-Fa-f]{6}$", cor or ""):
        cor = COR_PADRAO
    return ["swaybg", "-c", cor]


def aplicar_papel_de_parede():
    arquivo = pastas.ler_preferencia("papel-de-parede", "arquivo", str(PAPEL_PADRAO))
    cor = pastas.ler_preferencia("papel-de-parede", "cor", COR_PADRAO)
    _parar("swaybg")
    _iniciar(comando_papel(arquivo, cor))


# --------------------------------------------------------------------- telas

def interpretar_wlr_randr(saida):
    """Texto do 'wlr-randr' → [{'nome', 'descricao', 'ligada', 'modos': [...], 'modo', 'escala'}]."""
    telas, atual, em_modos = [], None, False
    for linha in saida.splitlines():
        if linha and not linha.startswith(" "):
            nome, _, descricao = linha.partition(" ")
            atual = {"nome": nome, "descricao": descricao.strip().strip('"'), "ligada": True,
                     "modos": [], "modo": "", "escala": 1.0}
            telas.append(atual)
            em_modos = False
            continue
        if atual is None:
            continue
        texto = linha.strip()
        if texto.startswith("Modes:"):
            em_modos = True
            continue
        modo = re.match(r"^(\d+)x(\d+) px, ([\d.]+) Hz(.*)$", texto)
        if em_modos and modo:
            valor = f"{modo.group(1)}x{modo.group(2)}@{float(modo.group(3)):.3f}"
            rotulo = f"{modo.group(1)} × {modo.group(2)} ({round(float(modo.group(3)))} Hz)"
            item = {"valor": valor, "rotulo": rotulo, "preferido": "preferred" in modo.group(4)}
            if not any(m["rotulo"] == rotulo for m in atual["modos"]):
                atual["modos"].append(item)
            if "current" in modo.group(4):
                atual["modo"] = valor
            continue
        em_modos = False if ":" in texto and not modo else em_modos
        if texto.startswith("Enabled:"):
            atual["ligada"] = texto.split(":", 1)[1].strip() == "yes"
        elif texto.startswith("Scale:"):
            try:
                atual["escala"] = round(float(texto.split(":", 1)[1]), 2)
            except ValueError:
                pass
    return telas


def comando_tela(nome, modo=None, escala=None):
    comando = ["wlr-randr", "--output", nome]
    if modo:
        comando += ["--mode", modo]
    if escala:
        comando += ["--scale", f"{float(escala):g}"]
    return comando


def aplicar_telas():
    """Reaplica a resolução e a escala guardadas para cada tela que estiver conectada."""
    try:
        saida = subprocess.run(["wlr-randr"], capture_output=True, text=True, check=False, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return
    for tela in interpretar_wlr_randr(saida):
        modo = pastas.ler_preferencia("telas", tela["nome"] + ".modo", "")
        escala = pastas.ler_preferencia("telas", tela["nome"] + ".escala", "")
        if modo or escala:
            _rodar(*comando_tela(tela["nome"], modo or None, escala or None))


# ------------------------------------------------------------ modo escuro

# Cores escuras das janelas (labwc lê este arquivo por cima do tema DuiaOS)
TEMA_ESCURO = """# DuiaOS — modo escuro das janelas (Configurações › Aparência). Gerado; apagado no modo claro.
window.active.border.color: #4A5363
window.inactive.border.color: #353B46
window.active.title.bg.color: #2A2F39
window.inactive.title.bg.color: #22262E
window.active.title.separator.color: #353B46
window.inactive.title.separator.color: #2A2F39
window.active.label.text.color: #E6EAF0
window.inactive.label.text.color: #7A8494
window.active.button.unpressed.image.color: #A3ADBB
window.inactive.button.unpressed.image.color: #7A8494
window.active.shadow.color: #00000070
window.inactive.shadow.color: #00000040
menu.border.color: #353B46
menu.items.bg.color: #262B34
menu.items.text.color: #E6EAF0
menu.items.active.bg.color: #2E6BE6
menu.items.active.text.color: #FFFFFF
menu.separator.color: #353B46
menu.title.bg.color: #1B1F27
menu.title.text.color: #A3ADBB
osd.bg.color: #262B34
osd.border.color: #353B46
osd.label.text.color: #E6EAF0
"""


# Estilo futurista (Aurora, ADR 052): janelas em azul-noite profundo ou pérola, com borda luminosa
_CABECALHO_FUTURISTA = "# DuiaOS — estilo futurista das janelas (Configurações › Aparência). Gerado.\n"
_FUTURISTA = {
    True: {"borda": "#3D4F8F", "borda_inativa": "#232C4D", "titulo": "#121933", "titulo_inativo": "#0E1428",
           "texto": "#EEF2FF", "texto_inativo": "#6C7AA6", "botao": "#9AA6C7", "menu": "#141A2E", "menu_texto": "#EEF2FF",
           "ativo": "#5B8CFF", "sombra": "#05081680"},
    False: {"borda": "#B9C4EE", "borda_inativa": "#D9DFF0", "titulo": "#F7F8FF", "titulo_inativo": "#EEF0FA",
            "texto": "#0E1430", "texto_inativo": "#8089A8", "botao": "#5A6690", "menu": "#FFFFFF", "menu_texto": "#0E1430",
            "ativo": "#3D5BFF", "sombra": "#1B2A6B40"},
}


def tema_das_janelas(escuro, futurista):
    """Texto do themerc-override do labwc para o modo e o estilo ("" = o tema DuiaOS sem mudanças)."""
    if not futurista:
        return TEMA_ESCURO if escuro else ""
    c = _FUTURISTA[bool(escuro)]
    return _CABECALHO_FUTURISTA + f"""window.active.border.color: {c['borda']}
window.inactive.border.color: {c['borda_inativa']}
window.active.title.bg.color: {c['titulo']}
window.inactive.title.bg.color: {c['titulo_inativo']}
window.active.title.separator.color: {c['titulo']}
window.inactive.title.separator.color: {c['titulo_inativo']}
window.active.label.text.color: {c['texto']}
window.inactive.label.text.color: {c['texto_inativo']}
window.active.button.unpressed.image.color: {c['botao']}
window.inactive.button.unpressed.image.color: {c['texto_inativo']}
window.active.shadow.color: {c['sombra']}
window.inactive.shadow.color: {c['sombra'][:7]}30
menu.border.color: {c['borda']}
menu.items.bg.color: {c['menu']}
menu.items.text.color: {c['menu_texto']}
menu.items.active.bg.color: {c['ativo']}
menu.items.active.text.color: #FFFFFF
menu.separator.color: {c['borda_inativa']}
menu.title.bg.color: {c['titulo']}
menu.title.text.color: {c['texto_inativo']}
osd.bg.color: {c['menu']}
osd.border.color: {c['borda']}
osd.label.text.color: {c['menu_texto']}
"""


def atualizar_modo_automatico(agora=None):
    """Modo Automático (ADR 056): claro de dia, escuro à noite, pelo nascer e pôr do sol (sol.py).
    A escolha fica em [aparencia] automatico = sim; o modo em vigor continua em "modo" (claro ou
    escuro), que é o que todos os programas leem. Devolve True se o modo mudou agora."""
    if pastas.ler_preferencia("aparencia", "automatico", "nao") != "sim":
        return False
    import sol
    certo = "escuro" if sol.e_noite(agora) else "claro"
    if pastas.ler_preferencia("aparencia", "modo", "claro") == certo:
        return False
    pastas.gravar_preferencia("aparencia", "modo", certo)
    return True


# Botões dos aplicativos que desenham a própria barra de título (Chrome, Firefox, aplicativos GNOME):
# os mesmos da barra do DuiaOS, à direita — expandir, minimizar e, no canto, fechar (ADR 054 e 058).
# O padrão do GNOME é "appmenu:close": só o botão de fechar.
BOTOES_GTK = ":maximize,minimize,close"

# Navegadores feitos sobre o Chromium: "browser.custom_chrome_frame" falso = "Usar a barra de título e as
# bordas do sistema", ou seja, a barra do DuiaOS (bolinhas azuis), em vez da barra própria.
NAVEGADORES_CHROMIUM = {
    "google-chrome": ("google-chrome", "google-chrome-stable"), "google-chrome-beta": ("google-chrome-beta",),
    "chromium": ("chromium", "chromium-browser"), "BraveSoftware/Brave-Browser": ("brave-browser", "brave"),
    "microsoft-edge": ("microsoft-edge", "microsoft-edge-stable"), "vivaldi": ("vivaldi", "vivaldi-stable"),
}


def barra_do_sistema_nos_navegadores(configuracao=None, instalado=None):
    """Liga a barra de título do sistema nos navegadores Chromium instalados, perfil por perfil. Não mexe
    num navegador aberto (ele regravaria o arquivo ao fechar): fica para a próxima entrada na sessão.
    Navegador instalado e nunca aberto: o arquivo de preferências já nasce com a opção. Devolve os
    arquivos que mudaram."""
    import json
    import shutil
    configuracao = Path(configuracao or pastas.CONFIG)
    instalado = instalado or (lambda nomes: any(shutil.which(n) for n in nomes))
    mudados = []
    for pasta, programas in NAVEGADORES_CHROMIUM.items():
        dados = configuracao / pasta
        if not instalado(programas):
            continue
        if dados.joinpath("SingletonLock").is_symlink() or dados.joinpath("SingletonLock").exists():
            continue                                   # aberto agora
        perfis = [p for p in dados.glob("*/Preferences") if p.parent.name == "Default" or p.parent.name.startswith("Profile ")]
        if not perfis:
            perfis = [dados / "Default" / "Preferences"]
        for arquivo in perfis:
            try:
                atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.is_file() else {}
                if not isinstance(atual, dict):
                    continue
                navegador = atual.setdefault("browser", {})
                if not isinstance(navegador, dict) or navegador.get("custom_chrome_frame") is False:
                    continue
                navegador["custom_chrome_frame"] = False
                arquivo.parent.mkdir(parents=True, exist_ok=True)
                temporario = arquivo.with_name("Preferences.duiaos-tmp")
                temporario.write_text(json.dumps(atual, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                os.replace(temporario, arquivo)
                mudados.append(arquivo)
            except (OSError, ValueError):
                continue
    return mudados


def aplicar_aparencia(escuro=None):
    """Modo escuro e estilo nas janelas (labwc) e nos aplicativos GTK; os do DuiaOS mudam sozinhos."""
    if escuro is None:
        escuro = pastas.ler_preferencia("aparencia", "modo", "claro") == "escuro"
    futurista = pastas.estilo_da_interface() == "futurista"
    override = pastas.CONFIG / "labwc" / "themerc-override"
    try:
        texto = tema_das_janelas(escuro, futurista)
        if texto:
            override.parent.mkdir(parents=True, exist_ok=True)
            override.write_text(texto, encoding="utf-8")
        elif override.is_file() and override.read_text(encoding="utf-8").startswith("# DuiaOS — "):
            override.unlink()                    # só apaga o que o DuiaOS gerou
    except OSError:
        pass
    for versao in ("gtk-3.0", "gtk-4.0"):
        arquivo = pastas.CONFIG / versao / "settings.ini"
        try:
            linhas = arquivo.read_text(encoding="utf-8").splitlines() if arquivo.is_file() else ["[Settings]"]
            linhas = [l for l in linhas if not l.startswith(("gtk-application-prefer-dark-theme", "gtk-decoration-layout"))]
            if "[Settings]" not in linhas:
                linhas.insert(0, "[Settings]")
            linhas.insert(linhas.index("[Settings]") + 1, f"gtk-application-prefer-dark-theme={'1' if escuro else '0'}")
            linhas.insert(linhas.index("[Settings]") + 1, f"gtk-decoration-layout={BOTOES_GTK}")
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        except OSError:
            pass
    _rodar("gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark" if escuro else "default")
    _rodar("gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", BOTOES_GTK)
    _rodar("labwc", "--reconfigure")


# ---------------------------------------------------------------- bloqueio

def comando_swayidle(bloquear_minutos, repousar_minutos, bloquear, descanso_minutos=0, descanso=""):
    """Tela de Descanso, bloqueio automático e repouso (0 = nunca). A tela sempre bloqueia antes de repousar."""
    comando = ["swayidle", "-w"]
    if descanso_minutos > 0 and descanso:
        comando += ["timeout", str(descanso_minutos * 60), descanso, "resume", "pkill -f descanso/main.py"]
    if bloquear_minutos > 0:
        comando += ["timeout", str(bloquear_minutos * 60), bloquear]
    if repousar_minutos > 0:
        comando += ["timeout", str(repousar_minutos * 60), "systemctl suspend"]
    comando += ["before-sleep", bloquear, "lock", bloquear]
    return comando


def _minutos(chave, padrao):
    valor = pastas.ler_preferencia("energia", chave, str(padrao))
    return int(valor) if valor.isdigit() else padrao


def aplicar_bloqueio():
    _parar("swayidle")
    bloquear = str(PASTA_SHELL / "bloqueio" / "bloquear")
    descanso = f"python3 {PASTA_SHELL / 'descanso' / 'main.py'}"
    minutos_descanso = pastas.ler_preferencia("descanso", "minutos", "0")
    _iniciar(comando_swayidle(_minutos("bloquear", BLOQUEIO_PADRAO), _minutos("repousar", 0), bloquear,
                              int(minutos_descanso) if minutos_descanso.isdigit() else 0, descanso))


def main(argumentos):
    acao = argumentos[0] if argumentos else "aplicar"
    if acao == "papel-de-parede":          # só de reserva: na sessão, quem desenha é a Área de Trabalho
        aplicar_papel_de_parede()
    if acao in ("aplicar", "aparencia"):
        atualizar_modo_automatico()
        aplicar_aparencia()
    if acao in ("aplicar", "telas"):
        aplicar_telas()
    if acao in ("aplicar", "bloqueio"):
        aplicar_bloqueio()
    if acao == "aplicar":
        pastas.criar_pastas_padrao()
        barra_do_sistema_nos_navegadores()
        import controles
        controles.aplicar_luz_noturna()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
