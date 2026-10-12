// DuiaOS — Barra de Recursos.
// Mostra o símbolo do DuiaOS, data e hora, Wi-Fi, volume e bateria.
// Um clique no símbolo abre o Menu de Energia.
// A posição (topo, base, esquerda ou direita) vem de configuracao.posicao.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

Window {
    id: barra

    // Cores e fontes da identidade visual (branding/README.md)
    readonly property color corFundo: "#F7F9FC"
    readonly property color corBorda: "#DDE3EC"
    readonly property color corTexto: "#1F2933"
    readonly property color corTextoSecundario: "#5B6675"
    readonly property color corAzulNoite: "#1A3A73"
    readonly property color corAzulDuia: "#2E6BE6"
    readonly property color corAviso: "#E8A33D"
    readonly property string fonte: "Inter"

    // Posição e tamanho
    readonly property string posicao: configuracao.posicao
    readonly property bool horizontal: posicao === "topo" || posicao === "base"
    readonly property int espessura: horizontal ? 36 : 72

    width: horizontal ? Screen.width : espessura
    height: horizontal ? espessura : Screen.height
    visible: true
    color: corFundo
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
    LayerShell.Window.exclusionZone: espessura
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-barra-de-recursos"

    // Data e hora, atualizadas a cada segundo
    property date agora: new Date()
    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: barra.agora = new Date()
    }
    readonly property var local: Qt.locale("pt_BR")

    // Linha fina no lado voltado para a área de trabalho
    Rectangle {
        color: barra.corBorda
        width: barra.horizontal ? parent.width : 1
        height: barra.horizontal ? 1 : parent.height
        x: barra.posicao === "esquerda" ? parent.width - 1 : 0
        y: barra.posicao === "topo" ? parent.height - 1 : 0
    }

    // Símbolo do DuiaOS: o "D" aberto e o ponto em órbita
    component Simbolo: Canvas {
        width: 22; height: 22
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            ctx.scale(width / 104, height / 104)
            ctx.translate(-12, -8)
            ctx.lineWidth = 14
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.strokeStyle = barra.corAzulNoite
            ctx.beginPath()
            ctx.moveTo(58, 100)
            ctx.lineTo(28, 100)
            ctx.lineTo(28, 20)
            ctx.lineTo(58, 20)
            ctx.arc(58, 60, 40, -Math.PI / 2, 20 * Math.PI / 180, false)
            ctx.stroke()
            ctx.fillStyle = barra.corAzulDuia
            ctx.beginPath()
            ctx.arc(80.94, 92.77, 8, 0, 2 * Math.PI)
            ctx.fill()
        }
    }

    // Área clicável sobre o símbolo: abre o Menu de Energia
    component BotaoEnergia: MouseArea {
        anchors { fill: parent; margins: -6 }
        cursorShape: Qt.PointingHandCursor
        onClicked: sistema.abrirMenuDeEnergia()
    }

    component Rotulo: Text {
        font { family: barra.fonte; pixelSize: 13 }
        color: barra.corTexto
        horizontalAlignment: Text.AlignHCenter
    }

    // ---------- Barra horizontal (topo ou base) ----------
    Item {
        anchors.fill: parent
        visible: barra.horizontal

        Simbolo {
            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
            BotaoEnergia {}
        }
        Rotulo {
            anchors.centerIn: parent
            font { pixelSize: 14; weight: Font.DemiBold }
            text: barra.agora.toLocaleDateString(barra.local, "ddd, d 'de' MMM") + "   " + barra.agora.toLocaleTimeString(barra.local, "HH:mm")
        }
        Row {
            anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
            spacing: 20
            Rotulo {
                color: sistema.wifi !== "" ? barra.corTexto : barra.corTextoSecundario
                text: sistema.wifi !== "" ? "Wi-Fi  " + sistema.wifi : "Sem rede"
            }
            Rotulo {
                visible: sistema.volume >= 0
                color: sistema.mudo ? barra.corTextoSecundario : barra.corTexto
                text: sistema.mudo ? "Som  mudo" : "Som  " + sistema.volume + "%"
            }
            Rotulo {
                visible: sistema.bateria >= 0
                color: (!sistema.carregando && sistema.bateria <= 15) ? barra.corAviso : barra.corTexto
                text: (sistema.carregando ? "Carregando  " : "Bateria  ") + sistema.bateria + "%"
            }
        }
    }

    // ---------- Barra vertical (esquerda ou direita) ----------
    Item {
        anchors.fill: parent
        visible: !barra.horizontal

        Simbolo {
            anchors { top: parent.top; topMargin: 14; horizontalCenter: parent.horizontalCenter }
            BotaoEnergia {}
        }
        Column {
            anchors { top: parent.top; topMargin: 52; horizontalCenter: parent.horizontalCenter }
            spacing: 2
            Rotulo {
                anchors.horizontalCenter: parent.horizontalCenter
                font { pixelSize: 16; weight: Font.DemiBold }
                text: barra.agora.toLocaleTimeString(barra.local, "HH:mm")
            }
            Rotulo {
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 11
                color: barra.corTextoSecundario
                text: barra.agora.toLocaleDateString(barra.local, "ddd") + "\n" + barra.agora.toLocaleDateString(barra.local, "d MMM")
            }
        }
        Column {
            anchors { bottom: parent.bottom; bottomMargin: 16; horizontalCenter: parent.horizontalCenter }
            spacing: 12
            Rotulo {
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 11
                color: sistema.wifi !== "" ? barra.corTexto : barra.corTextoSecundario
                text: sistema.wifi !== "" ? "Wi-Fi" : "Sem\nrede"
            }
            Rotulo {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: sistema.volume >= 0
                font.pixelSize: 11
                color: sistema.mudo ? barra.corTextoSecundario : barra.corTexto
                text: "Som\n" + (sistema.mudo ? "mudo" : sistema.volume + "%")
            }
            Rotulo {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: sistema.bateria >= 0
                font.pixelSize: 11
                color: (!sistema.carregando && sistema.bateria <= 15) ? barra.corAviso : barra.corTexto
                text: (sistema.carregando ? "Carr.\n" : "Bat.\n") + sistema.bateria + "%"
            }
        }
    }
}
