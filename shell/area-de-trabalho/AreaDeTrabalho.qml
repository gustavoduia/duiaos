// DuiaOS — Área de Trabalho: uma camada "background" do layer-shell em cada tela, por baixo de
// todas as janelas. Os ícones ficam só na tela principal (a do notebook, quando houver).
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Item {
    id: raizArea
    // Papel estendido por todas as telas: a área que elas ocupam juntas e onde cada uma começa
    function recorte(tela) {
        var telas = Qt.application.screens
        var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9
        for (var i = 0; i < telas.length; i++) {
            x0 = Math.min(x0, telas[i].virtualX); y0 = Math.min(y0, telas[i].virtualY)
            x1 = Math.max(x1, telas[i].virtualX + telas[i].width); y1 = Math.max(y1, telas[i].virtualY + telas[i].height)
        }
        return { largura: x1 - x0, altura: y1 - y0, dx: tela.virtualX - x0, dy: tela.virtualY - y0 }
    }
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            required property int index
            screen: modelData
            width: modelData.width; height: modelData.height
            visible: true
            color: "transparent"       // até o papel de parede carregar, aparece o fundo imediato (shell/sessao/fundo-imediato)
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
                nomeTela: modelData.name
                estendido: raizArea.recorte(modelData)
            }
        }
    }
}
