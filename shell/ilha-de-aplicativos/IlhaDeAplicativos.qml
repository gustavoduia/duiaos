// DuiaOS — Ilha de Aplicativos.
// Uma faixa arredondada que flutua acima da borda de baixo da tela,
// com os aplicativos fixados e os abertos (marcados com um ponto azul).
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

Window {
    id: janela

    readonly property color corFundo: "#F7F9FC"
    readonly property color corBorda: "#DDE3EC"
    readonly property color corDestaque: "#E8F0FE"
    readonly property color corAzulNoite: "#1A3A73"
    readonly property color corAzulDuia: "#2E6BE6"
    readonly property string fonte: "Manrope"

    readonly property int tamanhoIcone: 44
    readonly property int distanciaBorda: 10   // espaço entre a Ilha e a borda da tela

    width: Math.max(ilhaFundo.width, 120)
    height: ilhaFundo.height + distanciaBorda
    visible: true
    color: "transparent"
    title: "Ilha de Aplicativos"

    LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: height
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-ilha-de-aplicativos"

    Rectangle {
        id: ilhaFundo
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
        width: linha.width + 20
        height: janela.tamanhoIcone + 24
        radius: 20
        color: janela.corFundo
        border { color: janela.corBorda; width: 1 }

        Row {
            id: linha
            anchors.centerIn: parent
            spacing: 6

            // Botão da Central de Aplicativos: grade de 3 x 3 pontos
            Item {
                width: janela.tamanhoIcone + 8
                height: janela.tamanhoIcone + 14
                Rectangle {
                    id: realceCentral
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
                    width: janela.tamanhoIcone + 8; height: width
                    radius: 12
                    color: (areaCentral.containsMouse || ilha.centralVisivel) ? janela.corDestaque : "transparent"
                }
                Grid {
                    anchors.centerIn: realceCentral
                    columns: 3; spacing: 5
                    scale: areaCentral.pressed ? 0.92 : 1.0
                    Repeater {
                        model: 9
                        Rectangle { width: 7; height: 7; radius: 2; color: janela.corAzulNoite }
                    }
                }
                MouseArea {
                    id: areaCentral
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: ilha.alternarCentral()
                }
            }
            Rectangle {
                visible: ilha.itens.length > 0
                width: 1; height: janela.tamanhoIcone - 8
                anchors.verticalCenter: parent.verticalCenter
                color: janela.corBorda
            }

            Repeater {
                model: ilha.itens

                delegate: Row {
                    required property var modelData
                    required property int index
                    spacing: 6

                    // Divisória entre os fixados e os abertos não fixados
                    Rectangle {
                        visible: !modelData.fixado && (index === 0 || ilha.itens[index - 1].fixado)
                        width: 1; height: janela.tamanhoIcone - 8
                        anchors.verticalCenter: parent.verticalCenter
                        color: janela.corBorda
                    }

                    Item {
                        width: janela.tamanhoIcone + 8
                        height: janela.tamanhoIcone + 14

                        Rectangle {
                            id: realce
                            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
                            width: janela.tamanhoIcone + 8; height: width
                            radius: 12
                            color: area.containsMouse ? janela.corDestaque : "transparent"
                        }

                        Image {
                            id: imagem
                            anchors.centerIn: realce
                            width: janela.tamanhoIcone; height: width
                            sourceSize: Qt.size(width * 2, height * 2)
                            source: modelData.icone !== "" ? "image://icone/" + modelData.icone : ""
                            visible: status === Image.Ready
                            scale: area.pressed ? 0.92 : (area.containsMouse ? 1.08 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 120 } }
                        }

                        // Sem ícone no tema: quadrado com a inicial do aplicativo
                        Rectangle {
                            anchors.centerIn: realce
                            visible: imagem.status !== Image.Ready
                            width: janela.tamanhoIcone; height: width
                            radius: 12
                            color: janela.corAzulDuia
                            scale: imagem.scale
                            Text {
                                anchors.centerIn: parent
                                text: modelData.nome.charAt(0).toUpperCase()
                                color: "white"
                                font { family: janela.fonte; pixelSize: 22; weight: Font.Bold }
                            }
                        }

                        // Ponto azul: aplicativo aberto
                        Rectangle {
                            visible: modelData.aberto
                            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 1 }
                            width: 5; height: 5; radius: 2.5
                            color: janela.corAzulDuia
                        }

                        MouseArea {
                            id: area
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: ilha.ativar(index)
                        }
                    }
                }
            }
        }
    }

    // Central de Aplicativos (janela própria, aparece por cima de tudo)
    CentralDeAplicativos {}
}
