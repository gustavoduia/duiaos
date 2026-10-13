#!/bin/bash
# =============================================================================
# DuiaOS — prepara ESTA máquina (Mac ou Dell) para gerar ISOs e organiza
# a pasta ~/Projetos. Roda na própria máquina.
#
# Não chame direto: use, no Mac, ferramentas/configurar-runners.sh mac|dell,
# que obtém os tokens e chama este script aqui ou, por SSH, no Dell.
#
# Argumentos: TOKEN_REGISTRO TOKEN_REMOCAO NOME MAQUINA(mac|dell)
#
# O que faz (pode rodar de novo; o que já existe é mantido ou refeito):
#   1. Pastas padrão:  ~/Projetos/duiaos            repositório privado (já existe)
#                      ~/Projetos/duiaos-fontes-abertas  cópia do público (só leitura)
#                      ~/Projetos/duiaos-isos       ISOs de teste
#                      ~/Projetos/duiaos-runner     runner do GitHub
#   2. Dependências: Dell = Docker + gh; Mac = Colima (com Rosetta) + Docker + gh.
#   3. Remove o runner antigo (~/actions-runner-duiaos ou ~/Projetos/duiaos-runner)
#      e registra de novo com o rótulo duiaos-MAQUINA, como serviço.
# =============================================================================
set -euo pipefail

TOKEN="${1:?falta o token de registro}"
TOKEN_REMOCAO="${2:?falta o token de remoção}"
NOME="${3:?falta o nome do runner}"
MAQUINA="${4:?falta a máquina (mac ou dell)}"
REPO_URL="https://github.com/gustavoduia/duiaos"
PUBLICO_URL="https://github.com/gustavoduia/duiaos-fontes-abertas.git"
PROJETOS="${HOME}/Projetos"
RUNNER="${PROJETOS}/duiaos-runner"
ISOS="${PROJETOS}/duiaos-isos"

log() { printf '\n==> %s\n' "$*"; }

case "$(uname -s)" in
  Linux)  SO=linux; ARQ=x64 ;;
  Darwin) SO=osx;   ARQ=arm64 ;;
  *) echo "Sistema não suportado: $(uname -s)" >&2; exit 1 ;;
esac

# ---------------------------------------------------------------------------
log "1/5 Dependências"
if [ "${SO}" = "linux" ]; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker.io git curl gh >/dev/null
  sudo systemctl enable --now docker
  sudo usermod -aG docker "${USER}"
  DOCKER="sudo docker"
else
  command -v brew >/dev/null 2>&1 || { echo "Instale o Homebrew primeiro: https://brew.sh" >&2; exit 1; }
  brew install colima docker gh
  # Rosetta: permite ao Mac gerar a ISO amd64 com boa velocidade.
  if ! /usr/bin/pgrep -q oahd; then
    softwareupdate --install-rosetta --agree-to-license
  fi
  log "Configurando o Colima (6 CPUs, 8 GB de RAM, até 80 GB de disco, Rosetta)"
  brew services stop colima >/dev/null 2>&1 || true
  colima stop >/dev/null 2>&1 || true
  colima start --cpu 6 --memory 8 --disk 80 --vm-type vz --mount-type virtiofs --vz-rosetta
  colima stop
  brew services start colima
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { echo "O Docker (Colima) não respondeu." >&2; exit 1; }
  DOCKER="docker"
fi

# ---------------------------------------------------------------------------
log "2/5 Pastas em ${PROJETOS}"
mkdir -p "${PROJETOS}" "${ISOS}"
if [ -d "${HOME}/duiaos-isos" ]; then
  echo "Movendo ISOs de ~/duiaos-isos para ${ISOS}"
  find "${HOME}/duiaos-isos" -maxdepth 1 -type f -exec mv -n {} "${ISOS}/" \;
  rmdir "${HOME}/duiaos-isos" 2>/dev/null || echo "AVISO: ~/duiaos-isos não ficou vazia; confira à mão."
fi
if [ -d "${PROJETOS}/duiaos-fontes-abertas/.git" ]; then
  git -C "${PROJETOS}/duiaos-fontes-abertas" pull -q --ff-only || true
else
  git clone -q "${PUBLICO_URL}" "${PROJETOS}/duiaos-fontes-abertas" \
    || echo "AVISO: não consegui clonar o repositório público (ele já foi criado?)."
fi

# ---------------------------------------------------------------------------
log "3/5 Parando builds que tenham ficado rodando"
ANTIGOS="$(${DOCKER} ps -aq --filter 'name=^duiaos-build-' || true)"
# Builds anteriores a esta versão não tinham nome; param-se os que usam debian:trixie.
ANTIGOS="${ANTIGOS} $(${DOCKER} ps -q --filter 'ancestor=debian:trixie' || true)"
ANTIGOS="$(echo "${ANTIGOS}" | xargs)"
if [ -n "${ANTIGOS}" ]; then
  # shellcheck disable=SC2086
  ${DOCKER} rm -f ${ANTIGOS} >/dev/null && echo "Parados: ${ANTIGOS}"
else
  echo "Nenhum."
fi

# ---------------------------------------------------------------------------
log "4/5 Removendo o runner antigo (se houver)"
for VELHO in "${HOME}/actions-runner-duiaos" "${RUNNER}"; do
  [ -f "${VELHO}/.runner" ] || continue
  echo "Removendo ${VELHO}"
  (
    cd "${VELHO}"
    if [ "${SO}" = "linux" ]; then
      sudo ./svc.sh stop >/dev/null 2>&1 || true
      sudo ./svc.sh uninstall >/dev/null 2>&1 || true
    else
      ./svc.sh stop >/dev/null 2>&1 || true
      ./svc.sh uninstall >/dev/null 2>&1 || true
    fi
    ./config.sh remove --token "${TOKEN_REMOCAO}" || true
  )
  rm -rf "${VELHO:?}"
done

# ---------------------------------------------------------------------------
log "5/5 Instalando o runner ${NOME} (rótulo duiaos-${MAQUINA}) em ${RUNNER}"
VERSAO="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
  | sed -n 's/.*"tag_name": *"v\([^"]*\)".*/\1/p' | head -n 1)"
[ -n "${VERSAO}" ] || { echo "Não consegui descobrir a versão do runner." >&2; exit 1; }
mkdir -p "${RUNNER}"
cd "${RUNNER}"
curl -fsSL -o runner.tar.gz \
  "https://github.com/actions/runner/releases/download/v${VERSAO}/actions-runner-${SO}-${ARQ}-${VERSAO}.tar.gz"
tar xzf runner.tar.gz
rm -f runner.tar.gz
./config.sh --unattended --url "${REPO_URL}" --token "${TOKEN}" \
  --name "${NOME}" --labels "duiaos-${MAQUINA}" --work _work --replace
# Grava o PATH atual (Homebrew, Docker) para o serviço usar.
./env.sh >/dev/null
if [ "${SO}" = "linux" ]; then
  sudo ./svc.sh install "${USER}"
  sudo ./svc.sh start
else
  ./svc.sh install
  ./svc.sh start
fi

log "Pronto"
echo "Runner:  ${RUNNER} (rótulo duiaos-${MAQUINA})"
echo "ISOs:    ${ISOS}"
echo "Público: ${PROJETOS}/duiaos-fontes-abertas (EULA, licenças e código aberto: edite direto nele, na main)"
echo "Confira em ${REPO_URL}/settings/actions/runners (deve aparecer como Idle)."
