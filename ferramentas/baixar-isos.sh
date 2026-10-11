#!/bin/bash
# =============================================================================
# DuiaOS — baixa as ISOs de teste geradas nos servidores do GitHub para
# ~/Projetos/duiaos-isos no Mac e, se pedido, envia também para o Dell.
# Rode NO MAC.
#
#   bash ferramentas/baixar-isos.sh                # último build concluído com sucesso
#   bash ferramentas/baixar-isos.sh dell           # idem, e copia para o Dell
#   bash ferramentas/baixar-isos.sh 38182154412    # um build específico (número do gh run list)
#
# As ISOs de teste ficam 7 dias no GitHub. Variável opcional: DELL=usuario@endereco.
# =============================================================================
set -euo pipefail

DELL="${DELL:-gustavo@duiaos}"
DESTINO="${HOME}/Projetos/duiaos-isos"
RUN=""; PARA_DELL=false
for ARG in "$@"; do
  case "${ARG}" in
    dell) PARA_DELL=true ;;
    *[!0-9]*|"") echo "Argumento inválido: ${ARG}" >&2; exit 1 ;;
    *) RUN="${ARG}" ;;
  esac
done

if [ -z "${RUN}" ]; then
  RUN="$(gh run list --repo gustavoduia/duiaos --workflow gerar-iso.yml --status success -L 1 \
    --json databaseId --jq '.[0].databaseId')"
fi
[ -n "${RUN}" ] || { echo "Nenhum build concluído encontrado." >&2; exit 1; }

mkdir -p "${DESTINO}"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
echo "Baixando as ISOs do build ${RUN}..."
gh run download "${RUN}" --repo gustavoduia/duiaos -D "${TMP}"
NOVOS="$(find "${TMP}" -type f -exec basename {} \;)"
find "${TMP}" -type f -exec mv -f {} "${DESTINO}/" \;
echo "No Mac, em ${DESTINO}:"
ls -lh "${DESTINO}"

if [ "${PARA_DELL}" = true ]; then
  echo
  echo "Copiando para o Dell (${DELL}:~/Projetos/duiaos-isos)..."
  ssh "${DELL}" 'mkdir -p ~/Projetos/duiaos-isos'
  while IFS= read -r F; do
    echo "  ${F}"
    scp -q "${DESTINO}/${F}" "${DELL}:Projetos/duiaos-isos/"
  done <<< "${NOVOS}"
  ssh "${DELL}" 'ls -lh ~/Projetos/duiaos-isos'
fi
