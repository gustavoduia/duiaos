// Interruptor liga/desliga.
import QtQuick

Rectangle {
    id: raiz
    property bool ligado: false
    property bool ativo: true
    signal alternado(bool ligado)
    width: 40; height: 24; radius: 12
    opacity: ativo ? 1 : 0.45
    color: ligado ? Tema.azulDuia : Tema.controleDesligado
    Behavior on color { ColorAnimation { duration: Tema.animacao } }
    Aurora { anchors.fill: parent; radius: parent.radius; visible: Tema.futurista; opacity: raiz.ligado ? 1 : 0
             Behavior on opacity { NumberAnimation { duration: Tema.animacao } } }
    Rectangle {
        width: 20; height: 20; radius: 10
        y: 2
        x: raiz.ligado ? raiz.width - width - 2 : 2
        color: "white"
        border { color: Qt.rgba(0, 0, 0, 0.08); width: 1 }
        Behavior on x { NumberAnimation { duration: Tema.animacao; easing.type: Easing.OutCubic } }
    }
    MouseArea {
        anchors.fill: parent
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.alternado(!raiz.ligado)
    }
}
