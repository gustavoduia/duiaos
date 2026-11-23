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
#   LANCAMENTO         sim (tag do sistema: exige a mesma tag nos dois repositórios) ou nao (main).
#   VERSAO_SISTEMA     versão lançada (ex.: 0.3.0), usada com LANCAMENTO=sim.
#   APPS_REF           (opcional) branch ou tag a usar nos dois repositórios.
#
# Sem o token, falha sempre: o duiaos-desktop depende do duiaos-ora e do duiaos-mailbox (ADR 074), então
# publicar ou gerar uma ISO sem eles deixaria os computadores sem conseguir atualizar.
# =============================================================================
set -euo pipefail

SAIDA="${1:?Uso: bash pacotes/trazer-apps.sh PASTA_DE_SAIDA}"
LANCAMENTO="${LANCAMENTO:-nao}"
TOKEN="${DUIAOS_TOKEN_APPS:-${DUIAOS_TOKEN_WISE:-}}"

if [ -z "${TOKEN}" ]; then
  echo "Falta o segredo DUIAOS_TOKEN_APPS (leitura do duiaos-ora e do duiaos-mailbox): o DuiaOS não sai sem" >&2
  echo "o Ora e o Mail Box. Passo a passo: docs/continuidade/TOKEN-DOS-APLICATIVOS.md" >&2
  exit 1
fi

if [ "${LANCAMENTO}" = "sim" ]; then
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
    if [ "${LANCAMENTO}" = "sim" ]; then
      echo "Não consegui baixar o ${REPO} na tag ${REF}: confira se a tag existe e se o token lê o repositório." >&2
    else
      echo "Sem acesso ao ${REPO} (${REF}): o segredo DUIAOS_TOKEN_APPS precisa ler esse repositório." >&2
      echo "Passo a passo: docs/continuidade/TOKEN-DOS-APLICATIVOS.md" >&2
    fi
    exit 1
  fi
  if [ "${LANCAMENTO}" = "sim" ]; then
    DEB="$(VERSAO_DEB="${VERSAO_SISTEMA//-/\~}" bash "${TRABALHO}/${APP}/pacote/construir.sh" "${SAIDA}")"
  else
    DEB="$(bash "${TRABALHO}/${APP}/pacote/construir.sh" "${SAIDA}")"
  fi
  echo "${REPO} (${REF}, $(git -C "${TRABALHO}/${APP}" rev-parse --short=7 HEAD)): ${DEB}"
done
