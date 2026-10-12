// DuiaOS — lista de opções de energia (Bloquear, Encerrar sessão, Suspender,
// Reiniciar, Reiniciar no Windows, Desligar). Usada na Tela de Entrada, na
// Tela de Bloqueio e no Menu de Energia da sessão.
import QtQuick
import "estilo.js" as Estilo

Rectangle {
    id: menu

    property var opcoes: []        // [{id, titulo, descricao}]
    property bool mostrarDescricao: true
    signal escolhido(string id)

    width: 320
    height: coluna.height + 16
    radius: 18
    color: Estilo.cartao
    border { color: Estilo.borda; width: 1 }

    Column {
        id: coluna
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
        spacing: 2

        Repeater {
            model: menu.opcoes
            delegate: Rectangle {
                id: linha
                required property var modelData
                width: coluna.width
                height: menu.mostrarDescricao ? 58 : 44
                radius: 12
                color: area.containsMouse || linha.activeFocus ? Estilo.destaque : "transparent"
                activeFocusOnTab: true
                Keys.onReturnPressed: menu.escolhido(modelData.id)
                Keys.onEnterPressed: menu.escolhido(modelData.id)
                Keys.onSpacePressed: menu.escolhido(modelData.id)

                Column {
                    anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14
                              verticalCenter: parent.verticalCenter }
                    spacing: 2
                    Text {
                        text: linha.modelData.titulo
                        font { family: Estilo.fonteTexto; pixelSize: 15; weight: Font.DemiBold }
                        color: linha.modelData.id === "desligar" ? Estilo.azulNoite : Estilo.texto
                    }
                    Text {
                        visible: menu.mostrarDescricao
                        width: parent.width
                        elide: Text.ElideRight
                        text: linha.modelData.descricao
                        font { family: Estilo.fonteTexto; pixelSize: 12 }
                        color: Estilo.textoSecundario
                    }
                }
                MouseArea {
                    id: area
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: menu.escolhido(linha.modelData.id)
                }
            }
        }
    }
}
