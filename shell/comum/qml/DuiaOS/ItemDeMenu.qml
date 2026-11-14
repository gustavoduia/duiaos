// Linha de menu: ícone, texto e atalho; realce azul ao passar o mouse.
import QtQuick

Rectangle {
    id: raiz
    property string texto: ""
    property string icone: ""
    property string atalho: ""
    property bool ativo: true
    property bool perigo: false
    signal clicado()
    width: parent ? parent.width : 220
    height: 30
    radius: 7
    color: area.containsMouse && ativo ? Tema.azulDuia : "transparent"
    readonly property color corTexto: area.containsMouse && ativo ? "white" : (ativo ? (perigo ? Tema.erro : Tema.texto) : Tema.textoApagado)
    Icone {
        id: ic
        visible: raiz.icone !== ""
        anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter }
        nome: raiz.icone; tamanho: 16; cor: raiz.corTexto
    }
    Text {
        anchors { left: raiz.icone !== "" ? ic.right : parent.left; leftMargin: raiz.icone !== "" ? 9 : 12
                  right: textoAtalho.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
        text: raiz.texto
        elide: Text.ElideRight
        color: raiz.corTexto
        font { family: Tema.fonteTexto; pixelSize: 13 }
    }
    Text {
        id: textoAtalho
        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
        text: raiz.atalho
        color: area.containsMouse && raiz.ativo ? "#DDE7FB" : Tema.textoApagado
        font { family: Tema.fonteTexto; pixelSize: 12 }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        onClicked: raiz.clicado()
    }
    Accessible.role: Accessible.MenuItem
    Accessible.name: texto
}
