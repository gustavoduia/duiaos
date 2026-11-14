// Botão só com ícone (barra de ferramentas, Barra de Recursos).
import QtQuick

Rectangle {
    id: raiz
    property string icone: ""
    property color corIcone: Tema.texto
    property int tamanhoIcone: 18
    property bool marcado: false
    property bool ativo: true
    property string dica: ""
    signal clicado()
    width: 30; height: 30
    radius: 8
    opacity: ativo ? 1 : 0.35
    color: marcado ? Tema.destaque : (area.pressed ? Qt.rgba(0.06, 0.09, 0.14, 0.12)
           : (area.containsMouse ? Qt.rgba(0.06, 0.09, 0.14, 0.06) : "transparent"))
    Icone { anchors.centerIn: parent; nome: raiz.icone; cor: raiz.marcado ? Tema.azulDuia : raiz.corIcone; tamanho: raiz.tamanhoIcone }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        onClicked: raiz.clicado()
    }
    Accessible.role: Accessible.Button
    Accessible.name: dica
}
