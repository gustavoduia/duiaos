// DuiaOS — pilha de Downloads: balão ao lado da Ilha com os arquivos mais novos.
import QtQuick
import DuiaOS
import "posicao.js" as Posicao

Item {
    id: pilha
    MouseArea { anchors.fill: parent; onClicked: ilha.fecharDownloads() }
    focus: true
    Keys.onEscapePressed: ilha.fecharDownloads()

    Cartao {
        id: cartao
        width: 4 * 92 + 28
        height: colunaPilha.implicitHeight + 24
        readonly property var lugar: Posicao.balao(ilha.opcoes.posicao, pilha.width, pilha.height, ilha.ancoraDownloads, width, height)
        x: lugar.x
        y: lugar.y
        MouseArea { anchors.fill: parent }
        Column {
            id: colunaPilha
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
            spacing: 8
            Text { text: "Downloads"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 15; weight: Font.Bold } }
            Grid {
                columns: 4
                spacing: 0
                Repeater {
                    model: ilha.downloads
                    Rectangle {
                        required property var modelData
                        width: 92; height: 98; radius: 10
                        color: areaArquivo.containsMouse ? Tema.destaque : "transparent"
                        Item {
                            id: figura
                            width: 52; height: 52
                            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 8 }
                            Image {
                                id: miniatura
                                anchors.fill: parent
                                source: modelData.miniatura
                                sourceSize: Qt.size(104, 104)
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                visible: status === Image.Ready
                            }
                            Ladrilho { anchors.fill: parent; visible: !miniatura.visible; icone: modelData.icone; estilo: "claro"; tamanho: 52 }
                        }
                        Text {
                            anchors { left: parent.left; right: parent.right; top: figura.bottom; topMargin: 6; leftMargin: 4; rightMargin: 4 }
                            text: modelData.nome
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                            color: Tema.texto
                            font { family: Tema.fonteTexto; pixelSize: 11 }
                        }
                        MouseArea { id: areaArquivo; anchors.fill: parent; hoverEnabled: true; onClicked: ilha.abrirArquivo(modelData.caminho) }
                    }
                }
            }
            Rotulo { visible: ilha.downloads.length === 0; secundario: true; text: "A pasta Downloads está vazia." }
            Separador {}
            ItemDeMenu { texto: "Abrir a pasta Downloads"; icone: "pasta"; onClicado: ilha.abrirPasta("downloads") }
        }
    }
}
