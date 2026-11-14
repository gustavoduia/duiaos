#!/usr/bin/env python3
"""DuiaOS — aplica as escolhas das Configurações na sessão (papel de parede, telas,
luz noturna e bloqueio automático).

Chamado por sessao/autostart ao entrar e pelas Configurações quando algo muda:
  sessao.py aplicar                  tudo (início da sessão)
  sessao.py papel-de-parede          só o papel de parede
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
PAPEL_PADRAO = PAPEIS_DO_SISTEMA / "orbita.jpg"
COR_PADRAO = "#E8F0FE"
BLOQUEIO_PADRAO = 10          # minutos
EXTENSOES_DE_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")


def _iniciar(comando):
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def _parar(programa):
    subprocess.run(["pkill", "-u", str(os.getuid()), "-x", programa], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
    saida = subprocess.run(["wlr-randr"], capture_output=True, text=True, check=False).stdout
    for tela in interpretar_wlr_randr(saida):
        modo = pastas.ler_preferencia("telas", tela["nome"] + ".modo", "")
        escala = pastas.ler_preferencia("telas", tela["nome"] + ".escala", "")
        if modo or escala:
            subprocess.run(comando_tela(tela["nome"], modo or None, escala or None), check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- bloqueio

def comando_swayidle(bloquear_minutos, repousar_minutos, bloquear):
    """Bloqueio automático e repouso (0 = nunca). A tela sempre bloqueia antes de repousar."""
    comando = ["swayidle", "-w"]
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
    _iniciar(comando_swayidle(_minutos("bloquear", BLOQUEIO_PADRAO), _minutos("repousar", 0), bloquear))


def main(argumentos):
    acao = argumentos[0] if argumentos else "aplicar"
    if acao in ("aplicar", "papel-de-parede"):
        aplicar_papel_de_parede()
    if acao in ("aplicar", "telas"):
        aplicar_telas()
    if acao in ("aplicar", "bloqueio"):
        aplicar_bloqueio()
    if acao == "aplicar":
        pastas.criar_pastas_padrao()
        import controles
        controles.aplicar_luz_noturna()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
