// DuiaOS — balões de notificação, um embaixo do outro (o mais novo em cima).
import QtQuick
import DuiaOS

Column {
    id: baloes
    width: 360
    spacing: 10
    Repeater {
        model: notificacoes.visiveis
        Cartao {
            id: balao
            required property var modelData
            width: baloes.width
            height: conteudo.implicitHeight + 24
            raio: 16
            Rectangle { visible: modelData.urgencia >= 2; anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 1 }
                        width: 4; radius: 2; color: Tema.erro }
            MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; id: area
                        onClicked: notificacoes.clicar(modelData.id) }
            Column {
                id: conteudo
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                spacing: 6
                Row {
                    width: parent.width
                    spacing: 10
                    Item {
                        width: 36; height: 36
                        Image { id: img; anchors.fill: parent; fillMode: Image.PreserveAspectCrop; asynchronous: true
                                sourceSize: Qt.size(72, 72); visible: status === Image.Ready
                                source: modelData.tipoIcone === "arquivo" ? modelData.valorIcone
                                        : (modelData.tipoIcone === "tema" ? "image://icone/" + modelData.valorIcone : "") }
                        Ladrilho { anchors.fill: parent; visible: !img.visible; tamanho: 36; radius: 9
                                   icone: modelData.app === "Wise" ? "ia" : "ponto"; estilo: "azul" }
                    }
                    Column {
                        width: parent.width - 46 - 26
                        Row {
                            spacing: 6
                            Text { text: modelData.app; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
                            Text { text: modelData.quando; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11 } }
                        }
                        Text { width: parent.width; text: modelData.titulo; elide: Text.ElideRight; color: Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Bold } }
                        Text { width: parent.width; visible: modelData.texto !== ""; text: modelData.texto; textFormat: Text.StyledText
                               wrapMode: Text.WordWrap; maximumLineCount: 4; elide: Text.ElideRight
                               color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                    }
                }
                Row {
                    visible: modelData.acoes.length > 0
                    anchors.right: parent.right
                    spacing: 6
                    Repeater {
                        model: modelData.acoes
                        Botao { required property var modelData; texto: modelData.rotulo; height: 28
                                onClicado: notificacoes.acionar(balao.modelData.id, modelData.chave) }
                    }
                }
            }
            BotaoIcone {
                anchors { right: parent.right; top: parent.top; margins: 8 }
                width: 22; height: 22; icone: "fechar"; tamanhoIcone: 12; corIcone: Tema.textoSecundario
                opacity: area.containsMouse || hovered ? 1 : 0.55
                property bool hovered: false
                onClicado: notificacoes.fechar(balao.modelData.id)
            }
        }
    }
}
