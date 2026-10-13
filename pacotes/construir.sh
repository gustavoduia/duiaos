#!/bin/bash
# =============================================================================
# DuiaOS — gera os pacotes .deb do código próprio (ADR 023).
#
#   duiaos-identidade  identidade, padrões do sistema, scripts, repositório apt
#   duiaos-shell       interface gráfica (pasta shell/) e Tela de Entrada
#   duiaos-ia          IA do sistema: serviço org.duiaos.IA1, comando e Central de IA
#   duiaos-agente      agente do sistema: ações aprovadas (org.duiaos.Agente1, ADR 034)
#   duiaos-relatorios  registros do sistema e "Ajude a melhorar o DuiaOS" (ADR 040)
#   duiaos-desktop     metapacote: instala e mantém todos os acima
#   (o duiaos-ollama, por arquitetura, tem o próprio duiaos-ollama/construir.sh)
#
# Uso: bash pacotes/construir.sh PASTA_DE_SAIDA
#
# Variáveis de ambiente (as três primeiras saem de pacotes/versao.sh):
#   VERSAO_DEB      versão dos pacotes (padrão: 0.0.0+local)
#   VERSAO_SISTEMA  versão mostrada no sistema, ex.: 0.2.0 ou dev-abc1234
#   SUITE           canal do repositório apt: estavel ou teste (padrão: teste)
#   CHAVE_PUBLICA   chave pública do repositório apt (formato binário .gpg).
#                   Sem ela, os pacotes saem sem o repositório de atualizações.
#   APT_URL         endereço do repositório apt
#
# Usado pelo build da ISO (build/build.sh) e pelo workflow pacotes.yml.
# Precisa só de: bash, dpkg-deb, find, md5sum, du, sed.
# =============================================================================
set -euo pipefail

SAIDA="${1:?Uso: bash pacotes/construir.sh PASTA_DE_SAIDA}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACOTES="${RAIZ}/pacotes"
VERSAO_DEB="${VERSAO_DEB:-0.0.0+local}"
VERSAO_SISTEMA="${VERSAO_SISTEMA:-dev-local}"
SUITE="${SUITE:-teste}"
CHAVE_PUBLICA="${CHAVE_PUBLICA:-}"
APT_URL="${APT_URL:-https://gustavoduia.github.io/duiaos-fontes-abertas/apt}"

mkdir -p "${SAIDA}"
SAIDA="$(cd "${SAIDA}" && pwd)"
TRABALHO="$(mktemp -d)"
trap 'rm -rf "${TRABALHO}"' EXIT

echo "==> Pacotes do DuiaOS ${VERSAO_DEB} (sistema ${VERSAO_SISTEMA}, canal ${SUITE})"

# Dependências da interface: shell/pacotes.list (um pacote por linha)
DEPENDENCIAS_SHELL="$(grep -v '^[[:space:]]*#' "${RAIZ}/shell/pacotes.list" \
  | sed 's/[[:space:]]//g' | sed '/^$/d' | paste -sd, - | sed 's/,/, /g')"

# Copia o modelo do pacote (DEBIAN/ e raiz/) para a pasta de montagem
preparar() {
  local NOME="$1" DESTINO="${TRABALHO}/$1"
  mkdir -p "${DESTINO}/DEBIAN"
  if [ -d "${PACOTES}/${NOME}/raiz" ]; then
    cp -R "${PACOTES}/${NOME}/raiz/." "${DESTINO}/"
  fi
  cp "${PACOTES}/${NOME}/DEBIAN/"* "${DESTINO}/DEBIAN/"
}

# Fecha o pacote: troca os marcadores, ajusta permissões, conffiles,
# md5sums e tamanho, e gera o .deb
fechar() {
  local NOME="$1" DESTINO="${TRABALHO}/$1"
  find "${DESTINO}" -name '__pycache__' -prune -exec rm -rf {} +
  find "${DESTINO}" -type d -exec chmod 0755 {} +
  find "${DESTINO}" -type f ! -perm -u+x -exec chmod 0644 {} +
  find "${DESTINO}" -type f -perm -u+x -exec chmod 0755 {} +

  local ARQ
  for ARQ in "${DESTINO}"/DEBIAN/*; do
    sed -i \
      -e "s|@VERSAO_DEB@|${VERSAO_DEB}|g" \
      -e "s|@VERSAO_SISTEMA@|${VERSAO_SISTEMA}|g" \
      -e "s|@DEPENDENCIAS_SHELL@|${DEPENDENCIAS_SHELL}|g" \
      "${ARQ}"
  done

  # Todo arquivo em /etc é de configuração (o dpkg preserva as mudanças da pessoa)
  if [ -d "${DESTINO}/etc" ]; then
    (cd "${DESTINO}" && find etc -type f | sort | sed 's|^|/|') > "${DESTINO}/DEBIAN/conffiles"
  fi
  (cd "${DESTINO}" && find . -path ./DEBIAN -prune -o -type f -printf '%P\0' \
    | sort -z | xargs -0 -r md5sum) > "${DESTINO}/DEBIAN/md5sums"
  [ -s "${DESTINO}/DEBIAN/md5sums" ] || rm -f "${DESTINO}/DEBIAN/md5sums"

  local TAMANHO
  TAMANHO="$(du -sk --exclude=DEBIAN "${DESTINO}" | cut -f1)"
  sed -i "/^Version:/a Installed-Size: ${TAMANHO}" "${DESTINO}/DEBIAN/control"

  dpkg-deb --root-owner-group -Zxz --build "${DESTINO}" \
    "${SAIDA}/${NOME}_${VERSAO_DEB}_all.deb" >/dev/null
  echo "    ${NOME}_${VERSAO_DEB}_all.deb"
}

# ---------------------------------------------------------- duiaos-identidade
preparar duiaos-identidade
ID="${TRABALHO}/duiaos-identidade"
install -d "${ID}/usr/share/duiaos/licenca"
# EULA, licenças e marca vêm do repositório duiaos-fontes-abertas (ADR 043): nos workflows, clonado em
# ./fontes-abertas; no Mac e no Dell, ~/Projetos/duiaos-fontes-abertas (ao lado deste repositório).
FONTES_ABERTAS="${DUIAOS_FONTES_ABERTAS:-}"
for CANDIDATO in "${RAIZ}/fontes-abertas" "${RAIZ}/../duiaos-fontes-abertas"; do
  [ -n "${FONTES_ABERTAS}" ] || { [ -f "${CANDIDATO}/EULA.md" ] && FONTES_ABERTAS="${CANDIDATO}"; }
done
if [ -z "${FONTES_ABERTAS}" ] || [ ! -f "${FONTES_ABERTAS}/EULA.md" ]; then
  echo "Não achei o duiaos-fontes-abertas (EULA e licenças). Clone-o ao lado deste repositório:" >&2
  echo "  git clone https://github.com/gustavoduia/duiaos-fontes-abertas ../duiaos-fontes-abertas" >&2
  exit 1
fi
install -m 0644 "${FONTES_ABERTAS}/EULA.md" "${FONTES_ABERTAS}/LICENCAS-DE-TERCEIROS.md" \
  "${FONTES_ABERTAS}/TRADEMARKS.md" "${ID}/usr/share/duiaos/licenca/"
if [ -n "${CHAVE_PUBLICA}" ] && [ -s "${CHAVE_PUBLICA}" ]; then
  install -D -m 0644 "${CHAVE_PUBLICA}" "${ID}/usr/share/keyrings/duiaos.gpg"
  install -d "${ID}/usr/share/duiaos/apt"
  cat > "${ID}/usr/share/duiaos/apt/duiaos.sources" <<EOF
# DuiaOS — repositório de atualizações do DuiaOS (canal ${SUITE}).
# Atualizar: sudo apt update && sudo apt full-upgrade
Types: deb
URIs: ${APT_URL}
Suites: ${SUITE}
Components: main
Signed-By: /usr/share/keyrings/duiaos.gpg
EOF
else
  echo "    AVISO: sem CHAVE_PUBLICA; o sistema sai sem o repositório de atualizações." >&2
fi
fechar duiaos-identidade

# --------------------------------------------------------------- duiaos-shell
preparar duiaos-shell
SH="${TRABALHO}/duiaos-shell"
install -d "${SH}/usr/share/duiaos" "${SH}/etc/xdg/labwc" "${SH}/usr/share/wayland-sessions"
cp -R "${RAIZ}/shell" "${SH}/usr/share/duiaos/shell"
install -m 0644 "${RAIZ}/shell/sessao/autostart" "${RAIZ}/shell/sessao/environment" \
  "${RAIZ}/shell/sessao/rc.xml" "${SH}/etc/xdg/labwc/"
install -m 0644 "${RAIZ}/shell/sessao/duiaos.desktop" "${SH}/usr/share/wayland-sessions/"
fechar duiaos-shell

# ------------------------------------------------------------------ duiaos-ia
preparar duiaos-ia
IA="${TRABALHO}/duiaos-ia"
install -d "${IA}/usr/share/duiaos/ia" "${IA}/usr/share/duiaos/central-de-ia"
install -m 0644 "${RAIZ}"/ia/*.py "${RAIZ}/ia/catalogo.json" "${IA}/usr/share/duiaos/ia/"
install -m 0644 "${RAIZ}"/apps/central-de-ia/*.py "${RAIZ}"/apps/central-de-ia/*.qml \
  "${IA}/usr/share/duiaos/central-de-ia/"
fechar duiaos-ia

# -------------------------------------------------------------- duiaos-agente
preparar duiaos-agente
AG="${TRABALHO}/duiaos-agente"
install -d "${AG}/usr/share/duiaos/agente"
install -m 0644 "${RAIZ}"/agente/*.py "${AG}/usr/share/duiaos/agente/"
fechar duiaos-agente

# ---------------------------------------------------------- duiaos-relatorios
preparar duiaos-relatorios
RL="${TRABALHO}/duiaos-relatorios"
install -d "${RL}/usr/lib/python3/dist-packages/duiaos_relatorios" \
  "${RL}/usr/lib/python3/dist-packages/duiaos_registro"
install -m 0644 "${RAIZ}"/relatorios/*.py "${RL}/usr/lib/python3/dist-packages/duiaos_relatorios/"
install -m 0644 "${RAIZ}"/relatorios/duiaos_registro/*.py "${RL}/usr/lib/python3/dist-packages/duiaos_registro/"
# Tela "Ajude a melhorar o DuiaOS" (1ª entrada e Central de Aplicativos)
install -d "${RL}/usr/share/duiaos/ajude-a-melhorar"
install -m 0644 "${RAIZ}"/apps/ajude-a-melhorar/*.py "${RAIZ}"/apps/ajude-a-melhorar/*.qml \
  "${RL}/usr/share/duiaos/ajude-a-melhorar/"
fechar duiaos-relatorios

# ------------------------------------------------------------- duiaos-desktop
preparar duiaos-desktop
fechar duiaos-desktop
