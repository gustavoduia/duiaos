// DuiaOS — janela dos balões de notificação: camada overlay presa ao canto de cima, à direita,
// abaixo da Barra de Recursos; só existe enquanto há balões.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: janela
    screen: Telas.principal(Qt.application.screens)
    width: 380
    height: Math.max(1, baloes.height + 20)
    visible: notificacoes.visiveis.length > 0
    color: "transparent"
    title: "Notificações"
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.exclusionZone: 0
    LayerShell.Window.margins.top: 6
    LayerShell.Window.margins.right: 6
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-notificacoes"
    Baloes { id: baloes; x: 10; y: 10 }
}
