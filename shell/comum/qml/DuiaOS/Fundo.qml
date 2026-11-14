// Fundo de tela: imagem, imagem com movimento (GIF/WebP animado), vídeo (sem som, em laço) ou cor.
// Usado pela Área de Trabalho (papel de parede) e pela Tela de Descanso.
import QtQuick

Rectangle {
    id: fundo
    property string arquivo: ""          // caminho; vazio = só a cor
    property color corFundo: "#E8F0FE"
    property bool tocando: true          // vídeos e animações param quando false
    color: corFundo

    readonly property string extensao: arquivo.toLowerCase().split(".").pop()
    readonly property string tipo: arquivo === "" ? "cor"
        : (["mp4", "webm", "mkv", "mov", "m4v", "ogv"].indexOf(extensao) >= 0 ? "video"
        : (["gif", "webp"].indexOf(extensao) >= 0 ? "animada" : "imagem"))
    readonly property string url: arquivo === "" ? "" : (arquivo.indexOf("file:") === 0 ? arquivo : "file://" + arquivo)

    Image {
        anchors.fill: parent
        visible: fundo.tipo === "imagem"
        source: visible ? fundo.url : ""
        fillMode: Image.PreserveAspectCrop
        sourceSize: Qt.size(fundo.width, fundo.height)
        asynchronous: true
        cache: false
    }
    AnimatedImage {
        anchors.fill: parent
        visible: fundo.tipo === "animada"
        source: visible ? fundo.url : ""
        fillMode: Image.PreserveAspectCrop
        playing: fundo.tocando
        asynchronous: true
        cache: false
    }
    // Vídeo num arquivo à parte: sem o módulo de multimídia, o resto continua funcionando
    Loader {
        anchors.fill: parent
        active: fundo.tipo === "video"
        source: active ? Qt.resolvedUrl("FundoVideo.qml") : ""
        onLoaded: { item.fonte = fundo.url; item.tocando = Qt.binding(function () { return fundo.tocando }) }
    }
}
