#!/bin/bash
# =============================================================================
# DuiaOS — dispara a geração de ISOs de teste. Rode NO MAC.
#
#   bash ferramentas/gerar-iso.sh                       # as duas, na máquina padrão
#   bash ferramentas/gerar-iso.sh arm64=nao             # só a amd64
#   bash ferramentas/gerar-iso.sh amd64=nao             # só a arm64
#
# Máquina padrão: repositório público → GitHub; privado → amd64 no Dell, arm64 no Mac.
# Opções:  amd64 = github | dell | nao     arm64 = github | mac | dell | nao
# (dell/mac só com o repositório privado e os runners retomados.)
#
# Depois: GitHub → bash ferramentas/baixar-isos.sh [dell]
#         Dell   → bash ferramentas/trazer-isos.sh
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
case "${AMD64}" in padrao|github|dell|nao) ;; *)
  echo "amd64=${AMD64} inválido (use github, dell ou nao)" >&2; exit 1 ;;
esac
case "${ARM64}" in padrao|github|mac|dell|nao) ;; *)
  echo "arm64=${ARM64} inválido (use github, mac, dell ou nao)" >&2; exit 1 ;;
esac

cd "$(dirname "${BASH_SOURCE[0]}")/.."
echo "Gerando: amd64=${AMD64} arm64=${ARM64} (branch main)"
gh workflow run gerar-iso.yml --ref main -f amd64="${AMD64}" -f arm64="${ARM64}"
sleep 6
RUN="$(gh run list --workflow gerar-iso.yml -L 1 --json databaseId --jq '.[0].databaseId')"
gh run list --workflow gerar-iso.yml -L 1
cat <<TXT

Acompanhar:  gh run watch ${RUN}      (Ctrl+C sai sem cancelar o build)
Cancelar:    gh run cancel ${RUN}
Ao terminar: bash ferramentas/baixar-isos.sh ${RUN}       (acrescente "dell" para enviar ao Dell)
TXT
