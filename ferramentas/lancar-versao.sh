#!/bin/bash
# =============================================================================
# DuiaOS — lança uma versão: cria a tag vX.Y.Z e envia ao GitHub, o que gera
# as duas ISOs e publica o Release no repositório público (rode NO MAC).
#
#   bash ferramentas/lancar-versao.sh 0.1.0
#   bash ferramentas/lancar-versao.sh 1.0.0-beta.1
#
# Confere antes: branch main, sem alterações locais, igual ao GitHub e tag nova.
# =============================================================================
set -euo pipefail

VERSAO="${1:-}"
if ! [[ "${VERSAO}" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?$ ]]; then
  echo "Uso: bash $0 X.Y.Z   (ex.: 0.1.0 ou 1.0.0-beta.1)" >&2
  exit 1
fi
TAG="v${VERSAO}"

cd "$(git rev-parse --show-toplevel)"
[ "$(git branch --show-current)" = "main" ] || { echo "Mude para a main: git switch main" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "Há alterações não commitadas (git status)." >&2; exit 1; }
git fetch -q --tags origin
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "A main local difere do GitHub. Rode: git pull" >&2; exit 1; }
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
  echo "A tag ${TAG} já existe." >&2
  exit 1
fi

echo "Lançando DuiaOS ${VERSAO} a partir de $(git log -1 --oneline)"
read -r -p "Confirma? (s/N) " R
[ "${R}" = "s" ] || [ "${R}" = "S" ] || { echo "Cancelado."; exit 1; }

git tag -a "${TAG}" -m "DuiaOS ${VERSAO}"
git push origin "${TAG}"

echo
echo "Tag enviada. Acompanhe o build (o Dell e o Mac precisam estar ligados):"
sleep 8
gh run list --workflow gerar-iso.yml -L 1 || true
echo "Ou: gh run watch"
