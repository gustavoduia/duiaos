// Ícone de aplicativo do tema do sistema (image://icone), com a inicial como reserva.
import QtQuick
import QtQuick.Window

Item {
    property string icone: ""
    property string nome: ""
    property int tamanho: 44
    // Lado com que a imagem é carregada (veja Icone.qml): fixo no maior tamanho quando o ícone é animado
    property int resolucao: 0
    property int base: 0                    // aceito por igualdade com o Ladrilho (os ícones do tema não têm traço)
    // Tamanho exato dos pixels da tela (ADR 068); animado, o mipmap só entra se a imagem for mais que o dobro do
    // tamanho em repouso (veja Icone.qml)
    readonly property real densidade: Screen.devicePixelRatio > 0 ? Screen.devicePixelRatio : 1
    readonly property int ladoImagem: Math.max(1, Math.round((resolucao || tamanho) * densidade))
    width: tamanho; height: tamanho

    Image {
        id: imagem
        anchors.fill: parent
        sourceSize: Qt.size(parent.ladoImagem, parent.ladoImagem)
        source: parent.icone !== "" ? "image://icone/" + parent.icone : ""
        visible: status === Image.Ready
        asynchronous: true
        smooth: true
        mipmap: parent.resolucao > 2 * (parent.base || parent.tamanho)
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
