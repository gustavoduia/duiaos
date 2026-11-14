// Linha clicável de lista (redes Wi-Fi, dispositivos), com ícone, texto, detalhe e conteúdo à direita.
import QtQuick

Rectangle {
    id: raiz
    property string icone: ""
    property color corIcone: Tema.texto
    property string texto: ""
    property string detalhe: ""
    property bool marcada: false
    default property alias direita: lado.data
    signal clicada()
    width: parent ? parent.width : 260
    height: detalhe !== "" ? 44 : 34
    radius: 8
    color: area.containsMouse ? Qt.rgba(0.06, 0.09, 0.14, 0.05) : "transparent"
    Rectangle {
        id: fundoIcone
        visible: raiz.icone !== ""
        width: 26; height: 26; radius: 13
        anchors { left: parent.left; leftMargin: 6; verticalCenter: parent.verticalCenter }
        color: raiz.marcada ? Tema.azulDuia : Tema.controleDesligado
        Icone { anchors.centerIn: parent; nome: raiz.icone; tamanho: 15; cor: raiz.marcada ? "white" : raiz.corIcone }
    }
    Column {
        anchors { left: raiz.icone !== "" ? fundoIcone.right : parent.left; leftMargin: 10
                  right: lado.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
        Text { width: parent.width; text: raiz.texto; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: raiz.marcada ? Font.DemiBold : Font.Normal } }
        Text { width: parent.width; visible: raiz.detalhe !== ""; text: raiz.detalhe; elide: Text.ElideRight; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; onClicked: raiz.clicada() }
    Row {
        id: lado
        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
        spacing: 6
        z: 2
    }
}
