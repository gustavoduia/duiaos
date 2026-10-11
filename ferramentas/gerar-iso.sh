#!/bin/bash
# =============================================================================
# DuiaOS — dispara a geração de ISOs de teste escolhendo onde gerar cada uma.
# Rode NO MAC.
#
#   bash ferramentas/gerar-iso.sh                        # padrão: amd64 no Dell, arm64 no Mac
#   bash ferramentas/gerar-iso.sh amd64=mac arm64=mac    # as duas no Mac
#   bash ferramentas/gerar-iso.sh amd64=dell arm64=dell  # as duas no Dell (arm64 é lenta)
#   bash ferramentas/gerar-iso.sh amd64=mac arm64=nao    # só a amd64, no Mac
#   bash ferramentas/gerar-iso.sh arm64=github amd64=nao # só a arm64, nos servidores do GitHub
#
# Opções para cada arquitetura: mac, dell, github, nao (omitida = padrão).
# As ISOs ficam em ~/Projetos/duiaos-isos na máquina que gerou
# (traga as do Dell para o Mac com: bash ferramentas/trazer-isos.sh).
# =============================================================================
set -euo pipefail

AMD64="padrao"; ARM64="padrao"
for ARG in "$@"; do
  case "${ARG}" in
    amd64=*) AMD64="${ARG#amd64=}" ;;
    arm64=*) ARM64="${ARG#arm64=}" ;;
    *) echo "Argumento inválido: ${ARG} (use amd64=... e/ou arm64=...)" >&2; exit 1 ;;
  esac
done
for V in "${AMD64}" "${ARM64}"; do
  case "${V}" in padrao|mac|dell|github|nao) ;; *)
    echo "Opção inválida: ${V} (use mac, dell, github ou nao)" >&2; exit 1 ;;
  esac
done

cd "$(dirname "${BASH_SOURCE[0]}")/.."
echo "Gerando: amd64=${AMD64} arm64=${ARM64} (branch main)"
gh workflow run gerar-iso.yml --ref main -f amd64="${AMD64}" -f arm64="${ARM64}"
sleep 6
gh run list --workflow gerar-iso.yml -L 1
cat <<'TXT'

Acompanhar:  gh run watch            (Ctrl+C sai sem cancelar o build)
Situação:    gh run list --workflow gerar-iso.yml -L 3
Cancelar:    gh run cancel NUMERO
TXT
