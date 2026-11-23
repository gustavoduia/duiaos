#!/bin/bash
# =============================================================================
# DuiaOS — publica pacotes .deb no repositório apt (pasta de um site estático).
#
# Uso: bash pacotes/publicar.sh PASTA_DO_REPOSITORIO ARQUIVO.deb...
#
# Fluxo único de atualizações (ADR 074): todo pacote publicado vai para todos os
# computadores, de qualquer ISO. Os canais "estavel" (o gravado nas ISOs) e
# "teste" (o das ISOs antigas de desenvolvimento) mostram o MESMO índice, de uma
# pasta de pacotes só. Assim nenhum computador fica de fora de uma atualização.
#
# Estrutura gerada (padrão do Debian):
#   pool/main/*.deb                        pacotes (as versões mais novas de cada
#                                          pacote em cada arquitetura)
#   dists/estavel/...  dists/teste/...     índice (Packages) e Release assinados
#   duiaos.asc, duiaos.gpg                 chave pública (texto e binária)
#
# Limites do GitHub Pages: nenhum arquivo passa de 100 MB e o site todo deve
# ficar abaixo de 1 GB. O script confere os dois antes de publicar.
#
# Requer: apt-ftparchive (apt-utils), dpkg, gpg com a chave de assinatura
# importada (DUIAOS_APT_CHAVE_ID escolhe a chave; padrão: a primeira secreta).
# =============================================================================
set -euo pipefail

REPO="${1:?Uso: publicar.sh PASTA ARQUIVO.deb...}"
shift
[ "$#" -gt 0 ] || { echo "Nenhum .deb informado." >&2; exit 1; }
CANAIS="estavel teste"
ARQUITETURAS="amd64 arm64 all"
MANTER=3             # versões guardadas de cada pacote (o apt só precisa da mais nova)
MANTER_GRANDE=2      # pacotes acima de GRANDE_MB (motor web, Ollama, voz)
GRANDE_MB=25
LIMITE_ARQUIVO_MB=95
LIMITE_SITE_MB=950

CHAVE="${DUIAOS_APT_CHAVE_ID:-$(gpg --batch --list-secret-keys --with-colons | awk -F: '/^sec/ {print $5; exit}')}"
[ -n "${CHAVE}" ] || { echo "Nenhuma chave secreta no gpg para assinar." >&2; exit 1; }

mkdir -p "${REPO}/pool/main"
REPO="$(cd "${REPO}" && pwd)"
POOL="${REPO}/pool/main"

# Repositório antigo (um pool por canal): junta tudo na pasta única
for ANTIGO in "${REPO}"/pool/estavel "${REPO}"/pool/teste; do
  [ -d "${ANTIGO}" ] || continue
  for DEB in "${ANTIGO}"/*.deb; do
    [ -e "${DEB}" ] || continue
    [ -e "${POOL}/$(basename "${DEB}")" ] || mv "${DEB}" "${POOL}/"
  done
  rm -rf -- "${ANTIGO:?}"
done

for DEB in "$@"; do
  MB=$(( $(stat -c %s "${DEB}") / 1048576 ))
  if [ "${MB}" -gt "${LIMITE_ARQUIVO_MB}" ]; then
    echo "$(basename "${DEB}") tem ${MB} MB: passa do limite de ${LIMITE_ARQUIVO_MB} MB por arquivo do GitHub Pages." >&2
    echo "Divida o pacote (como o duiaos-motor-web e o duiaos-motor-web-chromium). Nada foi publicado." >&2
    exit 1
  fi
done
# Uma versão publicada não muda: se o arquivo já está no repositório (ex.: o
# duiaos-ollama, cuja versão só muda com uma versão nova do Ollama), fica o que
# já foi publicado. Trocar o conteúdo de uma versão quebra quem já baixou.
for DEB in "$@"; do
  if [ -e "${POOL}/$(basename "${DEB}")" ]; then
    echo "Já publicado (mantido): $(basename "${DEB}")"
  else
    cp "${DEB}" "${POOL}/"
  fi
done

# Mantém só as versões mais novas de cada pacote, em cada arquitetura
# (nome_versão_arquitetura.deb)
for GRUPO in $(find "${POOL}" -name '*.deb' -printf '%f\n' \
    | awk -F_ '{sub(/\.deb$/, "", $3); print $1 "_" $3}' | sort -u); do
  NOME="${GRUPO%_*}"
  ARQUITETURA="${GRUPO##*_}"
  VERSOES=()
  MAIOR=0
  for ARQ in "${POOL}/${NOME}"_*_"${ARQUITETURA}".deb; do
    VERSOES+=("$(dpkg-deb -f "${ARQ}" Version) ${ARQ}")
    TAM=$(( $(stat -c %s "${ARQ}") / 1048576 ))
    [ "${TAM}" -gt "${MAIOR}" ] && MAIOR="${TAM}"
  done
  GUARDAR="${MANTER}"
  [ "${MAIOR}" -gt "${GRANDE_MB}" ] && GUARDAR="${MANTER_GRANDE}"
  # Ordena pela regra de versões do Debian (da mais nova para a mais velha)
  ORDENADAS=()
  for ITEM in "${VERSOES[@]}"; do
    POS=${#ORDENADAS[@]}
    for i in "${!ORDENADAS[@]}"; do
      if dpkg --compare-versions "${ITEM%% *}" gt "${ORDENADAS[$i]%% *}"; then POS=$i; break; fi
    done
    ORDENADAS=("${ORDENADAS[@]:0:${POS}}" "${ITEM}" "${ORDENADAS[@]:${POS}}")
  done
  for ITEM in "${ORDENADAS[@]:${GUARDAR}}"; do
    rm -f "${ITEM#* }"
    echo "Removido (versão antiga): $(basename "${ITEM#* }")"
  done
done

TOTAL_MB=$(( $(du -sb "${REPO}" | cut -f1) / 1048576 ))
if [ "${TOTAL_MB}" -gt "${LIMITE_SITE_MB}" ]; then
  echo "O repositório ficaria com ${TOTAL_MB} MB (limite: ${LIMITE_SITE_MB} MB do GitHub Pages). Nada foi publicado." >&2
  exit 1
fi

# Índices: cada binary-ARQ lista os pacotes daquela arquitetura e os "all".
# O índice é gerado uma vez e copiado para cada canal (conteúdo idêntico).
cd "${REPO}"
for CANAL in ${CANAIS}; do
  DISTS="dists/${CANAL}"
  rm -rf -- "${DISTS:?}"
  for ARQ in ${ARQUITETURAS}; do
    mkdir -p "${DISTS}/main/binary-${ARQ}"
    apt-ftparchive --arch "${ARQ}" packages pool/main > "${DISTS}/main/binary-${ARQ}/Packages"
    gzip -9nkf "${DISTS}/main/binary-${ARQ}/Packages"
  done
  apt-ftparchive \
    -o APT::FTPArchive::Release::Origin=DuiaOS \
    -o APT::FTPArchive::Release::Label=DuiaOS \
    -o "APT::FTPArchive::Release::Suite=${CANAL}" \
    -o "APT::FTPArchive::Release::Codename=${CANAL}" \
    -o "APT::FTPArchive::Release::Architectures=${ARQUITETURAS}" \
    -o APT::FTPArchive::Release::Components=main \
    -o "APT::FTPArchive::Release::Description=Atualizações do DuiaOS (fluxo único; ADR 074)" \
    release "${DISTS}" > "${REPO}/Release.tmp"
  mv "${REPO}/Release.tmp" "${DISTS}/Release"
  gpg --batch --yes --local-user "${CHAVE}" --clearsign -o "${DISTS}/InRelease" "${DISTS}/Release"
  gpg --batch --yes --local-user "${CHAVE}" --armor --detach-sign -o "${DISTS}/Release.gpg" "${DISTS}/Release"
done
gpg --batch --yes --armor --export "${CHAVE}" > "${REPO}/duiaos.asc"
gpg --batch --yes --export "${CHAVE}" > "${REPO}/duiaos.gpg"   # formato do Signed-By

echo "Publicado em ${REPO} (canais ${CANAIS}, ${TOTAL_MB} MB):"
find "${POOL}" -name '*.deb' -printf '  %f\n' | sort
