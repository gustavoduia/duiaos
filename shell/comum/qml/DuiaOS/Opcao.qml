// Opção de escolha única (círculo marcado).
import QtQuick

Item {
    id: raiz
    property string texto: ""
    property string descricao: ""
    property bool marcada: false
    signal escolhida()
    width: parent ? parent.width : 240
    height: Math.max(28, colunaTexto.height + 8)
    Rectangle {
        id: bolinha
        width: 18; height: 18; radius: 9
        anchors { left: parent.left; top: parent.top; topMargin: 5 }
        color: "white"
        border { width: raiz.marcada ? 5 : 1.5; color: raiz.marcada ? Tema.azulDuia : Tema.bordaForte }
    }
    Column {
        id: colunaTexto
        anchors { left: bolinha.right; leftMargin: 10; right: parent.right; top: parent.top; topMargin: 4 }
        Text { text: raiz.texto; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } width: parent.width; wrapMode: Text.WordWrap }
        Text { visible: raiz.descricao !== ""; text: raiz.descricao; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } width: parent.width; wrapMode: Text.WordWrap }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: raiz.escolhida() }
    Accessible.role: Accessible.RadioButton
    Accessible.name: texto
    Accessible.checked: marcada
}
