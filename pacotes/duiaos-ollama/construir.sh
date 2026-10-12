#!/bin/bash
# =============================================================================
# DuiaOS — gera o pacote duiaos-ollama (ADR 030) a partir do release oficial.
#
# Uso: bash pacotes/duiaos-ollama/construir.sh ARQUITETURA PASTA_DE_SAIDA [CACHE]
#   ARQUITETURA  amd64 ou arm64
#   CACHE        pasta onde o .tar.zst baixado fica guardado (padrão: ~/.cache/duiaos)
#
# Baixa ollama-linux-ARQ.tar.zst do GitHub, confere o sha256 fixado em VERSAO,
# descarta as bibliotecas CUDA (NVIDIA, mais de 1 GB) e monta o .deb com
# /usr/bin/ollama, /usr/lib/ollama e o serviço ollama.service.
#
# Versão do pacote: OLLAMA-duiaosREVISAO (ex.: 0.40.3-duiaos1). Ela só muda
# quando VERSAO muda, por isso o repositório apt não recebe uma cópia nova a
# cada envio para a main (publicar.sh não sobrescreve uma versão já publicada).
#
# Precisa de: bash, curl, zstd, tar, sha256sum, dpkg-deb, find, md5sum, du, sed.
# =============================================================================
set -euo pipefail

ARQ="${1:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
SAIDA="${2:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
CACHE="${3:-${XDG_CACHE_HOME:-${HOME}/.cache}/duiaos}"
PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "${PASTA}/VERSAO"
case "${ARQ}" in
  amd64) SHA256="${SHA256_AMD64}" ;;
  arm64) SHA256="${SHA256_ARM64}" ;;
  *) echo "Arquitetura inválida: ${ARQ} (use amd64 ou arm64)" >&2; exit 1 ;;
esac
VERSAO_DEB="${OLLAMA}-duiaos${REVISAO}"
ARQUIVO="ollama-linux-${ARQ}-v${OLLAMA}.tar.zst"
URL="https://github.com/ollama/ollama/releases/download/v${OLLAMA}/ollama-linux-${ARQ}.tar.zst"

mkdir -p "${SAIDA}" "${CACHE}"
SAIDA="$(cd "${SAIDA}" && pwd)"
TRABALHO="$(mktemp -d)"
trap 'rm -rf "${TRABALHO}"' EXIT

echo "==> duiaos-ollama ${VERSAO_DEB} (${ARQ})"

# 1. Baixa (ou reaproveita do cache) e confere
if ! echo "${SHA256}  ${CACHE}/${ARQUIVO}" | sha256sum -c --status 2>/dev/null; then
  echo "    baixando ${URL}"
  PROGRESSO="-sS"; [ -t 2 ] && PROGRESSO="--progress-bar"
  curl -fL --retry 3 "${PROGRESSO}" -o "${CACHE}/${ARQUIVO}.parcial" "${URL}"
  mv "${CACHE}/${ARQUIVO}.parcial" "${CACHE}/${ARQUIVO}"
fi
if ! echo "${SHA256}  ${CACHE}/${ARQUIVO}" | sha256sum -c --status; then
  echo "O arquivo baixado não confere com o sha256 de VERSAO. Nada foi gerado." >&2
  rm -f "${CACHE}/${ARQUIVO}"
  exit 1
fi

# 2. Extrai sem o CUDA
mkdir -p "${TRABALHO}/extraido"
tar --zstd -xf "${CACHE}/${ARQUIVO}" -C "${TRABALHO}/extraido" \
  --no-same-owner --exclude='lib/ollama/cuda_*' --exclude='./lib/ollama/cuda_*'
EXTRAIDO="${TRABALHO}/extraido"
[ -x "${EXTRAIDO}/bin/ollama" ] || { echo "Release sem bin/ollama: formato mudou?" >&2; exit 1; }

# 3. Monta a árvore do pacote
D="${TRABALHO}/duiaos-ollama"
mkdir -p "${D}/DEBIAN" "${D}/usr/bin" "${D}/usr/lib"
cp -R "${PASTA}/raiz/." "${D}/"
cp "${PASTA}/DEBIAN/"* "${D}/DEBIAN/"
install -m 0755 "${EXTRAIDO}/bin/ollama" "${D}/usr/bin/ollama"
# O ollama procura as bibliotecas em <binário>/../lib/ollama
cp -R "${EXTRAIDO}/lib/ollama" "${D}/usr/lib/ollama"

DOC="${D}/usr/share/doc/duiaos-ollama"
install -d "${DOC}"
{
  echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
  echo "Upstream-Name: Ollama"
  echo "Source: https://github.com/ollama/ollama/releases/tag/v${OLLAMA}"
  echo "Comment: Binários oficiais do Ollama ${OLLAMA}, sem as bibliotecas CUDA."
  echo "  Empacotado pelo DuiaOS (pacotes/duiaos-ollama)."
  echo
  echo "Files: *"
  echo "Copyright: Ollama"
  echo "License: MIT"
  echo
  sed 's/^$/./; s/^/ /' "${PASTA}/LICENSE-ollama"
  # Licenças de terceiros que o próprio release traz (llama.cpp/ggml, Go,
  # cpp-httplib...): ficam em /usr/lib/ollama, junto das bibliotecas
  echo
  echo "Files: usr/lib/ollama/*"
  echo "Copyright: Ollama e autores do llama.cpp/ggml e demais componentes"
  echo "License: MIT"
  echo "Comment: Os textos das licenças de terceiros trazidos pelo release oficial"
  echo "  estão em:"
  find "${D}/usr/lib/ollama" -maxdepth 1 -type f -iname '*licen[cs]e*' -printf '  /usr/lib/ollama/%P\n' | sort
} > "${DOC}/copyright"

# 4. Fecha: permissões, marcadores, md5sums, tamanho
find "${D}" -type d -exec chmod 0755 {} +
find "${D}" -type f ! -perm -u+x -exec chmod 0644 {} +
find "${D}" -type f -perm -u+x -exec chmod 0755 {} +
for A in "${D}"/DEBIAN/*; do
  sed -i -e "s|@VERSAO_DEB@|${VERSAO_DEB}|g" -e "s|@ARQUITETURA@|${ARQ}|g" "${A}"
done
(cd "${D}" && find . -path ./DEBIAN -prune -o -type f -printf '%P\0' \
  | sort -z | xargs -0 -r md5sum) > "${D}/DEBIAN/md5sums"
TAMANHO="$(du -sk --exclude=DEBIAN "${D}" | cut -f1)"
sed -i "/^Version:/a Installed-Size: ${TAMANHO}" "${D}/DEBIAN/control"

dpkg-deb --root-owner-group -Zxz --build "${D}" \
  "${SAIDA}/duiaos-ollama_${VERSAO_DEB}_${ARQ}.deb" >/dev/null
echo "    duiaos-ollama_${VERSAO_DEB}_${ARQ}.deb ($(du -h "${SAIDA}/duiaos-ollama_${VERSAO_DEB}_${ARQ}.deb" | cut -f1))"
