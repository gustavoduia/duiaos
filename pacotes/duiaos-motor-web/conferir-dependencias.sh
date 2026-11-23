#!/bin/bash
# =============================================================================
# DuiaOS — confere se o motor web instala e abre num Debian 13 limpo (ADR 075).
#
# Uso (como root, DENTRO de um Debian 13 da arquitetura dos pacotes, ex.: um
# container debian:trixie):
#   bash pacotes/duiaos-motor-web/conferir-dependencias.sh PASTA_COM_OS_DEB
#
# Instala o duiaos-motor-web e o duiaos-motor-web-chromium com o apt (que puxa
# as dependências declaradas), procura bibliotecas que faltam nas peças que o Ora
# e o Mail Box carregam e importa o Qt WebEngine. Falha se faltar alguma: foi o
# que fez o Ora e o Mail Box não abrirem no ARM (a roda aarch64 usa bibliotecas
# do sistema que a de Intel/AMD traz dentro).
# =============================================================================
set -euo pipefail

PASTA="$(cd "${1:?Uso: conferir-dependencias.sh PASTA_COM_OS_DEB}" && pwd)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends "${PASTA}"/duiaos-motor-web-chromium_*.deb "${PASTA}"/duiaos-motor-web_*.deb >/dev/null

QT=/usr/lib/duiaos/motor-web/PySide6/Qt
PECAS=("${QT}/lib/libQt6WebEngineCore.so.6" "${QT}/libexec/QtWebEngineProcess" "${QT}/lib/libQt6WebEngineQuick.so.6"
       "${QT}/lib/libQt6Quick.so.6" "${QT}/lib/libQt6Gui.so.6" "${QT}/lib/libQt6WaylandClient.so.6"
       "${QT}"/plugins/platforms/libqwayland*.so "${QT}/plugins/platforms/libqxcb.so" "${QT}/plugins/platforms/libqoffscreen.so"
       /usr/lib/duiaos/motor-web/PySide6/QtWebEngineQuick.abi3.so /usr/lib/duiaos/motor-web/PySide6/QtQuick.abi3.so)
FALTAM="$(for PECA in "${PECAS[@]}"; do
  if [ -e "${PECA}" ]; then ldd "${PECA}" | grep 'not found' || true; fi
done | sort -u)"
if [ -n "${FALTAM}" ]; then
  echo "Bibliotecas que faltam no motor web ($(dpkg --print-architecture)):" >&2
  echo "${FALTAM}" >&2
  echo "Acrescente o pacote de cada uma ao DEBIAN/control (ou a DEPENDENCIAS_ARM64 em VERSAO)." >&2
  exit 1
fi
QT_QPA_PLATFORM=offscreen python3 -c "
import sys; sys.path.insert(0, '/usr/lib/duiaos/motor-web')
from PySide6 import QtWebEngineQuick, QtWebEngineCore, QtQuick, QtQml  # noqa: F401
print('Motor web conferido:', QtWebEngineCore.qWebEngineChromiumVersion())
"
