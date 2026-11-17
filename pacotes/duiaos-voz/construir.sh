#!/bin/bash
# =============================================================================
# DuiaOS — gera o pacote duiaos-voz (ADR 063): o comando duiaos-voz (GPL-3, do
# repositório duiaos-fontes-abertas, pasta voz/) e o motor sherpa-onnx (rodas
# oficiais do PyPI para o Python 3.13 do Debian 13, com o sha256 fixado em VERSAO).
#
# Uso: bash pacotes/duiaos-voz/construir.sh ARQUITETURA PASTA_DE_SAIDA [CACHE]
#   ARQUITETURA  amd64 ou arm64
#
# Precisa de: bash, python3 com pip, unzip, sha256sum, dpkg-deb, find, md5sum, du, sed.
# =============================================================================
set -euo pipefail

ARQ="${1:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
SAIDA="${2:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
CACHE="${3:-${XDG_CACHE_HOME:-${HOME}/.cache}/duiaos}/voz-${ARQ}"
PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "${PASTA}/../.." && pwd)"

# shellcheck source=/dev/null
. "${PASTA}/VERSAO"
case "${ARQ}" in
  amd64) PLATAFORMA=x86_64; SOMA="${SHA256_AMD64}"; SOMA_NUCLEO="${SHA256_NUCLEO_AMD64}" ;;
  arm64) PLATAFORMA=aarch64; SOMA="${SHA256_ARM64}"; SOMA_NUCLEO="${SHA256_NUCLEO_ARM64}" ;;
  *) echo "Arquitetura inválida: ${ARQ} (use amd64 ou arm64)" >&2; exit 1 ;;
esac
VERSAO_DEB="${SHERPA}-duiaos${REVISAO}"

# O programa (GPL-3) vem do duiaos-fontes-abertas: ./fontes-abertas nos workflows, ao lado nos computadores
FONTES=""
for CANDIDATO in "${DUIAOS_FONTES_ABERTAS:-}" "${RAIZ}/fontes-abertas" "${RAIZ}/../duiaos-fontes-abertas"; do
  [ -n "${FONTES}" ] || { [ -n "${CANDIDATO}" ] && [ -f "${CANDIDATO}/voz/duiaos-voz" ] && FONTES="${CANDIDATO}"; }
done
[ -n "${FONTES}" ] || { echo "Não achei voz/duiaos-voz no duiaos-fontes-abertas (clone-o ao lado deste repositório)." >&2; exit 1; }

mkdir -p "${SAIDA}" "${CACHE}"
SAIDA="$(cd "${SAIDA}" && pwd)"
TRABALHO="$(mktemp -d)"
trap 'rm -rf "${TRABALHO}"' EXIT
echo "==> duiaos-voz ${VERSAO_DEB} (${ARQ})"

# 1. Baixa (ou reaproveita) as duas rodas e confere
conferir() {
  local SOMAS
  SOMAS="$(sha256sum "${CACHE}"/sherpa_onnx-"${SHERPA}"-*.whl "${CACHE}"/sherpa_onnx_core-"${SHERPA}"-*.whl 2>/dev/null | cut -d' ' -f1 | sort | tr '\n' ' ')"
  [ "${SOMAS}" = "$(printf '%s\n%s\n' "${SOMA}" "${SOMA_NUCLEO}" | sort | tr '\n' ' ')" ]
}
if ! conferir; then
  rm -f "${CACHE}"/*.whl
  python3 -m pip download --quiet --no-deps --only-binary=:all: --python-version 3.13 \
    --platform "manylinux2014_${PLATAFORMA}" --platform "manylinux_2_17_${PLATAFORMA}" \
    -d "${CACHE}" "sherpa-onnx==${SHERPA}" "sherpa-onnx-core==${SHERPA}"
fi
conferir || { echo "As rodas baixadas não conferem com o sha256 de VERSAO. Nada foi gerado." >&2; rm -f "${CACHE}"/*.whl; exit 1; }

# 2. Monta a árvore do pacote
D="${TRABALHO}/duiaos-voz"
mkdir -p "${D}/DEBIAN" "${D}/usr/bin" "${D}/usr/lib/duiaos-voz" "${D}/usr/share/doc/duiaos-voz"
cp "${PASTA}/DEBIAN/"* "${D}/DEBIAN/"
for RODA in "${CACHE}"/*.whl; do unzip -q -o "${RODA}" -d "${D}/usr/lib/duiaos-voz"; done
rm -rf "${D}/usr/lib/duiaos-voz/sherpa_onnx/include" "${D}/usr/lib/duiaos-voz/bin"
install -m 0755 "${FONTES}/voz/duiaos-voz" "${D}/usr/lib/duiaos-voz/duiaos-voz"
cat > "${D}/usr/bin/duiaos-voz" <<'LANCADOR'
#!/bin/sh
# DuiaOS — voz do sistema (o programa e o motor ficam em /usr/lib/duiaos-voz)
PYTHONPATH=/usr/lib/duiaos-voz exec python3 /usr/lib/duiaos-voz/duiaos-voz "$@"
LANCADOR
chmod 0755 "${D}/usr/bin/duiaos-voz"
{
  echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
  echo "Upstream-Name: duiaos-voz"
  echo "Source: https://github.com/gustavoduia/duiaos-fontes-abertas"
  echo
  echo "Files: usr/lib/duiaos-voz/duiaos-voz usr/bin/duiaos-voz"
  echo "Copyright: 2026 DuiaOS"
  echo "License: GPL-3+"
  echo " Texto completo em /usr/share/common-licenses/GPL-3."
  echo
  echo "Files: usr/lib/duiaos-voz/sherpa_onnx*"
  echo "Copyright: Xiaomi Corporation e colaboradores do k2-fsa/sherpa-onnx"
  echo "License: Apache-2.0"
  echo "Comment: sherpa-onnx ${SHERPA} (https://github.com/k2-fsa/sherpa-onnx), rodas oficiais do PyPI."
  echo " Inclui o ONNX Runtime (MIT) e o espeak-ng (GPL-3+, https://github.com/espeak-ng/espeak-ng)."
  echo " Texto da Apache-2.0 em /usr/share/common-licenses/Apache-2.0."
} > "${D}/usr/share/doc/duiaos-voz/copyright"

# 3. Fecha
find "${D}" -name '__pycache__' -prune -exec rm -rf {} +
find "${D}" -type d -exec chmod 0755 {} +
find "${D}" -type f ! -perm -u+x -exec chmod 0644 {} +
for A in "${D}"/DEBIAN/*; do
  sed -i -e "s|@VERSAO_DEB@|${VERSAO_DEB}|g" -e "s|@ARQUITETURA@|${ARQ}|g" "${A}"
done
(cd "${D}" && find . -path ./DEBIAN -prune -o -type f -printf '%P\0' | sort -z | xargs -0 -r md5sum) > "${D}/DEBIAN/md5sums"
TAMANHO="$(du -sk --exclude=DEBIAN "${D}" | cut -f1)"
sed -i "/^Version:/a Installed-Size: ${TAMANHO}" "${D}/DEBIAN/control"
dpkg-deb --root-owner-group -Zxz --build "${D}" "${SAIDA}/duiaos-voz_${VERSAO_DEB}_${ARQ}.deb" >/dev/null
echo "    duiaos-voz_${VERSAO_DEB}_${ARQ}.deb ($(du -h "${SAIDA}/duiaos-voz_${VERSAO_DEB}_${ARQ}.deb" | cut -f1))"
