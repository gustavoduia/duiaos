// Cartão flutuante com borda fina e sombra suave (sem efeitos de GPU).
import QtQuick

Item {
    id: raiz
    property alias cor: fundo.color
    property int raio: Tema.raioGrande
    default property alias conteudo: fundo.data

    Repeater {
        model: 3
        Rectangle {
            required property int index
            anchors.fill: fundo
            anchors.margins: -(index + 1) * 2
            anchors.topMargin: -(index + 1) * 1.5
            anchors.bottomMargin: -(index + 1) * 3
            radius: raio + (index + 1) * 2
            color: "transparent"
            border { width: 2; color: Qt.rgba(0.06, 0.09, 0.14, 0.05 - index * 0.012) }
        }
    }
    Rectangle {
        id: fundo
        anchors.fill: parent
        radius: raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        clip: false
    }
}
