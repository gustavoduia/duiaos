#!/bin/bash
# =============================================================================
# DuiaOS — gera o pacote duiaos-motor-web (ADR 072): o Qt WebEngine (Chromium) e o PySide6 das rodas
# oficiais do PyPI, na versão fixada em VERSAO, conferidas pelo sha256.
#
# Uso: bash pacotes/duiaos-motor-web/construir.sh ARQUITETURA PASTA_DE_SAIDA [CACHE]
#   ARQUITETURA  amd64 ou arm64
#   CACHE        pasta onde as rodas baixadas ficam guardadas (padrão: ~/.cache/duiaos)
#
# Instala em /usr/lib/duiaos/motor-web (PySide6, shiboken6 e o Qt com o QtWebEngineProcess). O Ora e o
# Mail Box põem essa pasta na frente do PySide6 do Debian (main.py); os outros programas não a veem.
#
# Versão do pacote: PYSIDE-duiaosREVISAO (ex.: 6.12.0-duiaos1); só muda quando VERSAO muda.
# Precisa de: bash, python3 com pip, unzip, sha256sum, dpkg-deb, find, md5sum, du, sed.
# =============================================================================
set -euo pipefail

ARQ="${1:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
SAIDA="${2:?Uso: construir.sh amd64|arm64 PASTA_DE_SAIDA [CACHE]}"
CACHE="${3:-${XDG_CACHE_HOME:-${HOME}/.cache}/duiaos}/motor-web"
PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "${PASTA}/VERSAO"
case "${ARQ}" in
  amd64) PLATAFORMA="${PLATAFORMA_AMD64}"; PREFIXO=SHA256_AMD64 ;;
  arm64) PLATAFORMA="${PLATAFORMA_ARM64}"; PREFIXO=SHA256_ARM64 ;;
  *) echo "Arquitetura inválida: ${ARQ} (use amd64 ou arm64)" >&2; exit 1 ;;
esac
VERSAO_DEB="${PYSIDE}-duiaos${REVISAO}"
# nome da roda no PyPI → versão
declare -A RODAS=([pyside6_essentials]="${PYSIDE}" [pyside6_addons]="${PYSIDE}" [shiboken6]="${PYSIDE}"
                  [pyside6_webengine]="${WEBENGINE}" [pyside6_pdf]="${WEBENGINE}")

mkdir -p "${SAIDA}" "${CACHE}/${ARQ}"
SAIDA="$(cd "${SAIDA}" && pwd)"
TRABALHO="$(mktemp -d)"
trap 'rm -rf "${TRABALHO}"' EXIT
echo "==> duiaos-motor-web ${VERSAO_DEB} (${ARQ}, Chromium do Qt WebEngine ${WEBENGINE})"

# 1. Baixa (ou reaproveita) e confere cada roda
arquivo() { echo "${CACHE}/${ARQ}/${1}-${RODAS[$1]}-cp310-abi3-${PLATAFORMA}.whl"; }
soma() { local v="${PREFIXO}_${1}"; echo "${!v}"; }
conferir() { echo "$(soma "$1")  $(arquivo "$1")" | sha256sum -c --status 2>/dev/null; }
for nome in "${!RODAS[@]}"; do
  if ! conferir "${nome}"; then
    python3 -m pip download --quiet --no-deps --only-binary=:all: --platform "${PLATAFORMA}" \
      --python-version 3.13 --implementation cp --abi abi3 -d "${CACHE}/${ARQ}" "${nome}==${RODAS[$nome]}"
  fi
  if ! conferir "${nome}"; then
    echo "A roda ${nome} ${RODAS[$nome]} (${ARQ}) não confere com o sha256 de VERSAO. Nada foi gerado." >&2
    exit 1
  fi
done

# 2. Monta a árvore do pacote
D="${TRABALHO}/duiaos-motor-web"
DESTINO="${D}/usr/lib/duiaos/motor-web"
mkdir -p "${D}/DEBIAN" "${DESTINO}"
cp "${PASTA}/DEBIAN/"* "${D}/DEBIAN/"
for nome in "${!RODAS[@]}"; do
  unzip -q -o "$(arquivo "${nome}")" -d "${DESTINO}"
done
# Ferramentas de desenvolvimento do Qt (designer, assistant, lupdate...) não servem ao sistema
rm -rf "${DESTINO}"/PySide6/{designer,assistant,linguist,lupdate,lrelease,qmlls,qmllint,qmlformat,balsam,balsamui} \
       "${DESTINO}"/PySide6/scripts "${DESTINO}"/PySide6/include "${DESTINO}"/PySide6/typesystems "${DESTINO}"/PySide6/glue
find "${DESTINO}" -name '*.pyi' -delete
# Módulos do Qt que o Ora e o Mail Box não usam (3D, gráficos, Designer, sensores...): sai a biblioteca,
# a ligação com o Python, os módulos QML e os plugins de cada um
QT="${DESTINO}/PySide6/Qt"
for MODULO in 3DAnimation 3DCore 3DExtras 3DInput 3DLogic 3DRender 3DQuick 3DQuickAnimation 3DQuickExtras \
              3DQuickInput 3DQuickRender 3DQuickScene2D 3DQuickScene3D Quick3D Designer DesignerComponents Graphs \
              GraphsWidgets Charts ChartsQml DataVisualization DataVisualizationQml Scxml ScxmlQml Sensors SensorsQuick \
              TextToSpeech RemoteObjects RemoteObjectsQml Bluetooth Nfc SerialBus SerialPort SpatialAudio Location \
              VirtualKeyboard VirtualKeyboardQml VirtualKeyboardSettings HttpServer; do
  rm -f "${QT}"/lib/libQt6"${MODULO}"*.so* "${DESTINO}"/PySide6/Qt"${MODULO}"*.abi3.so
done
rm -rf "${QT}"/qml/{Qt3D,QtQuick3D,QtGraphs,QtCharts,QtDataVisualization,QtScxml,QtSensors,QtTextToSpeech,QtRemoteObjects} \
       "${QT}"/qml/{QtBluetooth,QtNfc,QtLocation} "${QT}"/qml/QtQuick/VirtualKeyboard \
       "${QT}"/plugins/{sceneparsers,geometryloaders,renderers,renderplugins,designer,sensors,texttospeech,assetimporters} \
       "${QT}"/plugins/{geoservices,canbus,virtualkeyboard,platforminputcontexts/libqtvirtualkeyboardplugin.so}
# Traduções: português e inglês (o Chromium tem uma por idioma, ~60 MB no total)
find "${QT}/translations" -type f ! -name '*pt_BR*' ! -name '*pt-BR*' ! -name '*pt_PT*' ! -name '*pt-PT*' \
  ! -name '*_en.qm' ! -name 'en-US*' ! -name 'en-GB*' -delete
# O unzip não guarda o bit de execução das rodas: os executáveis do Qt (QtWebEngineProcess) precisam dele
chmod 0755 "${DESTINO}"/PySide6/Qt/libexec/* 2>/dev/null || true
[ -x "${DESTINO}/PySide6/Qt/libexec/QtWebEngineProcess" ] || { echo "Roda sem o QtWebEngineProcess: formato mudou?" >&2; exit 1; }

# As rodas guardam os links simbólicos das bibliotecas como cópias (libavcodec.so, .so.63, .so.63.1.101):
# cópias iguais na mesma pasta viram links para a de nome mais longo (~40 MB a menos)
python3 - "${DESTINO}" <<'PY'
import collections, hashlib, os, sys
grupos = collections.defaultdict(list)
for pasta, _, arquivos in os.walk(sys.argv[1]):
    for nome in arquivos:
        caminho = os.path.join(pasta, nome)
        if os.path.islink(caminho) or os.path.getsize(caminho) < 65536:
            continue
        with open(caminho, "rb") as f:
            grupos[(pasta, hashlib.sha256(f.read()).hexdigest())].append(nome)
for (pasta, _), nomes in grupos.items():
    if len(nomes) > 1:
        nomes.sort(key=len, reverse=True)
        for nome in nomes[1:]:
            os.remove(os.path.join(pasta, nome))
            os.symlink(nomes[0], os.path.join(pasta, nome))
PY

# O GitHub Pages aceita arquivos de até 100 MB e o motor inteiro passa disso: o Chromium (biblioteca
# QtWebEngineCore, recursos e o processo auxiliar) vai num pacote à parte, duiaos-motor-web-chromium,
# da mesma versão, do qual o duiaos-motor-web depende (ADR 074)
C="${TRABALHO}/duiaos-motor-web-chromium"
mkdir -p "${C}/DEBIAN" "${C}/usr/lib/duiaos/motor-web/PySide6/Qt/lib"
cp "${PASTA}/DEBIAN-chromium/control" "${C}/DEBIAN/control"
mv "${QT}"/lib/libQt6WebEngineCore.so* "${C}/usr/lib/duiaos/motor-web/PySide6/Qt/lib/"
mv "${QT}/resources" "${QT}/libexec" "${C}/usr/lib/duiaos/motor-web/PySide6/Qt/"
[ -d "${QT}/translations/qtwebengine_locales" ] && \
  install -d "${C}/usr/lib/duiaos/motor-web/PySide6/Qt/translations" && \
  mv "${QT}/translations/qtwebengine_locales" "${C}/usr/lib/duiaos/motor-web/PySide6/Qt/translations/"

for P in "${D}" "${C}"; do
DOC="${P}/usr/share/doc/$(basename "${P}")"
install -d "${DOC}"
{
  echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"
  echo "Upstream-Name: Qt for Python (PySide6) e Qt, com o Qt WebEngine (Chromium)"
  echo "Source: https://download.qt.io/official_releases/QtForPython/pyside6/ e https://code.qt.io/"
  echo "Comment: Rodas oficiais do PyPI, versão ${PYSIDE} (Qt WebEngine ${WEBENGINE}), sem modificações. Empacotado pelo DuiaOS"
  echo "  (pacotes/duiaos-motor-web). O código-fonte desta versão exata está nos endereços acima."
  echo ""
  echo "Files: usr/lib/duiaos/motor-web/*"
  echo "Copyright: The Qt Company Ltd. e colaboradores; Chromium: The Chromium Authors"
  echo "License: LGPL-3.0-only"
  echo " Os avisos de licença do Qt WebEngine e do Chromium vêm junto, em"
  echo " /usr/lib/duiaos/motor-web/PySide6/Qt/ e nos .dist-info. Texto da LGPL-3:"
  echo " /usr/share/common-licenses/LGPL-3."
} > "${DOC}/copyright"
done

# 3. Fecha os pacotes
fechar() {
  local P="$1" NOME
  NOME="$(basename "${P}")"
  local EXTRA=""
  [ "${ARQ}" = "arm64" ] && EXTRA=", ${DEPENDENCIAS_ARM64}"
  sed -i -e "s|@VERSAO_DEB@|${VERSAO_DEB}|g" -e "s|@ARQUITETURA@|${ARQ}|g" -e "s|@DEPENDENCIAS_ARQ@|${EXTRA}|g" "${P}/DEBIAN/control"
  find "${P}" -name '__pycache__' -prune -exec rm -rf {} +
  find "${P}" -type d -exec chmod 0755 {} +
  find "${P}" -type f ! -perm -u+x -exec chmod 0644 {} +
  find "${P}" -type f -perm -u+x -exec chmod 0755 {} +
  (cd "${P}" && find . -path ./DEBIAN -prune -o -type f -printf '%P\0' | xargs -0 md5sum) > "${P}/DEBIAN/md5sums"
  local TAMANHO
  TAMANHO="$(du -sk --exclude=DEBIAN "${P}" | cut -f1)"
  echo "Installed-Size: ${TAMANHO}" >> "${P}/DEBIAN/control"
  dpkg-deb --root-owner-group -Zxz --build "${P}" "${SAIDA}/${NOME}_${VERSAO_DEB}_${ARQ}.deb" >/dev/null
  echo "    ${SAIDA}/${NOME}_${VERSAO_DEB}_${ARQ}.deb ($(du -h "${SAIDA}/${NOME}_${VERSAO_DEB}_${ARQ}.deb" | cut -f1), ${TAMANHO} KB instalado)"
}
fechar "${C}"
fechar "${D}"
