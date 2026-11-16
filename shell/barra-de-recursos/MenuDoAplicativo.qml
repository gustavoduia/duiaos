// DuiaOS — um menu do aplicativo em foco aberto pela Barra de Recursos (ADR 057), com os submenus
// em cascata: cada nível é um cartão; passar o mouse num submenu abre o nível seguinte ao lado.
// Os itens vêm de sistema.itensDoMenu (menus.py): {id, rotulo, tipo, ativo, marcado, atalho, itens}.
import QtQuick
import DuiaOS

Item {
    id: raiz
    anchors.fill: parent
    property var posicionar                  // função do ConteudoPainel que encosta o cartão na barra
    readonly property bool aberto: sistema.painel.indexOf("appmenu") === 0
    // Níveis abertos: [{itens, x, y}]; o primeiro é o menu da barra
    property var niveis: []
    onAbertoChanged: if (!aberto) niveis = []
    Connections {
        target: sistema
        function onMenusMudaram() { if (raiz.aberto) raiz.niveis = [{ itens: sistema.itensDoMenu, x: 0, y: 0 }] }
        function onPainelMudou() { if (raiz.aberto) raiz.niveis = [{ itens: sistema.itensDoMenu, x: 0, y: 0 }] }
    }
    function abrirSubmenu(nivel, item, cartao, itens) {
        var p = item.mapToItem(raiz, 0, 0)
        var largura = 280
        var x = cartao.x + cartao.width - 6
        if (x + largura > raiz.width - 6) x = cartao.x - largura + 6          // sem espaço à direita: abre à esquerda
        var lista = niveis.slice(0, nivel + 1)
        lista.push({ itens: itens, x: x, y: Math.max(6, p.y - 12) })
        fechar.stop()
        niveis = lista
    }
    // Ao sair de um submenu em diagonal, o mouse passa por outros itens: o submenu só fecha se o mouse
    // não chegar nele em 300 ms (como no macOS)
    property int nivelAFechar: -1
    function fecharDepois(nivel) {
        if (niveis.length <= nivel + 1) return
        nivelAFechar = nivel
        fechar.restart()
    }
    Timer { id: fechar; interval: 300; onTriggered: if (raiz.nivelAFechar >= 0 && raiz.niveis.length > raiz.nivelAFechar + 1) raiz.niveis = raiz.niveis.slice(0, raiz.nivelAFechar + 1) }

    Repeater {
        model: raiz.niveis
        delegate: Cartao {
            id: cartao
            required property var modelData
            required property int index
            readonly property var itens: modelData.itens
            width: Math.max(220, Math.min(380, larguraTexto + 24))
            height: Math.min(raiz.height - 12, coluna.implicitHeight + 16)
            property real larguraTexto: 0
            Component.onCompleted: {
                if (index === 0) raiz.posicionar(cartao, true)
                else { x = modelData.x; y = Math.min(modelData.y, raiz.height - height - 6) }
            }
            onHeightChanged: if (index === 0) raiz.posicionar(cartao, true)
            MouseArea { anchors.fill: parent }     // clique dentro não fecha
            HoverHandler { onHoveredChanged: if (hovered && cartao.index > raiz.nivelAFechar) fechar.stop() }
            // Carregando (a leitura do aplicativo leva um instante)
            Text {
                visible: cartao.itens.length === 0
                anchors.centerIn: parent
                text: "Carregando…"
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 13 }
            }
            Flickable {
                anchors { fill: parent; margins: 8 }
                contentHeight: coluna.implicitHeight
                clip: contentHeight > height
                interactive: contentHeight > height
                Column {
                    id: coluna
                    width: parent.width
                    Repeater {
                        model: cartao.itens
                        delegate: Loader {
                            required property var modelData
                            width: coluna.width
                            sourceComponent: modelData.tipo === "separador" ? separador : linha
                            Component { id: separador; Item { height: 9; Rectangle { anchors.centerIn: parent; width: parent.width - 16; height: 1; color: Tema.borda } } }
                            Component {
                                id: linha
                                Rectangle {
                                    id: linhaMenu
                                    readonly property var dado: modelData
                                    readonly property bool submenu: dado.tipo === "submenu"
                                    readonly property bool realcado: area.containsMouse && dado.ativo
                                    readonly property color corTexto: realcado ? "white" : (dado.ativo ? Tema.texto : Tema.textoApagado)
                                    height: 28
                                    radius: Tema.futurista ? 8 : 6
                                    color: realcado ? Tema.azulDuia : "transparent"
                                    Aurora { anchors.fill: parent; radius: parent.radius; visible: Tema.futurista && linhaMenu.realcado }
                                    Component.onCompleted: cartao.larguraTexto = Math.max(cartao.larguraTexto, nome.implicitWidth + tecla.implicitWidth + 64)
                                    Text {
                                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                                        width: 14
                                        visible: linhaMenu.dado.marcado
                                        text: "✓"
                                        color: linhaMenu.corTexto
                                        font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Bold }
                                    }
                                    Text {
                                        id: nome
                                        anchors { left: parent.left; leftMargin: 26; right: tecla.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                        text: linhaMenu.dado.rotulo
                                        elide: Text.ElideRight
                                        color: linhaMenu.corTexto
                                        font { family: Tema.fonteTexto; pixelSize: 13 }
                                    }
                                    Text {
                                        id: tecla
                                        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                        text: linhaMenu.submenu ? "›" : linhaMenu.dado.atalho
                                        color: linhaMenu.realcado ? "#DDE7FB" : Tema.textoApagado
                                        font { family: Tema.fonteTexto; pixelSize: linhaMenu.submenu ? 16 : 12 }
                                    }
                                    MouseArea {
                                        id: area
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: linhaMenu.dado.ativo ? Qt.PointingHandCursor : Qt.ArrowCursor
                                        onContainsMouseChanged: {
                                            if (!containsMouse) return
                                            if (linhaMenu.submenu && linhaMenu.dado.ativo) raiz.abrirSubmenu(cartao.index, linhaMenu, cartao, linhaMenu.dado.itens)
                                            else raiz.fecharDepois(cartao.index)
                                        }
                                        onClicked: {
                                            if (!linhaMenu.dado.ativo) return
                                            if (linhaMenu.submenu) raiz.abrirSubmenu(cartao.index, linhaMenu, cartao, linhaMenu.dado.itens)
                                            else sistema.acionarMenu(linhaMenu.dado.id)
                                        }
                                    }
                                    Accessible.role: linhaMenu.submenu ? Accessible.ButtonMenu : Accessible.MenuItem
                                    Accessible.name: linhaMenu.dado.rotulo
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
