#!/usr/bin/env bash
# =============================================================================
# DuiaOS — gera a ISO do sistema com o live-build do Debian.
#
# Precisa rodar como root dentro de um Debian 13 (trixie). No GitHub Actions
# isso acontece num container Docker; no Dell, pode rodar direto no sistema.
#
# Variáveis de ambiente (todas opcionais):
#   ARCH            amd64 ou arm64 (padrão: a arquitetura da máquina)
#   DUIAOS_VERSION  versão que aparece no sistema (padrão: 0.0.0-dev)
#   WORK_DIR        pasta de trabalho do live-build (padrão: /tmp/duiaos-build-ARCH)
#   VERSAO_DEB      versão dos pacotes do DuiaOS (pacotes/versao.sh; padrão: 0.0.0+local)
#   SUITE           canal do repositório apt gravado no sistema: estavel ou teste
#
# Resultado: out/duiaos-VERSÃO-ARCH.iso, o .sha256 e a lista de pacotes (.packages).
# =============================================================================
set -euo pipefail

ARCH="${ARCH:-$(dpkg --print-architecture)}"
VERSION="${DUIAOS_VERSION:-0.0.0-dev}"
CODENAME="zoinho"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${WORK_DIR:-/tmp/duiaos-build-${ARCH}}"
OUT="${ROOT}/out"
ISO_LIMIT_BYTES=$((2 * 1024 * 1024 * 1024 - 1))   # limite por arquivo dos releases do GitHub

log() { printf '\n==> %s\n' "$*"; }

case "${ARCH}" in
  amd64|arm64) ;;
  *) echo "Arquitetura não suportada: ${ARCH} (use amd64 ou arm64)" >&2; exit 1 ;;
esac

if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa rodar como root." >&2
  exit 1
fi

log "DuiaOS ${VERSION} (${CODENAME}) — arquitetura ${ARCH}"

log "Instalando o live-build"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq live-build curl ca-certificates zstd >/dev/null   # curl e zstd: pacote duiaos-ollama

log "Preparando a pasta de trabalho ${WORK}"
rm -rf "${WORK}"
mkdir -p "${WORK}" "${OUT}"
cd "${WORK}"

# Volume da ISO: no máximo 32 caracteres.
VOLUME="DuiaOS ${VERSION}"
VOLUME="${VOLUME:0:32}"

# Secure Boot: a ISO e o sistema instalado iniciam com o Secure Boot ligado
# (shim e GRUB assinados). Assim o usuário não precisa desligá-lo na BIOS,
# o que evita pedidos de chave do BitLocker em computadores com Windows.
# Instalador: debian-installer em modo "live" (copia o sistema da ISO
# para o disco). Respostas pré-definidas em config/includes.installer/.
# Firmwares: o live-build não instala todos automaticamente
# (--firmware-chroot false). Entram só os listados em package-lists/.
log "Configurando o live-build"
lb config \
  --mode debian \
  --distribution trixie \
  --architecture "${ARCH}" \
  --archive-areas "main contrib non-free non-free-firmware" \
  --binary-images iso-hybrid \
  --debian-installer live \
  --uefi-secure-boot enable \
  --debian-installer-distribution trixie \
  --firmware-chroot false \
  --firmware-binary false \
  --image-name duiaos \
  --iso-application "DuiaOS" \
  --iso-publisher "DuiaOS; https://github.com/gustavoduia/duiaos-fontes-abertas" \
  --iso-volume "${VOLUME}" \
  --memtest none \
  --bootappend-live "boot=live components quiet splash hostname=duiaos username=duia locales=pt_BR.UTF-8 keyboard-layouts=br timezone=America/Sao_Paulo"

log "Copiando a configuração do DuiaOS"
cp -a "${ROOT}/build/config/." config/
if [ -d "${ROOT}/build/arch/${ARCH}" ]; then
  cp -a "${ROOT}/build/arch/${ARCH}/." config/
fi

# Código próprio do DuiaOS: os pacotes .deb (duiaos-identidade, duiaos-shell,
# duiaos-desktop e duiaos-ollama) são gerados aqui, do mesmo commit, e instalados na ISO pelo
# live-build (config/packages.chroot). O sistema instalado recebe as
# atualizações seguintes pelo repositório apt do DuiaOS (ADR 023).
# Variáveis vindas do workflow: VERSAO_DEB, SUITE e, se houver, a chave
# pública em pacotes/chave.gpg (exportada do segredo DUIAOS_APT_CHAVE).
log "Gerando os pacotes do DuiaOS"
CHAVE="${ROOT}/pacotes/chave.gpg"
[ -s "${CHAVE}" ] || CHAVE=""
VERSAO_DEB="${VERSAO_DEB:-0.0.0+local}" VERSAO_SISTEMA="${VERSION}" SUITE="${SUITE:-teste}" \
  CHAVE_PUBLICA="${CHAVE}" bash "${ROOT}/pacotes/construir.sh" config/packages.chroot
# Ollama (IA local, ADR 030): pacote da arquitetura da ISO, feito do release
# oficial sem CUDA. O modelo padrão não vai na ISO: é baixado no 1º login.
bash "${ROOT}/pacotes/duiaos-ollama/construir.sh" "${ARCH}" config/packages.chroot \
  "${OLLAMA_CACHE:-${ROOT}/.cache/ollama}"

chmod +x config/hooks/normal/*.hook.* 2>/dev/null || true

log "Gerando a ISO (isso leva de 10 a 30 minutos)"
lb build

ISO_SRC="$(find . -maxdepth 1 -name '*.iso' -print -quit)"
if [ -z "${ISO_SRC}" ]; then
  echo "O live-build terminou sem gerar a ISO. Veja o log acima." >&2
  exit 1
fi

ISO_NAME="duiaos-${VERSION}-${ARCH}.iso"
mv "${ISO_SRC}" "${OUT}/${ISO_NAME}"

# Lista de pacotes com versões exatas: publicada com a ISO para que qualquer
# pessoa localize o código-fonte de cada componente livre (snapshot.debian.org).
PACKAGES_SRC="$(find . -maxdepth 1 -name '*.packages' -print -quit)"
if [ -n "${PACKAGES_SRC}" ]; then
  cp "${PACKAGES_SRC}" "${OUT}/duiaos-${VERSION}-${ARCH}.packages"
else
  echo "AVISO: o live-build não gerou a lista de pacotes (*.packages)." >&2
fi
cd "${OUT}"
sha256sum "${ISO_NAME}" > "${ISO_NAME}.sha256"

SIZE="$(stat -c %s "${ISO_NAME}")"
log "ISO pronta: out/${ISO_NAME} ($((SIZE / 1024 / 1024)) MiB)"
if [ "${SIZE}" -gt "${ISO_LIMIT_BYTES}" ]; then
  echo "ERRO: a ISO passou de 2 GiB, o limite por arquivo dos releases do GitHub." >&2
  exit 1
fi
