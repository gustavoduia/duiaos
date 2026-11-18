#!/bin/bash
# =============================================================================
# DuiaOS — laboratório de rede para os testes (ADR 069): um NetworkManager de verdade cuidando de duas
# placas virtuais, sem mexer na rede da máquina.
#
#   veth-a  ↔  veth-b (rede "com-dhcp", 10.77.0.0/24, dnsmasq entrega endereço e DNS)
#   veth-c  ↔  veth-d (rede "sem-dhcp", 10.88.0.0/24, ninguém entrega endereço: precisa de IP fixo)
#
# O outro lado de cada par fica num namespace de rede próprio. O NetworkManager só cuida de veth-a e
# veth-c (todas as outras placas ficam "não gerenciadas"), então a conexão da máquina não muda.
#
# Feito para o ambiente do Claude e para contêineres de teste (roda como root, precisa de CAP_NET_ADMIN).
# NÃO rode no computador de uso: ele troca a configuração do NetworkManager.
#
# Uso: sudo bash ferramentas/laboratorio-rede.sh [subir|descer]
# =============================================================================
set -euo pipefail
ACAO="${1:-subir}"
CONF=/etc/NetworkManager/conf.d/99-duiaos-laboratorio.conf

if [ "${ACAO}" = "descer" ]; then
  pkill -x NetworkManager 2>/dev/null || true
  for ns in duiaos-com-dhcp duiaos-sem-dhcp; do ip netns del "${ns}" 2>/dev/null || true; done
  ip link del veth-a 2>/dev/null || true
  ip link del veth-c 2>/dev/null || true
  rm -f "${CONF}"
  exit 0
fi

command -v NetworkManager >/dev/null || { echo "Instale o network-manager." >&2; exit 1; }
command -v dnsmasq >/dev/null || { echo "Instale o dnsmasq-base." >&2; exit 1; }

# D-Bus do sistema e udev (sem o udev, o NetworkManager deixa toda placa como "não gerenciada")
mkdir -p /run/dbus
pgrep -x dbus-daemon >/dev/null || dbus-daemon --system --fork
pgrep -f systemd-udevd >/dev/null || /usr/lib/systemd/systemd-udevd --daemon

mkdir -p /etc/NetworkManager/conf.d
cat > "${CONF}" <<'EOF'
[main]
plugins=keyfile
[keyfile]
unmanaged-devices=except:interface-name:veth-a;except:interface-name:veth-c
[device-laboratorio]
match-device=interface-name:veth-a;interface-name:veth-c
managed=1
EOF

par() {  # par LOCAL REMOTO NAMESPACE ENDERECO_REMOTO
  ip link show "$1" >/dev/null 2>&1 && return 0
  ip netns add "$3" 2>/dev/null || true
  ip link add "$1" type veth peer name "$2"
  ip link set "$2" netns "$3"
  ip -n "$3" addr add "$4" dev "$2"
  ip -n "$3" link set "$2" up
  ip -n "$3" link set lo up
}
par veth-a veth-b duiaos-com-dhcp 10.77.0.1/24
par veth-c veth-d duiaos-sem-dhcp 10.88.0.1/24

if ! ip netns pids duiaos-com-dhcp 2>/dev/null | grep -q .; then
  ip netns exec duiaos-com-dhcp dnsmasq --interface=veth-b --bind-interfaces --dhcp-range=10.77.0.50,10.77.0.99,1h \
    --dhcp-option=option:dns-server,10.77.0.1 --port=0 --pid-file=/run/duiaos-laboratorio-dnsmasq.pid
fi
udevadm trigger --action=add --subsystem-match=net
udevadm settle

if pgrep -x NetworkManager >/dev/null; then
  nmcli general reload
else
  NetworkManager
fi
for _ in $(seq 1 30); do
  nmcli -t -f DEVICE,STATE device 2>/dev/null | grep -q '^veth-a:connected' && break
  sleep 0.5
done
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device
