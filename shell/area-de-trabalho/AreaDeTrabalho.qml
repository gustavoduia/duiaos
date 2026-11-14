// DuiaOS — Área de Trabalho: uma camada "background" do layer-shell em cada tela, por baixo de
// todas as janelas. Os ícones ficam só na tela principal (a do notebook, quando houver).
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Item {
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            required property int index
            screen: modelData
            width: modelData.width; height: modelData.height
            visible: true
            color: "black"
            title: "Área de Trabalho"
            LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                       | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
            LayerShell.Window.layer: LayerShell.Window.LayerBackground
            LayerShell.Window.exclusionZone: -1
            LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
            LayerShell.Window.scope: "duiaos-area-de-trabalho"
            ConteudoArea {
                anchors.fill: parent
                mostrarIcones: index === Telas.indicePrincipal(Qt.application.screens)
            }
        }
    }
}
