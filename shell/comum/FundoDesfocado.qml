// DuiaOS — fundo desfocado das Telas de Entrada e de Bloqueio (opção "Desfocar" nas Configurações).
// Arquivo à parte: sem o módulo QtQuick.Effects (qml6-module-qtquick-effects), a tela mostra o
// fundo sem desfoque em vez de falhar.
import QtQuick
import QtQuick.Effects

MultiEffect {
    property Item fonte
    source: fonte
    blurEnabled: true
    blur: 1.0
    blurMax: 56
    saturation: 0.1
}
