#!/bin/sh
# DuiaOS — minimiza a janela da frente (botão amarelo da barra de título e Super+M).
# A Ilha de Aplicativos faz o efeito (gênio ou escala) e minimiza; sem a Ilha, o
# labwc minimiza direto, sem efeito.
ARQUIVO_PID="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/duiaos-ilha-de-aplicativos.pid"
if [ -f "${ARQUIVO_PID}" ] && kill -USR2 "$(cat "${ARQUIVO_PID}")" 2>/dev/null; then
  exit 0
fi
exec wlrctl toplevel minimize state:active
