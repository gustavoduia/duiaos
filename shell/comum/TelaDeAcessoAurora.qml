// DuiaOS — Telas de Entrada e de Bloqueio no estilo futurista "Aurora" (ADR 052).
// Carregado por TelaDeAcesso.qml, que guarda o estado ("tela") e desenha o fundo.
//
// O papel de parede escurece num véu azul-noite; o relógio fica grande e leve no canto de baixo;
// no centro, a pessoa: a foto dentro de uma órbita (o símbolo do DuiaOS) e a senha numa cápsula de
// vidro com o botão de entrar dentro dela. Tudo sem efeitos de placa de vídeo (funciona em
// qualquer computador).
import QtQuick
import "estilo.js" as Estilo

Item {
    id: raiz
    property Item tela                    // TelaDeAcesso (estado, pessoas, sinais)

    readonly property color ciano: "#22D3EE"
    readonly property color azul: "#5B8CFF"
    readonly property color violeta: "#A78BFA"
    readonly property color textoClaro: "#F2F5FF"
    readonly property color textoSuave: Qt.rgba(0.86, 0.90, 1, 0.72)
    readonly property color vidro: Qt.rgba(1, 1, 1, 0.09)
    readonly property color bordaVidro: Qt.rgba(0.72, 0.80, 1, 0.30)
    readonly property color erro: "#FF7A93"
    property bool senhaVisivel: false
    // Com o tom azul mais transparente, o texto claro ganha um contorno escuro para não sumir num papel de parede claro
    readonly property color contorno: Qt.rgba(0.03, 0.05, 0.15, 0.6 * Math.max(0, Math.min(100, tela.transparenciaDoVeu)) / 100)

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

    // Degradê aurora reutilizado (anel, botão de entrar)
    component Aurora: Rectangle {
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: raiz.ciano }
            GradientStop { position: 0.5; color: raiz.azul }
            GradientStop { position: 1.0; color: raiz.violeta }
        }
    }

    // ------------------------------------------------------------ véu
    // O tom azul-noite por cima do papel de parede. A transparência (0 a 100%) e o brilho vêm das
    // Configurações › Papel de parede › Tela de Bloqueio / Tela de Entrada (ADR 056).
    Rectangle {
        anchors.fill: parent
        opacity: 1 - Math.max(0, Math.min(100, tela.transparenciaDoVeu)) / 100
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#080D26" }
            GradientStop { position: 0.55; color: "#0A0F30" }
            GradientStop { position: 1.0; color: "#05081A" }
        }
    }
    // Brilho perto da senha (e, se pedido, atrás do relógio das outras telas): radial ou linear
    readonly property bool comBrilho: tela.brilho !== "nenhum" && (!tela.somenteFundo || tela.brilhoNasOutrasTelas)
    Canvas {
        visible: raiz.comBrilho && tela.brilho === "radial"
        width: Math.min(parent.width, 900); height: width
        anchors { horizontalCenter: parent.horizontalCenter; verticalCenter: tela.somenteFundo ? parent.verticalCenter : centro.verticalCenter }
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            const g = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, width / 2)
            g.addColorStop(0, "rgba(91, 140, 255, 0.34)")
            g.addColorStop(0.45, "rgba(124, 92, 246, 0.14)")
            g.addColorStop(1, "rgba(10, 15, 31, 0)")
            ctx.fillStyle = g
            ctx.fillRect(0, 0, width, height)
        }
    }
    Rectangle {
        visible: raiz.comBrilho && tela.brilho === "linear"
        width: parent.width; height: Math.min(parent.height * 0.5, 460)
        anchors.verticalCenter: tela.somenteFundo ? parent.verticalCenter : centro.verticalCenter
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0.36, 0.55, 1, 0) }
            GradientStop { position: 0.5; color: Qt.rgba(0.40, 0.48, 1, 0.30) }
            GradientStop { position: 1.0; color: Qt.rgba(0.49, 0.36, 0.96, 0) }
        }
    }

    // ------------------------------------------------------------ relógio
    property date agora: new Date()
    readonly property var local: Qt.locale("pt_BR")
    Timer { interval: 1000; running: true; repeat: true; onTriggered: raiz.agora = new Date() }

    Column {
        id: relogio
        // Com a senha na tela, o relógio fica no canto de baixo; nos monitores extras, no centro
        anchors { left: tela.somenteFundo ? undefined : parent.left; bottom: tela.somenteFundo ? undefined : parent.bottom
                  leftMargin: 48; bottomMargin: 40; centerIn: tela.somenteFundo ? parent : undefined }
        spacing: -6
        Text {
            text: raiz.agora.toLocaleTimeString(raiz.local, "HH:mm")
            color: raiz.textoClaro
            style: Text.Outline; styleColor: raiz.contorno
            font { family: Estilo.fonteTitulo; pixelSize: Math.max(72, Math.round(raiz.height * 0.15)); weight: Font.ExtraLight; letterSpacing: -4 }
        }
        Text {
            leftPadding: 6
            text: { var t = raiz.agora.toLocaleDateString(raiz.local, "dddd, d 'de' MMMM"); return t.charAt(0).toUpperCase() + t.slice(1) }
            color: raiz.textoSuave
            style: Text.Outline; styleColor: raiz.contorno
            font { family: Estilo.fonteTexto; pixelSize: 19; weight: Font.Medium }
        }
    }

    // ------------------------------------------------------------ a pessoa e a senha
    Column {
        id: centro
        visible: !tela.somenteFundo
        width: 380
        anchors { horizontalCenter: parent.horizontalCenter; verticalCenter: parent.verticalCenter; verticalCenterOffset: -raiz.height * 0.04 }
        spacing: 0
        transform: Translate { id: deslocamento }
        SequentialAnimation {
            id: tremor
            NumberAnimation { target: deslocamento; property: "x"; to: -12; duration: 50 }
            NumberAnimation { target: deslocamento; property: "x"; to: 12; duration: 70 }
            NumberAnimation { target: deslocamento; property: "x"; to: -6; duration: 60 }
            NumberAnimation { target: deslocamento; property: "x"; to: 0; duration: 50 }
        }

        // Foto dentro da órbita: um anel aurora e um ponto que dá a volta devagar
        Item {
            id: orbita
            width: 148; height: 148
            anchors.horizontalCenter: parent.horizontalCenter
            Aurora { anchors.centerIn: parent; width: 128; height: 128; radius: 64; opacity: tela.ocupado ? 1 : 0.9 }
            Rectangle { anchors.centerIn: parent; width: 122; height: 122; radius: 61; color: "#0C1226" }
            Rectangle {
                id: foto
                anchors.centerIn: parent
                width: 112; height: 112; radius: 56
                clip: true
                gradient: Gradient { GradientStop { position: 0; color: "#3B4FB8" } GradientStop { position: 1; color: "#1A2460" } }
                Image {
                    id: fotoConta
                    anchors.fill: parent
                    source: tela.pessoa.foto || ""
                    sourceSize: Qt.size(224, 224)
                    visible: status === Image.Ready
                    smooth: true
                }
                Text {
                    visible: !fotoConta.visible
                    anchors.centerIn: parent
                    text: tela.pessoa.nome.length > 0 ? tela.pessoa.nome.charAt(0).toUpperCase() : "?"
                    color: "white"
                    font { family: Estilo.fonteTitulo; pixelSize: 46; weight: Font.Bold }
                }
            }
            // O ponto em órbita (mais rápido enquanto confere a senha)
            Item {
                anchors.fill: parent
                RotationAnimator on rotation { from: 0; to: 360; duration: tela.ocupado ? 1400 : 14000; loops: Animation.Infinite; running: raiz.visible }
                Rectangle { width: 12; height: 12; radius: 6; x: parent.width / 2 - 6; y: 0; color: raiz.ciano
                            Rectangle { anchors.centerIn: parent; width: 22; height: 22; radius: 11; color: raiz.ciano; opacity: 0.25 } }
            }
        }
        Item { width: 1; height: 18 }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            text: tela.pessoa.nome
            color: raiz.textoClaro
            style: Text.Outline; styleColor: raiz.contorno
            font { family: Estilo.fonteTitulo; pixelSize: 30; weight: Font.Bold; letterSpacing: -0.5 }
        }
        Item { width: 1; height: 6 }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: tela.ocupado ? "Conferindo a senha…" : (tela.emBloqueio ? "Sessão bloqueada" : "Digite a senha para entrar")
            color: raiz.textoSuave
            style: Text.Outline; styleColor: raiz.contorno
            font { family: Estilo.fonteTexto; pixelSize: 14 }
        }
        Item { width: 1; height: 26 }

        // Cápsula da senha: campo de vidro com "mostrar a senha" e o botão de entrar dentro
        Item {
            width: parent.width; height: 58
            // Anel de foco: a aurora acende em volta da cápsula
            Aurora {
                anchors { fill: parent; margins: -2 }
                radius: height / 2
                opacity: tela.mensagem !== "" ? 0 : (campoSenha.activeFocus ? 0.85 : 0)
                Behavior on opacity { NumberAnimation { duration: 180 } }
            }
            Rectangle {
                anchors { fill: parent; margins: -2 }
                radius: height / 2
                color: raiz.erro
                visible: tela.mensagem !== ""
            }
            Rectangle {
                id: capsula
                anchors.fill: parent
                radius: height / 2
                color: "#111836"
                Rectangle { anchors.fill: parent; radius: parent.radius; color: raiz.vidro; border { color: raiz.bordaVidro; width: 1 } }
                // Cadeado
                Canvas {
                    id: cadeado
                    width: 18; height: 20
                    anchors { left: parent.left; leftMargin: 22; verticalCenter: parent.verticalCenter }
                    onPaint: {
                        const ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "rgba(220, 230, 255, 0.75)"
                        ctx.lineWidth = 1.8
                        ctx.lineJoin = "round"
                        ctx.beginPath(); ctx.arc(9, 7.5, 4.5, Math.PI, 0, false); ctx.lineTo(13.5, 9.5); ctx.moveTo(4.5, 7.5); ctx.lineTo(4.5, 9.5); ctx.stroke()
                        ctx.beginPath(); ctx.rect(2.5, 9.5, 13, 9); ctx.stroke()
                    }
                }
                TextInput {
                    id: campoSenha
                    anchors { left: cadeado.right; leftMargin: 14; right: olho.left; rightMargin: 8; top: parent.top; bottom: parent.bottom }
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: raiz.senhaVisivel ? TextInput.Normal : TextInput.Password
                    passwordCharacter: "•"
                    enabled: !tela.ocupado
                    focus: !tela.somenteFundo
                    color: raiz.textoClaro
                    selectionColor: raiz.azul
                    font { family: Estilo.fonteTexto; pixelSize: 17; letterSpacing: raiz.senhaVisivel || text.length === 0 ? 0 : 3 }
                    clip: true
                    onAccepted: raiz.enviar()
                    onTextEdited: tela.mensagem = ""
                    Keys.onEscapePressed: {
                        if (menuEnergia.visible) menuEnergia.visible = false
                        else text = ""
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: campoSenha.text.length === 0
                        text: "Senha"
                        color: Qt.rgba(0.86, 0.90, 1, 0.5)
                        font { family: Estilo.fonteTexto; pixelSize: 16 }
                    }
                }
                // Mostrar ou esconder a senha
                Item {
                    id: olho
                    width: 34; height: 34
                    visible: campoSenha.text.length > 0
                    anchors { right: botaoEntrar.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
                    Rectangle { anchors.fill: parent; radius: 17; color: areaOlho.containsMouse ? Qt.rgba(1, 1, 1, 0.12) : "transparent" }
                    Canvas {
                        id: desenhoOlho
                        anchors.centerIn: parent
                        width: 20; height: 20
                        property bool aberto: raiz.senhaVisivel
                        onAbertoChanged: requestPaint()
                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = "rgba(220, 230, 255, 0.85)"
                            ctx.lineWidth = 1.7
                            ctx.lineCap = "round"
                            ctx.beginPath(); ctx.moveTo(2, 10); ctx.quadraticCurveTo(10, 1.5, 18, 10); ctx.quadraticCurveTo(10, 18.5, 2, 10); ctx.stroke()
                            ctx.beginPath(); ctx.arc(10, 10, 2.6, 0, 2 * Math.PI); ctx.stroke()
                            if (!aberto) { ctx.beginPath(); ctx.moveTo(4, 16.5); ctx.lineTo(16, 3.5); ctx.stroke() }
                        }
                    }
                    MouseArea { id: areaOlho; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: { raiz.senhaVisivel = !raiz.senhaVisivel; campoSenha.forceActiveFocus() } }
                    Accessible.role: Accessible.Button
                    Accessible.name: raiz.senhaVisivel ? "Esconder a senha" : "Mostrar a senha"
                }
                // Entrar
                Aurora {
                    id: botaoEntrar
                    width: 46; height: 46; radius: 23
                    anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                    opacity: campoSenha.text.length === 0 && !tela.ocupado ? 0.6 : 1
                    scale: areaEntrar.pressed ? 0.92 : (areaEntrar.containsMouse ? 1.06 : 1)
                    Behavior on scale { NumberAnimation { duration: 110 } }
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                    Canvas {
                        anchors.centerIn: parent
                        width: 20; height: 20
                        visible: !tela.ocupado
                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = "white"; ctx.lineWidth = 2.2; ctx.lineCap = "round"; ctx.lineJoin = "round"
                            ctx.beginPath(); ctx.moveTo(3, 10); ctx.lineTo(17, 10); ctx.moveTo(11, 4); ctx.lineTo(17, 10); ctx.lineTo(11, 16); ctx.stroke()
                        }
                    }
                    // Conferindo: um arco girando
                    Canvas {
                        anchors.centerIn: parent
                        width: 22; height: 22
                        visible: tela.ocupado
                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = "white"; ctx.lineWidth = 2.4; ctx.lineCap = "round"
                            ctx.beginPath(); ctx.arc(11, 11, 8, 0, Math.PI * 1.3); ctx.stroke()
                        }
                        RotationAnimator on rotation { from: 0; to: 360; duration: 800; loops: Animation.Infinite; running: tela.ocupado }
                    }
                    MouseArea { id: areaEntrar; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                enabled: !tela.ocupado; onClicked: raiz.enviar() }
                    Accessible.role: Accessible.Button
                    Accessible.name: tela.emBloqueio ? "Desbloquear" : "Entrar"
                }
            }
        }

        // Mensagem de erro
        Item {
            width: parent.width
            height: tela.mensagem !== "" ? textoErro.height + 14 : 0
            Behavior on height { NumberAnimation { duration: 140 } }
            clip: true
            Text {
                id: textoErro
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: tela.mensagem
                color: raiz.erro
                font { family: Estilo.fonteTexto; pixelSize: 13; weight: Font.Medium }
            }
        }
        Item { width: 1; height: 14 }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: "Enter para " + (tela.emBloqueio ? "desbloquear" : "entrar")
            color: Qt.rgba(0.86, 0.90, 1, 0.42)
            font { family: Estilo.fonteTexto; pixelSize: 12 }
        }
    }

    // ------------------------------------------- outras pessoas (só na entrada)
    Row {
        visible: !tela.somenteFundo && !tela.emBloqueio && tela.usuarios.length > 1
        anchors { horizontalCenter: parent.horizontalCenter; top: centro.bottom; topMargin: 34 }
        spacing: 12
        Repeater {
            model: tela.usuarios
            delegate: Rectangle {
                id: ficha
                required property var modelData
                required property int index
                readonly property bool atual: index === tela.usuarioAtual
                width: linhaFicha.width + 22
                height: 44
                radius: 22
                color: atual ? Qt.rgba(1, 1, 1, 0.16) : (areaFicha.containsMouse ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(1, 1, 1, 0.05))
                border { color: atual ? raiz.ciano : raiz.bordaVidro; width: 1 }
                Row {
                    id: linhaFicha
                    anchors.centerIn: parent
                    spacing: 9
                    Aurora {
                        width: 30; height: 30; radius: 15
                        anchors.verticalCenter: parent.verticalCenter
                        Text { anchors.centerIn: parent; text: ficha.modelData.nome.charAt(0).toUpperCase(); color: "white"
                               font { family: Estilo.fonteTitulo; pixelSize: 14; weight: Font.Bold } }
                    }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: ficha.modelData.nome; color: raiz.textoClaro
                           font { family: Estilo.fonteTexto; pixelSize: 14; weight: ficha.atual ? Font.DemiBold : Font.Normal } }
                }
                MouseArea {
                    id: areaFicha
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: { tela.usuarioAtual = ficha.index; tela.mensagem = ""; raiz.limparSenha() }
                }
            }
        }
    }

    // ------------------------------------------------------------ energia
    MouseArea {   // clique fora do menu fecha o menu
        anchors.fill: parent
        visible: menuEnergia.visible
        onClicked: menuEnergia.visible = false
    }
    Rectangle {
        id: botaoEnergia
        visible: !tela.somenteFundo && tela.opcoesEnergia.length > 0
        anchors { right: parent.right; bottom: parent.bottom; margins: 40 }
        width: 52; height: 52; radius: 26
        color: areaEnergia.containsMouse || menuEnergia.visible ? Qt.rgba(1, 1, 1, 0.18) : raiz.vidro
        border { color: raiz.bordaVidro; width: 1 }
        Canvas {
            anchors.centerIn: parent
            width: 20; height: 20
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = "#F2F5FF"; ctx.lineWidth = 2; ctx.lineCap = "round"
                ctx.beginPath(); ctx.arc(10, 11, 7.5, -Math.PI / 2 + 0.75, 3 * Math.PI / 2 - 0.75, false); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(10, 2); ctx.lineTo(10, 10); ctx.stroke()
            }
        }
        MouseArea { id: areaEnergia; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: menuEnergia.visible = !menuEnergia.visible }
        Accessible.role: Accessible.Button
        Accessible.name: "Energia"
    }
    MenuDeEnergia {
        id: menuEnergia
        visible: false
        mostrarDescricao: false
        width: 260
        opcoes: tela.opcoesEnergia
        anchors { right: botaoEnergia.right; bottom: botaoEnergia.top; bottomMargin: 12 }
        onEscolhido: (id) => { visible = false; tela.acaoEnergia(id) }
        onVisibleChanged: if (!visible && !tela.somenteFundo) campoSenha.forceActiveFocus()
    }

    // Entrada única: a tela clareia e a pessoa sobe um pouco
    opacity: 0
    Component.onCompleted: { opacity = 1; subida.start(); if (!tela.somenteFundo) campoSenha.forceActiveFocus() }
    Behavior on opacity { NumberAnimation { duration: 320 } }
    NumberAnimation { id: subida; target: deslocamento; property: "y"; from: 18; to: 0; duration: 420; easing.type: Easing.OutCubic }
}
