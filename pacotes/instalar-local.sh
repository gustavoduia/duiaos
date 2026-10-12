#!/bin/bash
# =============================================================================
# DuiaOS — gera os pacotes do DuiaOS a partir desta pasta do repositório e os
# instala NESTE computador. Serve para testar uma branch (pull request) antes
# do merge, sem esperar o repositório apt.
#
# Onde rodar: 🔗 DELL (sessão SSH), na pasta do repositório:
#   cd ~/Projetos/duiaos && git fetch --tags && git checkout BRANCH && git pull
#   bash pacotes/instalar-local.sh
#
# A versão gerada é a do commit atual (pacotes/versao.sh); depois do merge,
# a versão publicada no repositório apt é mais nova e substitui esta no
# próximo "sudo apt full-upgrade".
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

TEMP="$(mktemp -d)"
trap 'rm -rf "${TEMP}"' EXIT

eval "$(bash pacotes/versao.sh)"
# Mantém o repositório de atualizações: reaproveita a chave e o canal instalados
CHAVE=""
if [ -s /usr/share/keyrings/duiaos.gpg ]; then
  cp /usr/share/keyrings/duiaos.gpg "${TEMP}/chave.gpg"
  CHAVE="${TEMP}/chave.gpg"
fi
if [ -r /etc/apt/sources.list.d/duiaos.sources ]; then
  SUITE="$(sed -n 's/^Suites:[[:space:]]*//p' /etc/apt/sources.list.d/duiaos.sources | head -n 1)"
fi

VERSAO_DEB="${VERSAO_DEB}" VERSAO_SISTEMA="${VERSAO_SISTEMA}" SUITE="${SUITE:-teste}" \
  CHAVE_PUBLICA="${CHAVE}" bash pacotes/construir.sh "${TEMP}/debs"

# Ollama (IA local) da arquitetura deste computador; o download (~1,5 GB) fica
# guardado em ~/.cache/duiaos e só se repete quando a versão do Ollama mudar.
if ! command -v zstd >/dev/null || ! command -v curl >/dev/null; then
  sudo apt-get install -y -qq zstd curl
fi
bash pacotes/duiaos-ollama/construir.sh "$(dpkg --print-architecture)" "${TEMP}/debs"

chmod 755 "${TEMP}" "${TEMP}/debs"
chmod 644 "${TEMP}"/debs/*.deb
sudo apt-get install -y --allow-downgrades \
  -o Dpkg::Options::=--force-confnew "${TEMP}"/debs/*.deb
echo
echo "Instalado: DuiaOS ${VERSAO_SISTEMA} (pacotes ${VERSAO_DEB}). Reinicie para ver tudo: sudo reboot"
