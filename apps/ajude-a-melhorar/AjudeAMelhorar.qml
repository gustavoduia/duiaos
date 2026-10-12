// DuiaOS — "Ajude a melhorar o DuiaOS": a pessoa escolhe o que o computador envia (ADR 040).
// Nenhuma opção vem marcada: nada é enviado até a pessoa escolher. Dados: ajude.nivel, ajude.situacaoJson;
// ação: ajude.escolher(nivel).
import QtQuick
import QtQuick.Window
import QtQuick.Controls

ApplicationWindow {
    id: janela
    width: 640
    height: 680
    minimumWidth: 420
    minimumHeight: 560
    visible: true
    title: "Ajude a melhorar o DuiaOS"
    color: cores.fundo

    QtObject {
        id: cores
        readonly property color fundo: "#F7F9FC"
        readonly property color cartao: "#FFFFFF"
        readonly property color destaque: "#E8F0FE"
        readonly property color azul: "#2E6BE6"
        readonly property color azulEscuro: "#255BC7"
        readonly property color noite: "#1A3A73"
        readonly property color texto: "#1F2933"
        readonly property color secundario: "#5B6675"
        readonly property color borda: "#DDE3EC"
        readonly property color sucesso: "#2FA67A"
        readonly property color erro: "#D9534F"
        readonly property color erroFundo: "#FBECEB"
    }
    readonly property string fonteTitulo: "Manrope"
    readonly property string fonte: "Inter"

    // Escolha feita na tela (ainda não gravada). Vazia = nada marcado.
    property string selecionado: ["desligado", "erros", "erros_e_uso"].indexOf(ajude.nivel) >= 0 ? ajude.nivel : ""
    property string mensagemErro: ""
    property bool gravado: false
    readonly property bool desenvolvimento: ajude.nivel === "desenvolvimento"
    readonly property bool mudou: selecionado !== "" && selecionado !== ajude.nivel

    readonly property var opcoes: [
        { id: "erros_e_uso", titulo: "Enviar erros e uso",
          texto: "Falhas, erros e informações do computador, mais contagens de uso: quais aplicativos e recursos são usados e quantas vezes. Nunca o conteúdo." },
        { id: "erros", titulo: "Enviar só erros",
          texto: "Falhas de programas, erros do sistema e as informações do computador (processador, memória, placa de vídeo, versões)." },
        { id: "desligado", titulo: "Não enviar nada",
          texto: "Os registros continuam só neste computador, para você e para o suporte." }
    ]

    Connections {
        target: ajude
        function onTerminou(ok, mensagem) {
            janela.mensagemErro = ok ? "" : mensagem
            janela.gravado = ok
            if (ok && ajude.primeiraEntrada) fechar.start()
        }
    }
    Timer { id: fechar; interval: 1200; onTriggered: Qt.quit() }

    component Rotulo: Text {
        color: cores.texto
        font { family: janela.fonte; pixelSize: 14 }
        wrapMode: Text.WordWrap
        lineHeight: 1.25
    }

    component Botao: Rectangle {
        id: botao
        property alias texto: rotuloBotao.text
        property bool principal: false
        property bool ativo: true
        signal clicado()
        implicitHeight: 40
        implicitWidth: rotuloBotao.implicitWidth + 36
        radius: 10
        opacity: ativo ? 1 : 0.45
        color: principal ? (areaBotao.containsMouse && ativo ? cores.azulEscuro : cores.azul)
                         : (areaBotao.containsMouse && ativo ? cores.destaque : cores.cartao)
        border.color: principal ? "transparent" : cores.borda
        Accessible.role: Accessible.Button
        Accessible.name: texto
        Accessible.onPressAction: if (ativo) clicado()
        Text {
            id: rotuloBotao
            anchors.centerIn: parent
            color: botao.principal ? "#FFFFFF" : cores.noite
            font { family: janela.fonte; pixelSize: 14; weight: Font.DemiBold }
        }
        MouseArea {
            id: areaBotao
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: botao.ativo ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (botao.ativo) botao.clicado()
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        Column {
            width: Math.min(parent.width - 48, 560)
            x: (parent.width - width) / 2
            topPadding: 32
            bottomPadding: 32
            spacing: 18

            Row {
                spacing: 14
                Image {
                    source: "file:///usr/share/icons/hicolor/scalable/apps/duiaos-ajude-a-melhorar.svg"
                    width: 48; height: 48
                    sourceSize: Qt.size(96, 96)
                    visible: status === Image.Ready
                }
                Column {
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        text: "Ajude a melhorar o DuiaOS"
                        color: cores.noite
                        font { family: janela.fonteTitulo; pixelSize: 24; weight: Font.Bold }
                        Accessible.role: Accessible.Heading
                    }
                    Text {
                        text: "Você escolhe o que este computador envia."
                        color: cores.secundario
                        font { family: janela.fonte; pixelSize: 14 }
                    }
                }
            }

            Rotulo {
                width: parent.width
                text: "Quando um programa falha, o DuiaOS anota o que aconteceu no registro do sistema. Se você "
                      + "permitir, esses relatórios vão para quem desenvolve o DuiaOS, e as falhas são corrigidas "
                      + "nas próximas atualizações. Senhas, arquivos, o que você escreve e as conversas com o Wise "
                      + "nunca são enviados; seu nome e o do computador são apagados antes."
            }

            // Computador de teste: mudar só pelo terminal
            Rectangle {
                visible: janela.desenvolvimento
                width: parent.width
                height: textoTeste.implicitHeight + 24
                radius: 12
                color: cores.destaque
                Rotulo {
                    id: textoTeste
                    anchors { fill: parent; margins: 12 }
                    text: "Este é um computador de teste do DuiaOS: ele envia os registros completos "
                          + "(nível desenvolvimento). Ao escolher uma opção abaixo, ele passa a enviar só o que "
                          + "ela diz."
                }
            }

            Column {
                width: parent.width
                spacing: 10
                Accessible.role: Accessible.RadioButton
                Repeater {
                    model: janela.opcoes
                    delegate: Rectangle {
                        id: cartao
                        required property var modelData
                        readonly property bool marcado: janela.selecionado === modelData.id
                        width: parent.width
                        height: conteudoCartao.implicitHeight + 28
                        radius: 14
                        color: marcado ? cores.destaque : cores.cartao
                        border.color: marcado ? cores.azul : (areaCartao.containsMouse ? "#B8C7E0" : cores.borda)
                        border.width: marcado ? 2 : 1
                        Accessible.role: Accessible.RadioButton
                        Accessible.name: modelData.titulo
                        Accessible.description: modelData.texto
                        Accessible.checkable: true
                        Accessible.checked: marcado
                        Accessible.onPressAction: janela.selecionado = modelData.id

                        Row {
                            id: conteudoCartao
                            x: 16; y: 14
                            width: parent.width - 32
                            spacing: 14
                            Rectangle {
                                width: 20; height: 20; radius: 10
                                y: 2
                                color: "transparent"
                                border.color: cartao.marcado ? cores.azul : "#9AA6B6"
                                border.width: 2
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 10; height: 10; radius: 5
                                    color: cores.azul
                                    visible: cartao.marcado
                                }
                            }
                            Column {
                                width: parent.width - 34
                                spacing: 4
                                Text {
                                    text: cartao.modelData.titulo
                                    color: cores.texto
                                    font { family: janela.fonte; pixelSize: 15; weight: Font.DemiBold }
                                }
                                Rotulo {
                                    width: parent.width
                                    text: cartao.modelData.texto
                                    color: cores.secundario
                                    font.pixelSize: 13
                                }
                            }
                        }
                        MouseArea {
                            id: areaCartao
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: { janela.selecionado = cartao.modelData.id; janela.gravado = false }
                        }
                    }
                }
            }

            Rotulo {
                width: parent.width
                visible: !ajude.administrador
                color: cores.secundario
                font.pixelSize: 13
                text: "Para mudar esta escolha, é preciso a senha de quem administra este computador."
            }

            Rectangle {
                visible: janela.mensagemErro !== ""
                width: parent.width
                height: textoErro.implicitHeight + 20
                radius: 10
                color: cores.erroFundo
                Rotulo { id: textoErro; anchors { fill: parent; margins: 10 } color: cores.erro; text: janela.mensagemErro }
            }

            Rotulo {
                width: parent.width
                visible: janela.gravado
                color: cores.sucesso
                font.weight: Font.DemiBold
                text: ajude.nivel === "desligado" ? "Pronto: nada será enviado." : "Pronto. Obrigado por ajudar!"
            }

            Item {
                width: parent.width
                height: 44
                Text {
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    text: "O que é enviado?"
                    color: cores.azul
                    font { family: janela.fonte; pixelSize: 14; underline: areaLink.containsMouse }
                    Accessible.role: Accessible.Link
                    Accessible.name: text
                    Accessible.onPressAction: ajude.abrirDocumentacao()
                    MouseArea {
                        id: areaLink
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: ajude.abrirDocumentacao()
                    }
                }
                Row {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    spacing: 10
                    Botao {
                        texto: ajude.primeiraEntrada && ajude.nivel === "nao_escolhido" ? "Perguntar depois" : "Fechar"
                        onClicado: Qt.quit()
                    }
                    Botao {
                        texto: ajude.ocupado ? "Gravando…" : "Confirmar"
                        principal: true
                        ativo: janela.mudou && !ajude.ocupado
                        onClicado: ajude.escolher(janela.selecionado)
                    }
                }
            }
        }
    }
}
