// DuiaOS — balões de notificação, um embaixo do outro (o mais novo em cima). Identidade própria
// (ADR 058), partindo da Órbita do DuiaOS:
//   - uma faixa de luz à esquerda, no degradê aurora (vermelha quando é urgente);
//   - cabeçalho fino: ícone pequeno, nome do aplicativo e hora — com o mouse em cima, a hora dá
//     lugar ao botão de fechar;
//   - embaixo, a linha do tempo: mostra quanto falta para o balão sumir e para com o mouse em cima;
//   - as ações ocupam o rodapé inteiro, divididas em partes iguais;
//   - o balão desce da Barra de Recursos ao chegar.
import QtQuick
import DuiaOS

Column {
    id: baloes
    width: 360
    spacing: 8
    move: Transition { NumberAnimation { properties: "y"; duration: Tema.animacao; easing.type: Easing.OutCubic } }

    Repeater {
        model: notificacoes.visiveis
        delegate: Item {
            id: balao
            required property var modelData
            readonly property bool urgente: modelData.urgencia >= 2
            readonly property int duracao: modelData.duracao || 0          // 0 = fica até a pessoa fechar
            width: baloes.width
            height: cartao.height

            // Chegada: desce um pouco e aparece
            opacity: 0
            transform: Translate { id: desce; y: -14 }
            Component.onCompleted: chegada.start()
            ParallelAnimation {
                id: chegada
                NumberAnimation { target: balao; property: "opacity"; to: 1; duration: 200; easing.type: Easing.OutCubic }
                NumberAnimation { target: desce; property: "y"; to: 0; duration: 260; easing.type: Easing.OutBack; easing.overshoot: 1.2 }
            }

            HoverHandler {
                id: sobre
                onHoveredChanged: notificacoes.pausar(balao.modelData.id, hovered)
            }

            Rectangle {
                id: cartao
                width: parent.width
                height: corpo.implicitHeight
                radius: Tema.futurista ? 18 : 14
                color: Tema.vidro
                border { color: Tema.futurista ? Tema.brilho : Tema.borda; width: 1 }
                clip: true

                // Sombra curta embaixo (sem efeitos de placa de vídeo)
                Rectangle {
                    z: -1
                    anchors { fill: parent; topMargin: 4; bottomMargin: -4; leftMargin: 2; rightMargin: 2 }
                    radius: parent.radius
                    color: Tema.sombra
                    opacity: 0.6
                }

                // Faixa de luz à esquerda, ao lado do cabeçalho e do texto (não do rodapé das ações)
                Rectangle {
                    x: 6; y: 12
                    height: textos.y + textos.height - 24
                    width: 3; radius: 1.5
                    gradient: Gradient {
                        GradientStop { position: 0; color: balao.urgente ? Tema.erro : Tema.aurora1 }
                        GradientStop { position: 0.5; color: balao.urgente ? Tema.erro : Tema.aurora2 }
                        GradientStop { position: 1; color: balao.urgente ? Qt.darker(Tema.erro, 1.2) : Tema.aurora3 }
                    }
                }

                MouseArea {
                    id: area
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: notificacoes.clicar(balao.modelData.id)
                }

                Column {
                    id: corpo
                    width: parent.width

                    // Cabeçalho: ícone pequeno, aplicativo e hora (ou o fechar, com o mouse em cima)
                    Item {
                        width: parent.width
                        height: 34
                        Item {
                            id: icone
                            x: 18; anchors.verticalCenter: parent.verticalCenter
                            width: 20; height: 20
                            Image {
                                id: img
                                anchors.fill: parent
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                                sourceSize: Qt.size(40, 40)
                                visible: status === Image.Ready
                                source: balao.modelData.tipoIcone === "arquivo" ? balao.modelData.valorIcone
                                        : (balao.modelData.tipoIcone === "tema" ? "image://icone/" + balao.modelData.valorIcone : "")
                            }
                            Ladrilho {
                                anchors.fill: parent
                                visible: !img.visible
                                tamanho: 20; radius: 6
                                icone: balao.modelData.app === "Wise" ? "ia" : (balao.modelData.app === "Atualizações" ? "atualizacao" : "sino")
                                estilo: "azul"
                            }
                        }
                        Text {
                            anchors { left: icone.right; leftMargin: 8; right: canto.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            text: balao.modelData.app
                            elide: Text.ElideRight
                            color: Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
                        }
                        Item {
                            id: canto
                            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                            width: Math.max(hora.implicitWidth, 24); height: 24
                            Text {
                                id: hora
                                anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                                visible: !sobre.hovered
                                text: balao.modelData.quando
                                color: Tema.textoApagado
                                font { family: Tema.fonteTexto; pixelSize: 11 }
                            }
                            BotaoIcone {
                                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                visible: sobre.hovered
                                width: 24; height: 24
                                icone: "fechar"; tamanhoIcone: 11; corIcone: Tema.textoSecundario
                                onClicado: notificacoes.fechar(balao.modelData.id)
                                Accessible.name: "Fechar notificação"
                            }
                        }
                    }

                    // Título e texto
                    Column {
                        id: textos
                        x: 18
                        width: parent.width - 36
                        spacing: 3
                        bottomPadding: balao.modelData.acoes.length > 0 ? 12 : 14
                        Text {
                            width: parent.width
                            text: balao.modelData.titulo
                            elide: Text.ElideRight
                            color: Tema.texto
                            font { family: Tema.fonteTitulo; pixelSize: 14; weight: Font.Bold }
                        }
                        Text {
                            width: parent.width
                            visible: balao.modelData.texto !== ""
                            text: balao.modelData.texto
                            textFormat: Text.StyledText
                            wrapMode: Text.WordWrap
                            maximumLineCount: 4
                            elide: Text.ElideRight
                            lineHeight: 1.15
                            color: Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 13 }
                        }
                    }

                    // Ações: o rodapé inteiro, em partes iguais
                    Item {
                        visible: balao.modelData.acoes.length > 0
                        width: parent.width
                        height: visible ? 38 : 0
                        Rectangle { width: parent.width; height: 1; color: Tema.borda }
                        Row {
                            anchors { fill: parent; topMargin: 1 }
                            Repeater {
                                model: balao.modelData.acoes
                                delegate: Rectangle {
                                    id: acao
                                    required property var modelData
                                    required property int index
                                    width: parent.width / balao.modelData.acoes.length
                                    height: parent.height
                                    color: toqueAcao.containsMouse ? Tema.realce : "transparent"
                                    Rectangle { visible: acao.index > 0; width: 1; height: parent.height; color: Tema.borda }
                                    Text {
                                        anchors.centerIn: parent
                                        width: parent.width - 16
                                        horizontalAlignment: Text.AlignHCenter
                                        elide: Text.ElideRight
                                        text: acao.modelData.rotulo
                                        color: acao.index === 0 ? Tema.azulDuia : Tema.texto
                                        font { family: Tema.fonteTexto; pixelSize: 13; weight: acao.index === 0 ? Font.DemiBold : Font.Normal }
                                    }
                                    MouseArea {
                                        id: toqueAcao
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: notificacoes.acionar(balao.modelData.id, acao.modelData.chave)
                                    }
                                    Accessible.role: Accessible.Button
                                    Accessible.name: acao.modelData.rotulo
                                }
                            }
                        }
                    }
                }

                // Linha do tempo: quanto falta para o balão sumir (para com o mouse em cima). Fica dentro
                // das curvas do cartão, embaixo do texto (ou em cima do rodapé das ações).
                Rectangle {
                    visible: balao.duracao > 0
                    x: 18
                    y: textos.y + textos.height - 5
                    height: 2; radius: 1
                    width: (parent.width - 36) * tempo.resta
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: Tema.aurora1 }
                        GradientStop { position: 1; color: Tema.aurora3 }
                    }
                    opacity: 0.7
                    QtObject { id: tempo; property real resta: 1 }
                    NumberAnimation {
                        target: tempo; property: "resta"; from: 1; to: 0
                        duration: Math.max(1, balao.duracao)
                        running: balao.duracao > 0
                        paused: running && sobre.hovered
                    }
                }
            }
            Accessible.role: Accessible.AlertMessage
            Accessible.name: modelData.app + ": " + modelData.titulo
        }
    }
}
