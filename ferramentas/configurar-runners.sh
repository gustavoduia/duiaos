#!/bin/bash
# =============================================================================
# DuiaOS — registra os runners próprios (rode NO MAC, na pasta do repositório).
#
#   bash ferramentas/configurar-runners.sh mac    # runner arm64 neste Mac
#   bash ferramentas/configurar-runners.sh dell   # runner amd64 no Dell, por SSH
#
# Variável opcional: DELL=usuario@endereco (padrão duia@duiaos).
# Precisa do gh autenticado como dono do repositório (gh auth login).
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos"
DELL="${DELL:-duia@duiaos}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

gh auth status >/dev/null 2>&1 || { echo "Rode antes: gh auth login" >&2; exit 1; }
token() { gh api -X POST "repos/${REPO}/actions/runners/registration-token" --jq .token; }

case "${1:-}" in
  mac)
    bash "${AQUI}/runner-instalar.sh" "$(token)" "mac-m4" "duiaos-arm64"
    ;;
  dell)
    scp -q "${AQUI}/runner-instalar.sh" "${DELL}:/tmp/duiaos-runner-instalar.sh"
    ssh -t "${DELL}" "bash /tmp/duiaos-runner-instalar.sh '$(token)' dell-latitude duiaos-amd64; rm -f /tmp/duiaos-runner-instalar.sh"
    ;;
  *)
    echo "Uso: bash $0 mac|dell" >&2
    exit 1
    ;;
esac
