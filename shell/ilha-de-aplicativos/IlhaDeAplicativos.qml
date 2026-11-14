// DuiaOS — Ilha de Aplicativos.
// Uma faixa arredondada que flutua acima da borda de baixo da tela, com a Central de
// Aplicativos, os aplicativos fixados e os abertos (ponto embaixo) e, depois da
// divisória, a pasta Aplicativos, a pilha de Downloads e a Lixeira.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: janela
    // Fica na tela principal (a do notebook, quando houver; comum/telas.js)
    screen: Telas.principal(Qt.application.screens)
    readonly property int distanciaBorda: 8   // espaço entre a Ilha e a borda da tela

    width: Math.max(conteudo.width, 120)
    height: conteudo.height + distanciaBorda
    visible: true
    color: "transparent"
    title: "Ilha de Aplicativos"

    LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: height
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-ilha-de-aplicativos"

    Ilha {
        id: conteudo
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
        deslocamentoX: (Screen.width - janela.width) / 2
    }

    // Central de Aplicativos (janela própria, aparece por cima de tudo)
    CentralDeAplicativos {}

    // Pilha de Downloads e menu do botão direito (camada por cima da área de trabalho; clique fora fecha)
    Window {
        screen: janela.screen
        width: Screen.width; height: Screen.height      // o compositor ajusta à área livre
        visible: ilha.downloadsVisivel || ilha.menu.tipo !== undefined
        color: "transparent"
        title: "Downloads"
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                   | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        LayerShell.Window.scope: "duiaos-pilha-de-downloads"
        ConteudoDownloads { anchors.fill: parent; visible: ilha.downloadsVisivel }
        MenuDaIlha { anchors.fill: parent; visible: ilha.menu.tipo !== undefined }
    }
}
