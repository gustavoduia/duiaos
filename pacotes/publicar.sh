#!/bin/bash
# =============================================================================
# DuiaOS — publica pacotes .deb no repositório apt (pasta de um site estático).
#
# Uso: bash pacotes/publicar.sh PASTA_DO_REPOSITORIO CANAL ARQUIVO.deb...
#   CANAL: estavel ou teste
#
# Estrutura gerada (padrão do Debian):
#   pool/CANAL/*.deb                       pacotes (as 5 versões mais novas de cada)
#   dists/CANAL/main/binary-*/Packages     índice dos pacotes
#   dists/CANAL/Release, InRelease, Release.gpg   índice assinado
#   duiaos.asc                             chave pública para conferir as assinaturas
#
# Requer: apt-ftparchive (apt-utils), dpkg, gpg com a chave de assinatura
# importada (DUIAOS_APT_CHAVE_ID escolhe a chave; padrão: a primeira secreta).
# =============================================================================
set -euo pipefail

REPO="${1:?Uso: publicar.sh PASTA CANAL ARQUIVO.deb...}"
CANAL="${2:?Informe o canal: estavel ou teste}"
shift 2
[ "$#" -gt 0 ] || { echo "Nenhum .deb informado." >&2; exit 1; }
case "${CANAL}" in estavel|teste) ;; *) echo "Canal inválido: ${CANAL}" >&2; exit 1 ;; esac
MANTER=5
ARQUITETURAS="amd64 arm64 all"

CHAVE="${DUIAOS_APT_CHAVE_ID:-$(gpg --batch --list-secret-keys --with-colons | awk -F: '/^sec/ {print $5; exit}')}"
[ -n "${CHAVE}" ] || { echo "Nenhuma chave secreta no gpg para assinar." >&2; exit 1; }

mkdir -p "${REPO}/pool/${CANAL}"
REPO="$(cd "${REPO}" && pwd)"
cp -f "$@" "${REPO}/pool/${CANAL}/"

# Mantém só as versões mais novas de cada pacote
for NOME in $(find "${REPO}/pool/${CANAL}" -name '*.deb' -printf '%f\n' | cut -d_ -f1 | sort -u); do
  VERSOES=()
  for ARQ in "${REPO}/pool/${CANAL}/${NOME}"_*.deb; do
    VERSOES+=("$(dpkg-deb -f "${ARQ}" Version) ${ARQ}")
  done
  # Ordena pela regra de versões do Debian (da mais nova para a mais velha)
  ORDENADAS=()
  for ITEM in "${VERSOES[@]}"; do
    POS=${#ORDENADAS[@]}
    for i in "${!ORDENADAS[@]}"; do
      if dpkg --compare-versions "${ITEM%% *}" gt "${ORDENADAS[$i]%% *}"; then POS=$i; break; fi
    done
    ORDENADAS=("${ORDENADAS[@]:0:${POS}}" "${ITEM}" "${ORDENADAS[@]:${POS}}")
  done
  for ITEM in "${ORDENADAS[@]:${MANTER}}"; do
    rm -f "${ITEM#* }"
    echo "Removido (versão antiga): $(basename "${ITEM#* }")"
  done
done

# Índices
cd "${REPO}"
DISTS="dists/${CANAL}"
rm -rf "${DISTS}"
for ARQ in ${ARQUITETURAS}; do
  mkdir -p "${DISTS}/main/binary-${ARQ}"
  apt-ftparchive packages "pool/${CANAL}" > "${DISTS}/main/binary-${ARQ}/Packages"
  gzip -9nkf "${DISTS}/main/binary-${ARQ}/Packages"
done
apt-ftparchive \
  -o APT::FTPArchive::Release::Origin=DuiaOS \
  -o APT::FTPArchive::Release::Label=DuiaOS \
  -o "APT::FTPArchive::Release::Suite=${CANAL}" \
  -o "APT::FTPArchive::Release::Codename=${CANAL}" \
  -o "APT::FTPArchive::Release::Architectures=${ARQUITETURAS}" \
  -o APT::FTPArchive::Release::Components=main \
  -o "APT::FTPArchive::Release::Description=Pacotes do DuiaOS (canal ${CANAL})" \
  release "${DISTS}" > "${REPO}/Release.tmp"
mv "${REPO}/Release.tmp" "${DISTS}/Release"

# Assinaturas
gpg --batch --yes --local-user "${CHAVE}" --clearsign -o "${DISTS}/InRelease" "${DISTS}/Release"
gpg --batch --yes --local-user "${CHAVE}" --armor --detach-sign -o "${DISTS}/Release.gpg" "${DISTS}/Release"
gpg --batch --yes --armor --export "${CHAVE}" > "${REPO}/duiaos.asc"

echo "Canal ${CANAL} publicado em ${REPO}:"
find "${REPO}/pool/${CANAL}" -name '*.deb' -printf '  %f\n' | sort
