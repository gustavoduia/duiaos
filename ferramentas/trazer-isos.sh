#!/bin/bash
# =============================================================================
# DuiaOS — copia para o Mac as ISOs de teste geradas no Dell.
# Rode NO MAC. Origem e destino: ~/Projetos/duiaos-isos (Dell → Mac).
#
#   bash ferramentas/trazer-isos.sh
#
# Só copia o que ainda não existe no Mac. Variável opcional: DELL=usuario@endereco.
# =============================================================================
set -euo pipefail

DELL="${DELL:-gustavo@duiaos}"
DESTINO="${HOME}/Projetos/duiaos-isos"
mkdir -p "${DESTINO}"

ARQUIVOS="$(ssh "${DELL}" 'cd ~/Projetos/duiaos-isos 2>/dev/null && ls -1' || true)"
if [ -z "${ARQUIVOS}" ]; then
  echo "Nenhuma ISO no Dell em ~/Projetos/duiaos-isos."
  exit 0
fi

while IFS= read -r F; do
  if [ -e "${DESTINO}/${F}" ]; then
    echo "Já existe no Mac: ${F}"
  else
    echo "Copiando: ${F}"
    scp -q "${DELL}:Projetos/duiaos-isos/${F}" "${DESTINO}/"
  fi
done <<< "${ARQUIVOS}"

echo
ls -lh "${DESTINO}"
