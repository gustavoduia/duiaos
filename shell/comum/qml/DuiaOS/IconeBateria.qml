// Bateria desenhada: contorno, nível e raio quando carrega.
import QtQuick

Item {
    id: raiz
    property int nivel: 100
    property bool carregando: false
    property color cor: Tema.texto
    width: 25; height: 12
    Rectangle {
        id: corpo
        width: parent.width - 3; height: parent.height
        radius: 3.5
        color: "transparent"
        border { color: raiz.cor; width: 1.3 }
        opacity: 0.9
        Rectangle {
            x: 2; y: 2
            height: parent.height - 4
            width: Math.max(1.5, (parent.width - 4) * Math.max(0, Math.min(100, raiz.nivel)) / 100)
            radius: 1.6
            color: raiz.carregando ? Tema.sucesso : (raiz.nivel <= 15 ? Tema.erro : raiz.cor)
        }
    }
    Rectangle { x: corpo.width + 0.5; width: 2; height: 4.5; radius: 1; y: (parent.height - height) / 2; color: raiz.cor; opacity: 0.6 }
    Text {
        visible: raiz.carregando
        anchors.centerIn: corpo
        text: "⚡"
        font.pixelSize: 9
        color: "white"
        style: Text.Outline; styleColor: Tema.texto
    }
}
