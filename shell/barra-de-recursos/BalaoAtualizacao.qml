// DuiaOS — balão do ícone de atualizações (ao lado do relógio, ADR 058). Aparece sozinho quando chega um
// conjunto novo de atualizações e a cada clique no ícone; dois cliques no ícone (ou "Ver resumo") abrem
// Configurações › Atualizações já com o resumo. Fecha sozinho depois de alguns segundos sem o mouse por cima.
import QtQuick
import DuiaOS

Item {
    id: balao
    property string titulo: ""
    property string texto: ""
    property real ponta: width - 30              // onde fica a ponta (o ícone), ao longo da largura
    property bool pontaEmCima: true               // barra no topo: a ponta aponta para cima
    signal verResumo()
    signal fechar()

    width: 340
    height: cartao.height + 10

    // Ponta do balão, apontando para o ícone
    Rectangle {
        width: 14; height: 14
        rotation: 45
        x: Math.max(16, Math.min(balao.width - 30, balao.ponta - 7))
        y: balao.pontaEmCima ? 3 : balao.height - 17
        color: Tema.vidro
        border { color: Tema.futurista ? Tema.brilho : Tema.borda; width: 1 }
    }

    Cartao {
        id: cartao
        width: parent.width
        height: conteudo.implicitHeight + 32
        y: balao.pontaEmCima ? 10 : 0

        HoverHandler { id: sobre }
        Timer {
            // Some sozinho; enquanto o mouse está por cima, espera
            interval: 12000
            running: balao.visible && !sobre.hovered
            onTriggered: balao.fechar()
        }

        Column {
            id: conteudo
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
            spacing: 10

            Row {
                width: parent.width
                spacing: 12
                Rectangle {
                    width: 36; height: 36; radius: 10
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: Tema.aurora1 }
                        GradientStop { position: 1; color: Tema.aurora3 }
                    }
                    Icone { anchors.centerIn: parent; nome: "atualizacao"; tamanho: 18; cor: "#FFFFFF" }
                }
                Column {
                    width: parent.width - 36 - 12 - 24
                    spacing: 3
                    Text {
                        width: parent.width
                        text: balao.titulo
                        color: Tema.texto
                        elide: Text.ElideRight
                        font { family: Tema.fonteTitulo; pixelSize: 15; weight: Font.Bold }
                    }
                    Text {
                        width: parent.width
                        text: balao.texto
                        color: Tema.textoSecundario
                        wrapMode: Text.WordWrap
                        lineHeight: 1.15
                        font { family: Tema.fonteTexto; pixelSize: 13 }
                    }
                }
                // Fechar
                Rectangle {
                    width: 24; height: 24; radius: 12
                    color: areaFechar.containsMouse ? Tema.realce : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: "Fechar"
                    Icone { anchors.centerIn: parent; nome: "fechar"; tamanho: 12; cor: Tema.textoSecundario }
                    MouseArea { id: areaFechar; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: balao.fechar() }
                }
            }

            Item {
                width: parent.width
                height: botao.height
                Text {
                    anchors { left: parent.left; right: botao.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                    text: "Ou clique duas vezes no ícone."
                    color: Tema.textoSecundario
                    elide: Text.ElideRight
                    font { family: Tema.fonteTexto; pixelSize: 12 }
                }
                Botao {
                    id: botao
                    anchors.right: parent.right
                    texto: "Ver resumo"
                    tipo: "primario"
                    onClicado: balao.verResumo()
                }
            }
        }
    }
}
