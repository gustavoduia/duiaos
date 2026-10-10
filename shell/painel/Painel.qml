// DuiaOS — painel superior.
// À esquerda o símbolo, no centro data e hora, à direita Wi-Fi, volume e bateria.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

Window {
    id: painel

    // Cores e fontes da identidade visual (branding/README.md)
    readonly property color corFundo: "#F7F9FC"
    readonly property color corBorda: "#DDE3EC"
    readonly property color corTexto: "#1F2933"
    readonly property color corTextoSecundario: "#5B6675"
    readonly property color corAzulNoite: "#1A3A73"
    readonly property color corAzulDuia: "#2E6BE6"
    readonly property color corAviso: "#E8A33D"
    readonly property string fonte: "Inter"

    width: Screen.width
    height: 36
    visible: true
    color: corFundo
    title: "Painel do DuiaOS"

    // Preso ao topo da tela, ocupando a largura toda; as janelas não o cobrem.
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: height
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-painel"

    // Linha fina na borda de baixo
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color: painel.corBorda
    }

    // Símbolo do DuiaOS: o "D" aberto e o ponto em órbita
    Canvas {
        id: simbolo
        width: 22; height: 22
        anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            ctx.scale(width / 104, height / 104)
            ctx.translate(-12, -8)
            ctx.lineWidth = 14
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.strokeStyle = painel.corAzulNoite
            ctx.beginPath()
            ctx.moveTo(58, 100)
            ctx.lineTo(28, 100)
            ctx.lineTo(28, 20)
            ctx.lineTo(58, 20)
            ctx.arc(58, 60, 40, -Math.PI / 2, 20 * Math.PI / 180, false)
            ctx.stroke()
            ctx.fillStyle = painel.corAzulDuia
            ctx.beginPath()
            ctx.arc(80.94, 92.77, 8, 0, 2 * Math.PI)
            ctx.fill()
        }
    }

    // Data e hora no centro
    Text {
        id: relogio
        anchors.centerIn: parent
        font { family: painel.fonte; pixelSize: 14; weight: Font.DemiBold }
        color: painel.corTexto

        function atualizar() {
            const agora = new Date()
            const local = Qt.locale("pt_BR")
            text = agora.toLocaleDateString(local, "ddd, d 'de' MMM") + "   " + agora.toLocaleTimeString(local, "HH:mm")
        }
        Component.onCompleted: atualizar()
    }
    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: relogio.atualizar()
    }

    // Indicadores à direita
    Row {
        anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
        spacing: 20

        Text {
            font { family: painel.fonte; pixelSize: 13 }
            color: sistema.wifi !== "" ? painel.corTexto : painel.corTextoSecundario
            text: sistema.wifi !== "" ? "Wi-Fi  " + sistema.wifi : "Sem rede"
        }
        Text {
            visible: sistema.volume >= 0
            font { family: painel.fonte; pixelSize: 13 }
            color: sistema.mudo ? painel.corTextoSecundario : painel.corTexto
            text: sistema.mudo ? "Som  mudo" : "Som  " + sistema.volume + "%"
        }
        Text {
            visible: sistema.bateria >= 0
            font { family: painel.fonte; pixelSize: 13 }
            color: (!sistema.carregando && sistema.bateria <= 15) ? painel.corAviso : painel.corTexto
            text: (sistema.carregando ? "Carregando  " : "Bateria  ") + sistema.bateria + "%"
        }
    }
}
