#!/bin/bash
# =============================================================================
# DuiaOS — aplica o código do repositório a um DuiaOS JÁ INSTALADO, sem
# reinstalar. Faz o mesmo que a ISO faria: instala os pacotes da interface,
# copia os arquivos do sistema e da interface e liga a Tela de Entrada e a
# animação de boot.
#
# Onde rodar: 🔗 DELL (sessão SSH) — na janela já conectada ao Dell
# (ou 💻 DELL LOCAL, no teclado do próprio Dell). Nunca no Mac.
#   cd ~/Projetos/duiaos && git pull && sudo bash ferramentas/atualizar-sistema.sh
#
# Depois, reinicie. Para voltar ao início manual pelo terminal:
#   sudo systemctl disable greetd && sudo systemctl set-default multi-user.target
#
# Provisório: na P3b (ADR 023) as atualizações passam a vir pelo apt (.deb).
# Mantenha este script em sincronia com build/build.sh e os hooks da ISO.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INCLUDES="${ROOT}/build/config/includes.chroot_after_packages"
USUARIO="${SUDO_USER:-}"

log() { printf '\n==> %s\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Use com sudo: sudo bash $0" >&2
  exit 1
fi
. /etc/os-release
if [ "${ID:-}" != "duiaos" ]; then
  echo "Este computador não é um DuiaOS (${PRETTY_NAME:-desconhecido}). Nada foi feito." >&2
  exit 1
fi
if grep -qw 'boot=live' /proc/cmdline; then
  echo "Rodando no modo live (pendrive): instale o DuiaOS antes. Nada foi feito." >&2
  exit 1
fi

log "Código: $(git -C "${ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null) @ $(git -C "${ROOT}" rev-parse --short HEAD 2>/dev/null)"

log "Instalando os pacotes da interface (shell/pacotes.list)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# shellcheck disable=SC2046
apt-get install -y -q $(grep -v '^#' "${ROOT}/shell/pacotes.list" | grep -v '^[[:space:]]*$')

log "Copiando os arquivos do sistema (build/config/includes.chroot_after_packages)"
# Dono root e permissões do repositório (o -a manteria o dono "gustavo")
cp -R --preserve=mode,timestamps "${INCLUDES}/." /

log "Copiando a interface para /usr/share/duiaos/shell"
rm -rf /usr/share/duiaos/shell
cp -R --preserve=mode,timestamps "${ROOT}/shell" /usr/share/duiaos/shell
find /usr/share/duiaos/shell -name '__pycache__' -prune -exec rm -rf {} +
install -d /etc/xdg/labwc /usr/share/wayland-sessions /usr/share/duiaos/licenca
install -m 0644 "${ROOT}/shell/sessao/autostart" "${ROOT}/shell/sessao/environment" \
  "${ROOT}/shell/sessao/rc.xml" /etc/xdg/labwc/
install -m 0644 "${ROOT}/shell/sessao/duiaos.desktop" /usr/share/wayland-sessions/
install -m 0644 "${ROOT}/publico/EULA.md" "${ROOT}/publico/LICENCAS-DE-TERCEIROS.md" \
  "${ROOT}/publico/TRADEMARKS.md" /usr/share/duiaos/licenca/

# Configurações antigas do labwc na pasta do usuário (instruções de teste
# anteriores) teriam prioridade sobre as do sistema: guarda com outro nome.
if [ -n "${USUARIO}" ]; then
  PASTA_LABWC="$(getent passwd "${USUARIO}" | cut -d: -f6)/.config/labwc"
  for ARQUIVO in autostart environment rc.xml; do
    if [ -f "${PASTA_LABWC}/${ARQUIVO}" ]; then
      mv "${PASTA_LABWC}/${ARQUIVO}" "${PASTA_LABWC}/${ARQUIVO}.antes-p3"
      echo "Guardado: ${PASTA_LABWC}/${ARQUIVO}.antes-p3"
    fi
  done
fi

log "Ligando a Tela de Entrada e a animação de boot (mesmos passos do hook 0700)"
chmod +x /usr/lib/duiaos/* \
  /usr/share/duiaos/shell/entrada/iniciar \
  /usr/share/duiaos/shell/sessao/iniciar-sessao \
  /usr/share/duiaos/shell/bloqueio/bloquear
usermod -aG video _greetd
systemctl daemon-reload
systemctl enable greetd.service
systemctl set-default graphical.target
plymouth-set-default-theme duiaos

log "Atualizando a imagem de inicialização e o menu de boot"
update-initramfs -u
update-grub

log "Pronto. Reinicie para ver a animação de boot e a Tela de Entrada: sudo reboot"
