#!/bin/bash
# =============================================================================
# DuiaOS — prepara uma máquina para gerar ISOs e organiza ~/Projetos nela.
# Rode NO MAC, na pasta do repositório.
#
#   bash ferramentas/configurar-runners.sh mac    # este Mac
#   bash ferramentas/configurar-runners.sh dell   # o Dell, por SSH
#
# Pode rodar de novo: refaz o runner e mantém as ISOs. Não rode enquanto a
# máquina estiver gerando uma ISO (o build em andamento seria interrompido).
#
# Variável opcional: DELL=usuario@endereco (padrão gustavo@duiaos).
# Precisa do gh autenticado como dono do repositório (gh auth login).
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos"
DELL="${DELL:-gustavo@duiaos}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

gh auth status >/dev/null 2>&1 || { echo "Rode antes: gh auth login" >&2; exit 1; }
token() { gh api -X POST "repos/${REPO}/actions/runners/$1" --jq .token; }

case "${1:-}" in
  mac)
    bash "${AQUI}/runner-instalar.sh" "$(token registration-token)" "$(token remove-token)" "mac-m4" "mac"
    ;;
  dell)
    scp -q "${AQUI}/runner-instalar.sh" "${DELL}:/tmp/duiaos-runner-instalar.sh"
    ssh -t "${DELL}" "bash /tmp/duiaos-runner-instalar.sh '$(token registration-token)' '$(token remove-token)' dell-latitude dell; rm -f /tmp/duiaos-runner-instalar.sh"
    ;;
  *)
    echo "Uso: bash $0 mac|dell" >&2
    exit 1
    ;;
esac
