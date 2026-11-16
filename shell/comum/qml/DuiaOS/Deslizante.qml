// Controle deslizante (volume, brilho) com ícone dentro da trilha, no estilo do DuiaOS.
import QtQuick

Item {
    id: raiz
    property real valor: 50          // 0–100
    property string icone: ""
    property string iconeBaixo: icone
    property bool ativo: true
    signal movido(real valor)
    signal solto(real valor)         // ao largar o controle (para o que custa caro aplicar a cada passo)
    signal iconeClicado()
    height: 30
    opacity: ativo ? 1 : 0.45

    Rectangle {
        id: trilha
        anchors.fill: parent
        radius: height / 2
        color: Tema.controleDesligado
        border { color: Tema.borda; width: 1 }
        Rectangle {
            id: preenchido
            height: parent.height
            width: Math.max(parent.height, parent.width * Math.max(0, Math.min(100, raiz.valor)) / 100)
            radius: height / 2
            color: Tema.trilhaCheia
            border { color: Tema.bordaForte; width: Tema.futurista ? 0 : 1 }
            Aurora { anchors.fill: parent; radius: parent.radius; visible: Tema.futurista }
            Behavior on width { enabled: !area.pressed; NumberAnimation { duration: 90 } }
        }
    }
    Icone {
        anchors { left: parent.left; leftMargin: 7; verticalCenter: parent.verticalCenter }
        nome: raiz.valor < 35 ? raiz.iconeBaixo : raiz.icone
        tamanho: 16
        cor: Tema.futurista ? "white" : Tema.textoSecundario
        visible: raiz.icone !== ""
        MouseArea { anchors { fill: parent; margins: -6 } onClicked: raiz.iconeClicado(); z: 2 }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        anchors.leftMargin: raiz.icone !== "" ? 28 : 0
        enabled: raiz.ativo
        cursorShape: Qt.PointingHandCursor
        function mover(mouse) {
            var x = mouse.x + anchors.leftMargin
            raiz.movido(Math.round(Math.max(0, Math.min(1, x / raiz.width)) * 100))
        }
        onPressed: (mouse) => mover(mouse)
        onPositionChanged: (mouse) => { if (pressed) mover(mouse) }
        onReleased: raiz.solto(raiz.valor)
        onWheel: (roda) => raiz.movido(Math.max(0, Math.min(100, raiz.valor + (roda.angleDelta.y > 0 ? 5 : -5))))
    }
}
