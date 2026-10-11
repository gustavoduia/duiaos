#!/bin/bash
# =============================================================================
# DuiaOS — põe os runners próprios em espera (serviço desligado) ou os retoma.
# Rode NO MAC, na pasta do repositório (o Dell é acessado por SSH).
#
#   bash ferramentas/runners-espera.sh pausar           # Mac e Dell
#   bash ferramentas/runners-espera.sh retomar          # Mac e Dell
#   bash ferramentas/runners-espera.sh pausar dell      # só uma máquina (mac ou dell)
#   bash ferramentas/runners-espera.sh estado
#
# Enquanto o repositório for PÚBLICO, os runners devem ficar pausados (ADR 025).
# Pausar não apaga nada: a instalação em ~/Projetos/duiaos-runner continua lá.
# Variável opcional: DELL=usuario@endereco (padrão gustavo@duiaos).
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos"
DELL="${DELL:-gustavo@duiaos}"
ACAO="${1:-}"
ALVO="${2:-ambos}"

estado() {
  gh api "repos/${REPO}/actions/runners" --jq '.runners[] | "  \(.name): \(.status)"'
}

mac() {
  cd "${HOME}/Projetos/duiaos-runner"
  if [ "$1" = "pausar" ]; then
    ./svc.sh stop >/dev/null 2>&1 || true
    ./svc.sh uninstall >/dev/null 2>&1 || true
    brew services stop colima >/dev/null 2>&1 || true
    echo "Mac: runner pausado e Colima desligado."
  else
    brew services start colima >/dev/null
    ./svc.sh install >/dev/null
    ./svc.sh start >/dev/null
    echo "Mac: runner retomado."
  fi
}

dell() {
  if [ "$1" = "pausar" ]; then
    ssh -t "${DELL}" 'cd ~/Projetos/duiaos-runner && { sudo ./svc.sh stop; sudo ./svc.sh uninstall; } >/dev/null 2>&1; echo "Dell: runner pausado."'
  else
    ssh -t "${DELL}" 'cd ~/Projetos/duiaos-runner && sudo ./svc.sh install "$USER" >/dev/null && sudo ./svc.sh start >/dev/null && echo "Dell: runner retomado."'
  fi
}

case "${ACAO}" in
  pausar|retomar)
    case "${ALVO}" in
      mac)   mac "${ACAO}" ;;
      dell)  dell "${ACAO}" ;;
      ambos) mac "${ACAO}"; dell "${ACAO}" ;;
      *) echo "Máquina inválida: ${ALVO} (use mac, dell ou deixe em branco)" >&2; exit 1 ;;
    esac
    sleep 5
    echo "Situação no GitHub:"; estado
    ;;
  estado)
    estado
    ;;
  *)
    echo "Uso: bash $0 pausar|retomar [mac|dell]   ou   bash $0 estado" >&2
    exit 1
    ;;
esac
