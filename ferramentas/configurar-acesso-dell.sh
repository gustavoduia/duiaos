#!/bin/bash
# =============================================================================
# DuiaOS — dá ao Dell acesso SOMENTE DE LEITURA ao repositório privado
# (rode NO MAC, na pasta do repositório).
#
#   bash ferramentas/configurar-acesso-dell.sh
#
# Cria no Dell uma chave SSH só para o GitHub, cadastra essa chave no
# repositório como "deploy key" (sem permissão de escrita) e troca o endereço
# do ~/Projetos/duiaos do Dell para usá-la. Depois disso, git pull no Dell
# funciona com o repositório privado. Pode rodar de novo sem problema.
#
# Variável opcional: DELL=usuario@endereco (padrão gustavo@duiaos).
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos"
DELL="${DELL:-gustavo@duiaos}"
# Impressão digital oficial da chave ed25519 do github.com (docs.github.com).
GITHUB_FP="SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"

gh auth status >/dev/null 2>&1 || { echo "Rode antes: gh auth login" >&2; exit 1; }

echo "==> Criando a chave no Dell (se ainda não existir)"
CHAVE="$(ssh "${DELL}" 'test -f ~/.ssh/duiaos_github || ssh-keygen -q -t ed25519 -N "" -C "dell-duiaos-leitura" -f ~/.ssh/duiaos_github; cat ~/.ssh/duiaos_github.pub')"

echo "==> Cadastrando a chave no GitHub como somente leitura"
TMP="$(mktemp)"; trap 'rm -f "${TMP}"' EXIT
printf '%s\n' "${CHAVE}" > "${TMP}"
if gh repo deploy-key list --repo "${REPO}" | grep -q "dell-duiaos-leitura\|Dell (leitura)"; then
  echo "    Já cadastrada."
else
  gh repo deploy-key add "${TMP}" --repo "${REPO}" --title "Dell (leitura)"
fi

echo "==> Configurando o git no Dell"
ssh "${DELL}" "GITHUB_FP='${GITHUB_FP}' bash -s" <<'REMOTO'
set -euo pipefail
mkdir -p ~/.ssh && chmod 700 ~/.ssh
if ! grep -q '^Host github-duiaos$' ~/.ssh/config 2>/dev/null; then
  cat >> ~/.ssh/config <<'CFG'

Host github-duiaos
  HostName github.com
  User git
  IdentityFile ~/.ssh/duiaos_github
  IdentitiesOnly yes
CFG
fi
chmod 600 ~/.ssh/config
if ! ssh-keygen -F github.com >/dev/null 2>&1; then
  K="$(ssh-keyscan -t ed25519 github.com 2>/dev/null)"
  FP="$(printf '%s\n' "${K}" | ssh-keygen -lf - | awk '{print $2}')"
  if [ "${FP}" != "${GITHUB_FP}" ]; then
    echo "ERRO: a chave recebida do github.com não confere (${FP}). Abortando." >&2
    exit 1
  fi
  printf '%s\n' "${K}" >> ~/.ssh/known_hosts
fi
cd ~/Projetos/duiaos
git remote set-url origin git@github-duiaos:gustavoduia/duiaos.git
git pull --ff-only
echo "Dell pronto: $(git log -1 --oneline)"
REMOTO
