// Fundo de tela: imagem, imagem com movimento (GIF/WebP animado), vídeo (sem som, em laço) ou cor.
// Usado pela Área de Trabalho (papel de parede), pela Tela de Descanso e pelas Configurações.
// ajuste (shell/comum/papel.py): preencher, ajustar, esticar, centralizar ou lado-a-lado.
// estendido: {largura, altura, dx, dy} — uma imagem só por todas as telas; esta mostra a sua parte.
import QtQuick

Rectangle {
    id: fundo
    property string arquivo: ""          // caminho; vazio = só a cor
    property color corFundo: "#E8F0FE"
    property bool tocando: true          // vídeos e animações param quando false
    property string ajuste: "preencher"
    property var estendido: null
    property real escala: 1              // miniaturas: a imagem como ficaria numa tela maior
    color: corFundo
    clip: true

    readonly property int modoImagem: ajuste === "ajustar" ? Image.PreserveAspectFit
        : ajuste === "esticar" ? Image.Stretch
        : ajuste === "centralizar" ? Image.Pad
        : ajuste === "lado-a-lado" ? Image.Tile : Image.PreserveAspectCrop
    readonly property bool tamanhoNatural: ajuste === "centralizar" || ajuste === "lado-a-lado"
    // Área onde a imagem é desenhada: a tela, ou a área de todas as telas (estendido)
    readonly property real larguraArea: estendido ? estendido.largura * escala : width
    readonly property real alturaArea: estendido ? estendido.altura * escala : height
    readonly property real deslocX: estendido ? -estendido.dx * escala : 0
    readonly property real deslocY: estendido ? -estendido.dy * escala : 0

    readonly property string extensao: arquivo.toLowerCase().split(".").pop()
    readonly property string tipo: arquivo === "" ? "cor"
        : (["mp4", "webm", "mkv", "mov", "m4v", "ogv"].indexOf(extensao) >= 0 ? "video"
        : (["gif", "webp"].indexOf(extensao) >= 0 ? "animada" : "imagem"))
    readonly property string url: arquivo === "" ? "" : (arquivo.indexOf("file:") === 0 ? arquivo : "file://" + arquivo)

    Item {
        x: fundo.deslocX; y: fundo.deslocY
        width: fundo.larguraArea; height: fundo.alturaArea
        // Tamanho natural (centralizar, lado a lado) numa miniatura: desenha grande e reduz
        Image {
            id: imagem
            visible: fundo.tipo === "imagem"
            width: parent.width / fundo.escala; height: parent.height / fundo.escala
            scale: fundo.escala
            transformOrigin: Item.TopLeft
            source: visible ? fundo.url : ""
            fillMode: fundo.modoImagem
            sourceSize: fundo.tamanhoNatural ? undefined : Qt.size(width, height)
            asynchronous: true
            cache: false
        }
        AnimatedImage {
            visible: fundo.tipo === "animada"
            width: parent.width / fundo.escala; height: parent.height / fundo.escala
            scale: fundo.escala
            transformOrigin: Item.TopLeft
            source: visible ? fundo.url : ""
            fillMode: fundo.modoImagem
            playing: fundo.tocando
            asynchronous: true
            cache: false
        }
        // Vídeo num arquivo à parte: sem o módulo de multimídia, o resto continua funcionando
        Loader {
            anchors.fill: parent
            active: fundo.tipo === "video"
            source: active ? Qt.resolvedUrl("FundoVideo.qml") : ""
            onLoaded: {
                item.fonte = fundo.url
                item.tocando = Qt.binding(function () { return fundo.tocando })
                item.ajuste = Qt.binding(function () { return fundo.ajuste })
            }
        }
    }
}
