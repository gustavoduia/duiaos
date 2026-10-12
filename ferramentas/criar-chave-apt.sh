#!/bin/bash
# =============================================================================
# DuiaOS — cria a chave que assina o repositório apt do DuiaOS (ADR 028).
# Rode NO MAC, uma vez só.
#
#   bash ferramentas/criar-chave-apt.sh
#
# 1. Gera uma chave ed25519 (válida por 10 anos), sem senha, numa pasta
#    temporária (não mexe no seu chaveiro do gpg).
# 2. Cadastra a chave privada no segredo DUIAOS_APT_CHAVE do repositório
#    gustavoduia/duiaos (o GitHub Actions assina os pacotes com ela).
# 3. Guarda uma cópia em ~/Projetos/duiaos-chaves/ — guarde-a também no seu
#    gerenciador de senhas e NUNCA a envie para um repositório.
#
# Trocar a chave depois exige atualizar todos os computadores instalados;
# por isso o script recusa se o segredo já existir (use --substituir).
# Requer: gpg (brew install gnupg) e gh autenticado.
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos"
SEGREDO="DUIAOS_APT_CHAVE"
PASTA="${HOME}/Projetos/duiaos-chaves"
COPIA="${PASTA}/duiaos-apt-privada.asc"

command -v gpg >/dev/null || { echo "Instale o GnuPG: brew install gnupg" >&2; exit 1; }
command -v gh >/dev/null || { echo "Instale o GitHub CLI: brew install gh" >&2; exit 1; }

if gh secret list --repo "${REPO}" | grep -q "^${SEGREDO}\b" && [ "${1:-}" != "--substituir" ]; then
  echo "O segredo ${SEGREDO} já existe em ${REPO}. Nada foi feito." >&2
  echo "Para trocar a chave (todos os DuiaOS instalados precisarão da nova): bash $0 --substituir" >&2
  exit 1
fi

GNUPGHOME="$(mktemp -d)"
export GNUPGHOME
trap 'rm -rf "${GNUPGHOME}"' EXIT

echo "Gerando a chave..."
gpg --batch --quiet --passphrase '' \
  --quick-gen-key "DuiaOS (repositório apt) <53358870+gustavoduia@users.noreply.github.com>" ed25519 sign 10y
IMPRESSAO="$(gpg --batch --list-secret-keys --with-colons | awk -F: '/^fpr/ {print $10; exit}')"

mkdir -p "${PASTA}"
chmod 700 "${PASTA}"
gpg --batch --armor --export-secret-keys "${IMPRESSAO}" > "${COPIA}"
chmod 600 "${COPIA}"

gh secret set "${SEGREDO}" --repo "${REPO}" < "${COPIA}"

echo
echo "Pronto."
echo "  Impressão digital: ${IMPRESSAO}"
echo "  Segredo ${SEGREDO} cadastrado em ${REPO}."
echo "  Cópia da chave privada: ${COPIA}"
echo "  Guarde esse arquivo no seu gerenciador de senhas."
