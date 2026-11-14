// Aviso curto que aparece e some (ex.: "Conectado a Casa").
import QtQuick

Rectangle {
    id: raiz
    property string texto: ""
    function mostrar(mensagem) { texto = mensagem; opacity = 1; tempo.restart() }
    width: textoAviso.implicitWidth + 32
    height: 32
    radius: 16
    color: Tema.azulProfundo
    opacity: 0
    visible: opacity > 0
    Behavior on opacity { NumberAnimation { duration: 180 } }
    Text { id: textoAviso; anchors.centerIn: parent; text: raiz.texto; color: "white"; font { family: Tema.fonteTexto; pixelSize: 13 } }
    Timer { id: tempo; interval: 3500; onTriggered: raiz.opacity = 0 }
}
