// DuiaOS — Duia App Store.
// Lateral com a busca, Descobrir, as categorias, Instalados e Atualizações; à direita, a página
// (vitrine, lista em grade ou a página do aplicativo), no estilo das lojas do macOS e do Windows.
import QtQuick
import QtQuick.Window
import DuiaOS

Window {
    id: janela
    // Menus na Barra de Recursos (ADR 059): Loja, Editar e Categorias
    readonly property var menusDoApp: {
        var it = function (id, rotulo, atalho, marcado) { return { id: id, rotulo: rotulo, tipo: marcado === undefined ? "item" : "marcavel",
                                                                  ativo: true, marcado: marcado === true, atalho: atalho || "", itens: [] } }
        var sep = { id: -1, rotulo: "", tipo: "separador", ativo: false, marcado: false, atalho: "", itens: [] }
        var categorias = []
        for (var i = 0; i < loja.categorias.length; i++)
            categorias.push(it("pagina:categoria:" + loja.categorias[i].id, loja.categorias[i].nome, "",
                               loja.pagina === "categoria:" + loja.categorias[i].id))
        return [{ rotulo: "Loja", itens: [it("pagina:descobrir", "Descobrir", "", loja.pagina === "descobrir"),
                                          it("pagina:instalados", "Instalados", "", loja.pagina === "instalados"),
                                          it("pagina:atualizacoes", "Atualizações", "", loja.pagina === "atualizacoes"), sep,
                                          it("recarregar", "Atualizar o catálogo"), sep, it("fechar", "Fechar")] },
                { rotulo: "Editar", itens: [it("buscar", "Buscar aplicativos")] },
                { rotulo: "Categorias", itens: categorias }]
    }
    onMenusDoAppChanged: menuDoApp.definirMenus(menusDoApp)
    Connections {
        target: menuDoApp
        function onAcionado(id) {
            if (id.indexOf("pagina:") === 0) loja.irPara(id.slice(7))
            else if (id === "recarregar") loja.recarregarCatalogo()
            else if (id === "buscar") busca.entrada.forceActiveFocus()
            else if (id === "fechar") Qt.quit()
        }
    }
    width: 1120; height: 740
    minimumWidth: 800; minimumHeight: 520
    visible: true
    color: Tema.fundo
    title: "Duia App Store"

    Connections {
        target: loja
        function onAviso(texto) { aviso.mostrar(texto) }
        function onMostrar() { janela.raise(); janela.requestActivate() }
    }

    Rectangle { anchors.fill: parent; color: Tema.fundo }        // fundo também nas capturas

    // ============================================================ componentes
    // Ícone de um aplicativo do catálogo: arquivo do AppStream, endereço da internet, ícone do tema
    // ou a inicial num quadrado colorido.
    component IconeLoja: Item {
        id: il
        property var app: ({})
        property int tamanho: 56
        width: tamanho; height: tamanho
        property bool reserva: false
        onAppChanged: reserva = false
        readonly property string fonteImagem: {
            if (reserva) return app && app.iconeReserva ? "image://icone/" + app.iconeReserva : ""
            var i = app && app.icone ? app.icone : ""
            if (i === "") return ""
            if (i.charAt(0) === "/") return "file://" + i
            if (i.indexOf("http") === 0) return i
            return "image://icone/" + i
        }
        readonly property var paleta: [["#6FA0F7", "#2E6BE6"], ["#8B7CF6", "#5B3FD9"], ["#4CC38A", "#1E8E5A"],
                                       ["#F5A25D", "#D9692B"], ["#F0708A", "#C73A5B"], ["#5BC0DE", "#2A86A8"]]
        readonly property var cores: paleta[Math.abs(janela.hash(app && app.nome ? app.nome : "")) % paleta.length]
        Image {
            id: imagemIcone
            anchors.fill: parent
            source: il.fonteImagem
            sourceSize: Qt.size(il.tamanho * 2, il.tamanho * 2)
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            visible: status === Image.Ready
            onStatusChanged: if (status === Image.Error && !il.reserva) il.reserva = true
        }
        Rectangle {
            anchors.fill: parent
            visible: imagemIcone.status !== Image.Ready
            radius: il.tamanho * 0.24
            gradient: Gradient { GradientStop { position: 0; color: il.cores[0] } GradientStop { position: 1; color: il.cores[1] } }
            Text {
                anchors.centerIn: parent
                text: (il.app && il.app.nome ? il.app.nome : "?").charAt(0).toUpperCase()
                color: "white"
                font { family: Tema.fonteTitulo; pixelSize: il.tamanho * 0.46; weight: Font.Bold }
            }
        }
    }

    // Botão de cada aplicativo: Obter → andamento → Abrir (ou Atualizar)
    component BotaoApp: Item {
        id: ba
        property var app: ({})
        property bool grande: false
        readonly property string situacao: app && app.id ? (loja.situacao[app.id] || "disponivel") : "disponivel"
        readonly property var tarefa: app && app.id ? loja.tarefas[app.id] : undefined
        implicitWidth: situacao === "andamento" ? (grande ? 210 : 34) : rotulo.implicitWidth + (grande ? 40 : 28)
        implicitHeight: grande ? 34 : 28
        width: implicitWidth; height: implicitHeight

        Rectangle {
            visible: ba.situacao !== "andamento"
            anchors.fill: parent
            radius: height / 2
            readonly property bool cheio: ba.situacao === "disponivel" || ba.situacao === "atualizavel"
            color: cheio ? (areaBotao.pressed ? Tema.azulEscuro : Tema.azulDuia)
                         : (areaBotao.containsMouse ? Tema.controleDesligado : Tema.destaque)
            Text {
                id: rotulo
                anchors.centerIn: parent
                text: ba.situacao === "instalado" ? "Abrir" : (ba.situacao === "atualizavel" ? "Atualizar" : "Obter")
                color: parent.cheio ? "white" : Tema.azulDuia
                font { family: Tema.fonteTexto; pixelSize: ba.grande ? 14 : 12; weight: Font.Bold }
            }
            MouseArea {
                id: areaBotao
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (ba.situacao === "instalado") loja.abrir(ba.app.id)
                    else if (ba.situacao === "atualizavel") loja.atualizar(ba.app.id)
                    else loja.instalar(ba.app.id)
                }
            }
        }
        // Andamento: anel com a porcentagem (clique cancela) e, no botão grande, o que está fazendo
        Row {
            visible: ba.situacao === "andamento"
            spacing: 10
            anchors.verticalCenter: parent.verticalCenter
            Anel {
                fracao: ba.tarefa ? ba.tarefa.fracao : 0
                tamanho: ba.grande ? 32 : 28
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: loja.cancelar(ba.app.id) }
            }
            Text {
                visible: ba.grande
                width: 168
                anchors.verticalCenter: parent.verticalCenter
                text: ba.tarefa ? ba.tarefa.mensagem : ""
                elide: Text.ElideRight
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 12 }
            }
        }
    }

    // Anel de andamento; sem porcentagem conhecida, gira
    component Anel: Item {
        id: anel
        property real fracao: 0
        property int tamanho: 28
        width: tamanho; height: tamanho
        onFracaoChanged: tela.requestPaint()
        Canvas {
            id: tela
            anchors.fill: parent
            onPaint: {
                var c = getContext("2d"); c.reset()
                var r = width / 2 - 2.5
                c.lineWidth = 3
                c.strokeStyle = Tema.controleDesligado
                c.beginPath(); c.arc(width / 2, height / 2, r, 0, 2 * Math.PI); c.stroke()
                c.strokeStyle = Tema.azulDuia
                c.lineCap = "round"
                var parte = anel.fracao > 0.01 ? anel.fracao : 0.25
                c.beginPath(); c.arc(width / 2, height / 2, r, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * parte); c.stroke()
            }
            RotationAnimator on rotation { from: 0; to: 360; duration: 1100; loops: Animation.Infinite; running: anel.fracao <= 0.01 && anel.visible }
        }
        Rectangle { anchors.centerIn: parent; width: anel.tamanho * 0.3; height: width; radius: 2; color: Tema.azulDuia }
    }

    // Selo de onde vem o aplicativo
    component SeloFonte: Rectangle {
        property string fonte: "flathub"
        implicitWidth: textoSelo.implicitWidth + 14
        implicitHeight: 20
        radius: 10
        color: fonte === "flathub" ? Tema.destaque : Tema.controleDesligado
        Text {
            id: textoSelo
            anchors.centerIn: parent
            text: parent.fonte === "flathub" ? "Flathub" : "Debian"
            color: parent.fonte === "flathub" ? Tema.azulDuia : Tema.textoSecundario
            font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold }
        }
    }

    // Cartão de um aplicativo nas grades
    component CartaoApp: Rectangle {
        id: cartao
        property var app: ({})
        width: 300; height: 84
        radius: Tema.raio
        color: areaCartao.containsMouse ? Tema.realce : "transparent"
        MouseArea { id: areaCartao; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: loja.abrirApp(cartao.app.id) }
        IconeLoja { id: iconeCartao; app: cartao.app; tamanho: 56; anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter } }
        Column {
            anchors { left: iconeCartao.right; leftMargin: 12; right: botaoCartao.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
            spacing: 2
            Text { width: parent.width; text: cartao.app.nome || ""; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
            Text { width: parent.width; text: cartao.app.resumo || ""; elide: Text.ElideRight; maximumLineCount: 2; wrapMode: Text.WordWrap; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
        }
        BotaoApp { id: botaoCartao; app: cartao.app; anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter } }
        Rectangle { anchors { left: iconeCartao.right; leftMargin: 12; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda; opacity: 0.6 }
    }

    // Grade de cartões que se ajusta à largura
    component Grade: Grid {
        id: grade
        property var apps: []
        property int largura: 600
        columns: Math.max(1, Math.floor((largura + 12) / 312))
        columnSpacing: 12
        rowSpacing: 4
        Repeater {
            model: grade.apps
            delegate: CartaoApp {
                required property var modelData
                app: modelData
                width: (grade.largura - (grade.columns - 1) * 12) / grade.columns
            }
        }
    }

    function hash(texto) { var h = 0; for (var i = 0; i < texto.length; i++) h = (h * 31 + texto.charCodeAt(i)) | 0; return h }

    // ================================================================ lateral
    Rectangle {
        id: lateral
        width: 236
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        color: Tema.lateral
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Tema.borda }

        Campo {
            id: busca
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            icone: "busca"; dica: "Buscar aplicativos"
            Component.onCompleted: texto = loja.termo
            entrada.onTextChanged: atrasoBusca.restart()
            Timer { id: atrasoBusca; interval: 220; onTriggered: loja.buscar(busca.texto) }
        }

        Flickable {
            anchors { left: parent.left; right: parent.right; top: busca.bottom; bottom: rodapeLateral.top; margins: 10 }
            contentHeight: colunaLateral.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: colunaLateral
                width: parent.width
                spacing: 2
                ItemLateral { pagina: "descobrir"; nome: "Descobrir"; icone: "estrela" }
                Item { width: 1; height: 10 }
                Text { x: 8; text: "Categorias"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
                Item { width: 1; height: 4 }
                Repeater {
                    model: loja.categorias
                    delegate: ItemLateral {
                        required property var modelData
                        pagina: "categoria:" + modelData.id; nome: modelData.nome; icone: modelData.icone
                    }
                }
                Item { width: 1; height: 10 }
                Text { x: 8; text: "Neste computador"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
                Item { width: 1; height: 4 }
                ItemLateral { pagina: "instalados"; nome: "Instalados"; icone: "computador" }
                ItemLateral { pagina: "atualizacoes"; nome: "Atualizações"; icone: "reiniciar"; numero: loja.numeroAtualizacoes }
            }
        }
        // Marca da loja
        Row {
            id: rodapeLateral
            anchors { left: parent.left; bottom: parent.bottom; margins: 14 }
            spacing: 10
            Ladrilho { tamanho: 30; radius: 8; icone: "sacola"; estilo: "azul" }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text { text: "Duia App Store"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 13; weight: Font.Bold } }
                Text {
                    text: loja.carregando ? "Carregando o catálogo…" : (loja.totais.flathub + loja.totais.debian) + " aplicativos"
                    color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 }
                }
            }
        }
    }

    component ItemLateral: Rectangle {
        id: item
        property string pagina: ""
        property string nome: ""
        property string icone: ""
        property int numero: 0
        readonly property bool atual: loja.pagina === pagina
        width: parent ? parent.width : 200
        height: 32; radius: 8
        color: atual ? Tema.azulDuia : (areaItem.containsMouse ? Tema.realce : "transparent")
        Icone { id: iconeItem; anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter } nome: item.icone; tamanho: 17; cor: item.atual ? "white" : Tema.azulDuia }
        Text {
            anchors { left: iconeItem.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
            text: item.nome
            color: item.atual ? "white" : Tema.texto
            font { family: Tema.fonteTexto; pixelSize: 13; weight: item.atual ? Font.DemiBold : Font.Normal }
        }
        Rectangle {
            visible: item.numero > 0
            anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
            width: Math.max(20, textoNumero.implicitWidth + 10); height: 20; radius: 10
            color: item.atual ? "white" : Tema.azulDuia
            Text { id: textoNumero; anchors.centerIn: parent; text: item.numero; color: item.atual ? Tema.azulDuia : "white"; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.Bold } }
        }
        MouseArea { id: areaItem; anchors.fill: parent; hoverEnabled: true; onClicked: { busca.texto = ""; loja.irPara(item.pagina) } }
    }

    // ================================================================ conteúdo
    Item {
        id: conteudo
        anchors { left: lateral.right; right: parent.right; top: parent.top; bottom: parent.bottom }

        // Barra de cima: voltar e título da página
        Item {
            id: topo
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 52
            BotaoIcone {
                id: voltar
                visible: loja.pagina === "app" || loja.pagina === "busca"
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                icone: "seta-esquerda"
                onClicado: { if (loja.pagina === "busca") busca.texto = ""; loja.voltar() }
            }
            Text {
                anchors { left: voltar.visible ? voltar.right : parent.left; leftMargin: voltar.visible ? 10 : 28; verticalCenter: parent.verticalCenter }
                visible: loja.pagina !== "app"
                text: loja.pagina === "descobrir" ? "Descobrir"
                    : loja.pagina === "instalados" ? "Instalados"
                    : loja.pagina === "atualizacoes" ? "Atualizações"
                    : loja.pagina === "busca" ? "Resultados para “" + loja.termo + "”"
                    : loja.pagina.indexOf("categoria:") === 0 ? loja.nomeCategoria(loja.pagina.substring(10)) : ""
                color: Tema.azulNoite
                font { family: Tema.fonteTitulo; pixelSize: 24; weight: Font.Bold }
            }
            Botao {
                visible: loja.pagina === "atualizacoes" && loja.numeroAtualizacoes > 0
                anchors { right: parent.right; rightMargin: 24; verticalCenter: parent.verticalCenter }
                tipo: "primario"; texto: "Atualizar tudo"
                onClicado: loja.atualizarTudo()
            }
        }

        // Aviso do Flathub (sem internet, flatpak ausente…)
        Rectangle {
            id: faixaErro
            visible: loja.erroFlathub !== "" && !loja.carregando
            anchors { left: parent.left; right: parent.right; top: topo.bottom; leftMargin: 24; rightMargin: 24 }
            height: visible ? 40 : 0
            radius: 10
            color: Qt.rgba(0.91, 0.64, 0.24, 0.14)
            Icone { id: iconeErro; anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter } nome: "info"; tamanho: 16; cor: Tema.aviso }
            Text {
                anchors { left: iconeErro.right; leftMargin: 8; right: tentar.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                text: "Flathub: " + loja.erroFlathub
                elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 }
            }
            Botao { id: tentar; anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter } texto: "Tentar de novo"; height: 28; onClicado: loja.recarregarCatalogo() }
        }

        Flickable {
            id: rolagem
            anchors { left: parent.left; right: parent.right; top: faixaErro.bottom; bottom: parent.bottom; topMargin: faixaErro.visible ? 10 : 0 }
            contentHeight: paginaAtual.item ? paginaAtual.item.implicitHeight + 40 : 0
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Connections { target: loja; function onMudou() { rolagem.contentY = 0 } }
            Loader {
                id: paginaAtual
                x: 24; width: rolagem.width - 48
                sourceComponent: loja.pagina === "descobrir" ? paginaDescobrir : (loja.pagina === "app" ? paginaApp : paginaLista)
            }
        }

        // Carregando o catálogo pela primeira vez
        Column {
            anchors.centerIn: parent
            visible: loja.carregando && loja.lista.length === 0 && loja.pagina !== "app"
                     && (loja.pagina !== "descobrir" || loja.vitrine.destaques.length === 0)
            spacing: 12
            Anel { anchors.horizontalCenter: parent.horizontalCenter; tamanho: 36; fracao: 0 }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Carregando o catálogo de aplicativos…"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
        }
    }

    // --------------------------------------------------------------- Descobrir
    Component {
        id: paginaDescobrir
        Column {
            spacing: 26
            // Destaques: cartões grandes coloridos
            Grid {
                id: gradeDestaques
                width: parent.width
                columns: width > 760 ? 2 : 1
                columnSpacing: 16; rowSpacing: 16
                Repeater {
                    model: loja.vitrine.destaques
                    delegate: Rectangle {
                        required property var modelData
                        width: (gradeDestaques.width - (gradeDestaques.columns - 1) * 16) / gradeDestaques.columns
                        height: 196
                        radius: Tema.raioGrande
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: modelData.cores ? modelData.cores[0] : Tema.azulDuia }
                            GradientStop { position: 1; color: modelData.cores ? modelData.cores[1] : Tema.azulNoite }
                        }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: loja.abrirApp(modelData.app.id) }
                        Column {
                            anchors { left: parent.left; right: iconeDestaque.left; top: parent.top; margins: 22 }
                            spacing: 6
                            Text { text: "DESTAQUE"; color: Qt.rgba(1, 1, 1, 0.7); font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.Bold; letterSpacing: 1 } }
                            Text { width: parent.width; text: modelData.titulo; wrapMode: Text.WordWrap; color: "white"; font { family: Tema.fonteTitulo; pixelSize: 24; weight: Font.Bold } }
                            Text { width: parent.width; text: modelData.texto; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight; color: Qt.rgba(1, 1, 1, 0.88); font { family: Tema.fonteTexto; pixelSize: 13 } }
                        }
                        IconeLoja { id: iconeDestaque; app: modelData.app; tamanho: 84; anchors { right: parent.right; top: parent.top; margins: 22 } }
                        Row {
                            anchors { left: parent.left; bottom: parent.bottom; margins: 20 }
                            spacing: 12
                            Text { anchors.verticalCenter: parent.verticalCenter; text: modelData.app.nome; color: "white"; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                            BotaoApp { app: modelData.app; anchors.verticalCenter: parent.verticalCenter }
                        }
                    }
                }
            }
            // Coleções
            Repeater {
                model: loja.vitrine.colecoes
                delegate: Column {
                    required property var modelData
                    width: parent.width
                    spacing: 8
                    Text { text: modelData.titulo; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 19; weight: Font.Bold } }
                    Rectangle { width: parent.width; height: 1; color: Tema.borda }
                    Grade { largura: parent.width; apps: modelData.apps.slice(0, Math.max(1, Math.floor((parent.width + 12) / 312)) * 2) }
                }
            }
            // Categorias em ladrilhos
            Column {
                width: parent.width
                spacing: 8
                Text { text: "Categorias"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 19; weight: Font.Bold } }
                Rectangle { width: parent.width; height: 1; color: Tema.borda }
                Grid {
                    id: gradeCategorias
                    width: parent.width
                    columns: Math.max(2, Math.floor((width + 12) / 212))
                    spacing: 12
                    Repeater {
                        model: loja.categorias
                        delegate: Rectangle {
                            required property var modelData
                            width: (gradeCategorias.width - (gradeCategorias.columns - 1) * 12) / gradeCategorias.columns
                            height: 58; radius: Tema.raio
                            color: areaCategoria.containsMouse ? Tema.realce : Tema.cartao
                            border { color: Tema.borda; width: 1 }
                            Ladrilho { id: ladrilhoCategoria; tamanho: 34; radius: 9; icone: modelData.icone; estilo: modelData.cor; anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter } }
                            Column {
                                anchors { left: ladrilhoCategoria.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                                Text { text: modelData.nome; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                                Text { visible: modelData.quantos > 0; text: modelData.quantos + " aplicativos"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
                            }
                            MouseArea { id: areaCategoria; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: loja.irPara("categoria:" + modelData.id) }
                        }
                    }
                }
            }
            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                text: "Os aplicativos vêm do Flathub (flathub.org) e do arquivo do Debian. Cada página diz de onde o "
                      + "aplicativo vem e qual é a licença dele. Os do Flathub ficam só na sua conta e não pedem senha."
                color: Tema.textoApagado
                font { family: Tema.fonteTexto; pixelSize: 11 }
            }
        }
    }

    // ------------------------------------------------- listas (categoria, busca…)
    Component {
        id: paginaLista
        Column {
            spacing: 8
            Text {
                visible: !loja.carregando && loja.lista.length === 0
                width: parent.width
                topPadding: 60
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: loja.pagina === "atualizacoes" ? "Tudo em dia. Os aplicativos do Debian se atualizam junto com o sistema, nas Configurações."
                    : loja.pagina === "instalados" ? "Nenhum aplicativo da loja instalado ainda."
                    : loja.pagina === "busca" ? "Nada encontrado. Tente outra palavra." : "Nenhum aplicativo nesta categoria."
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 14 }
            }
            Botao {
                visible: loja.pagina === "atualizacoes"
                anchors.horizontalCenter: parent.horizontalCenter
                texto: "Atualizações do sistema"; icone: "reiniciar"
                onClicado: loja.abrirAtualizacoesDoSistema()
            }
            Grade { largura: parent.width; apps: loja.lista }
        }
    }

    // ------------------------------------------------------- página do aplicativo
    Component {
        id: paginaApp
        Column {
            id: pa
            readonly property var app: loja.app
            readonly property string situacao: app.id ? (loja.situacao[app.id] || "disponivel") : "disponivel"
            spacing: 20

            // Cabeçalho
            Item {
                width: parent.width
                height: 120
                IconeLoja { id: iconeGrande; app: pa.app; tamanho: 112 }
                Column {
                    anchors { left: iconeGrande.right; leftMargin: 22; right: parent.right; verticalCenter: parent.verticalCenter }
                    spacing: 4
                    Text { width: parent.width; text: pa.app.nome || ""; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 28; weight: Font.Bold } }
                    Text { width: parent.width; text: pa.app.resumo || ""; elide: Text.ElideRight; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 15 } }
                    Row {
                        spacing: 6
                        Text { anchors.verticalCenter: parent.verticalCenter; text: pa.app.desenvolvedor || ""; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 13 } }
                        Icone { visible: !!pa.app.verificado; anchors.verticalCenter: parent.verticalCenter; nome: "verificado"; tamanho: 15; cor: Tema.azulDuia }
                    }
                    Item { width: 1; height: 6 }
                    Row {
                        spacing: 10
                        BotaoApp { app: pa.app; grande: true }
                        Botao {
                            visible: pa.situacao === "instalado" || pa.situacao === "atualizavel"
                            texto: "Remover"; height: 34
                            onClicado: loja.remover(pa.app.id)
                        }
                    }
                }
            }

            // Fichinha: fonte, licença, versão, categoria
            Rectangle {
                width: parent.width
                height: 74
                radius: Tema.raio
                color: Tema.cartao
                border { color: Tema.borda; width: 1 }
                Row {
                    anchors.fill: parent
                    Repeater {
                        model: [
                            { titulo: "VEM DE", valor: pa.app.fonte === "flathub" ? "Flathub" : "Debian", selo: true },
                            { titulo: "LICENÇA", valor: pa.app.licenca || "", livre: pa.app.livre },
                            { titulo: "VERSÃO", valor: pa.app.versao || "—" },
                            { titulo: loja.tamanhoApp.baixar ? "DOWNLOAD" : "TAMANHO", valor: loja.tamanhoApp.texto || "—" },
                            { titulo: "CATEGORIA", valor: (pa.app.categorias && pa.app.categorias.length) ? loja.nomeCategoria(pa.app.categorias[0]) : "—" }
                        ]
                        delegate: Item {
                            required property var modelData
                            required property int index
                            width: parent.width / 5; height: parent.height
                            Rectangle { visible: index > 0; width: 1; height: parent.height - 24; anchors.verticalCenter: parent.verticalCenter; color: Tema.borda }
                            Column {
                                anchors.centerIn: parent
                                width: parent.width - 20
                                spacing: 6
                                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: modelData.titulo; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                                SeloFonte { visible: !!modelData.selo; fonte: pa.app.fonte || "flathub"; anchors.horizontalCenter: parent.horizontalCenter }
                                Text {
                                    visible: !modelData.selo
                                    width: parent.width; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                                    text: modelData.valor + (modelData.livre === true ? " · livre" : "")
                                    color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
                                }
                            }
                        }
                    }
                }
            }

            // Capturas de tela
            ListView {
                id: capturas
                visible: (pa.app.capturas || []).length > 0
                width: parent.width
                height: visible ? 300 : 0
                orientation: ListView.Horizontal
                spacing: 14
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: pa.app.capturas || []
                delegate: Rectangle {
                    required property var modelData
                    width: Math.min(capturas.width * 0.8, 480); height: 300
                    radius: Tema.raio
                    color: Tema.cartao
                    border { color: Tema.borda; width: 1 }
                    clip: true
                    Image {
                        id: imagemCaptura
                        anchors { fill: parent; margins: 1 }
                        source: modelData
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        sourceSize.width: 960
                    }
                    Anel { anchors.centerIn: parent; visible: imagemCaptura.status === Image.Loading; tamanho: 26; fracao: imagemCaptura.progress }
                    Text { anchors.centerIn: parent; visible: imagemCaptura.status === Image.Error; text: "Sem internet para a captura de tela"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 12 } }
                }
            }

            // Descrição
            Column {
                width: parent.width
                spacing: 8
                Text { text: "Sobre o aplicativo"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 18; weight: Font.Bold } }
                Text {
                    width: parent.width
                    text: pa.app.descricao || pa.app.resumo || ""
                    wrapMode: Text.WordWrap
                    lineHeight: 1.25
                    color: Tema.texto
                    font { family: Tema.fonteTexto; pixelSize: 13 }
                }
            }

            // Informações
            Rectangle {
                width: parent.width
                height: colunaInfo.implicitHeight
                radius: Tema.raio
                color: Tema.cartao
                border { color: Tema.borda; width: 1 }
                Column {
                    id: colunaInfo
                    width: parent.width
                    Repeater {
                        model: [
                            { titulo: "Desenvolvedor", valor: pa.app.desenvolvedor || "Não informado" },
                            { titulo: "Origem", valor: pa.app.fonte === "flathub" ? "Flathub — instalado só na sua conta, sem senha, em caixa de areia (sandbox)"
                                                                                : "Debian — instalado para todas as contas, pelo serviço de instalação do DuiaOS" },
                            { titulo: "Licença", valor: (pa.app.licenca || "") + (pa.app.livre ? " (software livre)" : "") },
                            { titulo: "Tamanho", valor: loja.tamanhoApp.baixar
                                  ? "Baixa " + loja.tamanhoApp.baixar + (loja.tamanhoApp.instalar ? " e ocupa " + loja.tamanhoApp.instalar + " depois de instalado" : "")
                                    + (loja.tamanhoApp.detalhe ? ". " + loja.tamanhoApp.detalhe : "")
                                  : (loja.tamanhoApp.instalar ? "Ocupa " + loja.tamanhoApp.instalar + " no computador" : (loja.tamanhoApp.detalhe || loja.tamanhoApp.texto || "—")) },
                            { titulo: "Identificador", valor: pa.app.fonte === "flathub" ? pa.app.pacote : "pacote " + pa.app.pacote },
                            { titulo: "Site", valor: pa.app.site || "", link: true }
                        ]
                        delegate: Item {
                            required property var modelData
                            required property int index
                            visible: modelData.valor !== ""
                            width: colunaInfo.width; height: visible ? 42 : 0
                            Rectangle { visible: index > 0; anchors { left: parent.left; right: parent.right; leftMargin: 14 } height: 1; color: Tema.borda }
                            Text { anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter } text: modelData.titulo; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
                            Text {
                                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                                width: parent.width * 0.68
                                horizontalAlignment: Text.AlignRight
                                elide: Text.ElideMiddle
                                text: modelData.valor
                                color: modelData.link ? Tema.azulDuia : Tema.texto
                                font { family: Tema.fonteTexto; pixelSize: 13; underline: !!modelData.link && areaLink.containsMouse }
                                MouseArea { id: areaLink; enabled: !!modelData.link; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: loja.abrirSite(modelData.valor) }
                            }
                        }
                    }
                }
            }

            // Também pela outra fonte
            Text {
                visible: !!pa.app.alternativa
                width: parent.width
                wrapMode: Text.WordWrap
                text: "Também disponível pelo " + (pa.app.alternativa && pa.app.alternativa.fonte === "debian" ? "Debian" : "Flathub") + ". "
                      + "<a href=\"alt\">Ver essa versão</a>"
                textFormat: Text.StyledText
                linkColor: Tema.azulDuia
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 12 }
                onLinkActivated: loja.abrirApp(pa.app.alternativa.id)
            }
        }
    }

    // ============================================================ confirmação
    Rectangle {
        anchors.fill: parent
        visible: loja.confirmacao.titulo !== undefined
        color: Qt.rgba(0, 0, 0, 0.28)
        MouseArea { anchors.fill: parent; onClicked: loja.fecharConfirmacao() }
        Rectangle {
            id: folha
            anchors.centerIn: parent
            width: 420
            height: colunaFolha.implicitHeight + 40
            radius: Tema.raioGrande
            color: Tema.cartao
            border { color: Tema.borda; width: 1 }
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaFolha
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 14
                Row {
                    spacing: 14
                    IconeLoja { app: loja.confirmacao.app || ({}); tamanho: 52 }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 300
                        text: loja.confirmacao.titulo || ""
                        wrapMode: Text.WordWrap
                        color: Tema.texto
                        font { family: Tema.fonteTitulo; pixelSize: 17; weight: Font.Bold }
                    }
                }
                Row {
                    spacing: 10
                    Anel { visible: !loja.confirmacao.pronto && !loja.confirmacao.recusa; tamanho: 20; fracao: 0 }
                    Text {
                        width: 380 - (loja.confirmacao.pronto || loja.confirmacao.recusa ? 0 : 30)
                        text: loja.confirmacao.texto || ""
                        wrapMode: Text.WordWrap
                        color: loja.confirmacao.recusa ? Tema.erro : Tema.textoSecundario
                        font { family: Tema.fonteTexto; pixelSize: 13 }
                    }
                }
                Row {
                    anchors.right: parent.right
                    spacing: 10
                    Botao { texto: loja.confirmacao.recusa ? "Fechar" : "Cancelar"; onClicado: loja.fecharConfirmacao() }
                    Botao {
                        visible: !loja.confirmacao.recusa
                        ativo: !!loja.confirmacao.pronto
                        tipo: loja.confirmacao.acao === "remover" ? "perigo" : "primario"
                        texto: loja.confirmacao.botao || "Continuar"
                        onClicado: loja.confirmar()
                    }
                }
            }
        }
    }

    // ================================================================ aviso
    Rectangle {
        id: aviso
        property string texto: ""
        function mostrar(t) { texto = t; opacity = 1; esconder.restart() }
        anchors { horizontalCenter: conteudo.horizontalCenter; bottom: parent.bottom; bottomMargin: 24 }
        width: Math.min(textoAviso.implicitWidth + 36, conteudo.width - 48)
        height: 40; radius: 20
        color: Tema.escuro ? "#E6EAF0" : "#1F2933"
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 180 } }
        Text { id: textoAviso; anchors.centerIn: parent; width: parent.width - 36; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; text: aviso.texto; color: Tema.escuro ? "#1F2933" : "white"; font { family: Tema.fonteTexto; pixelSize: 13 } }
        Timer { id: esconder; interval: 4200; onTriggered: aviso.opacity = 0 }
    }

    Timer { interval: 1500; running: capturaArquivo !== "" && !loja.carregando; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
