// DuiaOS — janela do alternador de aplicativos (Alt+Tab, ADR 077): camada por cima de tudo, com o teclado
// só para ela enquanto aparece (para saber quando o Alt é solto). O conteúdo fica em ConteudoAlternador.qml.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: alternador
    screen: Telas.principal(Qt.application.screens)
    visible: ilha.alternadorVisivel
    width: Screen.width
    height: Screen.height
    color: "transparent"
    title: "Alternador de aplicativos"

    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
    LayerShell.Window.scope: "duiaos-alternador"

    onVisibleChanged: if (visible) teclas.forceActiveFocus()

    MouseArea { anchors.fill: parent; onClicked: ilha.alternadorCancelar() }
    ConteudoAlternador { anchors.fill: parent }
    Item {
        id: teclas
        focus: true
        Keys.onPressed: (e) => {
            if (e.key === Qt.Key_Tab || e.key === Qt.Key_Right) { ilha.alternadorMover(1); e.accepted = true }
            else if (e.key === Qt.Key_Backtab || e.key === Qt.Key_Left) { ilha.alternadorMover(-1); e.accepted = true }
            else if (e.key === Qt.Key_Escape) { ilha.alternadorCancelar(); e.accepted = true }
            else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { ilha.alternadorConfirmar(); e.accepted = true }
        }
        Keys.onReleased: (e) => { if (e.key === Qt.Key_Alt) ilha.alternadorConfirmar() }
    }
}
