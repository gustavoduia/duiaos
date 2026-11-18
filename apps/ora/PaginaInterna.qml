// DuiaOS — Ora: moldura das páginas internas (histórico, favoritos, downloads, configurações):
// título com ícone, ações à direita e o conteúdo rolável, centralizado.
import QtQuick
import DuiaOS

Rectangle {
    id: raiz
    property var janelaOra
    property string titulo: ""
    property string icone: ""
    property alias acoes: linhaAcoes.data
    default property alias conteudo: coluna.data
    property real larguraMaxima: 880
    color: Tema.fundo

    Flickable {
        id: rolagem
        anchors.fill: parent
        contentHeight: coluna.implicitHeight + cabecalho.height + 64
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Item {
            id: cabecalho
            width: Math.min(rolagem.width - 64, raiz.larguraMaxima)
            x: (rolagem.width - width) / 2
            y: 32
            height: 48
            Icone { id: iconeTitulo; anchors { left: parent.left; verticalCenter: parent.verticalCenter } nome: raiz.icone; tamanho: 26; cor: Tema.azulDuia }
            Text {
                anchors { left: iconeTitulo.right; leftMargin: 12; verticalCenter: parent.verticalCenter }
                text: raiz.titulo
                color: Tema.azulNoite
                font { family: Tema.fonteTitulo; pixelSize: 26; weight: Font.Bold }
            }
            Row { id: linhaAcoes; anchors { right: parent.right; verticalCenter: parent.verticalCenter } spacing: 8 }
        }
        Column {
            id: coluna
            width: cabecalho.width
            x: cabecalho.x
            y: cabecalho.y + cabecalho.height + 20
            spacing: 14
        }
    }
}
