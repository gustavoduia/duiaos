#!/bin/sh
# DuiaOS — Alt+Tab (proximo) e Alt+Shift+Tab (anterior): o alternador de aplicativos da Ilha (ADR 077).
# Deixa o pedido num arquivo e avisa a Ilha pelo SIGUSR1 (o mesmo da Central). Sem a Ilha, o labwc
# só troca para outra janela, sem o alternador.
DIRECAO="${1:-proximo}"
case "${DIRECAO}" in proximo|anterior) ;; *) exit 2 ;; esac
PASTA="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
ARQUIVO_PID="${PASTA}/duiaos-ilha-de-aplicativos.pid"
if [ -f "${ARQUIVO_PID}" ]; then
  printf '%s\n' "${DIRECAO}" > "${PASTA}/duiaos-ilha-pedido"
  if kill -USR1 "$(cat "${ARQUIVO_PID}")" 2>/dev/null; then
    exit 0
  fi
  rm -f "${PASTA}/duiaos-ilha-pedido"
fi
# Sem a Ilha: traz para a frente a janela mais antiga da lista (troca simples, sem o alternador)
command -v wlrctl >/dev/null 2>&1 || exit 1
exec wlrctl toplevel focus state:inactive
