// DuiaOS — Menu de Energia da sessão.
// Escurece a tela e mostra as opções no centro. Abre ao clicar no símbolo
// do DuiaOS na Barra de Recursos ou com Ctrl+Alt+Delete. Esc ou um clique
// fora do cartão fecha o menu.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum"
import "../comum/estilo.js" as Estilo

Window {
    id: janela
    visible: true
    color: "transparent"
    title: "Menu de Energia"

    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                               | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
    LayerShell.Window.scope: "duiaos-menu-de-energia"

    Rectangle {
        id: veu
        anchors.fill: parent
        color: Estilo.azulProfundo
        opacity: 0
        Component.onCompleted: opacity = 0.35
        Behavior on opacity { NumberAnimation { duration: 150 } }
    }
    MouseArea { anchors.fill: parent; onClicked: menuEnergia.fechar() }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: menuEnergia.fechar()

        Rectangle {
            id: cartao
            anchors.centerIn: parent
            width: 380
            height: colunaCartao.height + 40
            radius: 24
            color: Estilo.cartao
            border { color: Estilo.borda; width: 1 }
            scale: 0.96
            Component.onCompleted: scale = 1
            Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            MouseArea { anchors.fill: parent }   // clique no cartão não fecha

            Column {
                id: colunaCartao
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 12
                Row {
                    spacing: 10
                    leftPadding: 8
                    Simbolo { width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Energia"
                        font { family: Estilo.fonteTitulo; pixelSize: 20; weight: Font.Bold }
                        color: Estilo.azulNoite
                    }
                }
                MenuDeEnergia {
                    width: parent.width
                    opcoes: menuEnergia.opcoes
                    border.width: 0
                    onEscolhido: (id) => menuEnergia.escolher(id)
                }
            }
        }
    }
}
