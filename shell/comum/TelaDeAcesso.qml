// DuiaOS — visual único da Tela de Entrada e da Tela de Bloqueio.
//
// É a mesma tela nos dois momentos; muda só o texto que descreve o que
// está acontecendo:
//   modo "entrada"  — iniciar uma sessão (depois de ligar ou de encerrar a sessão)
//   modo "bloqueio" — desbloquear uma sessão aberta, porém bloqueada
import QtQuick
import "estilo.js" as Estilo

Item {
    id: tela

    property string modo: "entrada"
    readonly property bool emBloqueio: modo === "bloqueio"
    property var usuarios: []            // [{usuario, nome}]
    property int usuarioAtual: 0
    property bool ocupado: false         // verificando a senha
    property string mensagem: ""         // erro ou aviso da autenticação
    property var opcoesEnergia: []       // [{id, titulo, descricao}]
    property string versao: "DuiaOS"
    property string papelDeParede: ""
    property bool somenteFundo: false    // monitores extras: só o fundo e o relógio

    signal entrar(string usuario, string senha)
    signal acaoEnergia(string id)

    readonly property var pessoa: usuarios.length > 0
        ? usuarios[Math.min(usuarioAtual, usuarios.length - 1)]
        : ({ usuario: "", nome: "" })

    function limparSenha() {
        campoSenha.text = ""
        campoSenha.forceActiveFocus()
    }
    function avisarErro() {
        limparSenha()
        tremor.restart()
    }
    function enviar() {
        if (tela.ocupado || tela.pessoa.usuario === "")
            return
        menuEnergia.visible = false
        tela.entrar(tela.pessoa.usuario, campoSenha.text)
    }

    // ------------------------------------------------------------ fundo
    Rectangle { anchors.fill: parent; color: Estilo.fundo }
    Image {
        anchors.fill: parent
        source: tela.papelDeParede
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        smooth: true
    }
    // Véu claro: suaviza o papel de parede e destaca o cartão
    Rectangle { anchors.fill: parent; color: Estilo.fundo; opacity: 0.35 }

    // ------------------------------------------------------------ relógio
    property date agora: new Date()
    readonly property var local: Qt.locale("pt_BR")
    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: tela.agora = new Date()
    }

    Column {
        id: relogio
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top
                  topMargin: Math.round(tela.height * (tela.somenteFundo ? 0.30 : 0.10)) }
        spacing: 0
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: tela.agora.toLocaleTimeString(tela.local, "HH:mm")
            font { family: Estilo.fonteTitulo; pixelSize: Math.max(64, Math.round(tela.height * 0.10)); weight: Font.Bold }
            font.letterSpacing: -2
            color: Estilo.azulNoite
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: tela.agora.toLocaleDateString(tela.local, "dddd, d 'de' MMMM")
            font { family: Estilo.fonteTexto; pixelSize: 20 }
            color: Estilo.textoSecundario
        }
    }

    // ------------------------------------------------------------ cartão
    Rectangle {
        id: cartao
        visible: !tela.somenteFundo
        width: 380
        height: conteudo.height + 56
        anchors { horizontalCenter: parent.horizontalCenter; top: relogio.bottom
                  topMargin: Math.max(32, Math.round(tela.height * 0.06)) }
        radius: 24
        color: Estilo.cartao
        border { color: Estilo.borda; width: 1 }
        transform: Translate { id: deslocamento }

        SequentialAnimation {
            id: tremor
            NumberAnimation { target: deslocamento; property: "x"; to: -10; duration: 50 }
            NumberAnimation { target: deslocamento; property: "x"; to: 10; duration: 70 }
            NumberAnimation { target: deslocamento; property: "x"; to: -6; duration: 60 }
            NumberAnimation { target: deslocamento; property: "x"; to: 0; duration: 50 }
        }

        Column {
            id: conteudo
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 28 }
            spacing: 0

            // Avatar com a inicial do nome
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 84; height: 84; radius: 42
                color: Estilo.azulDuia
                Text {
                    anchors.centerIn: parent
                    text: tela.pessoa.nome.length > 0 ? tela.pessoa.nome.charAt(0).toUpperCase() : "?"
                    font { family: Estilo.fonteTitulo; pixelSize: 36; weight: Font.Bold }
                    color: "white"
                }
            }
            Item { width: 1; height: 14 }
            Text {
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                text: tela.pessoa.nome
                font { family: Estilo.fonteTitulo; pixelSize: 22; weight: Font.Bold }
                color: Estilo.texto
            }
            Item { width: 1; height: 4 }
            Text {
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: tela.emBloqueio
                      ? "Sessão bloqueada. Digite a senha para desbloquear."
                      : "Digite a senha para iniciar a sessão."
                font { family: Estilo.fonteTexto; pixelSize: 14 }
                color: Estilo.textoSecundario
            }
            Item { width: 1; height: 22 }

            // Campo de senha
            Rectangle {
                width: parent.width
                height: 48
                radius: 12
                color: Estilo.fundo
                border {
                    width: campoSenha.activeFocus ? 2 : 1
                    color: tela.mensagem !== "" ? Estilo.erro
                         : campoSenha.activeFocus ? Estilo.azulDuia : Estilo.borda
                }
                TextInput {
                    id: campoSenha
                    anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    passwordCharacter: "•"
                    enabled: !tela.ocupado
                    focus: !tela.somenteFundo
                    font { family: Estilo.fonteTexto; pixelSize: 16 }
                    color: Estilo.texto
                    selectionColor: Estilo.destaque
                    clip: true
                    onAccepted: tela.enviar()
                    onTextEdited: tela.mensagem = ""
                    Keys.onEscapePressed: {
                        if (menuEnergia.visible) menuEnergia.visible = false
                        else text = ""
                    }
                }
                Text {
                    anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                    visible: campoSenha.text.length === 0
                    text: "Senha"
                    font { family: Estilo.fonteTexto; pixelSize: 16 }
                    color: Estilo.textoSecundario
                }
            }

            // Mensagem de erro
            Item {
                width: parent.width
                height: tela.mensagem !== "" ? textoErro.height + 10 : 0
                Behavior on height { NumberAnimation { duration: 120 } }
                clip: true
                Text {
                    id: textoErro
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                    wrapMode: Text.WordWrap
                    text: tela.mensagem
                    font { family: Estilo.fonteTexto; pixelSize: 13 }
                    color: Estilo.erro
                }
            }
            Item { width: 1; height: 14 }

            // Botão principal
            Rectangle {
                id: botaoEntrar
                width: parent.width
                height: 48
                radius: 12
                opacity: tela.ocupado ? 0.7 : 1
                color: areaEntrar.pressed ? Estilo.azulNoite
                     : areaEntrar.containsMouse ? "#255BC7" : Estilo.azulDuia
                Text {
                    anchors.centerIn: parent
                    text: tela.ocupado ? "Verificando…" : (tela.emBloqueio ? "Desbloquear" : "Entrar")
                    font { family: Estilo.fonteTexto; pixelSize: 16; weight: Font.DemiBold }
                    color: "white"
                }
                MouseArea {
                    id: areaEntrar
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    enabled: !tela.ocupado
                    onClicked: tela.enviar()
                }
            }
        }
    }

    // ------------------------------------------- outras pessoas (só na entrada)
    Row {
        visible: !tela.somenteFundo && !tela.emBloqueio && tela.usuarios.length > 1
        anchors { horizontalCenter: parent.horizontalCenter; top: cartao.bottom; topMargin: 24 }
        spacing: 10
        Repeater {
            model: tela.usuarios
            delegate: Rectangle {
                id: ficha
                required property var modelData
                required property int index
                readonly property bool atual: index === tela.usuarioAtual
                width: linhaFicha.width + 24
                height: 40
                radius: 20
                color: atual ? Estilo.cartao : (areaFicha.containsMouse ? Estilo.destaque : "transparent")
                border { color: atual ? Estilo.azulDuia : Estilo.borda; width: 1 }
                Row {
                    id: linhaFicha
                    anchors.centerIn: parent
                    spacing: 8
                    Rectangle {
                        width: 26; height: 26; radius: 13
                        color: Estilo.azulDuia
                        anchors.verticalCenter: parent.verticalCenter
                        Text {
                            anchors.centerIn: parent
                            text: ficha.modelData.nome.charAt(0).toUpperCase()
                            font { family: Estilo.fonteTitulo; pixelSize: 13; weight: Font.Bold }
                            color: "white"
                        }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: ficha.modelData.nome
                        font { family: Estilo.fonteTexto; pixelSize: 14 }
                        color: Estilo.texto
                    }
                }
                MouseArea {
                    id: areaFicha
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        tela.usuarioAtual = ficha.index
                        tela.mensagem = ""
                        tela.limparSenha()
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------ rodapé
    Row {
        anchors { left: parent.left; bottom: parent.bottom; margins: 28 }
        spacing: 10
        Simbolo { width: 24; height: 24; anchors.verticalCenter: parent.verticalCenter }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: tela.versao
            font { family: Estilo.fonteTexto; pixelSize: 13 }
            color: Estilo.textoSecundario
        }
    }

    // Botão Energia e o menu que ele abre
    MouseArea {   // clique fora do menu fecha o menu
        anchors.fill: parent
        visible: menuEnergia.visible
        onClicked: menuEnergia.visible = false
    }
    Rectangle {
        id: botaoEnergia
        visible: !tela.somenteFundo && tela.opcoesEnergia.length > 0
        anchors { right: parent.right; bottom: parent.bottom; margins: 24 }
        width: linhaEnergia.width + 28
        height: 44
        radius: 22
        color: areaEnergia.containsMouse || menuEnergia.visible ? Estilo.cartao : Qt.rgba(1, 1, 1, 0.7)
        border { color: Estilo.borda; width: 1 }
        Row {
            id: linhaEnergia
            anchors.centerIn: parent
            spacing: 8
            // Ícone de energia: arco com um traço no alto
            Canvas {
                width: 18; height: 18
                anchors.verticalCenter: parent.verticalCenter
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.reset()
                    ctx.strokeStyle = Estilo.azulNoite
                    ctx.lineWidth = 2
                    ctx.lineCap = "round"
                    ctx.beginPath()
                    ctx.arc(9, 10, 7, -Math.PI / 2 + 0.75, 3 * Math.PI / 2 - 0.75, false)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.moveTo(9, 1.5)
                    ctx.lineTo(9, 9)
                    ctx.stroke()
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "Energia"
                font { family: Estilo.fonteTexto; pixelSize: 14; weight: Font.Medium }
                color: Estilo.texto
            }
        }
        MouseArea {
            id: areaEnergia
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: menuEnergia.visible = !menuEnergia.visible
        }
    }
    MenuDeEnergia {
        id: menuEnergia
        visible: false
        mostrarDescricao: false
        width: 260
        opcoes: tela.opcoesEnergia
        anchors { right: botaoEnergia.right; bottom: botaoEnergia.top; bottomMargin: 10 }
        onEscolhido: (id) => { visible = false; tela.acaoEnergia(id) }
        onVisibleChanged: if (!visible && !tela.somenteFundo) campoSenha.forceActiveFocus()
    }

    // Aparece suavemente
    opacity: 0
    Component.onCompleted: { opacity = 1; if (!somenteFundo) campoSenha.forceActiveFocus() }
    Behavior on opacity { NumberAnimation { duration: 250 } }
}
