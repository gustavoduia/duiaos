#!/bin/bash
# =============================================================================
# DuiaOS — lança uma versão: cria a tag vX.Y.Z no Wise e no DuiaOS e envia ao
# GitHub, o que gera as duas ISOs (com o Wise instalado, ADR 042), publica o
# Release no repositório público e os pacotes no canal "estavel" do
# repositório apt (rode NO MAC). As notas da versão vêm de
# notas-de-versao/X.Y.Z.md (as linhas "- ..." viram as Novidades do site).
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
[ -s "notas-de-versao/${VERSAO}.md" ] || { echo "Escreva antes notas-de-versao/${VERSAO}.md (novidades)." >&2; exit 1; }

# O Wise vai junto (ADR 042): a mesma tag no repositório dele, na main atualizada
WISE="${DUIAOS_WISE:-$(dirname "$(pwd)")/duiaos-wise}"
[ -d "${WISE}/.git" ] || { echo "Não achei o Wise em ${WISE} (ou defina DUIAOS_WISE)." >&2; exit 1; }
[ "$(git -C "${WISE}" branch --show-current)" = "main" ] || { echo "Wise: mude para a main (cd ${WISE} && git switch main)" >&2; exit 1; }
[ -z "$(git -C "${WISE}" status --porcelain)" ] || { echo "Wise: há alterações não commitadas." >&2; exit 1; }
git -C "${WISE}" fetch -q --tags origin
[ "$(git -C "${WISE}" rev-parse HEAD)" = "$(git -C "${WISE}" rev-parse origin/main)" ] || { echo "Wise: rode git pull na main." >&2; exit 1; }
WISE_TEM_TAG=0
git -C "${WISE}" rev-parse -q --verify "refs/tags/${TAG}" >/dev/null && WISE_TEM_TAG=1

echo "Lançando DuiaOS ${VERSAO} a partir de $(git log -1 --oneline)"
echo "Wise: $(git -C "${WISE}" log -1 --oneline)$([ "${WISE_TEM_TAG}" = 1 ] && echo " (tag ${TAG} já existe e será usada)")"
read -r -p "Confirma? (s/N) " R
[ "${R}" = "s" ] || [ "${R}" = "S" ] || { echo "Cancelado."; exit 1; }

if [ "${WISE_TEM_TAG}" = 0 ]; then
  git -C "${WISE}" tag -a "${TAG}" -m "Wise ${VERSAO} (DuiaOS ${VERSAO})"
  git -C "${WISE}" push origin "${TAG}"
fi
git tag -a "${TAG}" -m "DuiaOS ${VERSAO}"
git push origin "${TAG}"

echo
# Onde as ISOs são geradas depende da visibilidade do repositório (ADR 025)
if [ "$(gh api repos/gustavoduia/duiaos --jq .private 2>/dev/null)" = "true" ]; then
  echo "Tag enviada. Repositório privado: ISOs no Dell (amd64) e no Mac (arm64) — os dois precisam estar ligados."
else
  echo "Tag enviada. Repositório público: as duas ISOs são geradas nos servidores do GitHub (Mac e Dell podem ficar desligados)."
fi
echo "Acompanhe o build:"
sleep 8
gh run list --workflow gerar-iso.yml -L 1 || true
echo "Ou: gh run watch"
