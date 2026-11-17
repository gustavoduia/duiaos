// DuiaOS — Explorador de Arquivos.
// Barra lateral (Favoritos, Locais, Lixeira) · barra de ferramentas (voltar, avançar,
// caminho, nova pasta, ícones/lista, ordem, busca) · arquivos em ícones ou lista ·
// menu do clique direito · Informações · "Abrir com" · progresso de cópia.
import QtQuick
import QtQuick.Window
import DuiaOS

Window {
    id: janela
    width: 1040; height: 660
    minimumWidth: 640; minimumHeight: 400
    visible: true
    color: Tema.fundo
    title: explorador.titulo

    // ------------------------------------------------------------ seleção
    property var selecao: ({})                 // caminho → true
    property int atual: -1                     // item com o foco do teclado
    property string renomeando: ""
    property string filtro: ""                  // Aplicativos e Lixeira: filtro local
    readonly property var visiveis: {
        var lista = explorador.itens
        if (filtro === "" || (explorador.especial !== "aplicativos" && explorador.especial !== "lixeira")) return lista
        var f = filtro.toLowerCase()
        return lista.filter(function (i) { return i.nome.toLowerCase().indexOf(f) >= 0 })
    }
    function selecionados() {
        var lista = []
        for (var i = 0; i < visiveis.length; i++) if (selecao[visiveis[i].caminho]) lista.push(visiveis[i].caminho)
        return lista
    }
    // Quantos estão selecionados, sem percorrer a pasta inteira (a seleção só guarda os marcados)
    readonly property int numSelecionados: { var n = 0; for (var c in selecao) if (selecao[c]) n++; return n }
    function quantosSelecionados() { return numSelecionados }
    // Descompactar: todos os selecionados são arquivos compactados (.zip, .tar.gz, .7z, .rar…)
    function selecionadosCompactados() {
        var n = 0
        for (var i = 0; i < visiveis.length; i++) {
            if (!selecao[visiveis[i].caminho]) continue
            if (visiveis[i].compactado !== true) return []
            n++
        }
        return n > 0 ? selecionados() : []
    }
    function limpar() { selecao = ({}); atual = -1 }
    function escolher(indice, modificadores) {
        if (indice < 0 || indice >= visiveis.length) return
        var caminho = visiveis[indice].caminho
        var nova = Object.assign({}, selecao)
        if (modificadores & Qt.ControlModifier) {
            if (nova[caminho]) delete nova[caminho]; else nova[caminho] = true
        } else if ((modificadores & Qt.ShiftModifier) && atual >= 0) {
            nova = ({})
            var de = Math.min(atual, indice), ate = Math.max(atual, indice)
            for (var i = de; i <= ate; i++) nova[visiveis[i].caminho] = true
            selecao = nova
            return
        } else {
            nova = ({}); nova[caminho] = true
        }
        selecao = nova
        atual = indice
    }
    function selecionarTudo() {
        var nova = ({})
        for (var i = 0; i < visiveis.length; i++) nova[visiveis[i].caminho] = true
        selecao = nova
    }
    function abrirSelecionados() {
        var lista = selecionados()
        if (lista.length > 0) explorador.abrirItem(lista[0])
    }
    // ---------------------------------------------- menus na Barra de Recursos (ADR 059)
    // Montados aqui porque é o QML que sabe o que está selecionado; a Barra mostra e devolve o id.
    function it(id, rotulo, atalho, ativo, marcado) {
        return { id: id, rotulo: rotulo, tipo: marcado === undefined ? "item" : "marcavel", ativo: ativo !== false,
                 marcado: marcado === true, atalho: atalho || "", itens: [] }
    }
    function sub(id, rotulo, itens) { return { id: id, rotulo: rotulo, tipo: "submenu", ativo: true, marcado: false, atalho: "", itens: itens } }
    readonly property var sep: ({ id: -1, rotulo: "", tipo: "separador", ativo: false, marcado: false, atalho: "", itens: [] })
    function menusDoApp() {
        var n = janela.numSelecionados
        var normal = explorador.especial === ""
        var lixeira = explorador.especial === "lixeira"
        return [
            { rotulo: "Arquivo", itens: [
                it("nova-janela", "Nova janela"), it("nova-pasta", "Nova pasta", "Ctrl+Shift+N", normal), sep,
                it("abrir", "Abrir", "Enter", n > 0),
                it("descompactar", "Descompactar", "", janela.selecionadosCompactados().length > 0 && explorador.especial !== "lixeira"),
                it("terminal", "Abrir o terminal aqui", "", normal), sep,
                it("renomear", "Renomear", "F2", n === 1 && normal), it("informacoes", "Informações", "Ctrl+I", n > 0),
                it("lixeira", lixeira ? "Excluir para sempre" : "Mover para a Lixeira", "Delete", n > 0) ]
                .concat(lixeira ? [it("esvaziar", "Esvaziar a Lixeira")] : [])
                .concat([sep, it("fechar", "Fechar janela", "Ctrl+W")]) },
            { rotulo: "Editar", itens: [
                it("recortar", "Recortar", "Ctrl+X", n > 0 && normal), it("copiar", "Copiar", "Ctrl+C", n > 0),
                it("colar", "Colar", "Ctrl+V", explorador.podeColar && normal), sep,
                it("selecionar-tudo", "Selecionar tudo", "Ctrl+A"), it("copiar-caminho", "Copiar o caminho", "", n > 0), sep,
                it("buscar", "Buscar", "Ctrl+F") ] },
            { rotulo: "Exibir", itens: [
                it("icones", "Ícones", "Ctrl+1", true, explorador.visualizacao === "icones"),
                it("lista", "Lista", "Ctrl+2", true, explorador.visualizacao === "lista"), sep,
                sub("ordenar", "Ordenar por", [it("ordem:nome", "Nome", "", true, explorador.ordem === "nome"),
                                               it("ordem:data", "Data de modificação", "", true, explorador.ordem === "data"),
                                               it("ordem:tamanho", "Tamanho", "", true, explorador.ordem === "tamanho"),
                                               it("ordem:tipo", "Tipo", "", true, explorador.ordem === "tipo")]),
                it("ocultos", "Mostrar arquivos ocultos", "Ctrl+H", true, explorador.ocultos), sep,
                it("recarregar", "Recarregar", "F5") ] },
            { rotulo: "Ir", itens: [
                it("voltar", "Voltar", "Alt+Esquerda", explorador.podeVoltar), it("avancar", "Avançar", "Alt+Direita", explorador.podeAvancar),
                it("subir", "Pasta acima", "Alt+Cima", explorador.podeSubir), sep,
                it("ir:INICIO", "Início"), it("ir:DESKTOP", "Área de Trabalho"), it("ir:DOCUMENTS", "Documentos"),
                it("ir:DOWNLOAD", "Downloads"), it("ir:PICTURES", "Imagens"), it("ir:MUSIC", "Música"), it("ir:VIDEOS", "Vídeos"), sep,
                it("ir:aplicativos", "Aplicativos"), it("ir:lixeira", "Lixeira"), sep, it("ir-para", "Ir para…", "Ctrl+L") ] }
        ]
    }
    // Os menus da Barra são remontados um instante depois da última mudança (seleção, pasta, opções),
    // e não a cada uma: durante o retângulo de seleção a seleção muda a cada movimento do mouse.
    Timer { id: atualizarMenus; interval: 120; onTriggered: menuDoApp.definirMenus(janela.menusDoApp()) }
    onSelecaoChanged: atualizarMenus.restart()
    Connections { target: explorador; function onMudou() { atualizarMenus.restart() } }
    Component.onCompleted: menuDoApp.definirMenus(menusDoApp())
    Connections {
        target: menuDoApp
        function onAcionado(id) {
            var s = janela.selecionados()
            if (id.indexOf("ordem:") === 0) explorador.definirOrdem(id.slice(6))
            else if (id.indexOf("ir:") === 0) explorador.irParaPasta(id.slice(3))
            else switch (id) {
            case "nova-janela": explorador.novaJanela(); break
            case "nova-pasta": explorador.novaPasta(); break
            case "abrir": janela.abrirSelecionados(); break
            case "descompactar": explorador.descompactar(janela.selecionadosCompactados()); break
            case "terminal": explorador.abrirTerminalAqui(); break
            case "renomear": if (s.length === 1) janela.renomeando = s[0]; break
            case "informacoes": if (s.length > 0) dialogo.abrir("informacoes", s); break
            case "lixeira": janela.apagar(false); break
            case "esvaziar": dialogo.abrir("esvaziar", []); break
            case "fechar": Qt.quit(); break
            case "recortar": explorador.recortar(s); break
            case "copiar": explorador.copiar(s); break
            case "colar": explorador.colar(); break
            case "selecionar-tudo": janela.selecionarTudo(); break
            case "copiar-caminho": explorador.copiarCaminho(s); break
            case "buscar": campoBusca.entrada.forceActiveFocus(); break
            case "icones": explorador.definirVisualizacao("icones"); break
            case "lista": explorador.definirVisualizacao("lista"); break
            case "ocultos": explorador.alternarOcultos(); break
            case "recarregar": explorador.recarregar(); break
            case "voltar": explorador.voltar(); break
            case "avancar": explorador.avancar(); break
            case "subir": explorador.subir(); break
            case "ir-para": barraCaminho.editar(); break
            }
        }
    }

    function apagar(permanente) {
        var lista = selecionados()
        if (lista.length === 0) return
        if (explorador.especial === "lixeira" || permanente) dialogo.abrir("excluir", lista)
        else explorador.moverParaLixeira(lista)
        limpar()
    }

    Connections {
        target: explorador
        function onItensMudaram() {
            var nova = ({})
            var existe = ({})
            for (var i = 0; i < explorador.itens.length; i++) existe[explorador.itens[i].caminho] = true
            for (var c in janela.selecao) if (existe[c]) nova[c] = true
            janela.selecao = nova
            if (janela.atual >= janela.visiveis.length) janela.atual = janela.visiveis.length - 1
        }
        function onMudou() { }
        function onAviso(mensagem) { aviso.mostrar(mensagem) }
        function onRenomearNovo(caminho) {
            var nova = ({}); nova[caminho] = true
            janela.selecao = nova
            janela.renomeando = caminho
        }
        function onDestacar(caminho) {
            var nova = ({}); nova[caminho] = true
            janela.selecao = nova
            for (var i = 0; i < janela.visiveis.length; i++) {
                if (janela.visiveis[i].caminho !== caminho) continue
                janela.atual = i
                if (explorador.visualizacao === "icones") grade.positionViewAtIndex(i, GridView.Contain)
                else lista.positionViewAtIndex(i, ListView.Contain)
            }
        }
    }
    onVisiveisChanged: if (atual >= visiveis.length) atual = -1
    // Pasta aberta. O "local" do Python avisa pelo mesmo sinal de tudo (mudou), que também vem a cada
    // recarga da pasta; esta cópia só muda quando a pasta muda de verdade. Antes, cada recarga (um
    // arquivo novo na pasta, o fim de uma cópia) limpava a seleção e o filtro da busca.
    readonly property string pastaAberta: explorador.local
    onPastaAbertaChanged: limpar()

    // ------------------------------------------------------------ teclado
    Item {
        id: teclado
        anchors.fill: parent
        focus: true
        Keys.onPressed: (e) => {
            var ctrl = e.modifiers & Qt.ControlModifier
            var alt = e.modifiers & Qt.AltModifier
            if (janela.renomeando !== "") return
            if (e.key === Qt.Key_Escape) { menu.fechar(); dialogo.fechar(); janela.limpar() }
            else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) janela.abrirSelecionados()
            else if (e.key === Qt.Key_Delete) janela.apagar(e.modifiers & Qt.ShiftModifier)
            else if (e.key === Qt.Key_F2) { var s = janela.selecionados(); if (s.length === 1 && explorador.especial === "") janela.renomeando = s[0] }
            else if (e.key === Qt.Key_F5) explorador.recarregar()
            else if (ctrl && e.key === Qt.Key_W) Qt.quit()
            else if (ctrl && e.key === Qt.Key_A) janela.selecionarTudo()
            else if (ctrl && e.key === Qt.Key_C) explorador.copiar(janela.selecionados())
            else if (ctrl && e.key === Qt.Key_X) explorador.recortar(janela.selecionados())
            else if (ctrl && e.key === Qt.Key_V) explorador.colar()
            else if (ctrl && e.key === Qt.Key_H) explorador.alternarOcultos()
            else if (ctrl && e.key === Qt.Key_F) campoBusca.entrada.forceActiveFocus()
            else if (ctrl && e.key === Qt.Key_L) barraCaminho.editar()
            else if (ctrl && e.key === Qt.Key_1) explorador.definirVisualizacao("icones")
            else if (ctrl && e.key === Qt.Key_2) explorador.definirVisualizacao("lista")
            else if (ctrl && (e.modifiers & Qt.ShiftModifier) && e.key === Qt.Key_N) explorador.novaPasta()
            else if (ctrl && e.key === Qt.Key_I) { var l = janela.selecionados(); if (l.length > 0) dialogo.abrir("informacoes", l) }
            else if (e.key === Qt.Key_Backspace || (alt && e.key === Qt.Key_Left)) explorador.voltar()
            else if (alt && e.key === Qt.Key_Right) explorador.avancar()
            else if (alt && e.key === Qt.Key_Up) explorador.subir()
            else if (e.key === Qt.Key_Right || e.key === Qt.Key_Left || e.key === Qt.Key_Up || e.key === Qt.Key_Down) {
                var passo = 1
                if (e.key === Qt.Key_Up || e.key === Qt.Key_Down) passo = explorador.visualizacao === "icones" ? grade.colunas : 1
                if (e.key === Qt.Key_Left || e.key === Qt.Key_Up) passo = -passo
                if (explorador.visualizacao === "lista" && (e.key === Qt.Key_Left || e.key === Qt.Key_Right)) return
                janela.escolher(Math.max(0, Math.min(janela.visiveis.length - 1, janela.atual + passo)), e.modifiers & Qt.ShiftModifier)
                if (explorador.visualizacao === "icones") grade.positionViewAtIndex(janela.atual, GridView.Contain)
                else lista.positionViewAtIndex(janela.atual, ListView.Contain)
            } else return
            e.accepted = true
        }
    }

    // ======================================================== barra lateral
    Rectangle {
        id: lateral
        width: 214
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        color: Tema.lateral
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Tema.borda }

        component ItemLateral: Rectangle {
            id: il
            property string nome: ""
            property string icone: "pasta"
            property string destino: ""
            property bool marcado: explorador.local === destino
            property bool ejetavel: false
            signal clicado()
            signal ejetar()
            width: parent ? parent.width : 200
            height: 30
            radius: 7
            color: marcado ? Tema.selecao : (areaIl.containsMouse ? Tema.realce : "transparent")
            Icone { id: icIl; anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter } nome: il.icone; tamanho: 17; cor: Tema.azulDuia }
            Text {
                anchors { left: icIl.right; leftMargin: 9; right: parent.right; rightMargin: il.ejetavel ? 30 : 8; verticalCenter: parent.verticalCenter }
                text: il.nome; elide: Text.ElideRight
                color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: il.marcado ? Font.DemiBold : Font.Normal }
            }
            MouseArea { id: areaIl; anchors.fill: parent; hoverEnabled: true; onClicked: il.destino !== "" ? explorador.abrir(il.destino) : il.clicado() }
            BotaoIcone { visible: il.ejetavel; anchors { right: parent.right; rightMargin: 3; verticalCenter: parent.verticalCenter }
                         width: 24; height: 24; icone: "ejetar"; tamanhoIcone: 13; corIcone: Tema.textoSecundario; onClicado: il.ejetar() }
            DropArea {
                anchors.fill: parent
                enabled: il.destino !== "" && il.destino.indexOf(":") < 0
                onDropped: (d) => { if (d.hasUrls) explorador.soltar(d.urls, il.destino) }
                Rectangle { anchors.fill: parent; radius: 7; color: "transparent"; border { color: Tema.azulDuia; width: parent.containsDrag ? 2 : 0 } }
            }
        }
        component Secao: Text {
            width: parent.width
            leftPadding: 10; topPadding: 12; bottomPadding: 4
            color: Tema.textoApagado
            font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold }
        }

        Flickable {
            anchors { fill: parent; margins: 8; topMargin: 12 }
            contentHeight: colunaLateral.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: colunaLateral
                width: parent.width
                Secao { text: "Favoritos"; topPadding: 0 }
                Repeater { model: explorador.favoritos; ItemLateral { required property var modelData; nome: modelData.nome; icone: modelData.icone; destino: modelData.caminho } }
                ItemLateral { nome: "Aplicativos"; icone: "aplicativos"; destino: "aplicativos:" }
                Secao { text: "Locais" }
                ItemLateral { nome: "Computador"; icone: "computador"; destino: "/" }
                Repeater {
                    model: explorador.discos
                    ItemLateral {
                        required property var modelData
                        nome: modelData.nome; icone: "disco"
                        destino: ""
                        marcado: modelData.montado && explorador.local.indexOf(modelData.caminho) === 0
                        ejetavel: modelData.montado && modelData.removivel
                        onClicado: explorador.abrirDisco(modelData.dispositivo)
                        onEjetar: explorador.ejetar(modelData.dispositivo)
                    }
                }
                Item { width: 1; height: 8 }
                ItemLateral { nome: "Lixeira"; icone: explorador.lixeiraCheia ? "lixeira-cheia" : "lixeira"; destino: "lixeira:" }
            }
        }
    }

    // ===================================================== barra de ferramentas
    Rectangle {
        id: ferramentas
        anchors { left: lateral.right; right: parent.right; top: parent.top }
        height: 52
        color: Tema.fundo
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda }

        Row {
            id: navegacao
            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
            spacing: 2
            BotaoIcone { icone: "seta-esquerda"; ativo: explorador.podeVoltar; dica: "Voltar"; onClicado: explorador.voltar() }
            BotaoIcone { icone: "seta-direita"; ativo: explorador.podeAvancar; dica: "Avançar"; onClicado: explorador.avancar() }
        }

        // Caminho: botões de cada pasta; Ctrl+L (ou clique no espaço vazio) vira campo de texto
        Item {
            id: barraCaminho
            anchors { left: navegacao.right; leftMargin: 10; right: acoes.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
            height: 30
            property bool editando: false
            function editar() { editando = true; campoCaminho.texto = explorador.especial === "" ? explorador.local : explorador.titulo; campoCaminho.entrada.selectAll(); campoCaminho.entrada.forceActiveFocus() }
            MouseArea { anchors.fill: parent; onDoubleClicked: barraCaminho.editar() }
            Flickable {
                id: rolarTrilha
                visible: !barraCaminho.editando
                anchors.fill: parent
                contentWidth: trilha.width
                clip: true
                interactive: contentWidth > width
                onContentWidthChanged: contentX = Math.max(0, contentWidth - width)
                Row {
                    id: trilha
                    height: parent.height
                    Repeater {
                        model: explorador.trilha
                        Row {
                            required property var modelData
                            required property int index
                            height: 30
                            Icone { visible: index > 0; nome: "seta-direita"; tamanho: 12; cor: Tema.textoApagado; anchors.verticalCenter: parent.verticalCenter }
                            Rectangle {
                                height: 26; anchors.verticalCenter: parent.verticalCenter
                                width: textoTrilha.implicitWidth + 14; radius: 6
                                color: areaTrilha.containsMouse ? Tema.realce : "transparent"
                                Text {
                                    id: textoTrilha
                                    anchors.centerIn: parent
                                    text: modelData.nome
                                    color: index === explorador.trilha.length - 1 ? Tema.texto : Tema.textoSecundario
                                    font { family: Tema.fonteTexto; pixelSize: index === explorador.trilha.length - 1 ? 15 : 13
                                           weight: index === explorador.trilha.length - 1 ? Font.Bold : Font.Normal }
                                }
                                MouseArea { id: areaTrilha; anchors.fill: parent; hoverEnabled: true; onClicked: explorador.abrir(modelData.caminho) }
                                DropArea {
                                    anchors.fill: parent
                                    enabled: modelData.caminho.indexOf(":") < 0
                                    onDropped: (d) => { if (d.hasUrls) explorador.soltar(d.urls, modelData.caminho) }
                                }
                            }
                        }
                    }
                }
            }
            Campo {
                id: campoCaminho
                visible: barraCaminho.editando
                anchors.fill: parent
                onConfirmado: { explorador.irPara(texto); barraCaminho.editando = false; teclado.forceActiveFocus() }
                entrada.onActiveFocusChanged: if (!entrada.activeFocus) barraCaminho.editando = false
                entrada.Keys.onEscapePressed: { barraCaminho.editando = false; teclado.forceActiveFocus() }
            }
        }

        Row {
            id: acoes
            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
            spacing: 4
            Botao {
                visible: explorador.especial === "lixeira"
                texto: "Esvaziar"
                tipo: "perigo"
                ativo: explorador.itens.length > 0
                anchors.verticalCenter: parent.verticalCenter
                onClicado: dialogo.abrir("esvaziar", [])
            }
            BotaoIcone { icone: "nova-pasta"; dica: "Nova pasta"; ativo: explorador.especial === ""; anchors.verticalCenter: parent.verticalCenter
                         onClicado: explorador.novaPasta() }
            Rectangle {
                width: 64; height: 30; radius: 8
                anchors.verticalCenter: parent.verticalCenter
                color: Tema.controleDesligado
                Row {
                    anchors.centerIn: parent
                    BotaoIcone { width: 30; height: 26; icone: "aplicativos"; tamanhoIcone: 15; dica: "Ícones"; marcado: explorador.visualizacao === "icones"
                                 color: marcado ? Tema.cartao : "transparent"; onClicado: explorador.definirVisualizacao("icones") }
                    BotaoIcone { width: 30; height: 26; icone: "lista"; tamanhoIcone: 15; dica: "Lista"; marcado: explorador.visualizacao === "lista"
                                 color: marcado ? Tema.cartao : "transparent"; onClicado: explorador.definirVisualizacao("lista") }
                }
            }
            BotaoIcone {
                id: botaoMais
                icone: "controles"; dica: "Ordenar e mostrar"
                anchors.verticalCenter: parent.verticalCenter
                onClicado: {
                    var p = botaoMais.mapToItem(null, 0, botaoMais.height + 4)
                    menu.abrir("opcoes", p.x - 150, p.y)
                }
            }
            Campo {
                id: campoBusca
                width: 200
                anchors.verticalCenter: parent.verticalCenter
                icone: "busca"
                dica: explorador.especial === "aplicativos" ? "Buscar aplicativos" : (explorador.especial === "lixeira" ? "Buscar na Lixeira" : "Buscar nesta pasta")
                entrada.onTextChanged: buscaAtrasada.restart()
                entrada.Keys.onEscapePressed: { texto = ""; teclado.forceActiveFocus() }
                Timer {
                    id: buscaAtrasada
                    interval: 350
                    onTriggered: {
                        if (explorador.especial === "aplicativos" || explorador.especial === "lixeira") janela.filtro = campoBusca.texto
                        else explorador.buscar(campoBusca.texto)
                    }
                }
                Connections {
                    target: janela
                    function onPastaAbertaChanged() {
                        if (explorador.especial !== "busca" && campoBusca.texto !== "" && !campoBusca.entrada.activeFocus) campoBusca.texto = ""
                        janela.filtro = ""
                    }
                }
            }
        }
    }

    // ========================================================== conteúdo
    Item {
        id: area
        anchors { left: lateral.right; right: parent.right; top: ferramentas.bottom; bottom: rodape.top }
        clip: true
        Rectangle { anchors.fill: parent; color: Tema.cartao }

        // Espaço vazio: clique limpa a seleção; clique direito abre o menu da pasta; segurar o botão
        // esquerdo e arrastar desenha o retângulo de seleção (Ctrl inverte, Shift soma), rolando a
        // vista quando o ponteiro chega perto da borda. A roda do mouse rola a vista daqui também:
        // as vistas não são "interactive" para o arraste não virar rolagem (como num celular).
        MouseArea {
            id: fundoArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            preventStealing: true
            property bool arrastando: false
            property point inicio: Qt.point(0, 0)      // onde começou, nas coordenadas do conteúdo da vista
            property point ponteiro: Qt.point(0, 0)    // onde está, nas coordenadas desta área
            property var base: ({})
            property int modo: 0                       // 0 substitui, 1 soma (Shift), 2 inverte (Ctrl)
            readonly property real bordaRolagem: 28

            function vista() { return explorador.visualizacao === "icones" ? grade : lista }
            property string assinatura: ""             // faixa de linhas/colunas já aplicada à seleção
            property bool pendente: false

            // Linhas e colunas que o retângulo toca, por conta (sem percorrer os itens: numa pasta com
            // milhares de arquivos o custo é o mesmo). Na grade, o desenho de cada item ocupa 92 px no meio
            // da célula; na lista, a linha inteira (30 px).
            function faixaDeItens(x1, y1, x2, y2) {
                var n = janela.visiveis.length
                if (explorador.visualizacao === "icones") {
                    var cw = grade.cellWidth, ch = grade.cellHeight, cols = grade.colunas
                    var c1 = Math.max(0, Math.ceil((x1 - (cw + 92) / 2) / cw))
                    var c2 = Math.min(cols - 1, Math.floor((x2 - (cw - 92) / 2) / cw))
                    var l1 = Math.max(0, Math.ceil((y1 - ch + 6) / ch))
                    var l2 = Math.min(Math.ceil(n / cols) - 1, Math.floor((y2 - 2) / ch))
                    return { c1: c1, c2: c2, l1: l1, l2: l2, cols: cols }
                }
                return { c1: 0, c2: 0, l1: Math.max(0, Math.ceil((y1 - 30) / 30)), l2: Math.min(n - 1, Math.floor(y2 / 30)), cols: 1 }
            }
            function atualizar() {
                pendente = false
                var v = vista()
                var agora = mapToItem(v.contentItem, ponteiro.x, ponteiro.y)
                var x1 = Math.min(inicio.x, agora.x), y1 = Math.min(inicio.y, agora.y)
                var x2 = Math.max(inicio.x, agora.x), y2 = Math.max(inicio.y, agora.y)
                // O retângulo desenhado acompanha o mouse sempre (é barato)
                var a = v.contentItem.mapToItem(fundoArea, x1, y1)
                var b = v.contentItem.mapToItem(fundoArea, x2, y2)
                var topo = v.mapToItem(fundoArea, 0, 0).y
                var ya = Math.max(a.y, topo), yb = Math.min(b.y, topo + v.height)
                faixa.x = a.x; faixa.width = b.x - a.x
                faixa.y = ya; faixa.height = Math.max(0, yb - ya)
                // A seleção só muda quando o retângulo passa a tocar outros itens
                var f = faixaDeItens(x1, y1, x2, y2)
                var chave = f.c1 + "," + f.c2 + "," + f.l1 + "," + f.l2 + "," + f.cols
                if (chave === assinatura) return
                assinatura = chave
                var nova = modo === 0 ? ({}) : Object.assign({}, base)
                var ultimo = -1
                for (var l = f.l1; l <= f.l2; l++) {
                    for (var c = f.c1; c <= f.c2; c++) {
                        var i = l * f.cols + c
                        if (i >= janela.visiveis.length) break
                        var caminho = janela.visiveis[i].caminho
                        if (modo === 2 && base[caminho]) delete nova[caminho]; else nova[caminho] = true
                        ultimo = i
                    }
                }
                janela.selecao = nova
                if (ultimo >= 0) janela.atual = ultimo
            }
            function rolar(dy) {
                var v = vista()
                var maximo = v.originY + Math.max(0, v.contentHeight - v.height)
                var antes = v.contentY
                v.contentY = Math.max(v.originY, Math.min(maximo, v.contentY + dy))
                return v.contentY !== antes
            }

            onPressed: (m) => {
                teclado.forceActiveFocus()
                arrastando = false
                ponteiro = Qt.point(m.x, m.y)
                inicio = mapToItem(vista().contentItem, m.x, m.y)
                modo = (m.modifiers & Qt.ControlModifier) ? 2 : ((m.modifiers & Qt.ShiftModifier) ? 1 : 0)
                base = Object.assign({}, janela.selecao)
                assinatura = ""
                if (m.button === Qt.LeftButton && modo === 0) janela.limpar()
            }
            onPositionChanged: (m) => {
                if (!(m.buttons & Qt.LeftButton) || janela.visiveis.length === 0) return
                ponteiro = Qt.point(m.x, m.y)
                if (!arrastando) {
                    var c = mapToItem(vista().contentItem, m.x, m.y)
                    if (Math.abs(c.x - inicio.x) < 5 && Math.abs(c.y - inicio.y) < 5) return
                    arrastando = true
                    atualizar()
                    return
                }
                // Mouses rápidos mandam centenas de movimentos por segundo: o retângulo é refeito no máximo
                // uma vez por quadro da tela (o Timer abaixo), com a última posição
                pendente = true
            }
            onReleased: (m) => {
                if (arrastando) { if (pendente) atualizar(); arrastando = false; return }
                if (m.button === Qt.RightButton) {
                    janela.limpar()
                    var p = mapToItem(null, m.x, m.y)
                    menu.abrir("fundo", p.x, p.y)
                }
            }
            onCanceled: arrastando = false
            onWheel: (w) => {
                var dy = w.pixelDelta.y !== 0 ? -w.pixelDelta.y : -w.angleDelta.y / 120 * 96
                rolar(dy)
                if (arrastando) atualizar()
            }
            Timer {
                // Um quadro da tela (~60 por segundo): aplica o último movimento do mouse e, se o retângulo
                // encosta na borda de cima ou de baixo, rola a vista
                interval: 16
                repeat: true
                running: fundoArea.arrastando
                onTriggered: {
                    if (fundoArea.pendente) fundoArea.atualizar()
                    var v = fundoArea.vista()
                    var topo = v.mapToItem(fundoArea, 0, 0).y
                    var y = fundoArea.ponteiro.y
                    var passo = 0
                    if (y < topo + fundoArea.bordaRolagem) passo = -Math.min(40, (topo + fundoArea.bordaRolagem - y) / 2 + 4)
                    else if (y > topo + v.height - fundoArea.bordaRolagem) passo = Math.min(40, (y - topo - v.height + fundoArea.bordaRolagem) / 2 + 4)
                    if (passo !== 0 && fundoArea.rolar(passo * 0.55)) fundoArea.atualizar()
                }
            }
        }
        DropArea {
            anchors.fill: parent
            enabled: explorador.especial === ""
            onDropped: (d) => { if (d.hasUrls && d.source === null) explorador.soltar(d.urls, "") }
        }

        // Cada arquivo (ícones e lista usam a mesma lógica de clique e arraste)
        component Toque: MouseArea {
            id: toque
            required property var item
            required property int indice
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true
            drag.target: fantasma
            drag.threshold: 8
            onPressed: (m) => {
                teclado.forceActiveFocus()
                if (m.button === Qt.RightButton) {
                    if (!janela.selecao[item.caminho]) janela.escolher(indice, 0)
                } else if (!janela.selecao[item.caminho] || (m.modifiers & (Qt.ControlModifier | Qt.ShiftModifier))) {
                    janela.escolher(indice, m.modifiers)
                } else janela.atual = indice
            }
            onClicked: (m) => {
                if (m.button === Qt.RightButton) { var p = mapToItem(null, m.x, m.y); menu.abrir("item", p.x, p.y) }
                else if (!(m.modifiers & (Qt.ControlModifier | Qt.ShiftModifier)) && janela.quantosSelecionados() > 1) janela.escolher(indice, 0)
            }
            onDoubleClicked: (m) => { if (m.button === Qt.LeftButton) explorador.abrirItem(item.caminho) }
            Item {
                id: fantasma
                Drag.active: toque.drag.active
                Drag.dragType: Drag.Automatic
                Drag.supportedActions: Qt.CopyAction | Qt.MoveAction
                // Só monta a lista quando o arraste começa: antes, cada item visível percorria a pasta inteira a
                // cada mudança da seleção (o retângulo de seleção travava em pastas grandes)
                Drag.mimeData: toque.drag.active ? ({ "text/uri-list": janela.selecionados().map(function (c) { return "file://" + encodeURI(c) }).join("\r\n") }) : ({})
                Drag.hotSpot: Qt.point(0, 0)
            }
        }

        component AlvoDePasta: DropArea {
            required property var item
            enabled: item.pasta && explorador.especial === ""
            onDropped: (d) => { if (d.hasUrls) { explorador.soltar(d.urls, item.caminho); d.acceptProposedAction() } }
        }

        // Campo para renomear (no lugar do nome)
        component CampoRenomear: Rectangle {
            id: cr
            required property var item
            property bool centro: true
            visible: janela.renomeando === item.caminho
            height: 24
            radius: 5
            color: Tema.cartao
            border { color: Tema.azulDuia; width: 2 }
            z: 5
            TextInput {
                id: entradaRenomear
                anchors { fill: parent; leftMargin: 5; rightMargin: 5 }
                verticalAlignment: TextInput.AlignVCenter
                horizontalAlignment: cr.centro ? TextInput.AlignHCenter : TextInput.AlignLeft
                font { family: Tema.fonteTexto; pixelSize: 12 }
                color: Tema.texto
                selectionColor: Tema.azulDuia
                clip: true
                property bool feito: false
                onVisibleChanged: {
                    if (visible) {
                        feito = false
                        text = cr.item.nome
                        var ponto = cr.item.pasta ? -1 : text.lastIndexOf(".")
                        select(0, ponto > 0 ? ponto : text.length)
                        forceActiveFocus()
                    }
                }
                function concluir(salvar) {
                    if (feito) return
                    feito = true
                    if (salvar && text !== cr.item.nome) explorador.renomear(cr.item.caminho, text)
                    janela.renomeando = ""
                    teclado.forceActiveFocus()
                }
                Keys.onReturnPressed: concluir(true)
                Keys.onEnterPressed: concluir(true)
                Keys.onEscapePressed: concluir(false)
                onActiveFocusChanged: if (!activeFocus && visible) concluir(true)
            }
        }

        // ------------------------------------------------------- ícones
        GridView {
            id: grade
            visible: explorador.visualizacao === "icones"
            anchors { fill: parent; margins: 12 }
            readonly property int colunas: Math.max(1, Math.floor(width / 112))
            cellWidth: Math.floor(width / colunas)
            cellHeight: 118
            model: janela.visiveis
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: false              // arrastar no vazio seleciona (fundoArea); a roda rola por lá
            delegate: Item {
                id: celula
                required property var modelData
                required property int index
                width: grade.cellWidth; height: grade.cellHeight
                readonly property bool sel: janela.selecao[modelData.caminho] === true
                readonly property bool recortado: explorador.recortados.indexOf(modelData.caminho) >= 0
                Rectangle {
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 2 }
                    width: 76; height: 70; radius: 10
                    color: celula.sel ? Tema.pressionado : (toqueGrade.containsMouse ? Tema.realce : "transparent")
                }
                Item {
                    id: figura
                    width: 58; height: 58
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 8 }
                    opacity: celula.recortado || modelData.oculto ? 0.5 : 1
                    Image {
                        id: mini
                        anchors.fill: parent
                        source: modelData.miniatura
                        sourceSize: Qt.size(128, 128)
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        visible: status === Image.Ready
                    }
                    IconeApp { anchors.fill: parent; visible: modelData.app === true; icone: modelData.iconeApp || ""; nome: modelData.nome; tamanho: 58 }
                    Icone {
                        anchors.centerIn: parent
                        visible: !mini.visible && modelData.app !== true && modelData.pasta
                        nome: "pasta-cheia"; tamanho: 62; cor: "#4A82EE"
                    }
                    Ladrilho {
                        anchors.centerIn: parent
                        visible: !mini.visible && modelData.app !== true && !modelData.pasta
                        width: 44; height: 54; radius: 8
                        icone: modelData.icone; estilo: "claro"; tamanho: 46
                    }
                }
                Rectangle {
                    anchors { horizontalCenter: parent.horizontalCenter; top: figura.bottom; topMargin: 6 }
                    width: Math.min(nomeGrade.implicitWidth + 10, parent.width - 8)
                    height: nomeGrade.height + 4
                    radius: 5
                    color: celula.sel ? Tema.azulDuia : "transparent"
                    visible: janela.renomeando !== modelData.caminho
                    Text {
                        id: nomeGrade
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, celula.width - 18)
                        text: modelData.nome
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        maximumLineCount: celula.sel ? 3 : 2
                        elide: Text.ElideMiddle
                        color: celula.sel ? "white" : Tema.texto
                        font { family: Tema.fonteTexto; pixelSize: 12 }
                    }
                }
                CampoRenomear { item: modelData; anchors { horizontalCenter: parent.horizontalCenter; top: figura.bottom; topMargin: 5 } width: parent.width - 8 }
                // Só o desenho do item (ícone e nome): o espaço entre os ícones começa o retângulo de seleção
                Toque { id: toqueGrade; width: Math.min(parent.width, 92); height: parent.height - 6
                        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 2 }
                        item: modelData; indice: index; enabled: janela.renomeando !== modelData.caminho }
                AlvoDePasta { anchors.fill: toqueGrade; item: modelData }
            }
        }

        // -------------------------------------------------------- lista
        Item {
            visible: explorador.visualizacao === "lista"
            anchors.fill: parent
            readonly property var larguras: [0.46, 0.22, 0.12, 0.20]
            Row {
                id: cabecalhoLista
                x: 12; width: parent.width - 24; height: 30
                Repeater {
                    model: [["Nome", "nome"], [explorador.especial === "lixeira" ? "Excluído em" : "Modificado", "data"], ["Tamanho", "tamanho"], ["Tipo", "tipo"]]
                    Item {
                        required property var modelData
                        required property int index
                        width: cabecalhoLista.width * cabecalhoLista.parent.larguras[index]; height: 30
                        Text {
                            anchors { left: parent.left; leftMargin: index === 0 ? 34 : 6; verticalCenter: parent.verticalCenter }
                            text: modelData[0] + (explorador.ordem === modelData[1] && explorador.especial === "" ? "  ▾" : "")
                            color: explorador.ordem === modelData[1] ? Tema.texto : Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
                        }
                        MouseArea { anchors.fill: parent; enabled: explorador.especial === ""; onClicked: explorador.definirOrdem(modelData[1]) }
                    }
                }
            }
            Rectangle { anchors { left: parent.left; right: parent.right; top: cabecalhoLista.bottom } height: 1; color: Tema.borda }
            ListView {
                id: lista
                anchors { left: parent.left; right: parent.right; top: cabecalhoLista.bottom; bottom: parent.bottom; leftMargin: 8; rightMargin: 8; topMargin: 4 }
                model: janela.visiveis
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                interactive: false          // arrastar abaixo das linhas seleciona (fundoArea)
                delegate: Rectangle {
                    id: linhaLista
                    required property var modelData
                    required property int index
                    readonly property bool sel: janela.selecao[modelData.caminho] === true
                    width: lista.width; height: 30
                    radius: 6
                    color: sel ? Tema.azulDuia : (index % 2 ? Tema.listra : "transparent")
                    readonly property color corTexto: sel ? "white" : Tema.texto
                    readonly property color corSecundaria: sel ? "#DDE7FB" : Tema.textoSecundario
                    Row {
                        x: 4; height: parent.height
                        Item {
                            width: (lista.width - 8) * 0.46; height: parent.height
                            Item {
                                id: iconeLinha
                                width: 20; height: 20
                                anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
                                IconeApp { anchors.fill: parent; visible: modelData.app === true; icone: modelData.iconeApp || ""; nome: modelData.nome; tamanho: 20 }
                                Icone { anchors.centerIn: parent; visible: modelData.app !== true; nome: modelData.icone; tamanho: 18
                                        cor: linhaLista.sel ? "white" : (modelData.pasta ? "#5B8FEF" : Tema.textoSecundario) }
                            }
                            Text {
                                anchors { left: iconeLinha.right; leftMargin: 10; right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                                visible: janela.renomeando !== modelData.caminho
                                text: modelData.nome; elide: Text.ElideMiddle
                                opacity: modelData.oculto ? 0.6 : 1
                                color: linhaLista.corTexto; font { family: Tema.fonteTexto; pixelSize: 13 }
                            }
                            CampoRenomear { item: modelData; centro: false; anchors { left: iconeLinha.right; leftMargin: 6; right: parent.right; verticalCenter: parent.verticalCenter } }
                        }
                        Text { width: (lista.width - 8) * 0.22; anchors.verticalCenter: parent.verticalCenter; leftPadding: 6; elide: Text.ElideRight
                               text: explorador.especial === "lixeira" ? (modelData.excluidoTexto || "") : modelData.modificadoTexto
                               color: linhaLista.corSecundaria; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        Text { width: (lista.width - 8) * 0.12; anchors.verticalCenter: parent.verticalCenter; leftPadding: 6
                               text: modelData.tamanhoTexto; color: linhaLista.corSecundaria; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        Text { width: (lista.width - 8) * 0.20; anchors.verticalCenter: parent.verticalCenter; leftPadding: 6; elide: Text.ElideRight
                               text: modelData.tipo; color: linhaLista.corSecundaria; font { family: Tema.fonteTexto; pixelSize: 12 } }
                    }
                    Toque { anchors.fill: parent; item: modelData; indice: index; enabled: janela.renomeando !== modelData.caminho }
                    AlvoDePasta { anchors.fill: parent; item: modelData }
                }
            }
        }

        // Retângulo de seleção (desenhado por fundoArea)
        Rectangle {
            id: faixa
            visible: fundoArea.arrastando && width > 0 && height > 0
            z: 10
            radius: 3
            color: Qt.rgba(Tema.azulDuia.r, Tema.azulDuia.g, Tema.azulDuia.b, 0.16)
            border { color: Tema.azulDuia; width: 1 }
        }

        // Pasta vazia, erro ou buscando
        Column {
            anchors.centerIn: parent
            spacing: 10
            visible: janela.visiveis.length === 0
            Icone {
                anchors.horizontalCenter: parent.horizontalCenter
                nome: explorador.erro !== "" ? "cadeado" : (explorador.especial === "lixeira" ? "lixeira" : (explorador.especial === "busca" ? "busca" : "pasta"))
                tamanho: 48; cor: Tema.bordaForte
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: explorador.erro !== "" ? explorador.erro
                      : (explorador.buscando ? "Buscando…"
                      : (explorador.especial === "busca" ? "Nada encontrado." : (explorador.especial === "lixeira" ? "A Lixeira está vazia." : "Esta pasta está vazia.")))
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 14 }
            }
        }
    }

    // ============================================================ rodapé
    Rectangle {
        id: rodape
        anchors { left: lateral.right; right: parent.right; bottom: parent.bottom }
        height: 28
        color: Tema.fundo
        Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: 1; color: Tema.borda }
        Text {
            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
            text: (janela.quantosSelecionados() > 0 ? janela.quantosSelecionados() + " de " : "") + explorador.status
                  + (explorador.especial === "busca" && explorador.buscando ? " · buscando…" : "")
            color: Tema.textoSecundario
            font { family: Tema.fonteTexto; pixelSize: 12 }
        }
        Row {
            visible: explorador.tarefa.ativa
            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
            spacing: 8
            Text { anchors.verticalCenter: parent.verticalCenter; text: explorador.tarefa.titulo; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 140; height: 6; radius: 3; color: Tema.controleDesligado
                Rectangle { width: parent.width * explorador.tarefa.progresso; height: parent.height; radius: 3; color: Tema.azulDuia }
            }
            BotaoIcone { width: 22; height: 22; icone: "fechar"; tamanhoIcone: 12; dica: "Cancelar"; onClicado: explorador.cancelarTarefa() }
        }
    }

    // ======================================================== menu de contexto
    Item {
        id: menu
        anchors.fill: parent
        visible: tipoMenu !== ""
        z: 50
        property string tipoMenu: ""
        property real px: 0
        property real py: 0
        function abrir(tipo, x, y) { tipoMenu = tipo; px = x; py = y }
        function fechar() { tipoMenu = "" }
        function feito(f) { fechar(); f() }
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton; onClicked: menu.fechar() }

        Cartao {
            id: cartaoMenu
            width: 236
            height: colunaMenu.implicitHeight + 12
            x: Math.min(menu.px, janela.width - width - 6)
            y: Math.min(menu.py, janela.height - height - 6)
            raio: 10
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaMenu
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 6 }
                readonly property bool varios: janela.quantosSelecionados() > 1
                readonly property bool lixeira: explorador.especial === "lixeira"
                readonly property bool apps: explorador.especial === "aplicativos"
                readonly property bool emItem: menu.tipoMenu === "item"
                readonly property bool emFundo: menu.tipoMenu === "fundo"
                readonly property bool opcoes: menu.tipoMenu === "opcoes"
                readonly property string primeiro: menu.tipoMenu !== "" && janela.numSelecionados > 0 ? janela.selecionados()[0] : ""

                // Sobre os arquivos selecionados
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira; texto: "Abrir"; icone: "abrir"; onClicado: menu.feito(janela.abrirSelecionados) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira && !colunaMenu.apps && !colunaMenu.varios; texto: "Abrir com…"; icone: "aplicativos"
                             onClicado: menu.feito(function () { dialogo.abrir("abrirCom", janela.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira && !colunaMenu.apps && janela.selecionadosCompactados().length > 0
                             texto: "Descompactar"; icone: "compactado"
                             onClicado: menu.feito(function () { explorador.descompactar(janela.selecionadosCompactados()) }) }
                Separador { visible: colunaMenu.emItem && !colunaMenu.apps }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira && !colunaMenu.apps && !colunaMenu.varios && explorador.especial === ""; texto: "Renomear"; icone: "lapis"; atalho: "F2"
                             onClicado: menu.feito(function () { janela.renomeando = colunaMenu.primeiro }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.apps; texto: "Copiar"; icone: "copiar"; atalho: "Ctrl C"
                             onClicado: menu.feito(function () { explorador.copiar(janela.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.apps && !colunaMenu.lixeira; texto: "Recortar"; icone: "recortar"; atalho: "Ctrl X"
                             onClicado: menu.feito(function () { explorador.recortar(janela.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.apps; texto: "Copiar caminho"; icone: "copiar"
                             onClicado: menu.feito(function () { explorador.copiarCaminho(janela.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.apps; texto: "Informações"; icone: "info"; atalho: "Ctrl I"
                             onClicado: menu.feito(function () { dialogo.abrir("informacoes", janela.selecionados()) }) }
                Separador { visible: colunaMenu.emItem && !colunaMenu.apps }
                ItemDeMenu { visible: colunaMenu.emItem && colunaMenu.lixeira; texto: "Restaurar"; icone: "restaurar"
                             onClicado: menu.feito(function () { explorador.restaurar(janela.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.apps; perigo: true
                             texto: colunaMenu.lixeira ? "Excluir permanentemente" : "Mover para a Lixeira"; icone: "lixeira"; atalho: colunaMenu.lixeira ? "" : "Delete"
                             onClicado: menu.feito(function () { janela.apagar(false) }) }

                // No espaço vazio da pasta
                ItemDeMenu { visible: colunaMenu.emFundo && explorador.especial === ""; texto: "Nova pasta"; icone: "nova-pasta"; atalho: "Ctrl Shift N"
                             onClicado: menu.feito(explorador.novaPasta) }
                ItemDeMenu { visible: colunaMenu.emFundo && explorador.especial === ""; texto: "Colar"; icone: "colar"; atalho: "Ctrl V"; ativo: explorador.podeColar
                             onClicado: menu.feito(explorador.colar) }
                ItemDeMenu { visible: colunaMenu.emFundo && explorador.especial === ""; texto: "Abrir o Terminal aqui"; icone: "terminal"
                             onClicado: menu.feito(explorador.abrirTerminalAqui) }
                ItemDeMenu { visible: colunaMenu.emFundo && colunaMenu.lixeira; texto: "Esvaziar a Lixeira"; icone: "lixeira"; perigo: true; ativo: explorador.itens.length > 0
                             onClicado: menu.feito(function () { dialogo.abrir("esvaziar", []) }) }
                Separador { visible: colunaMenu.emFundo && explorador.especial === "" }

                // Ordenar e mostrar (também pelo botão da barra de ferramentas)
                Text { visible: colunaMenu.opcoes || (colunaMenu.emFundo && explorador.especial === ""); leftPadding: 10; topPadding: 4; bottomPadding: 2
                       text: "Ordenar por"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
                Repeater {
                    model: [["nome", "Nome"], ["data", "Data de modificação"], ["tamanho", "Tamanho"], ["tipo", "Tipo"]]
                    ItemDeMenu {
                        required property var modelData
                        visible: colunaMenu.opcoes || (colunaMenu.emFundo && explorador.especial === "")
                        texto: modelData[1]; icone: explorador.ordem === modelData[0] ? "check" : ""
                        onClicado: menu.feito(function () { explorador.definirOrdem(modelData[0]) })
                    }
                }
                Separador { visible: colunaMenu.opcoes || (colunaMenu.emFundo && explorador.especial === "") }
                ItemDeMenu { visible: colunaMenu.opcoes || (colunaMenu.emFundo && explorador.especial === ""); texto: "Mostrar arquivos ocultos"
                             icone: explorador.ocultos ? "check" : ""; atalho: "Ctrl H"; onClicado: menu.feito(explorador.alternarOcultos) }
                ItemDeMenu { visible: colunaMenu.opcoes; texto: "Ícones"; icone: explorador.visualizacao === "icones" ? "check" : ""; atalho: "Ctrl 1"
                             onClicado: menu.feito(function () { explorador.definirVisualizacao("icones") }) }
                ItemDeMenu { visible: colunaMenu.opcoes; texto: "Lista"; icone: explorador.visualizacao === "lista" ? "check" : ""; atalho: "Ctrl 2"
                             onClicado: menu.feito(function () { explorador.definirVisualizacao("lista") }) }
            }
        }
    }

    // ============================================================ diálogos
    Rectangle {
        id: dialogo
        anchors.fill: parent
        z: 60
        visible: tipo !== ""
        color: Qt.rgba(0.06, 0.09, 0.14, 0.28)
        property string tipo: ""
        property var caminhos: []
        property var info: ({})
        property var apps: []
        function abrir(t, lista) {
            caminhos = lista
            if (t === "informacoes") info = explorador.informacoes(lista[0])
            if (t === "abrirCom") apps = explorador.aplicativosPara(lista[0])
            tipo = t
        }
        function fechar() { tipo = ""; teclado.forceActiveFocus() }
        MouseArea { anchors.fill: parent; onClicked: dialogo.fechar() }

        Cartao {
            anchors.centerIn: parent
            width: 400
            height: colunaDialogo.implicitHeight + 40
            raio: 18
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaDialogo
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 10

                // Excluir / esvaziar
                Titulo {
                    visible: dialogo.tipo === "excluir" || dialogo.tipo === "esvaziar"
                    nivel: 2; width: parent.width; wrapMode: Text.WordWrap
                    text: dialogo.tipo === "esvaziar" ? "Esvaziar a Lixeira?"
                          : (dialogo.caminhos.length === 1 ? "Excluir permanentemente este item?" : "Excluir permanentemente " + dialogo.caminhos.length + " itens?")
                }
                Rotulo {
                    visible: dialogo.tipo === "excluir" || dialogo.tipo === "esvaziar"
                    width: parent.width; secundario: true
                    text: "Não dá para desfazer: os arquivos não poderão ser recuperados."
                }
                Row {
                    visible: dialogo.tipo === "excluir" || dialogo.tipo === "esvaziar"
                    anchors.right: parent.right
                    spacing: 8
                    Botao { texto: "Cancelar"; onClicado: dialogo.fechar() }
                    Botao {
                        texto: dialogo.tipo === "esvaziar" ? "Esvaziar" : "Excluir"; tipo: "perigo"
                        onClicado: {
                            if (dialogo.tipo === "esvaziar") explorador.esvaziarLixeira()
                            else explorador.excluirPermanentemente(dialogo.caminhos)
                            dialogo.fechar()
                        }
                    }
                }

                // Informações
                Row {
                    visible: dialogo.tipo === "informacoes"
                    spacing: 12
                    width: parent.width
                    Item {
                        width: 52; height: 52
                        Icone { anchors.centerIn: parent; nome: dialogo.info.icone || "arquivo"; tamanho: 44; cor: dialogo.info.pasta ? "#5B8FEF" : Tema.textoSecundario }
                    }
                    Column {
                        width: parent.width - 64
                        anchors.verticalCenter: parent.verticalCenter
                        Titulo { nivel: 2; width: parent.width; text: dialogo.info.nome || "" }
                        Rotulo { secundario: true; text: dialogo.info.tipo || "" }
                    }
                }
                Column {
                    visible: dialogo.tipo === "informacoes"
                    width: parent.width
                    spacing: 4
                    Repeater {
                        model: dialogo.tipo === "informacoes" ? [
                            ["Tamanho", dialogo.info.pasta ? (dialogo.info.conteudo || "") : (dialogo.info.tamanhoTexto || "")],
                            ["Onde está", dialogo.info.local || ""],
                            ["Modificado", dialogo.info.modificadoTexto || ""],
                            ["Criado", dialogo.info.criadoTexto || ""],
                            ["Permissão", dialogo.info.permissao || ""]
                        ].concat(dialogo.info.original ? [["Origem", dialogo.info.original]] : []) : []
                        Row {
                            required property var modelData
                            width: parent.width
                            spacing: 10
                            Text { width: 90; text: modelData[0]; horizontalAlignment: Text.AlignRight; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            TextEdit { width: parent.width - 100; text: modelData[1]; readOnly: true; selectByMouse: true; wrapMode: Text.WrapAnywhere
                                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        }
                    }
                }
                Botao { visible: dialogo.tipo === "informacoes"; anchors.right: parent.right; texto: "Fechar"; onClicado: dialogo.fechar() }

                // Abrir com
                Titulo { visible: dialogo.tipo === "abrirCom"; nivel: 2; text: "Abrir com" }
                Rotulo { visible: dialogo.tipo === "abrirCom" && dialogo.apps.length === 0; secundario: true; width: parent.width
                         text: "Nenhum aplicativo instalado diz abrir este tipo de arquivo. Procure um na Central de Aplicativos ou peça ao Wise." }
                Repeater {
                    model: dialogo.tipo === "abrirCom" ? dialogo.apps : []
                    LinhaDeLista {
                        required property var modelData
                        texto: modelData.nome
                        onClicada: { explorador.abrirCom(modelData.id, dialogo.caminhos[0]); dialogo.fechar() }
                        Botao { texto: "Usar sempre"; height: 26; onClicado: { explorador.definirPadrao(modelData.id, dialogo.caminhos[0]); explorador.abrirCom(modelData.id, dialogo.caminhos[0]); dialogo.fechar() } }
                    }
                }
                Botao { visible: dialogo.tipo === "abrirCom"; anchors.right: parent.right; texto: "Cancelar"; onClicado: dialogo.fechar() }
            }
        }
    }

    Aviso { id: aviso; anchors { horizontalCenter: area.horizontalCenter; bottom: rodape.top; bottomMargin: 14 } z: 70 }

    // Captura para conferência visual (main.py --captura)
    Timer {
        interval: 700; running: capturaArquivo !== ""
        onTriggered: {
            if (explorador.itens.length > 2) janela.escolher(1, 0)
            salvarCaptura.start()
        }
    }
    Timer { id: salvarCaptura; interval: 300; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
