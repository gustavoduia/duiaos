// DuiaOS — conteúdo da Área de Trabalho: papel de parede, ícones e menus de contexto.
// Botão esquerdo seleciona (duplo clique abre); botão direito abre o menu do que está embaixo.
import QtQuick
import DuiaOS

Item {
    id: raiz
    property bool mostrarIcones: true
    property string nomeTela: ""             // saída (eDP-1, HDMI-A-1…): cada tela pode ter o seu papel
    property var estendido: null             // {largura, altura, dx, dy}: uma imagem por todas as telas
    readonly property var meuPapel: { area.papeis; return area.papelDaTela(nomeTela) }
    property var selecao: ({})
    property string renomeando: ""
    focus: true

    function abrirMenu(tipo, x, y) { menu.abrir(tipo, x, y) }
    function selecionados() {
        var lista = []
        for (var i = 0; i < area.itens.length; i++) if (selecao[area.itens[i].caminho]) lista.push(area.itens[i].caminho)
        return lista
    }
    function escolher(caminho, modificadores) {
        var nova = (modificadores & (Qt.ControlModifier | Qt.ShiftModifier)) ? Object.assign({}, selecao) : ({})
        if ((modificadores & Qt.ControlModifier) && nova[caminho]) delete nova[caminho]
        else nova[caminho] = true
        selecao = nova
    }
    Connections {
        target: area
        function onRenomearNovo(caminho) { var n = ({}); n[caminho] = true; raiz.selecao = n; raiz.renomeando = caminho }
        function onAviso(m) { aviso.mostrar(m) }
        function onDestacar(caminho) { var n = ({}); n[caminho] = true; raiz.selecao = n }
    }
    function selecionadosCompactados() {
        var lista = []
        for (var i = 0; i < area.itens.length; i++) {
            if (!selecao[area.itens[i].caminho]) continue
            if (area.itens[i].compactado !== true) return []
            lista.push(area.itens[i].caminho)
        }
        return lista
    }

    Keys.onPressed: (e) => {
        if (renomeando !== "") return
        var ctrl = e.modifiers & Qt.ControlModifier
        var lista = selecionados()
        if (e.key === Qt.Key_Delete) area.moverParaLixeira(lista)
        else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { if (lista.length) area.abrir(lista[0]) }
        else if (e.key === Qt.Key_F2) { if (lista.length === 1) renomeando = lista[0] }
        else if (ctrl && e.key === Qt.Key_A) { var n = ({}); for (var i = 0; i < area.itens.length; i++) n[area.itens[i].caminho] = true; selecao = n }
        else if (ctrl && e.key === Qt.Key_C) area.copiar(lista)
        else if (ctrl && e.key === Qt.Key_X) area.recortar(lista)
        else if (ctrl && e.key === Qt.Key_V) area.colar()
        else if (e.key === Qt.Key_Escape) { menu.tipo = ""; selecao = ({}) }
        else return
        e.accepted = true
    }

    Fundo {
        anchors.fill: parent
        arquivo: raiz.meuPapel.arquivo || ""
        corFundo: raiz.meuPapel.cor || "#E8F0FE"
        // Ao entrar na sessão: nada de cor clara antes da imagem (o fundo imediato do autostart aparece por baixo)
        corCarregando: "transparent"
        onJaMostrouChanged: if (jaMostrou && raiz.mostrarIcones) area.fundoPronto()
        Component.onCompleted: if (jaMostrou && raiz.mostrarIcones) area.fundoPronto()
        ajuste: raiz.meuPapel.ajuste || "preencher"
        estendido: area.papeis.telas === "estender" ? raiz.estendido : null
    }

    // Clique no vazio: esquerdo limpa a seleção, direito abre o menu da área de trabalho.
    // Segurar o botão esquerdo e arrastar desenha o retângulo de seleção (Ctrl inverte, Shift soma).
    MouseArea {
        id: fundoArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        preventStealing: true
        property bool arrastando: false
        property point inicio: Qt.point(0, 0)
        property var base: ({})
        property int modo: 0                       // 0 substitui, 1 soma (Shift), 2 inverte (Ctrl)
        property var retangulos: []                // [{l, t, r, b, caminho}] guardados ao apertar (os ícones não se mexem)
        property string assinatura: ""
        property point ponteiro: Qt.point(0, 0)
        property bool pendente: false
        function guardarRetangulos() {
            var lista = []
            for (var i = 0; i < icones.count; i++) {
                var icone = icones.itemAt(i)
                if (!icone || !grade.visible) continue
                var p = icone.mapToItem(raiz, 0, 0)
                // só o desenho do ícone e do nome, não a célula inteira
                lista.push({ l: p.x + 12, r: p.x + icone.width - 12, t: p.y + 2, b: p.y + icone.height - 4,
                             caminho: icone.modelData.caminho })
            }
            retangulos = lista
        }
        function atualizar() {
            pendente = false
            var x = ponteiro.x, y = ponteiro.y
            var x1 = Math.min(inicio.x, x), y1 = Math.min(inicio.y, y)
            var x2 = Math.max(inicio.x, x), y2 = Math.max(inicio.y, y)
            faixa.x = x1; faixa.y = y1; faixa.width = x2 - x1; faixa.height = y2 - y1
            var tocados = []
            for (var i = 0; i < retangulos.length; i++) {
                var r = retangulos[i]
                if (r.l > x2 || r.r < x1 || r.t > y2 || r.b < y1) continue
                tocados.push(i)
            }
            var chave = tocados.join(",")
            if (chave === assinatura) return            // a seleção só muda quando o retângulo toca outros ícones
            assinatura = chave
            var nova = modo === 0 ? ({}) : Object.assign({}, base)
            for (var k = 0; k < tocados.length; k++) {
                var c = retangulos[tocados[k]].caminho
                if (modo === 2 && base[c]) delete nova[c]; else nova[c] = true
            }
            raiz.selecao = nova
        }
        onPressed: (m) => {
            raiz.forceActiveFocus()
            menu.tipo = ""
            arrastando = false
            inicio = Qt.point(m.x, m.y)
            modo = (m.modifiers & Qt.ControlModifier) ? 2 : ((m.modifiers & Qt.ShiftModifier) ? 1 : 0)
            base = Object.assign({}, raiz.selecao)
            assinatura = ""
            if (m.button === Qt.LeftButton && modo === 0) raiz.selecao = ({})
        }
        onPositionChanged: (m) => {
            if (!(m.buttons & Qt.LeftButton) || !raiz.mostrarIcones) return
            ponteiro = Qt.point(m.x, m.y)
            if (!arrastando) {
                if (Math.abs(m.x - inicio.x) < 5 && Math.abs(m.y - inicio.y) < 5) return
                arrastando = true
                guardarRetangulos()
                atualizar()
                return
            }
            pendente = true                          // aplicado no próximo quadro (Timer abaixo)
        }
        onReleased: (m) => {
            if (arrastando) { if (pendente) atualizar(); arrastando = false; return }
            if (m.button === Qt.RightButton) { raiz.selecao = ({}); menu.abrir("fundo", m.x, m.y) }
        }
        onCanceled: arrastando = false
        Timer { interval: 16; repeat: true; running: fundoArea.arrastando; onTriggered: if (fundoArea.pendente) fundoArea.atualizar() }
    }
    Rectangle {
        id: faixa
        visible: fundoArea.arrastando && width > 0 && height > 0
        z: 2
        radius: 3
        // Azul do DuiaOS translúcido: aparece em papéis de parede claros e escuros
        color: Qt.rgba(Tema.azulDuia.r, Tema.azulDuia.g, Tema.azulDuia.b, 0.22)
        border { color: Qt.rgba(Tema.azulDuia.r, Tema.azulDuia.g, Tema.azulDuia.b, 0.9); width: 1 }
    }

    // ------------------------------------------------------------- ícones
    Flow {
        id: grade
        visible: raiz.mostrarIcones
        anchors {
            fill: parent
            topMargin: area.posicaoBarra === "topo" ? 46 : 14
            bottomMargin: 96 + (area.posicaoBarra === "base" ? 34 : 0)
            rightMargin: area.posicaoBarra === "direita" ? 78 : 14
            leftMargin: area.posicaoBarra === "esquerda" ? 78 : 14
        }
        flow: Flow.TopToBottom
        layoutDirection: Qt.RightToLeft
        spacing: 4
        Repeater {
            id: icones
            model: area.itens
            Item {
                id: icone
                required property var modelData
                readonly property bool sel: raiz.selecao[modelData.caminho] === true
                width: 96; height: 98
                Rectangle {
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 2 }
                    width: 64; height: 62; radius: 10
                    color: icone.sel ? Qt.rgba(0, 0, 0, 0.22) : (toque.containsMouse ? Qt.rgba(1, 1, 1, 0.16) : "transparent")
                    border { color: icone.sel ? Qt.rgba(1, 1, 1, 0.45) : "transparent"; width: 1 }
                }
                Item {
                    id: figura
                    width: 52; height: 52
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 7 }
                    Image { id: mini; anchors.fill: parent; source: modelData.miniatura; sourceSize: Qt.size(104, 104)
                            fillMode: Image.PreserveAspectFit; asynchronous: true; visible: status === Image.Ready }
                    Icone { anchors.centerIn: parent; visible: !mini.visible && modelData.pasta; nome: "pasta-cheia"; tamanho: 56; cor: "#5B93F2" }
                    Ladrilho { anchors.centerIn: parent; visible: !mini.visible && !modelData.pasta; width: 40; height: 50; radius: 8
                               icone: modelData.icone; estilo: "claro"; tamanho: 42 }
                }
                Rectangle {
                    visible: raiz.renomeando !== modelData.caminho
                    anchors { horizontalCenter: parent.horizontalCenter; top: figura.bottom; topMargin: 5 }
                    width: Math.min(rotulo.implicitWidth + 10, parent.width - 4); height: rotulo.height + 4
                    radius: 5
                    // Fundo escuro discreto: o nome fica legível em papéis de parede claros e escuros
                    color: icone.sel ? Tema.azulDuia : Qt.rgba(0.06, 0.09, 0.14, 0.42)
                    Text {
                        id: rotulo
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, icone.width - 14)
                        text: modelData.nome
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        maximumLineCount: icone.sel ? 4 : 2
                        elide: Text.ElideMiddle
                        color: "white"
                        font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.Medium }
                    }
                }
                Rectangle {
                    visible: raiz.renomeando === modelData.caminho
                    anchors { horizontalCenter: parent.horizontalCenter; top: figura.bottom; topMargin: 4 }
                    width: parent.width - 4; height: 24; radius: 5
                    color: Tema.cartao; border { color: Tema.azulDuia; width: 2 }
                    TextInput {
                        id: entrada
                        anchors { fill: parent; leftMargin: 4; rightMargin: 4 }
                        verticalAlignment: TextInput.AlignVCenter; horizontalAlignment: TextInput.AlignHCenter
                        color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 }
                        clip: true
                        property bool feito: false
                        onVisibleChanged: if (visible) { feito = false; text = modelData.nome
                                              var p = modelData.pasta ? -1 : text.lastIndexOf("."); select(0, p > 0 ? p : text.length); forceActiveFocus() }
                        function concluir(salvar) {
                            if (feito) return
                            feito = true
                            if (salvar && text !== modelData.nome) area.renomear(modelData.caminho, text)
                            raiz.renomeando = ""; raiz.forceActiveFocus()
                        }
                        Keys.onReturnPressed: concluir(true)
                        Keys.onEnterPressed: concluir(true)
                        Keys.onEscapePressed: concluir(false)
                        onActiveFocusChanged: if (!activeFocus && visible) concluir(true)
                    }
                }
                MouseArea {
                    id: toque
                    anchors.fill: parent
                    enabled: raiz.renomeando !== modelData.caminho
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onPressed: (m) => {
                        raiz.forceActiveFocus()
                        menu.tipo = ""
                        if (m.button === Qt.RightButton) { if (!icone.sel) raiz.escolher(modelData.caminho, 0) }
                        else raiz.escolher(modelData.caminho, m.modifiers)
                    }
                    onClicked: (m) => { if (m.button === Qt.RightButton) { var p = mapToItem(raiz, m.x, m.y); menu.abrir("item", p.x, p.y) } }
                    onDoubleClicked: (m) => { if (m.button === Qt.LeftButton) area.abrir(modelData.caminho) }
                }
            }
        }
    }

    // ------------------------------------------------------ menu de contexto
    Item {
        id: menu
        anchors.fill: parent
        visible: tipo !== ""
        property string tipo: ""
        property real px: 0
        property real py: 0
        function abrir(t, x, y) { tipo = t; px = x; py = y }
        function feito(f) { tipo = ""; f() }
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton; onClicked: menu.tipo = "" }
        Cartao {
            width: 280
            height: colunaMenu.implicitHeight + 12
            x: Math.min(menu.px, raiz.width - width - 8)
            y: Math.min(menu.py, raiz.height - height - 8)
            raio: 10
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaMenu
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 6 }
                readonly property bool item: menu.tipo === "item"
                readonly property bool varios: raiz.selecionados().length > 1
                ItemDeMenu { visible: colunaMenu.item; texto: "Abrir"; icone: "abrir"; onClicado: menu.feito(function () { area.abrir(raiz.selecionados()[0]) }) }
                ItemDeMenu { visible: colunaMenu.item && raiz.selecionadosCompactados().length > 0; texto: "Descompactar"; icone: "compactado"
                             onClicado: menu.feito(function () { area.descompactar(raiz.selecionadosCompactados()) }) }
                ItemDeMenu { visible: colunaMenu.item && !colunaMenu.varios; texto: "Mostrar no Explorador de Arquivos"; icone: "pasta"
                             onClicado: menu.feito(function () { area.mostrarNoExplorador(raiz.selecionados()[0]) }) }
                Separador { visible: colunaMenu.item }
                ItemDeMenu { visible: colunaMenu.item && !colunaMenu.varios; texto: "Renomear"; icone: "lapis"; atalho: "F2"
                             onClicado: menu.feito(function () { raiz.renomeando = raiz.selecionados()[0] }) }
                ItemDeMenu { visible: colunaMenu.item; texto: "Copiar"; icone: "copiar"; atalho: "Ctrl C"; onClicado: menu.feito(function () { area.copiar(raiz.selecionados()) }) }
                ItemDeMenu { visible: colunaMenu.item; texto: "Recortar"; icone: "recortar"; atalho: "Ctrl X"; onClicado: menu.feito(function () { area.recortar(raiz.selecionados()) }) }
                Separador { visible: colunaMenu.item }
                ItemDeMenu { visible: colunaMenu.item; texto: "Mover para a Lixeira"; icone: "lixeira"; atalho: "Delete"; perigo: true
                             onClicado: menu.feito(function () { area.moverParaLixeira(raiz.selecionados()) }) }

                ItemDeMenu { visible: !colunaMenu.item; texto: "Nova pasta"; icone: "nova-pasta"; onClicado: menu.feito(area.novaPasta) }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Colar"; icone: "colar"; atalho: "Ctrl V"; onClicado: menu.feito(area.colar) }
                Separador { visible: !colunaMenu.item }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Organizar por nome"; icone: area.ordem === "nome" ? "check" : ""
                             onClicado: menu.feito(function () { area.definirOrdem("nome") }) }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Organizar por data"; icone: area.ordem === "data" ? "check" : ""
                             onClicado: menu.feito(function () { area.definirOrdem("data") }) }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Organizar por tipo"; icone: area.ordem === "tipo" ? "check" : ""
                             onClicado: menu.feito(function () { area.definirOrdem("tipo") }) }
                Separador { visible: !colunaMenu.item }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Abrir no Explorador de Arquivos"; icone: "pasta"; onClicado: menu.feito(function () { area.mostrarNoExplorador("") }) }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Abrir o Terminal aqui"; icone: "terminal"; onClicado: menu.feito(area.abrirTerminal) }
                Separador { visible: !colunaMenu.item }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Mudar o papel de parede…"; icone: "imagem"; onClicado: menu.feito(function () { area.abrirConfiguracoes("papel") }) }
                ItemDeMenu { visible: !colunaMenu.item; texto: "Configurações…"; icone: "engrenagem"; onClicado: menu.feito(function () { area.abrirConfiguracoes("aparencia") }) }
            }
        }
    }

    Aviso { id: aviso; anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 110 } }
}
