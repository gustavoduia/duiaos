#!/bin/bash
# =============================================================================
# DuiaOS — lança uma versão: cria a tag vX.Y.Z no Wise, no Ora, no Mail Box e no DuiaOS e envia ao
# GitHub, o que gera as duas ISOs (com o Wise, o Ora e o Mail Box, que recebem a
# mesma tag), publica o Release no repositório público e os pacotes no fluxo único
# de atualizações (ADR 074; a tag precisa estar no commit mais novo da main)
# (rode NO MAC). As notas da versão vêm de
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

# O Wise, o Ora e o Mail Box vão junto (ADR 042 e 073): a mesma tag em cada repositório, na main atualizada
PAI="$(dirname "$(pwd)")"
declare -A PASTAS=([Wise]="${DUIAOS_WISE:-${PAI}/duiaos-wise}" [Ora]="${DUIAOS_ORA:-${PAI}/duiaos-ora}"
                   [Mail\ Box]="${DUIAOS_MAILBOX:-${PAI}/duiaos-mailbox}")
declare -A TEM_TAG=()
for NOME in Wise Ora "Mail Box"; do
  PASTA="${PASTAS[${NOME}]}"
  [ -d "${PASTA}/.git" ] || { echo "Não achei o ${NOME} em ${PASTA} (clone os repositórios lado a lado)." >&2; exit 1; }
  [ "$(git -C "${PASTA}" branch --show-current)" = "main" ] || { echo "${NOME}: mude para a main (cd ${PASTA} && git switch main)" >&2; exit 1; }
  [ -z "$(git -C "${PASTA}" status --porcelain)" ] || { echo "${NOME}: há alterações não commitadas." >&2; exit 1; }
  git -C "${PASTA}" fetch -q --tags origin
  [ "$(git -C "${PASTA}" rev-parse HEAD)" = "$(git -C "${PASTA}" rev-parse origin/main)" ] || { echo "${NOME}: rode git pull na main." >&2; exit 1; }
  TEM_TAG[${NOME}]=0
  git -C "${PASTA}" rev-parse -q --verify "refs/tags/${TAG}" >/dev/null && TEM_TAG[${NOME}]=1
done

echo "Lançando DuiaOS ${VERSAO} a partir de $(git log -1 --oneline)"
for NOME in Wise Ora "Mail Box"; do
  echo "${NOME}: $(git -C "${PASTAS[${NOME}]}" log -1 --oneline)$([ "${TEM_TAG[${NOME}]}" = 1 ] && echo " (tag ${TAG} já existe e será usada)")"
done
read -r -p "Confirma? (s/N) " R
[ "${R}" = "s" ] || [ "${R}" = "S" ] || { echo "Cancelado."; exit 1; }

for NOME in Wise Ora "Mail Box"; do
  if [ "${TEM_TAG[${NOME}]}" = 0 ]; then
    git -C "${PASTAS[${NOME}]}" tag -a "${TAG}" -m "${NOME} ${VERSAO} (DuiaOS ${VERSAO})"
    git -C "${PASTAS[${NOME}]}" push origin "${TAG}"
  fi
done
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
