#!/bin/bash
# =============================================================================
# DuiaOS — gera os pacotes do Ora (duiaos-ora) e do Mail Box (duiaos-mailbox) a partir dos repositórios
# PRIVADOS gustavoduia/duiaos-ora e gustavoduia/duiaos-mailbox, para irem na ISO e no repositório apt junto
# com o resto do sistema (ADR 073: aplicativos padrão do DuiaOS, como o Wise).
#
# Uso: bash pacotes/trazer-apps.sh PASTA_DE_SAIDA
#
# Variáveis:
#   DUIAOS_TOKEN_APPS  token só de LEITURA dos dois repositórios (segredo do GitHub). Sem ele, usa o
#                      DUIAOS_TOKEN_WISE (que então precisa ter acesso de leitura aos dois repositórios).
#                      Fica só neste passo: não vai para a ISO nem para o log.
#   SUITE              estavel (lançamento: exige a tag igual à do sistema) ou teste (main).
#   VERSAO_SISTEMA     versão lançada (ex.: 0.3.0), usada com SUITE=estavel.
#   APPS_REF           (opcional) branch ou tag a usar nos dois repositórios.
#
# Sem o token: num lançamento, falha (o sistema não sai sem os aplicativos padrão); fora dele, avisa e segue.
# =============================================================================
set -euo pipefail

SAIDA="${1:?Uso: bash pacotes/trazer-apps.sh PASTA_DE_SAIDA}"
SUITE="${SUITE:-teste}"
TOKEN="${DUIAOS_TOKEN_APPS:-${DUIAOS_TOKEN_WISE:-}}"

if [ -z "${TOKEN}" ]; then
  if [ "${SUITE}" = "estavel" ]; then
    echo "Falta o segredo DUIAOS_TOKEN_APPS: um lançamento não sai sem o Ora e o Mail Box." >&2
    exit 1
  fi
  echo "::warning::Sem o segredo DUIAOS_TOKEN_APPS: pacotes e ISO de teste sem o Ora e o Mail Box."
  exit 0
fi

if [ "${SUITE}" = "estavel" ]; then
  REF="${APPS_REF:-v${VERSAO_SISTEMA:?VERSAO_SISTEMA é obrigatória num lançamento}}"
else
  REF="${APPS_REF:-main}"
fi

TRABALHO="$(mktemp -d)"
trap 'rm -rf -- "${TRABALHO:?}"' EXIT
# O token vai num cabeçalho só destes comandos (não fica na URL nem no .git/config)
AUTH="$(printf 'x-access-token:%s' "${TOKEN}" | base64 -w0)"
mkdir -p "${SAIDA}"

for APP in ora mailbox; do
  REPO="gustavoduia/duiaos-${APP}"
  if ! git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic ${AUTH}" \
      clone -q --filter=blob:none --branch "${REF}" "https://github.com/${REPO}.git" "${TRABALHO}/${APP}"; then
    echo "Não consegui baixar o ${REPO} (${REF}). Confira o token e, num lançamento, se a tag ${REF} existe." >&2
    exit 1
  fi
  if [ "${SUITE}" = "estavel" ]; then
    DEB="$(VERSAO_DEB="${VERSAO_SISTEMA//-/\~}" bash "${TRABALHO}/${APP}/pacote/construir.sh" "${SAIDA}")"
  else
    DEB="$(bash "${TRABALHO}/${APP}/pacote/construir.sh" "${SAIDA}")"
  fi
  echo "${REPO} (${REF}, $(git -C "${TRABALHO}/${APP}" rev-parse --short=7 HEAD)): ${DEB}"
done
