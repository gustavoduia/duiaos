// DuiaOS — Central de Aplicativos: camada em tela cheia com ConteudoCentral.qml
// (busca e grade de todos os aplicativos; clique direito fixa/desafixa na Ilha).
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: central
    // Fica na tela principal (a do notebook, quando houver; comum/telas.js)
    screen: Telas.principal(Qt.application.screens)
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
            conteudo.campo.text = ""
            conteudo.campo.forceActiveFocus()
        }
    }
    ConteudoCentral { id: conteudo; anchors.fill: parent }
}
