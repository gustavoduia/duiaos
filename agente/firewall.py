"""DuiaOS — firewall do sistema (firewalld), ADR 071.

Duas zonas próprias, instaladas pelo duiaos-agente em /usr/lib/firewalld/zones:
  duiaos-publica   padrão; nada entra (café, aeroporto, hotel)
  duiaos-privada   casa e trabalho: mDNS e acesso remoto (SSH, que a pessoa pode desligar)
Cada conexão do NetworkManager guarda a zona em connection.zone (o tipo de rede escolhido nas
Configurações ou na pergunta da Barra); o NetworkManager entrega a placa ao firewalld com essa zona.

`preparar()` roda uma vez, no postinst: põe as conexões que já existem como privadas (quem atualiza um
computador que já usava, por exemplo o acesso pelo SSH, não fica trancado do lado de fora) e só depois
troca a zona padrão para a pública. `configurar()` é o método ConfigurarFirewall do duiaos-agente.

Uso: firewall.py preparar      (postinst do duiaos-agente, como root)
"""
import os
import subprocess
import sys
from pathlib import Path

PUBLICA = "duiaos-publica"
PRIVADA = "duiaos-privada"
TIPOS_COM_ZONA = {"802-3-ethernet", "802-11-wireless", "gsm", "cdma", "bluetooth"}
MARCA = Path("/var/lib/duiaos/firewall-preparado")
FIREWALL_CMD = os.environ.get("DUIAOS_FIREWALL_CMD", "firewall-cmd").split()
FIREWALL_OFFLINE = os.environ.get("DUIAOS_FIREWALL_OFFLINE", "firewall-offline-cmd").split()


def _rodar(comando, tempo=30):
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=tempo, check=False)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", f"{comando[0]} não encontrado"
    except subprocess.TimeoutExpired:
        return 124, "", "demorou demais"


def ligado(rodar=_rodar):
    return rodar([*FIREWALL_CMD, "--state"])[1].strip() == "running"


def conexoes(rodar=_rodar):
    """[(uuid, tipo, zona, placa ativa)] do NetworkManager."""
    codigo, saida, _ = rodar(["nmcli", "-t", "-f", "UUID,TYPE,DEVICE", "connection", "show"])
    if codigo != 0:
        return []
    lista = []
    for linha in saida.splitlines():
        partes = linha.split(":")
        if len(partes) < 3 or partes[1] not in TIPOS_COM_ZONA:
            continue
        c2, zona, _ = rodar(["nmcli", "-t", "-g", "connection.zone", "connection", "show", partes[0]])
        lista.append((partes[0], partes[1], zona.strip() if c2 == 0 else "", partes[2]))
    return lista


def preparar(rodar=_rodar, marca=None):
    """Uma vez por computador. Devolve o que fez (para o registro do postinst)."""
    marca = Path(marca or MARCA)
    if marca.exists():
        return ["já preparado"]
    feito = []
    if not ligado(rodar):
        # ISO em construção (chroot) ou firewalld parado: grava só a zona padrão, para quando ele ligar
        if rodar([*FIREWALL_OFFLINE, f"--set-default-zone={PUBLICA}"])[0] == 0:
            feito.append("zona padrão gravada (firewalld parado)")
    else:
        rodar([*FIREWALL_CMD, "--reload"])           # carrega as zonas do DuiaOS
        for uuid, _tipo, zona, placa in conexoes(rodar):
            if zona:
                continue
            if rodar(["nmcli", "connection", "modify", uuid, "connection.zone", PRIVADA])[0] == 0:
                feito.append(f"conexão {uuid[:8]} privada")
                if placa:                             # vale na hora, sem derrubar a conexão (ex.: o SSH em uso)
                    rodar([*FIREWALL_CMD, f"--zone={PRIVADA}", f"--change-interface={placa}"])
        if rodar([*FIREWALL_CMD, f"--set-default-zone={PUBLICA}"])[0] == 0:
            feito.append("zona padrão pública")
    if feito:
        try:
            marca.parent.mkdir(parents=True, exist_ok=True)
            marca.write_text("\n".join(feito) + "\n")
        except OSError:
            pass
    return feito


def configurar(ligar, ssh, rodar=_rodar):
    """Liga ou desliga o firewall (serviço) e o acesso remoto (SSH) nas redes privadas."""
    if ligar:
        codigo, _, erro = rodar(["systemctl", "enable", "--now", "firewalld.service"], tempo=60)
        if codigo != 0:
            raise RuntimeError(erro.strip() or "não foi possível ligar o firewall")
        for _ in range(20):                          # o firewalld leva um instante para responder
            if ligado(rodar):
                break
            import time
            time.sleep(0.5)
        acao = "--add-service=ssh" if ssh else "--remove-service=ssh"
        for permanente in (["--permanent"], []):
            rodar([*FIREWALL_CMD, *permanente, f"--zone={PRIVADA}", acao])
    else:
        codigo, _, erro = rodar(["systemctl", "disable", "--now", "firewalld.service"], tempo=60)
        if codigo != 0:
            raise RuntimeError(erro.strip() or "não foi possível desligar o firewall")


if __name__ == "__main__":
    if sys.argv[1:] == ["preparar"]:
        for linha in preparar():
            print("duiaos-agente (firewall):", linha)
    else:
        print(__doc__)
        sys.exit(2)
