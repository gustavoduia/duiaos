// DuiaOS — Ora: barra de endereço.
// Fora de foco mostra o cadeado e o site em destaque; em foco, o endereço inteiro selecionado. Enquanto a
// pessoa digita, as sugestões (buscar no buscador escolhido, favoritos e histórico) aparecem por baixo.
// A estrela adiciona ou tira a página dos favoritos.
import QtQuick
import DuiaOS

Rectangle {
    id: barra
    property var janelaOra
    readonly property var aba: janelaOra ? janelaOra.aba : null
    readonly property string url: aba ? aba.url : ""
    readonly property bool web: aba !== null && aba.pagina === ""
    readonly property bool seguro: url.indexOf("https://") === 0
    property bool favorito: false
    property var sugestoes: []
    property int escolhida: -1

    function focar() { entrada.forceActiveFocus(); entrada.selectAll() }
    function atualizarFavorito() { favorito = web && url !== "" ? ora.ehFavorito(url) : false }
    function alternarFavorito() {
        if (!web || url === "") return
        favorito = ora.alternarFavorito(url, aba.titulo)
    }
    onUrlChanged: { if (!entrada.activeFocus) entrada.text = textoDoEndereco(); atualizarFavorito() }
    Connections { target: ora; function onFavoritosMudaram() { barra.atualizarFavorito() } }
    function textoDoEndereco() { return url.indexOf("ora://") === 0 ? url : url }

    function confirmar() {
        var texto = escolhida >= 0 && escolhida < sugestoes.length ? sugestoes[escolhida].url : entrada.text
        if (texto.trim() === "") return
        entrada.focus = false
        sugestoes = []
        janelaOra.abrir(texto, false)
        if (aba && aba.web) aba.web.forceActiveFocus()
    }
    function calcularSugestoes() {
        var texto = entrada.text.trim()
        if (!entrada.activeFocus || texto === "" || texto === url) { sugestoes = []; return }
        var buscador = ""
        var lista = ora.buscadores()
        for (var i = 0; i < lista.length; i++) if (lista[i].id === ora.configuracoes.buscador) buscador = lista[i].nome
        var itens = [{ url: texto, titulo: "Buscar “" + texto + "” no " + buscador, tipo: "busca" }]
        var achados = ora.sugestoes(texto)
        for (var j = 0; j < achados.length; j++) itens.push(achados[j])
        sugestoes = itens
        escolhida = -1
    }

    height: 36
    radius: height / 2
    color: entrada.activeFocus ? Tema.cartao : (Tema.futurista ? (Tema.escuro ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(0.2, 0.3, 0.6, 0.06))
                                                               : (Tema.escuro ? Qt.rgba(1, 1, 1, 0.07) : "#EEF1F6"))
    border { width: entrada.activeFocus ? 2 : (Tema.futurista ? 1 : 0); color: entrada.activeFocus ? Tema.azulDuia : Tema.borda }
    Aurora {
        visible: Tema.futurista && entrada.activeFocus
        z: -1
        anchors { fill: parent; margins: -3 }
        radius: parent.radius + 3
        opacity: 0.30
    }

    Icone {
        id: cadeado
        anchors { left: parent.left; leftMargin: 13; verticalCenter: parent.verticalCenter }
        nome: entrada.activeFocus || barra.url === "" ? "busca" : (barra.web ? (barra.seguro ? "cadeado" : "info") : "globo")
        tamanho: 14
        cor: !entrada.activeFocus && barra.web && !barra.seguro && barra.url.indexOf("http://") === 0 ? Tema.aviso : Tema.textoSecundario
    }
    Text {
        id: naoSeguro
        visible: !entrada.activeFocus && barra.web && barra.url.indexOf("http://") === 0
        anchors { left: cadeado.right; leftMargin: 6; verticalCenter: parent.verticalCenter }
        text: "Não seguro"
        color: Tema.aviso
        font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
    }
    TextInput {
        id: entrada
        anchors { left: naoSeguro.visible ? naoSeguro.right : cadeado.right; leftMargin: naoSeguro.visible ? 8 : 9
                  right: estrela.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
        clip: true
        color: Tema.texto
        selectionColor: Tema.azulDuia
        selectedTextColor: "white"
        font { family: Tema.fonteTexto; pixelSize: 14 }
        selectByMouse: true
        inputMethodHints: Qt.ImhUrlCharactersOnly | Qt.ImhNoAutoUppercase
        visible: activeFocus || barra.url === "" || barra.url.indexOf("ora://") === 0
        onActiveFocusChanged: {
            if (activeFocus) { text = barra.textoDoEndereco(); Qt.callLater(selectAll) }
            else { text = barra.textoDoEndereco(); barra.sugestoes = [] }
        }
        onTextEdited: barra.calcularSugestoes()
        onAccepted: barra.confirmar()
        Keys.onEscapePressed: { text = barra.textoDoEndereco(); barra.sugestoes = []; focus = false }
        Keys.onDownPressed: if (barra.sugestoes.length) barra.escolhida = Math.min(barra.escolhida + 1, barra.sugestoes.length - 1)
        Keys.onUpPressed: if (barra.sugestoes.length) barra.escolhida = Math.max(barra.escolhida - 1, -1)
        Text {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            visible: entrada.text === "" && !entrada.preeditText
            text: "Buscar ou digitar um endereço"
            color: Tema.textoApagado
            font: entrada.font
        }
    }
    // Fora de foco: o site em destaque e o resto do endereço apagado
    Text {
        anchors { left: entrada.left; right: entrada.right; verticalCenter: parent.verticalCenter }
        visible: !entrada.visible
        textFormat: Text.StyledText
        elide: Text.ElideRight
        font { family: Tema.fonteTexto; pixelSize: 14 }
        color: Tema.textoSecundario
        text: {
            var mostrar = ora.paraMostrar(barra.url)
            var dominio = ora.dominio(barra.url)
            var i = mostrar.indexOf(dominio)
            function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;") }
            if (dominio === "" || i < 0) return esc(mostrar)
            return esc(mostrar.slice(0, i)) + "<font color='" + Tema.texto + "'>" + esc(dominio) + "</font>" + esc(mostrar.slice(i + dominio.length))
        }
    }
    MouseArea {
        anchors { left: entrada.left; right: entrada.right; top: parent.top; bottom: parent.bottom }
        visible: !entrada.visible
        cursorShape: Qt.IBeamCursor
        onClicked: barra.focar()
    }
    BotaoIcone {
        id: estrela
        anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
        width: 28; height: 28; radius: 14
        visible: barra.web && barra.url !== "" && !janelaOra.privada
        icone: "estrela"; tamanhoIcone: 15
        corIcone: barra.favorito ? Tema.azulDuia : Tema.textoSecundario
        marcado: barra.favorito
        dica: barra.favorito ? "Tirar dos favoritos" : "Adicionar aos favoritos"
        onClicado: barra.alternarFavorito()
    }

    // ------------------------------------------------------------ sugestões (fora do cabeçalho, que corta)
    Rectangle {
        id: painel
        parent: janelaOra ? janelaOra.contentItem : barra
        visible: barra.sugestoes.length > 0 && entrada.activeFocus
        z: 60
        readonly property point origem: barra.mapToItem(parent, 0, barra.height + 6)
        x: origem.x; y: origem.y
        width: barra.width
        height: colunaSugestoes.implicitHeight + 12
        radius: Tema.raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        Column {
            id: colunaSugestoes
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 6 }
            Repeater {
                model: barra.sugestoes
                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    width: colunaSugestoes.width; height: 38; radius: 8
                    color: index === barra.escolhida || areaSug.containsMouse ? Tema.selecao : "transparent"
                    Icone {
                        id: iconeSug
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        nome: modelData.tipo === "busca" ? "busca" : (modelData.tipo === "favorito" ? "estrela" : "recentes")
                        tamanho: 14; cor: Tema.textoSecundario
                    }
                    Text {
                        id: tituloSug
                        anchors { left: iconeSug.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        width: Math.min(implicitWidth, parent.width * 0.55)
                        text: modelData.tipo === "busca" ? modelData.titulo : (modelData.titulo || modelData.url)
                        elide: Text.ElideRight
                        color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 }
                    }
                    Text {
                        visible: modelData.tipo !== "busca"
                        anchors { left: tituloSug.right; leftMargin: 8; right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        text: "— " + ora.paraMostrar(modelData.url)
                        elide: Text.ElideRight
                        color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 13 }
                    }
                    MouseArea { id: areaSug; anchors.fill: parent; hoverEnabled: true
                                onClicked: { barra.escolhida = index; barra.confirmar() } }
                }
            }
        }
    }
}
