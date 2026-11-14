// Ícone de aplicativo do tema do sistema (image://icone), com a inicial como reserva.
import QtQuick

Item {
    property string icone: ""
    property string nome: ""
    property int tamanho: 44
    width: tamanho; height: tamanho

    Image {
        id: imagem
        anchors.fill: parent
        sourceSize: Qt.size(parent.width * 2, parent.height * 2)
        source: parent.icone !== "" ? "image://icone/" + parent.icone : ""
        visible: status === Image.Ready
        asynchronous: true
    }
    Rectangle {
        anchors.fill: parent
        visible: imagem.status !== Image.Ready
        radius: width * 0.26
        gradient: Gradient {
            GradientStop { position: 0; color: "#4F86F0" }
            GradientStop { position: 1; color: Tema.azulDuia }
        }
        Text {
            anchors.centerIn: parent
            text: parent.parent.nome.charAt(0).toUpperCase()
            color: "white"
            font { family: Tema.fonteTitulo; pixelSize: parent.width * 0.48; weight: Font.Bold }
        }
    }
}
