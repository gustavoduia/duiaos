#!/bin/bash
# =============================================================================
# DuiaOS — instala o runner do GitHub Actions NA MÁQUINA ONDE RODA.
#
# Não chame direto: use ferramentas/configurar-runners.sh no Mac, que obtém o
# token de registro e chama este script no Mac ou, por SSH, no Dell.
#
# Argumentos: TOKEN_DE_REGISTRO NOME ROTULO
#   Dell (Debian/DuiaOS, x86_64): instala Docker, gh e o runner como serviço systemd.
#   Mac (macOS, Apple Silicon):   instala Colima (Docker), gh e o runner como serviço launchd.
# =============================================================================
set -euo pipefail

TOKEN="${1:?falta o token de registro}"
NOME="${2:?falta o nome do runner}"
ROTULO="${3:?falta o rótulo do runner}"
REPO_URL="https://github.com/gustavoduia/duiaos"
PASTA="${HOME}/actions-runner-duiaos"

log() { printf '\n==> %s\n' "$*"; }

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)  SO=linux; ARQ=x64 ;;
  Darwin-arm64)  SO=osx;   ARQ=arm64 ;;
  *) echo "Máquina não suportada: $(uname -s) $(uname -m)" >&2; exit 1 ;;
esac

if [ -f "${PASTA}/.runner" ]; then
  echo "O runner já está instalado em ${PASTA}. Nada a fazer."
  echo "Para reinstalar, remova-o primeiro (veja ferramentas/README.md)."
  exit 0
fi

if [ "${SO}" = "linux" ]; then
  log "Instalando Docker, git, curl e gh (pede a senha do sudo)"
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker.io git curl gh >/dev/null
  sudo systemctl enable --now docker
  sudo usermod -aG docker "${USER}"
  LIVRE_GB="$(df -BG --output=avail "${HOME}" | tail -n 1 | tr -dc '0-9')"
  if [ "${LIVRE_GB}" -lt 20 ]; then
    echo "AVISO: só ${LIVRE_GB} GB livres; cada build usa ~15 GB temporariamente." >&2
  fi
else
  if ! command -v brew >/dev/null 2>&1; then
    echo "Instale o Homebrew primeiro: https://brew.sh" >&2
    exit 1
  fi
  log "Instalando Colima, Docker (linha de comando) e gh"
  brew install colima docker gh
  if ! colima status >/dev/null 2>&1; then
    log "Criando a máquina Linux do Colima (6 CPUs, 8 GB de RAM, até 80 GB de disco)"
    colima start --cpu 6 --memory 8 --disk 80 --vm-type vz --mount-type virtiofs
    colima stop
  fi
  log "Deixando o Colima ligar sozinho com o Mac"
  brew services start colima
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { echo "O Docker (Colima) não respondeu." >&2; exit 1; }
fi

log "Baixando a versão mais recente do runner"
VERSAO="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
  | sed -n 's/.*"tag_name": *"v\([^"]*\)".*/\1/p' | head -n 1)"
[ -n "${VERSAO}" ] || { echo "Não consegui descobrir a versão do runner." >&2; exit 1; }
mkdir -p "${PASTA}"
cd "${PASTA}"
curl -fsSL -o runner.tar.gz \
  "https://github.com/actions/runner/releases/download/v${VERSAO}/actions-runner-${SO}-${ARQ}-${VERSAO}.tar.gz"
tar xzf runner.tar.gz
rm -f runner.tar.gz

log "Registrando o runner ${NOME} (rótulo ${ROTULO})"
./config.sh --unattended --url "${REPO_URL}" --token "${TOKEN}" \
  --name "${NOME}" --labels "${ROTULO}" --work _work --replace
# Grava o PATH atual (Homebrew, Docker) para o serviço usar.
./env.sh >/dev/null

log "Instalando o runner como serviço"
if [ "${SO}" = "linux" ]; then
  sudo ./svc.sh install "${USER}"
  sudo ./svc.sh start
else
  ./svc.sh install
  ./svc.sh start
fi

log "Pronto: runner ${NOME} instalado em ${PASTA}"
echo "Confira em ${REPO_URL}/settings/actions/runners (deve aparecer como Idle)."
