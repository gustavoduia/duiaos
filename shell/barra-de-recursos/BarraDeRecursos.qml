// DuiaOS — Barra de Recursos: janela presa à borda da tela (layer-shell) com o
// conteúdo de Barra.qml, e a camada do Painel (menu, balões, Central de Controle),
// que cobre a área de trabalho só enquanto algo está aberto.
// A posição (topo, base, esquerda ou direita) vem de configuracao.posicao.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: janela
    // Fica na tela principal (a do notebook, quando houver; comum/telas.js)
    screen: Telas.principal(Qt.application.screens)
    readonly property string posicao: configuracao.posicao
    readonly property bool horizontal: posicao === "topo" || posicao === "base"

    width: horizontal ? Screen.width : barra.espessura
    height: horizontal ? barra.espessura : Screen.height
    visible: true
    color: "transparent"
    title: "Barra de Recursos"

    LayerShell.Window.anchors: {
        if (posicao === "base")
            return LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        if (posicao === "esquerda")
            return LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
        if (posicao === "direita")
            return LayerShell.Window.AnchorRight | LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
        return LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    }
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: barra.espessura
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-barra-de-recursos"

    Barra { id: barra; anchors.fill: parent }

    // Camada do Painel: respeita a área da barra (exclusionZone 0), então a barra
    // continua clicável e outro ícone troca o balão aberto.
    Window {
        id: camada
        screen: janela.screen
        width: Screen.width; height: Screen.height      // o compositor ajusta à área livre
        visible: sistema.painel !== "" || sistema.confirmacao !== ""
        color: "transparent"
        title: "Painel da Barra de Recursos"
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                   | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        LayerShell.Window.scope: "duiaos-painel-da-barra"
        onVisibleChanged: if (visible) conteudo.forceActiveFocus()

        ConteudoPainel {
            id: conteudo
            anchors.fill: parent
            ocultos: barra.ocultos
            // A âncora vem em coordenadas da tela; a camada começa depois da barra
            deslocamento: janela.posicao === "topo" || janela.posicao === "esquerda" ? barra.espessura : 0
        }
    }
}
