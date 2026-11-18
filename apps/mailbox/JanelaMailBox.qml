// DuiaOS — Mail Box: a janela principal.
// À esquerda, Escrever e as contas com as pastas; no meio, a lista de mensagens com a busca; à direita, a
// mensagem aberta (cabeçalho, ações, anexos e o conteúdo, sem JavaScript e com imagens externas bloqueadas).
// Sem contas, o wizard ocupa a janela.
import QtQuick
import QtQuick.Window
import QtWebEngine
import DuiaOS

Window {
    id: janela
    width: 1280; height: 820
    minimumWidth: 900; minimumHeight: 560
    visible: true
    color: Tema.fundo
    title: (caixa.nomePastaAtual ? caixa.nomePastaAtual + " — " : "") + "Mail Box"
    property bool adicionando: caixa.contasLista.length === 0 || (typeof paginaDemonstracao !== "undefined" && paginaDemonstracao === "wizard")
    property bool gerenciando: false
    readonly property var leitura: caixa.leitura
    readonly property bool temLeitura: leitura && leitura.id !== undefined

    Connections {
        target: caixa
        function onAviso(texto) { aviso.mostrar(texto) }
        function onAbrirEscrever(campos) { componenteEscrever.createObject(janela, { campos: campos }) }
    }
    Component { id: componenteEscrever; Escrever { } }

    // ============================================================ menus na Barra (ADR 059)
    readonly property var menusDoApp: {
        var it = function (id, rotulo, atalho, ativo) { return { id: id, rotulo: rotulo, tipo: "item", ativo: ativo !== false,
                                                                 marcado: false, atalho: atalho || "", itens: [] } }
        var sep = { id: -1, rotulo: "", tipo: "separador", ativo: false, marcado: false, atalho: "", itens: [] }
        var m = janela.temLeitura
        return [{ rotulo: "Mail Box", itens: [it("nova", "Nova mensagem", "Ctrl+N"), it("atualizar", "Receber e-mails", "F5"), sep,
                                              it("adicionar", "Adicionar conta"), it("contas", "Contas"), sep, it("sair", "Fechar", "Ctrl+Q")] },
                { rotulo: "Mensagem", itens: [it("responder", "Responder", "Ctrl+R", m), it("responder-todos", "Responder a todos", "Ctrl+Shift+R", m),
                                              it("encaminhar", "Encaminhar", "Ctrl+Shift+F", m), sep,
                                              it("lida", m && janela.leitura.lida ? "Marcar como não lida" : "Marcar como lida", "Ctrl+U", m),
                                              it("sinalizar", m && janela.leitura.sinalizada ? "Tirar a sinalização" : "Sinalizar", "", m), sep,
                                              it("arquivar", "Arquivar", "E", m), it("apagar", "Mover para a Lixeira", "Delete", m)] },
                { rotulo: "Editar", itens: [it("buscar", "Buscar nas mensagens", "Ctrl+F")] }]
    }
    onMenusDoAppChanged: menuDoApp.definirMenus(menusDoApp)
    Connections {
        target: menuDoApp
        function onAcionado(id) { janela.executar(id) }
    }
    function executar(id) {
        var l = janela.leitura
        switch (id) {
        case "nova": caixa.novaMensagem(); break
        case "atualizar": caixa.atualizar(); break
        case "adicionar": janela.adicionando = true; break
        case "contas": janela.gerenciando = true; break
        case "sair": Qt.quit(); break
        case "responder": if (janela.temLeitura) caixa.responder(l.id, false); break
        case "responder-todos": if (janela.temLeitura) caixa.responder(l.id, true); break
        case "encaminhar": if (janela.temLeitura) caixa.encaminhar(l.id); break
        case "lida": if (janela.temLeitura) caixa.marcarLida(l.id, !l.lida); break
        case "sinalizar": if (janela.temLeitura) caixa.sinalizar(l.id, !l.sinalizada); break
        case "arquivar": if (janela.temLeitura) caixa.arquivar(l.id); break
        case "apagar": if (janela.temLeitura) caixa.apagar(l.id); break
        case "buscar": campoBusca.entrada.forceActiveFocus(); break
        }
    }
    Shortcut { sequences: ["Ctrl+N"]; onActivated: janela.executar("nova") }
    Shortcut { sequences: ["F5", "Ctrl+Shift+N"]; onActivated: janela.executar("atualizar") }
    Shortcut { sequences: ["Ctrl+R"]; onActivated: janela.executar("responder") }
    Shortcut { sequences: ["Ctrl+Shift+R"]; onActivated: janela.executar("responder-todos") }
    Shortcut { sequences: ["Ctrl+Shift+F"]; onActivated: janela.executar("encaminhar") }
    Shortcut { sequences: ["Ctrl+U"]; onActivated: janela.executar("lida") }
    Shortcut { sequences: ["Delete"]; enabled: !campoBusca.entrada.activeFocus; onActivated: janela.executar("apagar") }
    Shortcut { sequences: ["Ctrl+F"]; onActivated: janela.executar("buscar") }
    Shortcut { sequences: ["Ctrl+Q"]; onActivated: janela.executar("sair") }

    function iconeDaPasta(papel) {
        return ({ entrada: "pasta-downloads", enviados: "abrir", rascunhos: "lapis", lixeira: "lixeira", spam: "escudo",
                  arquivo: "compactado" })[papel] || "pasta"
    }
    function dataCurta(segundos) {
        var d = new Date(segundos * 1000), hoje = new Date()
        if (d.toDateString() === hoje.toDateString()) return d.toLocaleTimeString(Qt.locale("pt_BR"), "HH:mm")
        var ontem = new Date(hoje.getTime() - 86400000)
        if (d.toDateString() === ontem.toDateString()) return "Ontem"
        if (hoje - d < 6 * 86400000) return d.toLocaleDateString(Qt.locale("pt_BR"), "ddd")
        return d.toLocaleDateString(Qt.locale("pt_BR"), d.getFullYear() === hoje.getFullYear() ? "d MMM" : "dd/MM/yyyy")
    }
    function dataLonga(segundos) {
        return new Date(segundos * 1000).toLocaleString(Qt.locale("pt_BR"), "dddd, d 'de' MMMM 'de' yyyy, HH:mm")
    }
    readonly property var paleta: ["#2E6BE6", "#7C3AED", "#0EA5A4", "#E8833D", "#D9467A", "#2F9E5E", "#5B6CF0"]
    function corDe(texto) { var h = 0; for (var i = 0; i < texto.length; i++) h = (h * 31 + texto.charCodeAt(i)) % 997; return paleta[h % paleta.length] }

    Rectangle { anchors.fill: parent; color: Tema.fundo }

    // ============================================================ lateral: escrever, contas e pastas
    Rectangle {
        id: lateral
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        width: 252
        color: Tema.lateral
        Botao {
            id: botaoEscrever
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
            height: 40
            texto: "Escrever"; icone: "lapis"; tipo: "primario"
            onClicado: caixa.novaMensagem()
        }
        Flickable {
            anchors { left: parent.left; right: parent.right; top: botaoEscrever.bottom; bottom: rodapeLateral.top; topMargin: 12 }
            contentHeight: colunaPastas.implicitHeight + 12
            clip: true
            Column {
                id: colunaPastas
                anchors { left: parent.left; right: parent.right; margins: 8 }
                spacing: 1
                Repeater {
                    model: caixa.pastas
                    delegate: Item {
                        id: item
                        required property var modelData
                        width: colunaPastas.width
                        height: modelData.tipo === "conta" ? 38 : 34
                        readonly property bool escolhida: modelData.tipo === "pasta" && modelData.id === caixa.pastaAtual
                        Rectangle {
                            visible: item.modelData.tipo === "pasta"
                            anchors.fill: parent
                            radius: 8
                            color: item.escolhida ? Tema.selecao : (areaPasta.containsMouse ? Tema.realce : "transparent")
                        }
                        // cabeçalho da conta
                        Row {
                            visible: item.modelData.tipo === "conta"
                            anchors { left: parent.left; leftMargin: 8; right: parent.right; bottom: parent.bottom; bottomMargin: 6 }
                            spacing: 6
                            Text { width: parent.width - 24; text: item.modelData.nome; elide: Text.ElideRight
                                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold; capitalization: Font.AllUppercase; letterSpacing: 0.4 } }
                            Icone { visible: item.modelData.erro !== undefined && item.modelData.erro !== ""; nome: "rede-alerta"; tamanho: 13; cor: Tema.erro }
                        }
                        Icone {
                            visible: item.modelData.tipo === "pasta"
                            anchors { left: parent.left; leftMargin: 10 + (item.modelData.nivel > 0 ? 4 : 0); verticalCenter: parent.verticalCenter }
                            nome: janela.iconeDaPasta(item.modelData.papel); tamanho: 16
                            cor: item.escolhida ? Tema.azulDuia : Tema.textoSecundario
                        }
                        Text {
                            visible: item.modelData.tipo === "pasta"
                            anchors { left: parent.left; leftMargin: 40; right: contador.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
                            text: item.modelData.nome
                            elide: Text.ElideRight
                            color: item.escolhida ? Tema.azulDuia : Tema.texto
                            font { family: Tema.fonteTexto; pixelSize: 13; weight: item.modelData.nao_lidas > 0 || item.escolhida ? Font.DemiBold : Font.Normal }
                        }
                        Text {
                            id: contador
                            visible: item.modelData.tipo === "pasta" && item.modelData.nao_lidas > 0 && item.modelData.papel !== "enviados"
                            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                            text: item.modelData.nao_lidas
                            color: item.escolhida ? Tema.azulDuia : Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
                        }
                        MouseArea { id: areaPasta; anchors.fill: parent; hoverEnabled: true; enabled: item.modelData.tipo === "pasta"
                                    onClicked: caixa.escolherPasta(item.modelData.id) }
                    }
                }
            }
        }
        Item {
            id: rodapeLateral
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 52
            Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: 1; color: Tema.borda }
            Row {
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 2
                BotaoIcone { icone: "mais"; dica: "Adicionar conta"; onClicado: janela.adicionando = true }
                BotaoIcone { icone: "usuario"; dica: "Contas"; onClicado: janela.gerenciando = true }
                BotaoIcone {
                    id: botaoReceber
                    icone: "reiniciar"; dica: "Receber e-mails"
                    onClicado: caixa.atualizar()
                    RotationAnimation on rotation { running: caixa.sincronizando; from: 0; to: 360; duration: 1000; loops: Animation.Infinite
                                                    onStopped: botaoReceber.rotation = 0 }
                }
            }
            Text {
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                width: 100; horizontalAlignment: Text.AlignRight; elide: Text.ElideRight
                text: caixa.estado
                color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 }
            }
        }
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Tema.borda }
    }

    // ============================================================ lista de mensagens
    Rectangle {
        id: colunaLista
        anchors { left: lateral.right; top: parent.top; bottom: parent.bottom }
        width: Math.max(340, Math.min(420, janela.width * 0.3))
        color: Tema.fundo
        Item {
            id: cabecalhoLista
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 104
            Text {
                id: tituloPasta
                anchors { left: parent.left; leftMargin: 18; top: parent.top; topMargin: 16 }
                width: Math.min(implicitWidth, parent.width - 140)
                elide: Text.ElideRight
                text: caixa.nomePastaAtual
                color: Tema.azulNoite
                font { family: Tema.fonteTitulo; pixelSize: 22; weight: Font.Bold }
            }
            Text {
                anchors { left: tituloPasta.right; leftMargin: 10; baseline: tituloPasta.baseline }
                text: caixa.mensagens.length + (caixa.mensagens.length === 1 ? " mensagem" : " mensagens")
                color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 }
            }
            Campo {
                id: campoBusca
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 14; bottomMargin: 12 }
                icone: "busca"; dica: "Buscar por remetente, assunto ou texto"
                onTextoChanged: tempoBusca.restart()
                Timer { id: tempoBusca; interval: 250; onTriggered: caixa.buscar(campoBusca.texto) }
            }
        }
        ListView {
            id: lista
            anchors { left: parent.left; right: parent.right; top: cabecalhoLista.bottom; bottom: parent.bottom }
            clip: true
            model: caixa.mensagens
            boundsBehavior: Flickable.StopAtBounds
            delegate: Rectangle {
                id: linha
                required property var modelData
                required property int index
                readonly property bool escolhida: janela.temLeitura && janela.leitura.id === modelData.id
                width: lista.width
                height: 84
                color: escolhida ? Tema.selecao : (areaLinha.containsMouse ? Tema.realce : "transparent")
                Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 18 } height: 1; color: Tema.borda; visible: !linha.escolhida }
                Rectangle {
                    visible: !linha.modelData.lida
                    anchors { left: parent.left; leftMargin: 7; top: parent.top; topMargin: 20 }
                    width: 8; height: 8; radius: 4; color: Tema.azulDuia
                }
                Column {
                    anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 22; rightMargin: 14; topMargin: 12 }
                    spacing: 3
                    Item {
                        width: parent.width; height: 18
                        Text { anchors { left: parent.left; right: dataLinha.left; rightMargin: 8 }
                               text: linha.modelData.papel === "enviados" ? "Para: " + linha.modelData.para : (linha.modelData.de_nome || linha.modelData.de_email)
                               elide: Text.ElideRight; color: Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 14; weight: linha.modelData.lida ? Font.Medium : Font.Bold } }
                        Text { id: dataLinha; anchors.right: parent.right; text: janela.dataCurta(linha.modelData.data)
                               color: linha.modelData.lida ? Tema.textoApagado : Tema.azulDuia
                               font { family: Tema.fonteTexto; pixelSize: 12; weight: linha.modelData.lida ? Font.Normal : Font.DemiBold } }
                    }
                    Item {
                        width: parent.width; height: 18
                        Text { anchors { left: parent.left; right: marcas.left; rightMargin: 6 }
                               text: linha.modelData.assunto || "(sem assunto)"; elide: Text.ElideRight
                               color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: linha.modelData.lida ? Font.Normal : Font.DemiBold } }
                        Row {
                            id: marcas
                            anchors.right: parent.right
                            spacing: 4
                            Icone { visible: linha.modelData.tem_anexo === 1; nome: "documento"; tamanho: 13; cor: Tema.textoSecundario }
                            Icone { visible: linha.modelData.sinalizada === 1; nome: "estrela"; tamanho: 13; cor: Tema.aviso }
                            Icone { visible: linha.modelData.respondida === 1; nome: "seta-esquerda"; tamanho: 13; cor: Tema.textoSecundario }
                        }
                    }
                    Text { width: parent.width; text: linha.modelData.previa; elide: Text.ElideRight; maximumLineCount: 1
                           color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                }
                MouseArea { id: areaLinha; anchors.fill: parent; hoverEnabled: true
                            onClicked: caixa.abrirMensagem(linha.modelData.id)
                            onDoubleClicked: caixa.responder(linha.modelData.id, false) }
            }
            Text {
                anchors.centerIn: parent
                visible: lista.count === 0
                width: parent.width - 48
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: campoBusca.texto !== "" ? "Nenhuma mensagem combina com “" + campoBusca.texto + "”."
                                              : (caixa.sincronizando ? "Recebendo as mensagens…" : "Nenhuma mensagem nesta pasta.")
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 14 }
            }
        }
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Tema.borda }
    }

    // ============================================================ leitura
    Rectangle {
        id: areaLeitura
        anchors { left: colunaLista.right; right: parent.right; top: parent.top; bottom: parent.bottom }
        color: Tema.fundo

        Column {
            anchors.centerIn: parent
            visible: !janela.temLeitura
            spacing: 12
            Icone { anchors.horizontalCenter: parent.horizontalCenter; nome: "pasta-downloads"; tamanho: 56; cor: Tema.bordaForte }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Escolha uma mensagem para ler"
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 15 } }
        }

        Item {
            anchors.fill: parent
            visible: janela.temLeitura
            // ---------------------------------------------------- ações
            Row {
                id: acoes
                anchors { left: parent.left; leftMargin: 18; top: parent.top; topMargin: 12 }
                spacing: 2
                BotaoIcone { icone: "seta-esquerda"; dica: "Responder"; onClicado: janela.executar("responder") }
                BotaoIcone { icone: "usuarios"; dica: "Responder a todos"; onClicado: janela.executar("responder-todos") }
                BotaoIcone { icone: "seta-direita"; dica: "Encaminhar"; onClicado: janela.executar("encaminhar") }
                Rectangle { width: 1; height: 20; color: Tema.borda; anchors.verticalCenter: parent.verticalCenter }
                BotaoIcone { icone: "compactado"; dica: "Arquivar"; onClicado: janela.executar("arquivar") }
                BotaoIcone { icone: "lixeira"; dica: "Mover para a Lixeira"; onClicado: janela.executar("apagar") }
                BotaoIcone { icone: "olho"; dica: janela.temLeitura && janela.leitura.lida ? "Marcar como não lida" : "Marcar como lida"
                             onClicado: janela.executar("lida") }
                BotaoIcone { icone: "estrela"; dica: "Sinalizar"; marcado: janela.temLeitura && janela.leitura.sinalizada
                             corIcone: janela.temLeitura && janela.leitura.sinalizada ? Tema.aviso : Tema.texto
                             onClicado: janela.executar("sinalizar") }
                BotaoIcone { id: botaoMover; icone: "pasta"; dica: "Mover para…"; marcado: menuMover.visible; onClicado: menuMover.visible = !menuMover.visible }
            }
            // ---------------------------------------------------- cabeçalho da mensagem
            Text {
                id: assunto
                anchors { left: parent.left; right: parent.right; top: acoes.bottom; leftMargin: 24; rightMargin: 24; topMargin: 14 }
                text: janela.temLeitura ? janela.leitura.assunto : ""
                wrapMode: Text.WordWrap
                maximumLineCount: 3
                elide: Text.ElideRight
                color: Tema.texto
                font { family: Tema.fonteTitulo; pixelSize: 22; weight: Font.Bold }
            }
            Rectangle {
                id: avatar
                anchors { left: parent.left; leftMargin: 24; top: assunto.bottom; topMargin: 16 }
                width: 40; height: 40; radius: 20
                color: janela.corDe(janela.temLeitura ? janela.leitura.de_email : "")
                Text { anchors.centerIn: parent; color: "white"; font { family: Tema.fonteTitulo; pixelSize: 17; weight: Font.Bold }
                       text: janela.temLeitura ? (janela.leitura.de_nome || janela.leitura.de_email || "?").charAt(0).toUpperCase() : "" }
            }
            Column {
                anchors { left: avatar.right; leftMargin: 12; right: dataMensagem.left; rightMargin: 12; verticalCenter: avatar.verticalCenter }
                spacing: 2
                Text { width: parent.width; elide: Text.ElideRight; textFormat: Text.StyledText
                       text: janela.temLeitura ? "<b>" + (janela.leitura.de_nome || janela.leitura.de_email) + "</b>&nbsp;&nbsp;<font color='" + Tema.textoSecundario + "'>" + janela.leitura.de_email + "</font>" : ""
                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14 } }
                Text { width: parent.width; elide: Text.ElideRight
                       text: janela.temLeitura ? "Para: " + janela.leitura.para + (janela.leitura.cc ? "   Cc: " + janela.leitura.cc : "") : ""
                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
            }
            Text {
                id: dataMensagem
                anchors { right: parent.right; rightMargin: 24; verticalCenter: avatar.verticalCenter }
                text: janela.temLeitura ? janela.dataLonga(janela.leitura.data) : ""
                color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 }
            }
            // ---------------------------------------------------- imagens bloqueadas
            Rectangle {
                id: faixaImagens
                anchors { left: parent.left; right: parent.right; top: avatar.bottom; leftMargin: 24; rightMargin: 24; topMargin: 14 }
                height: visible ? 40 : 0
                visible: janela.temLeitura && janela.leitura.bloqueadas > 0 && !janela.leitura.remoto
                radius: 10
                color: Tema.destaque
                Icone { id: iconeEscudo; anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter } nome: "escudo"; tamanho: 16; cor: Tema.azulDuia }
                Text { anchors { left: iconeEscudo.right; leftMargin: 10; right: botaoImagens.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                       text: "Imagens externas bloqueadas para proteger a sua privacidade."
                       elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                Text { id: botaoImagens; anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                       text: "Mostrar imagens"; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
                       MouseArea { anchors.fill: parent; anchors.margins: -6; cursorShape: Qt.PointingHandCursor; onClicked: caixa.mostrarImagens() } }
            }
            // ---------------------------------------------------- anexos
            Flow {
                id: anexos
                anchors { left: parent.left; right: parent.right; top: faixaImagens.visible ? faixaImagens.bottom : avatar.bottom; leftMargin: 24; rightMargin: 24; topMargin: 12 }
                spacing: 8
                visible: janela.temLeitura && janela.leitura.anexos.length > 0
                height: visible ? implicitHeight : 0
                Repeater {
                    model: janela.temLeitura ? janela.leitura.anexos : []
                    delegate: Rectangle {
                        required property var modelData
                        height: 40; radius: 10
                        width: Math.min(260, linhaAnexo.implicitWidth + 24)
                        color: areaAnexo.containsMouse ? Tema.realce : Tema.cartao
                        border { width: 1; color: Tema.borda }
                        Row {
                            id: linhaAnexo
                            anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                            spacing: 8
                            Icone { nome: modelData.tipo === "application/pdf" ? "pdf" : (modelData.tipo.indexOf("image/") === 0 ? "imagem" : "documento")
                                    tamanho: 16; cor: Tema.azulDuia; anchors.verticalCenter: parent.verticalCenter }
                            Column {
                                anchors.verticalCenter: parent.verticalCenter
                                Text { text: modelData.nome; width: Math.min(implicitWidth, 190); elide: Text.ElideMiddle
                                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } }
                                Text { text: modelData.tamanho > 1e6 ? (modelData.tamanho / 1e6).toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(modelData.tamanho / 1e3)) + " KB"
                                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
                            }
                        }
                        MouseArea { id: areaAnexo; anchors.fill: parent; hoverEnabled: true; onClicked: caixa.abrirAnexo(janela.leitura.id, modelData.indice) }
                    }
                }
            }
            // ---------------------------------------------------- conteúdo
            Rectangle {
                id: moldura
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; top: anexos.visible ? anexos.bottom : (faixaImagens.visible ? faixaImagens.bottom : avatar.bottom)
                          margins: 16; topMargin: 14 }
                radius: Tema.raio
                color: "#ffffff"
                border { width: 1; color: Tema.borda }
                clip: true
                WebEngineView {
                    id: vista
                    anchors { fill: parent; margins: 1 }
                    profile: perfilLeitura
                    settings.javascriptEnabled: false
                    settings.javascriptCanOpenWindows: false
                    settings.localContentCanAccessRemoteUrls: false
                    settings.localContentCanAccessFileUrls: false
                    settings.autoLoadIconsForPage: false
                    settings.pluginsEnabled: false
                    backgroundColor: "white"
                    property string conteudo: janela.temLeitura ? janela.leitura.html : ""
                    onConteudoChanged: loadHtml(conteudo, "about:blank")
                    onNavigationRequested: (pedido) => {
                        if (pedido.navigationType === WebEngineNavigationRequest.LinkClickedNavigation) {
                            pedido.reject()
                            caixa.abrirLink(pedido.url.toString())
                        }
                    }
                    onNewWindowRequested: (pedido) => caixa.abrirLink(pedido.requestedUrl.toString())
                }
                Text {
                    anchors.centerIn: parent
                    visible: janela.temLeitura && janela.leitura.carregando
                    text: "Baixando a mensagem…"
                    color: "#5B6675"; font { family: Tema.fonteTexto; pixelSize: 14 }
                }
            }
            // ---------------------------------------------------- mover para
            Rectangle {
                id: menuMover
                visible: false
                z: 10
                x: acoes.x + botaoMover.x
                y: acoes.y + acoes.height + 4
                width: 240
                height: Math.min(360, colunaMover.implicitHeight + 12)
                radius: Tema.raio
                color: Tema.vidro
                border { color: Tema.borda; width: 1 }
                Flickable {
                    anchors { fill: parent; margins: 6 }
                    contentHeight: colunaMover.implicitHeight
                    clip: true
                    Column {
                        id: colunaMover
                        width: parent.width
                        Repeater {
                            model: caixa.pastasParaMover
                            delegate: ItemDeMenu { required property var modelData; width: colunaMover.width; texto: modelData.nome; icone: "pasta"
                                                   onClicado: { menuMover.visible = false; caixa.moverPara(janela.leitura.id, modelData.id) } }
                        }
                    }
                }
            }
        }
    }

    // ============================================================ contas
    Rectangle {
        anchors.fill: parent
        visible: janela.gerenciando
        color: Qt.rgba(0, 0, 0, Tema.escuro ? 0.5 : 0.25)
        z: 30
        MouseArea { anchors.fill: parent; onClicked: janela.gerenciando = false }
        Cartao {
            anchors.centerIn: parent
            width: 560
            height: Math.min(parent.height - 80, colunaContas.implicitHeight + 48)
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaContas
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 14
                Item {
                    width: parent.width; height: 32
                    Titulo { anchors.verticalCenter: parent.verticalCenter; text: "Contas" }
                    BotaoIcone { anchors { right: parent.right; verticalCenter: parent.verticalCenter } icone: "fechar"; dica: "Fechar"; onClicado: janela.gerenciando = false }
                }
                Repeater {
                    model: caixa.contasLista
                    delegate: Rectangle {
                        required property var modelData
                        width: colunaContas.width
                        height: colunaConta.implicitHeight + 24
                        radius: Tema.raio
                        color: Tema.fundo
                        border { width: 1; color: Tema.borda }
                        Column {
                            id: colunaConta
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                            spacing: 8
                            Item {
                                width: parent.width; height: 36
                                Column {
                                    anchors.verticalCenter: parent.verticalCenter
                                    Text { text: modelData.email; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                                    Text { text: (modelData.nome_provedor || modelData.servidor) + " · " + modelData.tipo.toUpperCase()
                                           color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                                }
                                Botao { anchors { right: parent.right; verticalCenter: parent.verticalCenter } texto: "Remover"; tipo: "perigo"
                                        onClicado: caixa.removerConta(modelData.id) }
                            }
                            Text { visible: modelData.erro !== ""; width: parent.width; wrapMode: Text.WordWrap; text: modelData.erro
                                   color: Tema.erro; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Campo { id: campoNome; width: parent.width; dica: "Seu nome, como os outros veem"; texto: modelData.nome
                                    entrada.onEditingFinished: caixa.editarConta(modelData.id, campoNome.texto, campoAssinatura.texto) }
                            Campo { id: campoAssinatura; width: parent.width; dica: "Assinatura (vai no fim das mensagens)"; texto: modelData.assinatura
                                    entrada.onEditingFinished: caixa.editarConta(modelData.id, campoNome.texto, campoAssinatura.texto) }
                        }
                    }
                }
                Botao { texto: "Adicionar conta"; icone: "mais"; onClicado: { janela.gerenciando = false; janela.adicionando = true } }
            }
        }
    }

    // ============================================================ wizard
    Wizard {
        anchors.fill: parent
        visible: janela.adicionando
        z: 40
        podeCancelar: caixa.contasLista.length > 0
        onConcluido: janela.adicionando = false
        onCancelado: janela.adicionando = false
    }

    Aviso { id: aviso; anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 24 } z: 50 }

    Timer {
        interval: 3000
        running: typeof capturaArquivo !== "undefined" && capturaArquivo !== "" && (typeof paginaDemonstracao === "undefined" || paginaDemonstracao !== "escrever")
        onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() })
    }
}
