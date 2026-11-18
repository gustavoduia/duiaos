// DuiaOS — Mail Box: wizard para adicionar uma conta.
// 1. Escolher o provedor (ou só digitar o e-mail) e a senha; quando o provedor pede senha de app, o passo a
//    passo e o link da página certa aparecem ali. 2. O Mail Box descobre os servidores (catálogo, MX, ISPDB,
//    autoconfig, SRV). 3. Testa a entrada e o envio. 4. Pronto. Sem descoberta, a configuração manual.
import QtQuick
import DuiaOS

Rectangle {
    id: wizard
    property bool podeCancelar: false
    signal concluido()
    signal cancelado()
    color: Tema.fundo

    property string estado: "inicio"          // inicio | procurando | manual | testando | pronto
    property string provedorEscolhido: ""
    property var config: ({})
    property string erro: ""
    property string origem: ""
    readonly property var provedorDetectado: campoEmail.texto.indexOf("@") > 0 ? caixa.provedorDe(campoEmail.texto.trim()) : ({})
    readonly property var guia: provedorEscolhido !== "" ? caixa.configuracaoDoProvedor(provedorEscolhido, campoEmail.texto.trim() || "voce@exemplo.com")
                                                          : provedorDetectado
    readonly property bool precisaOauth: guia && guia.autenticacao === "oauth"
    readonly property bool emailValido: /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(campoEmail.texto.trim())

    function reiniciar() { estado = "inicio"; erro = ""; provedorEscolhido = ""; campoSenha.texto = "" }
    onVisibleChanged: if (visible) reiniciar()

    function continuar() {
        erro = ""
        if (!emailValido) { erro = "Digite um endereço de e-mail completo."; return }
        if (campoSenha.texto === "") { erro = "Digite a senha."; return }
        if (provedorEscolhido !== "") { config = caixa.configuracaoDoProvedor(provedorEscolhido, campoEmail.texto.trim()); testar(); return }
        estado = "procurando"
        caixa.descobrir(campoEmail.texto.trim())
    }
    function testar() {
        estado = "testando"
        caixa.testarConta(campoEmail.texto.trim(), campoSenha.texto, config)
    }
    function abrirManual() {
        var email = campoEmail.texto.trim()
        var dominio = email.split("@")[1] || "exemplo.com"
        if (!config.entrada) config = { provedor: "", nome_provedor: dominio, autenticacao: "senha", salva_enviados: false, pastas: {},
                                        verificar_certificado: true,
                                        entrada: { tipo: "imap", host: "imap." + dominio, porta: 993, seguranca: "ssl", usuario: email },
                                        saida: { tipo: "smtp", host: "smtp." + dominio, porta: 465, seguranca: "ssl", usuario: email } }
        manEntradaTipo.valor = config.entrada.tipo
        manEntradaHost.texto = config.entrada.host; manEntradaPorta.texto = String(config.entrada.porta)
        manEntradaSeg.valor = config.entrada.seguranca; manUsuario.texto = config.entrada.usuario
        manSaidaHost.texto = config.saida.host; manSaidaPorta.texto = String(config.saida.porta); manSaidaSeg.valor = config.saida.seguranca
        estado = "manual"
    }
    function testarManual() {
        var c = JSON.parse(JSON.stringify(config))
        c.entrada = { tipo: manEntradaTipo.valor, host: manEntradaHost.texto.trim(), porta: parseInt(manEntradaPorta.texto) || 993,
                      seguranca: manEntradaSeg.valor, usuario: manUsuario.texto.trim() }
        c.saida = { tipo: "smtp", host: manSaidaHost.texto.trim(), porta: parseInt(manSaidaPorta.texto) || 465,
                    seguranca: manSaidaSeg.valor, usuario: manUsuario.texto.trim() }
        config = c
        testar()
    }

    Connections {
        target: caixa
        function onDescoberto(c, origemDescoberta) {
            if (wizard.estado !== "procurando") return
            if (!c || !c.entrada) { wizard.config = {}; wizard.erro = "Não encontramos as configurações deste provedor. Preencha os servidores."; wizard.abrirManual(); return }
            wizard.config = c
            wizard.origem = origemDescoberta
            if (c.autenticacao === "oauth") { wizard.estado = "inicio"; wizard.provedorEscolhido = c.provedor; return }
            wizard.testar()
        }
        function onTesteConcluido(ok, texto) {
            if (wizard.estado !== "testando") return
            if (ok) {
                caixa.salvarConta(campoNome.texto.trim(), campoEmail.texto.trim(), campoSenha.texto, wizard.config)
                wizard.estado = "pronto"
            } else {
                wizard.erro = texto
                wizard.estado = wizard.config.provedor ? "inicio" : "manual"
                if (wizard.estado === "manual") wizard.abrirManual()
            }
        }
    }

    // Fundo com o brilho aurora
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: parent.height * 0.5
        opacity: Tema.futurista ? 0.20 : 0.08
        gradient: Gradient { orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "transparent" } GradientStop { position: 0.35; color: Tema.aurora1 }
            GradientStop { position: 0.7; color: Tema.aurora3 } GradientStop { position: 1; color: "transparent" } }
    }
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: parent.height * 0.5
        gradient: Gradient { GradientStop { position: 0; color: Qt.rgba(Tema.fundo.r, Tema.fundo.g, Tema.fundo.b, 0) }
                             GradientStop { position: 1; color: Tema.fundo } }
    }
    MouseArea { anchors.fill: parent }       // nada passa para a janela de baixo

    BotaoIcone {
        visible: wizard.podeCancelar && wizard.estado !== "testando"
        anchors { right: parent.right; top: parent.top; margins: 16 }
        icone: "fechar"; dica: "Cancelar"
        onClicado: wizard.cancelado()
    }

    // componente: escolha entre opções em pílulas
    component Pilulas: Row {
        property var opcoes: []           // [[valor, rótulo]]
        property string valor: ""
        spacing: 6
        Repeater {
            model: parent.opcoes
            delegate: Rectangle {
                required property var modelData
                readonly property bool escolhida: parent.valor === modelData[0]
                width: rotulo.implicitWidth + 24; height: 32; radius: 16
                color: escolhida ? Tema.destaque : "transparent"
                border { width: 1; color: escolhida ? Tema.azulDuia : Tema.borda }
                Text { id: rotulo; anchors.centerIn: parent; text: modelData[1]; color: parent.escolhida ? Tema.azulDuia : Tema.texto
                       font { family: Tema.fonteTexto; pixelSize: 13; weight: parent.escolhida ? Font.DemiBold : Font.Normal } }
                MouseArea { anchors.fill: parent; onClicked: parent.parent.valor = modelData[0] }
            }
        }
    }

    Flickable {
        anchors.fill: parent
        contentHeight: Math.max(height, conteudo.implicitHeight + 120)
        clip: true
        Column {
            id: conteudo
            width: Math.min(parent.width - 64, 620)
            anchors.horizontalCenter: parent.horizontalCenter
            y: Math.max(48, (wizard.height - implicitHeight) * 0.35)
            spacing: 20

            // ------------------------------------------------ marca
            Column {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 64; height: 64; radius: 20
                    gradient: Gradient { orientation: Gradient.Vertical
                        GradientStop { position: 0; color: Tema.aurora1 } GradientStop { position: 1; color: Tema.aurora3 } }
                    Icone { anchors.centerIn: parent; nome: wizard.estado === "pronto" ? "check" : "pasta-downloads"; tamanho: 32; cor: "white" }
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: ({ inicio: "Adicionar uma conta de e-mail", procurando: "Procurando as configurações…",
                             manual: "Configuração dos servidores", testando: "Conectando à sua conta…", pronto: "Tudo pronto!" })[wizard.estado]
                    color: Tema.azulNoite
                    font { family: Tema.fonteTitulo; pixelSize: 26; weight: Font.Bold }
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(conteudo.width, 520)
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    color: Tema.textoSecundario
                    font { family: Tema.fonteTexto; pixelSize: 14 }
                    text: ({ inicio: "Escolha o seu provedor ou digite o endereço: o Mail Box descobre o resto.",
                             procurando: "Consultando o catálogo do DuiaOS e o seu provedor.",
                             manual: "Confira os dados que o seu provedor informa (normalmente na página de ajuda dele).",
                             testando: "Testando o recebimento e o envio de " + campoEmail.texto.trim() + ".",
                             pronto: "A conta " + campoEmail.texto.trim() + " foi adicionada. As mensagens já estão chegando." })[wizard.estado]
                }
            }

            // ------------------------------------------------ início
            Column {
                visible: wizard.estado === "inicio"
                width: parent.width
                spacing: 14
                Flow {
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: caixa.destaques().concat([{ id: "", nome: "Outro provedor" }])
                        delegate: Rectangle {
                            required property var modelData
                            readonly property bool escolhido: wizard.provedorEscolhido === modelData.id && (modelData.id !== "" || wizard.provedorEscolhido === "")
                            width: rotuloProvedor.implicitWidth + 30; height: 38; radius: 19
                            color: escolhido ? Tema.destaque : (areaProvedor.containsMouse ? Tema.realce : Tema.cartao)
                            border { width: 1; color: escolhido ? Tema.azulDuia : Tema.borda }
                            Text { id: rotuloProvedor; anchors.centerIn: parent; text: modelData.nome
                                   color: parent.escolhido ? Tema.azulDuia : Tema.texto
                                   font { family: Tema.fonteTexto; pixelSize: 13; weight: parent.escolhido ? Font.DemiBold : Font.Normal } }
                            MouseArea { id: areaProvedor; anchors.fill: parent; hoverEnabled: true
                                        onClicked: { wizard.provedorEscolhido = modelData.id; wizard.erro = "" } }
                        }
                    }
                }
                Campo { id: campoNome; width: parent.width; height: 40; icone: "usuario"; dica: "Seu nome (como as pessoas vão ver)" }
                Campo { id: campoEmail; width: parent.width; height: 40; icone: "globo"; dica: "Endereço de e-mail"
                        entrada.inputMethodHints: Qt.ImhEmailCharactersOnly | Qt.ImhNoAutoUppercase
                        onConfirmado: campoSenha.entrada.forceActiveFocus() }
                Campo { id: campoSenha; width: parent.width; height: 40; icone: "cadeado"; senha: true
                        visible: !wizard.precisaOauth
                        dica: wizard.guia && wizard.guia.autenticacao === "senha_de_app" ? "Senha de app" : "Senha"
                        onConfirmado: wizard.continuar() }

                // passo a passo do provedor
                Rectangle {
                    visible: wizard.guia && wizard.guia.ajuda !== undefined && wizard.guia.ajuda !== ""
                    width: parent.width
                    height: colunaAjuda.implicitHeight + 28
                    radius: Tema.raio
                    color: wizard.precisaOauth ? Qt.rgba(0.91, 0.64, 0.24, 0.12) : Tema.destaque
                    Column {
                        id: colunaAjuda
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
                        spacing: 8
                        Row {
                            spacing: 8
                            Icone { nome: wizard.precisaOauth ? "info" : "cadeado"; tamanho: 16; cor: wizard.precisaOauth ? Tema.aviso : Tema.azulDuia }
                            Text { text: wizard.guia ? wizard.guia.nome_provedor || "" : ""; color: Tema.texto
                                   font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                        }
                        Text { width: parent.width; wrapMode: Text.WordWrap; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 }
                               text: wizard.guia ? (wizard.guia.ajuda || "") : "" }
                        Text { visible: wizard.precisaOauth; width: parent.width; wrapMode: Text.WordWrap; color: Tema.textoSecundario
                               font { family: Tema.fonteTexto; pixelSize: 12 }
                               text: "O login da Microsoft no Mail Box chega numa próxima atualização, quando o registro do aplicativo na Microsoft estiver pronto." }
                        Text { visible: wizard.guia && wizard.guia.link_ajuda !== undefined && wizard.guia.link_ajuda !== "" && !wizard.precisaOauth
                               text: "Abrir a página do provedor"; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
                               MouseArea { anchors.fill: parent; anchors.margins: -4; cursorShape: Qt.PointingHandCursor; onClicked: caixa.abrirAjuda(wizard.guia.link_ajuda) } }
                    }
                }
                Text { visible: wizard.erro !== ""; width: parent.width; wrapMode: Text.WordWrap; text: wizard.erro
                       color: Tema.erro; font { family: Tema.fonteTexto; pixelSize: 13 } }
                Item {
                    width: parent.width; height: 40
                    Text {
                        anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                        text: "Configurar manualmente"
                        color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 13 }
                        MouseArea { anchors.fill: parent; anchors.margins: -4; cursorShape: Qt.PointingHandCursor
                                    onClicked: { if (!wizard.emailValido) { wizard.erro = "Digite o endereço de e-mail primeiro."; return }
                                                 wizard.config = {}; wizard.abrirManual() } }
                    }
                    Botao { anchors { right: parent.right; verticalCenter: parent.verticalCenter } height: 40
                            texto: "Continuar"; tipo: "primario"; ativo: !wizard.precisaOauth; onClicado: wizard.continuar() }
                }
            }

            // ------------------------------------------------ manual
            Cartao {
                visible: wizard.estado === "manual"
                width: parent.width
                height: colunaManual.implicitHeight + 40
                Column {
                    id: colunaManual
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                    spacing: 10
                    Text { text: "Recebimento"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                    Pilulas { id: manEntradaTipo; opcoes: [["imap", "IMAP (recomendado)"], ["pop3", "POP3"]]; valor: "imap"
                              onValorChanged: if (manEntradaPorta.texto === "993" || manEntradaPorta.texto === "995") manEntradaPorta.texto = valor === "imap" ? "993" : "995" }
                    Row {
                        width: parent.width; spacing: 8
                        Campo { id: manEntradaHost; width: parent.width - 108; dica: "Servidor (ex.: imap.exemplo.com)" }
                        Campo { id: manEntradaPorta; width: 100; dica: "Porta" }
                    }
                    Pilulas { id: manEntradaSeg; opcoes: [["ssl", "SSL/TLS"], ["starttls", "STARTTLS"], ["nenhuma", "Sem criptografia"]]; valor: "ssl" }
                    Campo { id: manUsuario; width: parent.width; dica: "Usuário (normalmente o próprio e-mail)" }
                    Separador { width: parent.width }
                    Text { text: "Envio (SMTP)"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                    Row {
                        width: parent.width; spacing: 8
                        Campo { id: manSaidaHost; width: parent.width - 108; dica: "Servidor (ex.: smtp.exemplo.com)" }
                        Campo { id: manSaidaPorta; width: 100; dica: "Porta" }
                    }
                    Pilulas { id: manSaidaSeg; opcoes: [["ssl", "SSL/TLS (465)"], ["starttls", "STARTTLS (587)"], ["nenhuma", "Sem criptografia"]]; valor: "ssl" }
                    Text { visible: wizard.erro !== ""; width: parent.width; wrapMode: Text.WordWrap; text: wizard.erro
                           color: Tema.erro; font { family: Tema.fonteTexto; pixelSize: 13 } }
                    Item {
                        width: parent.width; height: 40
                        Botao { anchors { left: parent.left; verticalCenter: parent.verticalCenter } texto: "Voltar"; onClicado: { wizard.erro = ""; wizard.estado = "inicio" } }
                        Botao { anchors { right: parent.right; verticalCenter: parent.verticalCenter } height: 40
                                texto: "Testar e continuar"; tipo: "primario"; onClicado: wizard.testarManual() }
                    }
                }
            }

            // ------------------------------------------------ esperando
            Item {
                visible: wizard.estado === "procurando" || wizard.estado === "testando"
                width: parent.width; height: 80
                Rectangle {
                    anchors.centerIn: parent
                    width: 40; height: 40; radius: 20
                    color: "transparent"
                    border { width: 3; color: Tema.azulDuia }
                    Rectangle { width: 12; height: 12; radius: 6; color: Tema.fundo; x: 24; y: -2 }
                    RotationAnimation on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: parent.visible }
                }
            }
            Text {
                visible: wizard.estado === "testando" && wizard.config.entrada !== undefined
                anchors.horizontalCenter: parent.horizontalCenter
                text: wizard.config.entrada ? wizard.config.entrada.host + " · " + wizard.config.saida.host : ""
                color: Tema.textoApagado; font { family: Tema.fonteCodigo; pixelSize: 12 }
            }

            // ------------------------------------------------ pronto
            Botao {
                visible: wizard.estado === "pronto"
                anchors.horizontalCenter: parent.horizontalCenter
                height: 42
                texto: "Abrir a Caixa de Entrada"; tipo: "primario"
                onClicado: wizard.concluido()
            }
        }
    }
}
