// DuiaOS — Ora: ícone de um site (o favicon que o motor guardou) ou a inicial num círculo colorido.
import QtQuick
import DuiaOS

Item {
    id: raiz
    property string url: ""
    property string titulo: ""
    property int tamanho: 16
    width: tamanho; height: tamanho
    readonly property string letra: {
        var base = ora.dominio(url) || titulo || "?"
        return base.charAt(0).toUpperCase()
    }
    readonly property var cores: ["#2E6BE6", "#7C3AED", "#0EA5A4", "#E8833D", "#D9467A", "#2F9E5E", "#5B6CF0"]
    Image {
        id: imagem
        anchors.fill: parent
        source: raiz.url !== "" && raiz.url.indexOf("http") === 0 ? "image://favicon/" + raiz.url : ""
        sourceSize: Qt.size(raiz.tamanho * 2, raiz.tamanho * 2)
        asynchronous: true
        visible: status === Image.Ready && implicitWidth > 1
    }
    Rectangle {
        anchors.fill: parent
        visible: !imagem.visible
        radius: width / 2
        color: raiz.cores[Math.abs(raiz.letra.charCodeAt(0)) % raiz.cores.length]
        Text {
            anchors.centerIn: parent
            text: raiz.letra
            color: "white"
            font { family: Tema.fonteTitulo; pixelSize: Math.round(raiz.tamanho * 0.55); weight: Font.Bold }
        }
    }
}
