// Campo de texto de uma linha.
import QtQuick

Rectangle {
    id: raiz
    property alias texto: entrada.text
    property alias entrada: entrada
    property string dica: ""
    property string icone: ""
    property bool senha: false
    signal confirmado()
    implicitHeight: 34
    radius: Math.min(height / 2, Tema.raioControle)
    color: Tema.futurista ? (Tema.escuro ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(1, 1, 1, 0.9)) : Tema.cartao
    border { color: entrada.activeFocus ? Tema.azulDuia : Tema.bordaForte; width: entrada.activeFocus ? 2 : 1 }
    // Anel de foco (futurista): um halo aurora em volta do campo
    Aurora {
        visible: Tema.futurista && entrada.activeFocus
        z: -1
        anchors { fill: parent; margins: -3 }
        radius: parent.radius + 3
        opacity: 0.35
    }
    Icone {
        id: iconeCampo
        visible: raiz.icone !== ""
        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
        nome: raiz.icone; tamanho: 15; cor: Tema.textoSecundario
    }
    TextInput {
        id: entrada
        anchors { left: raiz.icone !== "" ? iconeCampo.right : parent.left; right: parent.right
                  leftMargin: raiz.icone !== "" ? 8 : 12; rightMargin: 12; verticalCenter: parent.verticalCenter }
        font { family: Tema.fonteTexto; pixelSize: 13 }
        color: Tema.texto
        selectionColor: Tema.azulDuia
        clip: true
        activeFocusOnTab: true          // Tab passa para o próximo campo (o TextInput do Qt não faz isso sozinho)
        echoMode: raiz.senha ? TextInput.Password : TextInput.Normal
        onAccepted: raiz.confirmado()
        Text {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            text: raiz.dica
            visible: entrada.text === "" && !entrada.preeditText
            color: Tema.textoApagado
            font: entrada.font
        }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.IBeamCursor; onPressed: (m) => { entrada.forceActiveFocus(); m.accepted = false } }
}
