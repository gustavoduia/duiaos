// Botão de texto: "primario" (azul), "secundario" (contorno) ou "perigo".
import QtQuick

Rectangle {
    id: raiz
    property string texto: ""
    property string icone: ""
    property string tipo: "secundario"
    property bool ativo: true
    signal clicado()
    implicitWidth: linha.implicitWidth + 28
    implicitHeight: 34
    radius: 10
    opacity: ativo ? 1 : 0.5
    readonly property color corBase: tipo === "primario" ? Tema.azulDuia : (tipo === "perigo" ? Tema.erro : Tema.cartao)
    color: area.pressed ? Qt.darker(corBase, 1.12) : (area.containsMouse ? Qt.darker(corBase, 1.04) : corBase)
    border { width: tipo === "secundario" ? 1 : 0; color: Tema.bordaForte }
    Row {
        id: linha
        anchors.centerIn: parent
        spacing: 6
        Icone {
            visible: raiz.icone !== ""
            nome: raiz.icone; tamanho: 16
            cor: raiz.tipo === "secundario" ? Tema.texto : "white"
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: raiz.texto
            anchors.verticalCenter: parent.verticalCenter
            color: raiz.tipo === "secundario" ? Tema.texto : "white"
            font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.clicado()
    }
}
