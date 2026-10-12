"""DuiaOS — funções comuns da interface: versão, papel de parede, usuários e energia.

Usado pela Tela de Entrada, pela Tela de Bloqueio e pelo Menu de Energia.
"""
import os
import pwd
import subprocess
from pathlib import Path

PASTA_SHELL = Path(__file__).resolve().parents[1]
RAIZ_REPOSITORIO = PASTA_SHELL.parent

# Instalado: /usr/share/duiaos/...; no repositório (desenvolvimento): pacotes/duiaos-identidade/raiz/...
_INCLUDES = RAIZ_REPOSITORIO / "pacotes/duiaos-identidade/raiz"
PAPEIS_DE_PAREDE = [
    Path("/usr/share/duiaos/papel-de-parede/orbita.jpg"),
    _INCLUDES / "usr/share/duiaos/papel-de-parede/orbita.jpg",
]
REINICIAR_NO_WINDOWS = [
    Path("/usr/lib/duiaos/reiniciar-no-windows"),
    _INCLUDES / "usr/lib/duiaos/reiniciar-no-windows",
]
BLOQUEAR = PASTA_SHELL / "bloqueio" / "bloquear"

# Wise (repositório privado duiaos-wise, pacote duiaos-wise). Contrato com a
# interface: o comando abaixo existe quando o Wise está instalado, e
# "duiaos-wise --alternar" abre ou fecha a janela do Wise.
WISE = "/usr/bin/duiaos-wise"
WISE_DESKTOP = "duiaos-wise.desktop"


def wise_instalado():
    return os.access(WISE, os.X_OK)


def alternar_wise():
    """Abre ou fecha a janela do Wise (se ele estiver instalado)."""
    if wise_instalado():
        subprocess.Popen([WISE, "--alternar"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


def papel_de_parede():
    """Caminho (URL file://) do papel de parede padrão, ou '' se não existir."""
    for caminho in PAPEIS_DE_PAREDE:
        if caminho.is_file():
            return caminho.as_uri()
    return ""


def versao():
    """Ex.: 'DuiaOS 0.2.0 (Zoinho)', lido de /etc/os-release."""
    try:
        for linha in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if linha.startswith("PRETTY_NAME="):
                texto = linha.split("=", 1)[1].strip().strip('"')
                if texto.startswith("DuiaOS"):
                    return texto
    except OSError:
        pass
    return "DuiaOS"


def _limites_uid():
    """UID_MIN e UID_MAX de /etc/login.defs (padrão do Debian: 1000 e 60000)."""
    minimo, maximo = 1000, 60000
    try:
        for linha in Path("/etc/login.defs").read_text(encoding="utf-8").splitlines():
            partes = linha.split()
            if len(partes) == 2 and partes[0] == "UID_MIN":
                minimo = int(partes[1])
            elif len(partes) == 2 and partes[0] == "UID_MAX":
                maximo = int(partes[1])
    except (OSError, ValueError):
        pass
    return minimo, maximo


def usuarios():
    """Pessoas que podem entrar no computador: [{'usuario': 'gustavo', 'nome': 'Gustavo'}]."""
    minimo, maximo = _limites_uid()
    lista = []
    for conta in pwd.getpwall():
        if not minimo <= conta.pw_uid <= maximo:
            continue
        if conta.pw_shell.endswith(("nologin", "false")):
            continue
        nome = conta.pw_gecos.split(",")[0].strip() or conta.pw_name
        lista.append({"usuario": conta.pw_name, "nome": nome})
    lista.sort(key=lambda u: u["nome"].casefold())
    return lista


def usuario_atual():
    conta = pwd.getpwuid(os.getuid())
    return {"usuario": conta.pw_name, "nome": conta.pw_gecos.split(",")[0].strip() or conta.pw_name}


# --------------------------------------------------------------------- energia

def _primeiro(caminhos):
    return next((c for c in caminhos if c.is_file()), None)


def windows_disponivel():
    """True se o firmware tem o Windows Boot Manager (dual boot)."""
    script = _primeiro(REINICIAR_NO_WINDOWS)
    if not script:
        return False
    try:
        resultado = subprocess.run(["sh", str(script), "--verificar"], capture_output=True,
                                   timeout=5, check=False)
        return resultado.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def opcoes_de_energia(na_sessao):
    """Opções do menu de energia. na_sessao=True inclui Bloquear e Encerrar sessão."""
    opcoes = []
    if na_sessao:
        opcoes += [
            {"id": "bloquear", "titulo": "Bloquear",
             "descricao": "Protege a tela; os aplicativos continuam abertos"},
            {"id": "encerrar", "titulo": "Encerrar sessão",
             "descricao": "Fecha os aplicativos e volta à Tela de Entrada"},
        ]
    opcoes += [
        {"id": "suspender", "titulo": "Suspender",
         "descricao": "Economiza energia; volta de onde parou"},
        {"id": "reiniciar", "titulo": "Reiniciar",
         "descricao": "Desliga e liga o computador de novo"},
    ]
    if windows_disponivel():
        opcoes.append({"id": "windows", "titulo": "Reiniciar no Windows",
                       "descricao": "Abre o Windows uma vez; depois volta ao DuiaOS"})
    opcoes.append({"id": "desligar", "titulo": "Desligar",
                   "descricao": "Fecha tudo e desliga o computador"})
    return opcoes


COMANDOS_DE_ENERGIA = {
    "bloquear": [str(BLOQUEAR)],
    "encerrar": ["labwc", "--exit"],
    "suspender": ["systemctl", "suspend"],
    "reiniciar": ["systemctl", "reboot"],
    # Precisa de root: o serviço é liberado pelo polkit para quem está no computador.
    "windows": ["systemctl", "start", "--no-block", "duiaos-reiniciar-no-windows.service"],
    "desligar": ["systemctl", "poweroff"],
}


def executar_energia(acao):
    """Executa uma ação de energia sem esperar o fim. Devolve False se a ação não existe."""
    comando = COMANDOS_DE_ENERGIA.get(acao)
    if not comando:
        return False
    subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return True
