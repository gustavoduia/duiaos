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
apt-get install -y -qq live-build >/dev/null

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

# Interface gráfica (pasta shell/): código em /usr/share/duiaos/shell,
# configuração do labwc em /etc/xdg/labwc, sessão "DuiaOS" para gerenciadores
# de login e a lista de pacotes da interface (shell/pacotes.list).
INCLUDES="config/includes.chroot_after_packages"
install -d "${INCLUDES}/usr/share/duiaos" "${INCLUDES}/etc/xdg/labwc" "${INCLUDES}/usr/share/wayland-sessions"
rm -rf "${INCLUDES}/usr/share/duiaos/shell"
cp -a "${ROOT}/shell" "${INCLUDES}/usr/share/duiaos/shell"
find "${INCLUDES}/usr/share/duiaos/shell" -name '__pycache__' -prune -exec rm -rf {} +
install -m 0644 "${ROOT}/shell/sessao/autostart" "${ROOT}/shell/sessao/environment" \
  "${ROOT}/shell/sessao/rc.xml" "${INCLUDES}/etc/xdg/labwc/"
install -m 0644 "${ROOT}/shell/sessao/duiaos.desktop" "${INCLUDES}/usr/share/wayland-sessions/"
install -m 0644 "${ROOT}/shell/pacotes.list" config/package-lists/duiaos-interface.list.chroot

# Licença e avisos de terceiros dentro do sistema (fonte: pasta publico/).
LICENCA_DIR="config/includes.chroot_after_packages/usr/share/duiaos/licenca"
install -d "${LICENCA_DIR}"
install -m 0644 "${ROOT}/publico/EULA.md" "${ROOT}/publico/LICENCAS-DE-TERCEIROS.md" \
  "${ROOT}/publico/TRADEMARKS.md" "${LICENCA_DIR}/"

# Coloca a versão nos hooks (ex.: /etc/os-release).
find config/hooks -name '*.hook.*' -type f -exec \
  sed -i -e "s|@DUIAOS_VERSION@|${VERSION}|g" -e "s|@DUIAOS_CODENAME@|${CODENAME}|g" {} +
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
