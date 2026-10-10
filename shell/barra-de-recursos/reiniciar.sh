#!/bin/sh
# DuiaOS — reinicia a Barra de Recursos.
# Funciona no terminal da sessão gráfica e também pelo SSH.
PASTA="$(cd "$(dirname "$0")" && pwd)"

pkill -f "barra-de-recursos/main.py"
sleep 1

# Pelo SSH não existe tela definida: usa a sessão gráfica aberta.
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_RUNTIME_DIR
if [ -z "${WAYLAND_DISPLAY}" ]; then
  for socket in "${XDG_RUNTIME_DIR}"/wayland-[0-9]*; do
    case "${socket}" in *.lock) continue ;; esac
    [ -S "${socket}" ] && WAYLAND_DISPLAY="$(basename "${socket}")" && break
  done
  export WAYLAND_DISPLAY
fi
if [ -z "${WAYLAND_DISPLAY}" ]; then
  echo "Nenhuma sessão gráfica aberta. Inicie o labwc no Dell primeiro."
  exit 1
fi

nohup python3 "${PASTA}/main.py" >/tmp/duiaos-barra-de-recursos.log 2>&1 &
echo "Barra de Recursos reiniciada."
