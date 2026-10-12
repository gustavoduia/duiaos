#!/bin/bash
# =============================================================================
# DuiaOS — liga "Ajude a melhorar o DuiaOS" no nível DESENVOLVIMENTO num
# computador de teste, com envio pelo Git ao repositório privado
# gustavoduia/duiaos-diagnosticos (ADR 040). Rode NO MAC:
#
#   bash ferramentas/configurar-relatorios.sh                 # o Dell (gustavo@duiaos), máquina "dell"
#   DELL=usuario@endereco MAQUINA=nome bash ferramentas/configurar-relatorios.sh
#
# Antes: o computador precisa do pacote duiaos-relatorios (pacotes/instalar-local.sh ou apt).
# O que faz (pode rodar de novo sem problema):
#   1. cria o repositório privado, se ainda não existir;
#   2. cria no computador uma chave SSH do SISTEMA (/etc/duiaos/relatorios/chave_git, só root) e a
#      cadastra como deploy key com escrita, válida só nesse repositório;
#   3. grava /etc/duiaos/relatorios.conf (nível desenvolvimento, transporte git);
#   4. faz a primeira coleta e o primeiro envio.
# Pede a senha de administrador do computador (sudo) duas vezes.
# Para desligar: sudo duiaos-relatorios nivel desligado (e remova a deploy key no GitHub).
# =============================================================================
set -euo pipefail

REPO="gustavoduia/duiaos-diagnosticos"
DELL="${DELL:-gustavo@duiaos}"
MAQUINA="${MAQUINA:-dell}"
TITULO="DuiaOS ${MAQUINA} (relatórios, escrita)"
[[ "${MAQUINA}" =~ ^[a-z0-9-]+$ ]] || { echo "MAQUINA: só letras minúsculas, números e hífen" >&2; exit 1; }

gh auth status >/dev/null 2>&1 || { echo "Rode antes: gh auth login" >&2; exit 1; }

echo "==> Repositório ${REPO}"
if gh repo view "${REPO}" >/dev/null 2>&1; then
  echo "    Já existe."
else
  gh repo create "${REPO}" --private --add-readme \
    --description "Relatórios do DuiaOS (Ajude a melhorar o DuiaOS). PRIVADO: dados pessoais, nunca tornar público"
fi

echo "==> Conferindo o pacote duiaos-relatorios em ${DELL}"
ssh "${DELL}" "command -v duiaos-relatorios >/dev/null" || {
  echo "O computador ainda não tem o duiaos-relatorios. Instale a branch antes (pacotes/instalar-local.sh)." >&2
  exit 1
}

echo "==> Chave do sistema e configuração (sudo no computador)"
# shellcheck disable=SC2029  # REPO e MAQUINA expandem no Mac de propósito
ssh -t "${DELL}" "sudo sh -c '
  set -e
  install -d -m 0700 /etc/duiaos/relatorios
  test -f /etc/duiaos/relatorios/chave_git || \
    ssh-keygen -q -t ed25519 -N \"\" -C duiaos-relatorios-${MAQUINA} -f /etc/duiaos/relatorios/chave_git
  printf \"[relatorios]\nnivel = desenvolvimento\ntransporte = git\nrepositorio = git@github.com:${REPO}.git\nmaquina = ${MAQUINA}\n\" \
    > /etc/duiaos/relatorios.conf
  chmod 0644 /etc/duiaos/relatorios.conf
  install -m 0644 /etc/duiaos/relatorios/chave_git.pub /tmp/duiaos-relatorios-chave.pub
'"
CHAVE="$(ssh "${DELL}" "cat /tmp/duiaos-relatorios-chave.pub && rm -f /tmp/duiaos-relatorios-chave.pub")"

echo "==> Deploy key com escrita (só neste repositório)"
TMP="$(mktemp)"; trap 'rm -f "${TMP}"' EXIT
printf '%s\n' "${CHAVE}" > "${TMP}"
if gh repo deploy-key list --repo "${REPO}" | grep -qF "${TITULO}"; then
  echo "    Já cadastrada."
else
  gh repo deploy-key add "${TMP}" --repo "${REPO}" --title "${TITULO}" --allow-write
fi

echo "==> Primeira coleta e envio (sudo no computador)"
ssh -t "${DELL}" "sudo systemctl start duiaos-relatorios.service; duiaos-relatorios estado"
echo "Pronto. A coleta roda a cada hora; para enviar na hora: duiaos-relatorios enviar (no computador)."
