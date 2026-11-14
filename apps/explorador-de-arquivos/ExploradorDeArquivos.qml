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
    function quantosSelecionados() { return selecionados().length }
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
        function onLocalChanged() { janela.limpar() }
        function onMudou() { }
        function onAviso(mensagem) { aviso.mostrar(mensagem) }
        function onRenomearNovo(caminho) {
            var nova = ({}); nova[caminho] = true
            janela.selecao = nova
            janela.renomeando = caminho
        }
    }
    onVisiveisChanged: if (atual >= visiveis.length) atual = -1

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
        color: "#EEF2F7"
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
            color: marcado ? Qt.rgba(0.18, 0.42, 0.90, 0.14) : (areaIl.containsMouse ? Qt.rgba(0.06, 0.09, 0.14, 0.05) : "transparent")
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
                                color: areaTrilha.containsMouse ? Qt.rgba(0.06, 0.09, 0.14, 0.06) : "transparent"
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
                    target: explorador
                    function onLocalChanged() {
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

        // Clique no vazio: limpa a seleção; clique direito: menu da pasta
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: (m) => {
                teclado.forceActiveFocus()
                janela.limpar()
                if (m.button === Qt.RightButton) { var p = mapToItem(null, m.x, m.y); menu.abrir("fundo", p.x, p.y) }
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
                Drag.mimeData: ({ "text/uri-list": janela.selecionados().map(function (c) { return "file://" + encodeURI(c) }).join("\r\n") })
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
            color: "white"
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
            interactive: true
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
                    color: celula.sel ? Qt.rgba(0.06, 0.09, 0.14, 0.09) : (toqueGrade.containsMouse ? Qt.rgba(0.06, 0.09, 0.14, 0.04) : "transparent")
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
                Toque { id: toqueGrade; anchors.fill: parent; item: modelData; indice: index; enabled: janela.renomeando !== modelData.caminho }
                AlvoDePasta { anchors.fill: parent; item: modelData }
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
                delegate: Rectangle {
                    id: linhaLista
                    required property var modelData
                    required property int index
                    readonly property bool sel: janela.selecao[modelData.caminho] === true
                    width: lista.width; height: 30
                    radius: 6
                    color: sel ? Tema.azulDuia : (index % 2 ? "#F1F4F8" : "transparent")
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
                readonly property string primeiro: janela.selecionados().length > 0 ? janela.selecionados()[0] : ""

                // Sobre os arquivos selecionados
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira; texto: "Abrir"; icone: "abrir"; onClicado: menu.feito(janela.abrirSelecionados) }
                ItemDeMenu { visible: colunaMenu.emItem && !colunaMenu.lixeira && !colunaMenu.apps && !colunaMenu.varios; texto: "Abrir com…"; icone: "aplicativos"
                             onClicado: menu.feito(function () { dialogo.abrir("abrirCom", janela.selecionados()) }) }
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
