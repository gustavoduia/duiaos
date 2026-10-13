#!/bin/bash
# =============================================================================
# DuiaOS — conclui a organização dos repositórios (ADR 043): só a main, e toda
# instrução só no duiaos. Rode NO MAC uma vez, DEPOIS dos três merges:
#   duiaos #12 → duiaos-wise #10 → duiaos-websites #8 (nesta ordem).
#
#   bash ferramentas/organizar-repositorios.sh
#
# O que faz (pede confirmação antes):
#   1. Confere que os três PRs entraram na main.
#   2. Apaga todas as branches claude/* do duiaos, duiaos-wise e duiaos-websites
#      (o trabalho delas já está na main ou foi substituído; ver a memória de
#      12/10 19h51 em docs/continuidade/).
#   3. duiaos-diagnosticos: tira o CLAUDE.md e a regra de PR do README (main).
#   4. duiaos-fontes-abertas: o README deixa de dizer que é cópia do duiaos/publico (main).
#   5. Deixa as cópias do Mac em ~/Projetos na main atualizada.
# =============================================================================
set -euo pipefail

PROJETOS="${PROJETOS:-${HOME}/Projetos}"
DONO="gustavoduia"

for par in "duiaos 12" "duiaos-wise 10" "duiaos-websites 8"; do
  # shellcheck disable=SC2086
  set -- ${par}
  if [ "$(gh pr view "$2" -R "${DONO}/$1" --json state --jq .state)" != "MERGED" ]; then
    echo "Faça antes o merge de ${DONO}/$1 #$2 (ordem: duiaos #12, duiaos-wise #10, duiaos-websites #8)." >&2
    exit 1
  fi
done

echo "Branches que serão apagadas:"
for r in duiaos duiaos-wise duiaos-websites duiaos-diagnosticos duiaos-fontes-abertas; do
  gh api "repos/${DONO}/${r}/branches?per_page=100" --jq '.[].name' | grep '^claude/' | sed "s|^|  ${r}: |" || true
done
read -r -p "Confirma a organização? (s/N) " R
[ "${R}" = "s" ] || [ "${R}" = "S" ] || { echo "Cancelado."; exit 1; }

# 2. Branches claude/*
for r in duiaos duiaos-wise duiaos-websites duiaos-diagnosticos duiaos-fontes-abertas; do
  for b in $(gh api "repos/${DONO}/${r}/branches?per_page=100" --jq '.[].name' | grep '^claude/' || true); do
    gh api -X DELETE "repos/${DONO}/${r}/git/refs/heads/${b}" && echo "apagada: ${r} ${b}"
  done
done

copia() {   # garante ~/Projetos/NOME na main atualizada
  local NOME="$1"
  if [ ! -d "${PROJETOS}/${NOME}/.git" ]; then
    git clone -q "https://github.com/${DONO}/${NOME}.git" "${PROJETOS}/${NOME}"
  fi
  git -C "${PROJETOS}/${NOME}" checkout -q main
  git -C "${PROJETOS}/${NOME}" pull -q --rebase origin main
  git -C "${PROJETOS}/${NOME}" fetch -q --prune origin
}

# 3. duiaos-diagnosticos: só dados e a descrição deles
copia duiaos-diagnosticos
D="${PROJETOS}/duiaos-diagnosticos"
if [ -f "${D}/CLAUDE.md" ]; then git -C "${D}" rm -q CLAUDE.md; fi
python3 - "${D}/README.md" <<'EOF'
import sys
caminho = sys.argv[1]
texto = open(caminho, encoding="utf-8").read()
texto = texto.replace("- Documentação deste repositório (este README, o CLAUDE.md): branch `claude/...` + PR, merge pelo Gustavo.\n",
                      "- Instruções para quem desenvolve: no repositório oficial do projeto, o `duiaos` (ADR 043).\n")
texto = texto.replace("`main` sem pull request: são dados, não código.", "`main`: são dados, não código.")
open(caminho, "w", encoding="utf-8").write(texto)
EOF
git -C "${D}" add -A
if ! git -C "${D}" diff --cached --quiet; then
  git -C "${D}" commit -q -m "Instruções saem deste repositório (ADR 043 do DuiaOS): ficam no duiaos"
  git -C "${D}" push -q origin main && echo "duiaos-diagnosticos: atualizado"
fi

# 4. duiaos-fontes-abertas: fonte da verdade do que é aberto
copia duiaos-fontes-abertas
F="${PROJETOS}/duiaos-fontes-abertas"
python3 - "${F}/README.md" <<'EOF'
import re, sys
caminho = sys.argv[1]
texto = open(caminho, encoding="utf-8").read()
novo = re.sub(r"<!--.*?sincronizar-publico\.yml.*?-->\n", "<!--\n  README do repositório público https://github.com/gustavoduia/duiaos-fontes-abertas:\n"
              "  código aberto do DuiaOS (GPL-3 e outras licenças que exigem publicação), modificações em software\n"
              "  livre, EULA, licenças e marca. Editado direto aqui, na main (ADR 043 do DuiaOS).\n-->\n", texto, count=1, flags=re.S)
open(caminho, "w", encoding="utf-8").write(novo)
EOF
git -C "${F}" add -A
if ! git -C "${F}" diff --cached --quiet; then
  git -C "${F}" commit -q -m "Este repositório é a fonte do código aberto do DuiaOS (ADR 043)"
  git -C "${F}" push -q origin main && echo "duiaos-fontes-abertas: atualizado"
fi

# 5. Cópias do Mac na main
for r in duiaos duiaos-wise duiaos-websites; do copia "${r}"; done
echo
echo "Pronto. Todos os repositórios só com a main. No Dell, rode:"
echo "  cd ~/Projetos/duiaos && git checkout main && git pull && git fetch --prune"
echo "  cd ~/Projetos/duiaos-wise && git checkout main && git pull && git fetch --prune"
echo "  [ -d ~/Projetos/duiaos-fontes-abertas ] || git clone https://github.com/${DONO}/duiaos-fontes-abertas ~/Projetos/duiaos-fontes-abertas"
