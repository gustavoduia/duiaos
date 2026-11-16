// Botão de texto: "primario" (azul; no estilo futurista, cápsula com o degradê aurora e um halo),
// "secundario" (contorno) ou "perigo".
import QtQuick

Item {
    id: raiz
    property string texto: ""
    property string icone: ""
    property string tipo: "secundario"
    property bool ativo: true
    signal clicado()
    implicitWidth: linha.implicitWidth + (Tema.futurista ? 34 : 28)
    implicitHeight: 34
    opacity: ativo ? 1 : 0.5
    readonly property real raioBotao: Math.min(height / 2, Tema.raioControle)
    readonly property color corBase: tipo === "primario" ? Tema.azulDuia : (tipo === "perigo" ? Tema.erro : Tema.cartao)
    readonly property bool cheio: tipo !== "secundario"

    // Halo (futurista): a luz do botão principal vaza um pouco para fora
    Aurora {
        visible: Tema.futurista && raiz.tipo === "primario" && raiz.ativo
        anchors { fill: parent; margins: area.containsMouse ? -4 : -2 }
        radius: raiz.raioBotao + 4
        opacity: area.containsMouse ? 0.30 : 0.16
        Behavior on opacity { NumberAnimation { duration: Tema.animacao } }
    }
    Rectangle {
        id: fundo
        anchors.fill: parent
        radius: raiz.raioBotao
        color: area.pressed ? Qt.darker(raiz.corBase, 1.12) : (area.containsMouse ? Qt.darker(raiz.corBase, 1.04) : raiz.corBase)
        border { width: raiz.tipo === "secundario" ? 1 : 0; color: area.containsMouse && Tema.futurista ? Tema.azulDuia : Tema.bordaForte }
        Aurora {
            visible: Tema.futurista && raiz.tipo === "primario"
            anchors.fill: parent
            radius: parent.radius
            opacity: area.pressed ? 0.82 : 1
        }
        // Reflexo fino no alto (futurista)
        Rectangle {
            visible: Tema.futurista && raiz.cheio
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 1 }
            height: parent.height / 2; radius: parent.radius
            gradient: Gradient { GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 0.22) } GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0) } }
        }
    }
    Row {
        id: linha
        anchors.centerIn: parent
        spacing: 6
        Icone {
            visible: raiz.icone !== ""
            nome: raiz.icone; tamanho: 16
            cor: raiz.cheio ? "white" : Tema.texto
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: raiz.texto
            anchors.verticalCenter: parent.verticalCenter
            color: raiz.cheio ? "white" : Tema.texto
            font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
        }
    }
    scale: area.pressed && Tema.futurista ? 0.97 : 1
    Behavior on scale { NumberAnimation { duration: 90 } }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.clicado()
    }
    Accessible.role: Accessible.Button
    Accessible.name: texto
}
