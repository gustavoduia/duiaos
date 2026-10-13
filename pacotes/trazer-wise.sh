#!/bin/bash
# =============================================================================
# DuiaOS — gera o pacote do Wise (duiaos-wise_*.deb) a partir do repositório
# PRIVADO gustavoduia/duiaos-wise, para ir na ISO e no repositório apt junto
# com o resto do sistema (ADR 042: o Wise é parte nativa do DuiaOS).
#
# Uso: bash pacotes/trazer-wise.sh PASTA_DE_SAIDA
#
# Variáveis:
#   DUIAOS_TOKEN_WISE  token só de LEITURA do duiaos-wise (segredo do GitHub).
#                      Fica só neste passo: não vai para a ISO nem para o log.
#   SUITE              estavel (lançamento: exige a tag do Wise igual à do
#                      sistema) ou teste (main do Wise).
#   VERSAO_SISTEMA     versão lançada (ex.: 0.3.0), usada com SUITE=estavel.
#   WISE_REF           (opcional) branch ou tag do Wise a usar.
#
# Sem o token: num lançamento, falha (o sistema não sai sem o Wise); fora
# dele, avisa e segue sem o Wise.
# =============================================================================
set -euo pipefail

SAIDA="${1:?Uso: bash pacotes/trazer-wise.sh PASTA_DE_SAIDA}"
REPO="gustavoduia/duiaos-wise"
SUITE="${SUITE:-teste}"

if [ -z "${DUIAOS_TOKEN_WISE:-}" ]; then
  if [ "${SUITE}" = "estavel" ]; then
    echo "Falta o segredo DUIAOS_TOKEN_WISE: um lançamento não sai sem o Wise." >&2
    exit 1
  fi
  echo "::warning::Sem o segredo DUIAOS_TOKEN_WISE: pacotes e ISO de teste sem o Wise."
  exit 0
fi

if [ "${SUITE}" = "estavel" ]; then
  REF="${WISE_REF:-v${VERSAO_SISTEMA:?VERSAO_SISTEMA é obrigatória num lançamento}}"
else
  REF="${WISE_REF:-main}"
fi

TRABALHO="$(mktemp -d)"
trap 'rm -rf "${TRABALHO}"' EXIT
# O token vai num cabeçalho só deste comando (não fica na URL nem no .git/config)
AUTH="$(printf 'x-access-token:%s' "${DUIAOS_TOKEN_WISE}" | base64 -w0)"
if ! git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic ${AUTH}" \
    clone -q --filter=blob:none --branch "${REF}" "https://github.com/${REPO}.git" "${TRABALHO}/wise"; then
  echo "Não consegui baixar o Wise (${REF}). Confira o token e, num lançamento, se a tag ${REF} existe no ${REPO}." >&2
  exit 1
fi
git -C "${TRABALHO}/wise" -c "http.https://github.com/.extraheader=AUTHORIZATION: basic ${AUTH}" \
  fetch -q --tags origin

mkdir -p "${SAIDA}"
if [ "${SUITE}" = "estavel" ]; then
  DEB="$(VERSAO_DEB="${VERSAO_SISTEMA//-/\~}" bash "${TRABALHO}/wise/pacote/construir.sh" "${SAIDA}")"
else
  DEB="$(bash "${TRABALHO}/wise/pacote/construir.sh" "${SAIDA}")"
fi
echo "Wise (${REF}, $(git -C "${TRABALHO}/wise" rev-parse --short=7 HEAD)): ${DEB}"
