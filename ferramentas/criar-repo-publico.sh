#!/bin/bash
# =============================================================================
# DuiaOS — cria o repositório público duiaos-fontes-abertas, cadastra o token
# e faz a primeira sincronização (rode NO MAC, na pasta do repositório,
# DEPOIS de o patch de licença estar na main).
#
#   bash ferramentas/criar-repo-publico.sh
#
# Pode rodar de novo: o que já existe é mantido.
# =============================================================================
set -euo pipefail

INTERNO="gustavoduia/duiaos"
PUBLICO="gustavoduia/duiaos-fontes-abertas"

gh auth status >/dev/null 2>&1 || { echo "Rode antes: gh auth login" >&2; exit 1; }

echo "==> 1/4 Repositório público"
if gh repo view "${PUBLICO}" >/dev/null 2>&1; then
  echo "    ${PUBLICO} já existe."
else
  gh repo create "${PUBLICO}" --public \
    --description "DuiaOS: ISOs, EULA, licenças de terceiros e código-fonte aberto" \
    --disable-wiki
fi
gh repo edit "${PUBLICO}" --enable-issues=true --enable-projects=false \
  --enable-discussions=false --enable-wiki=false \
  --add-topic linux --add-topic debian --add-topic sistema-operacional >/dev/null

echo "==> 2/4 Token de acesso ao repositório público"
if gh secret list --repo "${INTERNO}" | grep -q '^DUIAOS_TOKEN_PUBLICO'; then
  echo "    O segredo DUIAOS_TOKEN_PUBLICO já existe no ${INTERNO}."
else
  cat <<'TXT'

    Vou abrir a página de criação de token no navegador. Preencha assim:
      Token name ............ duiaos-publico
      Expiration ............ 366 days (anote a data para renovar)
      Repository access ..... Only select repositories -> duiaos-fontes-abertas
      Permissions ........... Repository permissions -> Contents: Read and write
                              (Metadata: Read-only entra sozinho)
    Clique em "Generate token" e copie o token (começa com github_pat_).

TXT
  read -r -p "    Pressione Enter para abrir o navegador..." _
  open "https://github.com/settings/personal-access-tokens/new" 2>/dev/null || true
  echo
  echo "    Cole o token abaixo e pressione Enter (não aparece na tela):"
  gh secret set DUIAOS_TOKEN_PUBLICO --repo "${INTERNO}"
fi

echo "==> 3/4 Primeira sincronização da pasta publico/"
gh workflow run sincronizar-publico.yml --repo "${INTERNO}" --ref main
sleep 8
ID="$(gh run list --repo "${INTERNO}" --workflow sincronizar-publico.yml -L 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "${ID}" --repo "${INTERNO}" --exit-status

echo "==> 4/4 Conferência"
gh api "repos/${PUBLICO}/contents" --jq '.[].name'
echo
echo "Pronto: https://github.com/${PUBLICO}"
