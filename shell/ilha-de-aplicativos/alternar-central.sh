#!/bin/sh
# DuiaOS — abre ou fecha a Central de Aplicativos (atalho Super+Espaço).
# Envia o sinal SIGUSR1 só para o processo da Ilha de Aplicativos.
ARQUIVO_PID="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/duiaos-ilha-de-aplicativos.pid"
[ -f "${ARQUIVO_PID}" ] || exit 1
kill -USR1 "$(cat "${ARQUIVO_PID}")"
