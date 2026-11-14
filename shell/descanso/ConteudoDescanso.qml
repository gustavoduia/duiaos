// DuiaOS — o que a Tela de Descanso mostra: o fundo escolhido e, se pedido, o relógio.
// Qualquer tecla ou movimento do mouse (depois de um instante) fecha.
import QtQuick
import DuiaOS

Item {
    id: raiz
    property bool fechavel: false
    signal sair()
    focus: true
    Keys.onPressed: raiz.sair()
    Timer { interval: 1200; running: true; onTriggered: raiz.fechavel = true }

    Fundo { anchors.fill: parent; arquivo: arquivoDescanso; corFundo: corDescanso }
    Rectangle {
        anchors.fill: parent
        visible: mostrarRelogio
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.35) }
            GradientStop { position: 0.45; color: "transparent" }
        }
    }
    property date agora: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: raiz.agora = new Date() }
    Column {
        visible: mostrarRelogio
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: parent.height * 0.12 }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: { var t = raiz.agora.toLocaleDateString(Qt.locale("pt_BR"), "dddd, d 'de' MMMM"); return t.charAt(0).toUpperCase() + t.slice(1) }
            color: "white"; font { family: Tema.fonteTexto; pixelSize: 22; weight: Font.DemiBold }
            style: Text.Raised; styleColor: Qt.rgba(0, 0, 0, 0.3)
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: raiz.agora.toLocaleTimeString(Qt.locale("pt_BR"), "HH:mm")
            color: "white"; font { family: Tema.fonteTitulo; pixelSize: 120; weight: Font.Bold }
            style: Text.Raised; styleColor: Qt.rgba(0, 0, 0, 0.3)
        }
    }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.BlankCursor
        property point inicio: Qt.point(-1, -1)
        onPositionChanged: (m) => {
            if (inicio.x < 0) { inicio = Qt.point(m.x, m.y); return }
            if (raiz.fechavel && (Math.abs(m.x - inicio.x) > 8 || Math.abs(m.y - inicio.y) > 8)) raiz.sair()
        }
        onPressed: raiz.sair()
    }
}
