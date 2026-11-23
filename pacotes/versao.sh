#!/bin/bash
# =============================================================================
# DuiaOS — calcula a versão dos pacotes e o canal do repositório apt.
#
# Imprime quatro linhas (para "eval" ou para $GITHUB_ENV):
#   VERSAO_DEB=...      versão dos pacotes .deb (ordem crescente para o apt)
#   VERSAO_SISTEMA=...  versão mostrada no sistema (igual ao nome da ISO)
#   SUITE=estavel       canal gravado no sistema. Desde o ADR 074 há um fluxo único de
#                       atualizações: todo envio à main é uma atualização publicada para
#                       todos os computadores, de qualquer ISO (o canal "teste" é um espelho
#                       do "estavel", mantido para quem já o tinha gravado).
#   LANCAMENTO=sim|nao  sim numa tag vX.Y.Z (ISO oficial; exige o Wise, o Ora e o Mail Box
#                       com a mesma tag)
#
# Versão lançada (tag vX.Y.Z):  X.Y.Z
# Desenvolvimento:              X.Y.Z+gitDATA.SHA
#   (X.Y.Z = última tag; DATA = data do commit em UTC). Assim cada commit
#   novo da main é uma versão maior que a anterior e que a última lançada.
# Prévias (tag v1.0.0-beta.1) viram 1.0.0~beta.1 (menor que 1.0.0, como deve).
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

debian() { echo "${1//-/\~}"; }   # 1.0.0-beta.1 -> 1.0.0~beta.1

if [ "${GITHUB_REF_TYPE:-}" = "tag" ] && [[ "${GITHUB_REF_NAME:-}" == v[0-9]* ]]; then
  VERSAO="${GITHUB_REF_NAME#v}"
  echo "VERSAO_DEB=$(debian "${VERSAO}")"
  echo "VERSAO_SISTEMA=${VERSAO}"
  echo "SUITE=estavel"
  echo "LANCAMENTO=sim"
  exit 0
fi

BASE="$(git describe --tags --abbrev=0 --match 'v[0-9]*' 2>/dev/null || echo v0.0.0)"
DATA="$(TZ=UTC git log -1 --format=%cd --date=format-local:%Y%m%d%H%M%S)"
SHA="$(git rev-parse --short=7 HEAD)"
echo "VERSAO_DEB=$(debian "${BASE#v}")+git${DATA}.${SHA}"
echo "VERSAO_SISTEMA=dev-${SHA}"
echo "SUITE=estavel"
echo "LANCAMENTO=nao"
