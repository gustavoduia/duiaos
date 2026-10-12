// DuiaOS — Central de Aplicativos.
// Cobre a tela com um fundo escurecido e mostra, num cartão central,
// a busca e a grade de todos os aplicativos instalados.
// Enter abre o primeiro resultado · clique direito fixa/desafixa na Ilha · Esc fecha.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: central
    // Fica na tela principal (a do notebook, quando houver; comum/telas.js)
    screen: Telas.principal(Qt.application.screens)

    readonly property color corFundo: "#F7F9FC"
    readonly property color corSuperficie: "#FFFFFF"
    readonly property color corBorda: "#DDE3EC"
    readonly property color corDestaque: "#E8F0FE"
    readonly property color corTexto: "#1F2933"
    readonly property color corTextoSecundario: "#5B6675"
    readonly property color corAzulNoite: "#1A3A73"
    readonly property color corAzulDuia: "#2E6BE6"

    visible: ilha.centralVisivel
    width: Screen.width
    height: Screen.height
    color: "transparent"
    title: "Central de Aplicativos"

    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
    LayerShell.Window.scope: "duiaos-central-de-aplicativos"

    onVisibleChanged: {
        if (visible) {
            campo.text = ""
            campo.forceActiveFocus()
        }
    }

    // Fundo escurecido: clique fora do cartão fecha a Central
    Rectangle {
        anchors.fill: parent
        color: central.corTexto
        opacity: 0.35
        MouseArea {
            anchors.fill: parent
            onClicked: ilha.fecharCentral()
        }
    }

    Rectangle {
        id: cartao
        anchors.centerIn: parent
        width: Math.min(780, parent.width - 80)
        height: Math.min(560, parent.height - 120)
        radius: 24
        color: central.corFundo
        border { color: central.corBorda; width: 1 }

        MouseArea { anchors.fill: parent }   // cliques no cartão não fecham a Central

        Text {
            id: titulo
            anchors { left: parent.left; top: parent.top; leftMargin: 28; topMargin: 24 }
            text: "Central de Aplicativos"
            color: central.corAzulNoite
            font { family: "Manrope"; pixelSize: 20; weight: Font.Bold }
        }

        // Campo de busca
        Rectangle {
            id: caixaBusca
            anchors { left: parent.left; right: parent.right; top: titulo.bottom; leftMargin: 28; rightMargin: 28; topMargin: 16 }
            height: 44
            radius: 12
            color: central.corSuperficie
            border { color: campo.activeFocus ? central.corAzulDuia : central.corBorda; width: campo.activeFocus ? 2 : 1 }

            TextInput {
                id: campo
                anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                verticalAlignment: TextInput.AlignVCenter
                color: central.corTexto
                font { family: "Inter"; pixelSize: 15 }
                selectByMouse: true
                clip: true
                onTextChanged: ilha.buscar(text)
                Keys.onEscapePressed: ilha.fecharCentral()
                Keys.onReturnPressed: abrirPrimeiro()
                Keys.onEnterPressed: abrirPrimeiro()
                function abrirPrimeiro() {
                    if (ilha.resultados.length > 0)
                        ilha.abrirAplicativo(ilha.resultados[0].id)
                }
            }
            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                visible: campo.text === ""
                text: "Buscar aplicativos"
                color: central.corTextoSecundario
                font { family: "Inter"; pixelSize: 15 }
            }
        }

        // Grade de aplicativos
        GridView {
            id: grade
            anchors { left: parent.left; right: parent.right; top: caixaBusca.bottom; bottom: rodape.top
                      leftMargin: 20; rightMargin: 20; topMargin: 16; bottomMargin: 8 }
            clip: true
            cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 128)))
            cellHeight: 112
            model: ilha.resultados

            delegate: Item {
                required property var modelData
                width: grade.cellWidth
                height: grade.cellHeight

                Rectangle {
                    anchors { fill: parent; margins: 4 }
                    radius: 14
                    color: area.containsMouse ? central.corDestaque : "transparent"
                }

                Image {
                    id: icone
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 12 }
                    width: 48; height: 48
                    sourceSize: Qt.size(96, 96)
                    source: modelData.icone !== "" ? "image://icone/" + modelData.icone : ""
                    visible: status === Image.Ready
                }
                Rectangle {
                    anchors.centerIn: icone
                    visible: icone.status !== Image.Ready
                    width: 48; height: 48; radius: 12
                    color: central.corAzulDuia
                    Text {
                        anchors.centerIn: parent
                        text: modelData.nome.charAt(0).toUpperCase()
                        color: "white"
                        font { family: "Manrope"; pixelSize: 22; weight: Font.Bold }
                    }
                }

                // Marca de fixado na Ilha
                Rectangle {
                    visible: modelData.fixado
                    anchors { right: icone.right; top: icone.top; rightMargin: -4; topMargin: -4 }
                    width: 10; height: 10; radius: 5
                    color: central.corAzulDuia
                    border { color: central.corFundo; width: 2 }
                }

                Text {
                    anchors { left: parent.left; right: parent.right; top: icone.bottom; topMargin: 8; leftMargin: 8; rightMargin: 8 }
                    text: modelData.nome
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                    color: central.corTexto
                    font { family: "Inter"; pixelSize: 12 }
                }

                MouseArea {
                    id: area
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: (evento) => {
                        if (evento.button === Qt.RightButton)
                            ilha.alternarFixado(modelData.id)
                        else
                            ilha.abrirAplicativo(modelData.id)
                    }
                }
            }
        }

        Text {
            anchors.centerIn: grade
            visible: ilha.resultados.length === 0
            text: "Nenhum aplicativo encontrado"
            color: central.corTextoSecundario
            font { family: "Inter"; pixelSize: 14 }
        }

        Text {
            id: rodape
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 16 }
            text: "Enter abre o primeiro  ·  clique direito fixa na Ilha  ·  Esc fecha"
            color: central.corTextoSecundario
            font { family: "Inter"; pixelSize: 12 }
        }
    }
}
