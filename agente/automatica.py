#!/usr/bin/env python3
"""DuiaOS — atualização automática (ADR 058).

Cinco modos, escolhidos em Configurações › Atualizações e guardados em /etc/duiaos/atualizacoes.conf
(vale para o computador todo, como as próprias atualizações):

  desativado          o DuiaOS não procura sozinho (o botão Procurar continua funcionando)
  avisar              procura e avisa
  baixar              procura, avisa e deixa baixado (instalar fica para a pessoa, e é rápido)
  instalar-avisando   procura, avisa, baixa e instala, e avisa quando terminar
  instalar            procura, baixa e instala sem avisar (só avisa se for preciso reiniciar)

Quem procura é o temporizador duiaos-atualizacao-automatica (como root, 10 min depois de ligar e a
cada hora): este arquivo com --ciclo. A instalação passa pelo duiaos-agente (D-Bus, como root não
precisa do polkit), com o mesmo andamento, registros, reparo e idempotência da instalação pela tela.

O que foi encontrado fica em /var/lib/duiaos/atualizacoes/estado.json (legível por todos): a Barra de
Recursos lê esse arquivo para mostrar o ícone ao lado do relógio e o aviso. O agente também o
atualiza sempre que alguém procura ou instala pela tela, para o ícone nunca ficar desatualizado.
"""
import configparser
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

MODOS = ("desativado", "avisar", "baixar", "instalar-avisando", "instalar")
MODO_PADRAO = "baixar"
CONF = Path("/etc/duiaos/atualizacoes.conf")
ESTADO = Path("/var/lib/duiaos/atualizacoes/estado.json")
AGENTE = ("org.duiaos.Agente1", "/org/duiaos/Agente1")
# Pacotes que pedem reiniciar o computador (o resto do DuiaOS pede, no máximo, sair e entrar na sessão)
PEDEM_REINICIAR = ("linux-image", "systemd", "libc6", "dbus", "nvidia-", "firmware-", "intel-microcode", "amd64-microcode")
PEDEM_SESSAO = ("duiaos-shell", "duiaos-identidade", "labwc", "qt6-", "libqt6", "python3-pyside6", "qml6-")


# ------------------------------------------------------------------ configuração

def ler_modo(conf=None):
    conf = conf or CONF
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(conf, encoding="utf-8")
    except (configparser.Error, OSError):
        return MODO_PADRAO
    modo = config.get("automatica", "modo", fallback=MODO_PADRAO)
    return modo if modo in MODOS else MODO_PADRAO


def gravar_modo(modo, conf=None):
    conf = conf or CONF
    if modo not in MODOS:
        raise ValueError(f"modo desconhecido: {modo!r}")
    conf = Path(conf)
    conf.parent.mkdir(parents=True, exist_ok=True)
    temporario = conf.with_suffix(".tmp")
    temporario.write_text("# DuiaOS — atualização automática (Configurações › Atualizações; ADR 058)\n"
                          "# modo: " + " | ".join(MODOS) + "\n"
                          f"[automatica]\nmodo = {modo}\n", encoding="utf-8")
    os.chmod(temporario, 0o644)
    os.replace(temporario, conf)


# ------------------------------------------------------------------ estado

def ler_estado(arquivo=None):
    arquivo = arquivo or ESTADO
    try:
        dados = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_estado(mudar, arquivo=None):
    """Junta `mudar` ao estado e grava (atômico, legível por todos)."""
    arquivo = Path(arquivo or ESTADO)
    dados = {**ler_estado(arquivo), **mudar}
    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(arquivo.parent, 0o755)
        temporario = arquivo.with_suffix(".tmp")
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        os.chmod(temporario, 0o644)
        os.replace(temporario, arquivo)
    except OSError as erro:
        print("Atualização automática: não consegui gravar o estado:", erro, file=sys.stderr, flush=True)
    return dados


def reinicio(pacotes):
    """O que é preciso depois de instalar estes pacotes: "computador", "sessao" ou "nao"."""
    if any(p.startswith(PEDEM_REINICIAR) for p in pacotes):
        return "computador"
    if any(p.startswith(PEDEM_SESSAO) for p in pacotes):
        return "sessao"
    return "nao"


def assinatura(pacotes):
    """Identifica um conjunto de atualizações (para avisar uma vez só por conjunto)."""
    return hashlib.sha256("\n".join(sorted(pacotes)).encode()).hexdigest()[:16] if pacotes else ""


def registrar_verificacao(mudancas, arquivo=None, agora=None):
    """Depois de uma simulação de "atualizar o sistema" (pela tela ou pelo temporizador)."""
    pacotes = [f"{m['pacote']} {m.get('para', '')}".strip() for m in mudancas.get("atualizar", []) + mudancas.get("instalar", [])]
    nomes = [p.split(" ")[0] for p in pacotes]
    anterior = ler_estado(arquivo)
    mudar = {"verificado": int(agora or time.time()), "disponiveis": len(pacotes), "pacotes": pacotes[:400],
             "duiaos": sum(1 for n in nomes if n.startswith("duiaos-")), "assinatura": assinatura(pacotes),
             "reiniciar_previsto": reinicio(nomes), "erro": ""}
    if mudar["assinatura"] != anterior.get("assinatura"):
        mudar["baixadas"] = False                # outro conjunto: o que estava baixado não serve mais
    return gravar_estado(mudar, arquivo)


def registrar_download(arquivo=None):
    return gravar_estado({"baixadas": True, "baixadas_em": int(time.time())}, arquivo)


def registrar_instalacao(resultado, pacotes, arquivo=None, automatica=False, agora=None):
    """Depois de instalar (pela tela ou automaticamente). Com sucesso, não há mais nada disponível."""
    nomes = [p.split(" ")[0] for p in pacotes]
    mudar = {"instalacao": {"quando": int(agora or time.time()), "resultado": resultado, "quantidade": len(pacotes),
                            "reiniciar": reinicio(nomes) if resultado == "ok" else "nao", "automatica": automatica}}
    if resultado == "ok":
        mudar.update({"disponiveis": 0, "pacotes": [], "assinatura": "", "baixadas": False, "duiaos": 0})
    return gravar_estado(mudar, arquivo)


def registrar_erro(texto, arquivo=None):
    return gravar_estado({"erro": texto[:300], "verificado": int(time.time())}, arquivo)


# ------------------------------------------------------------------ ciclo (temporizador, como root)

def _chamar(metodo, *argumentos, tempo=600000):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    conexao = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    tipos = "(" + "s" * len(argumentos) + ")" if argumentos else None
    resposta = conexao.call_sync(AGENTE[0], AGENTE[1], AGENTE[0], metodo,
                                 GLib.Variant(tipos, argumentos) if tipos else None, None,
                                 Gio.DBusCallFlags.NONE, tempo, None)
    return resposta.unpack() if resposta is not None else ()


def baixar():
    """Baixa os pacotes da atualização, sem instalar (apt-get -d)."""
    ambiente = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C.UTF-8", "DEBIAN_FRONTEND": "noninteractive"}
    processo = subprocess.run(["apt-get", "-q", "-y", "-d", "-o", "DPkg::Lock::Timeout=600", "full-upgrade"],
                              capture_output=True, text=True, env=ambiente, timeout=3 * 3600, check=False)
    if processo.returncode != 0:
        raise RuntimeError("não consegui baixar: " + ((processo.stderr or processo.stdout).strip().splitlines() or [""])[-1][:200])


def preparar(forcar):
    plano = json.loads(_chamar("Preparar", "atualizar_sistema", json.dumps({"forcar": True} if forcar else {}))[0])
    mudancas = plano.get("mudancas", {})
    pacotes = [f"{m['pacote']} {m.get('para', '')}".strip() for m in mudancas.get("atualizar", []) + mudancas.get("instalar", [])]
    return plano, pacotes


def instalar():
    """Instala pelo duiaos-agente e espera terminar. Devolve (resultado, pacotes)."""
    plano, pacotes = preparar(forcar=False)
    if not pacotes:
        return "ok", []
    if plano.get("recusa"):
        raise RuntimeError(plano["recusa"].get("mensagem", "o agente recusou"))
    _chamar("Executar", plano["id"])
    limite = time.monotonic() + 4 * 3600
    while time.monotonic() < limite:
        time.sleep(5)
        estado = json.loads(_chamar("Estado")[0])
        ultima = estado.get("ultima") or {}
        if not estado.get("tarefa") and ultima.get("id") == plano["id"]:
            return ultima.get("resultado", "erro"), pacotes
    return "erro", pacotes


def rede_limitada(rodar=None):
    """A conexão em uso é limitada (celular, plano com franquia; marcada pela pessoa ou deduzida pelo
    NetworkManager)? Propriedade Metered do NetworkManager: 1 sim, 3 provavelmente sim (ADR 069)."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, text=True, timeout=10, check=False))
    try:
        saida = rodar(["busctl", "get-property", "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager",
                       "org.freedesktop.NetworkManager", "Metered"]).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    partes = saida.split()
    return len(partes) == 2 and partes[0] == "u" and partes[1] in ("1", "3")


def ciclo(modo=None, ao_preparar=None, ao_baixar=None, ao_instalar=None, limitada=None):
    """Uma rodada do temporizador. Devolve o que fez (para o registro e os testes).
    Numa rede limitada só procura e avisa: baixar e instalar ficam para quando houver outra rede (ADR 069)."""
    modo = modo or ler_modo()
    ao_preparar, ao_baixar, ao_instalar = ao_preparar or preparar, ao_baixar or baixar, ao_instalar or instalar
    if modo == "desativado":
        return "desativado"
    _plano, pacotes = ao_preparar(True)           # o agente grava o que achou (registrar_verificacao)
    if not pacotes:
        return "em-dia"
    if modo == "avisar":
        return "avisado"
    if (limitada or rede_limitada)():
        return "rede-limitada"
    if not ler_estado().get("baixadas"):
        ao_baixar()
        registrar_download()
    if modo == "baixar":
        return "baixado"
    resultado, instalados = ao_instalar()         # o agente grava a instalação (registrar_instalacao)
    if instalados:
        gravar_estado({"instalacao": {**ler_estado().get("instalacao", {}), "automatica": True}})
    return "instalado" if resultado == "ok" else "erro-ao-instalar"


def main(argumentos):
    try:
        import duiaos_registro
        duiaos_registro.ligar("duiaos-atualizacao-automatica")
    except ImportError:
        duiaos_registro = None
    if "--ciclo" not in argumentos:
        print(__doc__)
        return 2
    try:
        feito = ciclo()
    except Exception as erro:                     # noqa: BLE001 — sem rede, agente ocupado, apt travado…
        registrar_erro(str(erro))
        if duiaos_registro:
            duiaos_registro.aviso("atualizacao.automatica", "Atualização automática não terminou", erro=str(erro)[:300])
        print("Atualização automática:", erro, file=sys.stderr, flush=True)
        return 1
    if duiaos_registro:
        duiaos_registro.info("atualizacao.automatica", "Atualização automática", modo=ler_modo(), resultado=feito)
    print("Atualização automática:", feito, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
