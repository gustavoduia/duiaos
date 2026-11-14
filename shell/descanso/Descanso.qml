// DuiaOS — Tela de Descanso: uma camada overlay em cada tela, com o teclado só para ela.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

Item {
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            screen: modelData
            width: modelData.width; height: modelData.height
            visible: true
            color: "black"
            title: "Tela de Descanso"
            LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                       | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
            LayerShell.Window.layer: LayerShell.Window.LayerOverlay
            LayerShell.Window.exclusionZone: -1
            LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
            LayerShell.Window.scope: "duiaos-descanso"
            ConteudoDescanso { anchors.fill: parent; onSair: Qt.quit() }
        }
    }
}
