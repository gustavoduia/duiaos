// DuiaOS — conteúdo da Barra de Recursos (sem a janela, para servir também à demonstração).
//
// Esquerda: símbolo (Menu do DuiaOS), o aplicativo em uso e os menus dele (Arquivo, Editar…;
// menus.py, ADR 057). O Wise fica nos ícones da direita.
// Direita: seta do balão (ícones que não couberam), até 4 ícones de controle,
// Central de Controle e relógio (calendário).
import QtQuick
import DuiaOS

Rectangle {
    id: barra
    property string posicao: configuracao.posicao
    readonly property bool horizontal: posicao === "topo" || posicao === "base"
    readonly property int espessura: horizontal ? 32 : 64
    color: Tema.barra

    // ---------------------------------------------------------- relógio
    property date agora: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: barra.agora = new Date() }
    readonly property var local: Qt.locale("pt_BR")

    // ------------------------------------------------- ícones de controle
    function existe(id) {
        switch (id) {
        case "wise": return sistema.wise
        case "wifi": return rede.temPlaca || controles.wifiExiste       // qualquer placa de rede (cabo, Wi-Fi, celular)
        case "som": return controles.volume >= 0
        case "bateria": return controles.bateria >= 0
        case "bluetooth": return controles.bluetoothExiste
        case "brilho": return controles.brilho >= 0
        case "luz": return true
        }
        return false
    }
    readonly property var disponiveis: {
        var lista = []
        var ordem = configuracao.ordem
        for (var i = 0; i < ordem.length; i++)
            if (existe(ordem[i])) lista.push(ordem[i])
        return lista
    }
    readonly property var visiveis: disponiveis.slice(0, configuracao.maximoVisiveis)
    readonly property var ocultos: disponiveis.slice(configuracao.maximoVisiveis)

    // Posição do centro de um item na tela (para o balão nascer embaixo dele)
    function ancoraDe(item) {
        var p = item.mapToItem(null, item.width / 2, item.height / 2)
        return horizontal ? p.x : p.y
    }
    // Balão do ícone de atualizações (BalaoAtualizacao.qml, desenhado numa camada própria em BarraDeRecursos.qml)
    property bool balaoAtualizacao: false
    property real ancoraAtualizacao: 0
    function mostrarBalaoAtualizacao() {
        if (!horizontal || !botaoAtualizacao.visible || sistema.balaoTitulo === "") { sistema.notificarAtualizacao(); return }
        sistema.fecharPainel()
        ancoraAtualizacao = ancoraDe(botaoAtualizacao)
        balaoAtualizacao = true
    }
    function verResumoDasAtualizacoes() {
        balaoAtualizacao = false
        sistema.abrir("configuracoes:atualizacoes")
    }
    Connections {
        target: sistema
        function onPedirBalaoAtualizacao() { barra.mostrarBalaoAtualizacao() }
        function onAtualizacaoMudou() { if (!sistema.atualizacaoIcone) barra.balaoAtualizacao = false }
        function onPainelMudou() { if (sistema.painel !== "") barra.balaoAtualizacao = false }
    }

    function abrir(nome, item) {
        if (nome === "wise") { sistema.abrirWise(); return }
        sistema.abrirPainel(nome, ancoraDe(item))
    }

    // Linha fina no lado voltado para a área de trabalho
    Rectangle {
        color: Tema.borda
        width: barra.horizontal ? parent.width : 1
        height: barra.horizontal ? 1 : parent.height
        x: barra.posicao === "esquerda" ? parent.width - 1 : 0
        y: barra.posicao === "topo" ? parent.height - 1 : 0
    }

    // Botão da barra: realce arredondado ao passar o mouse ou com o balão aberto
    component BotaoDaBarra: Rectangle {
        id: botao
        property string painel: ""
        property bool aberto: painel !== "" && sistema.painel === painel
        default property alias conteudo: dentro.data
        signal clicado()
        signal clicadoDireito()
        signal duploClicado()
        width: barra.horizontal ? Math.max(28, dentro.childrenRect.width + 14) : 52
        height: barra.horizontal ? 24 : Math.max(26, dentro.childrenRect.height + 10)
        radius: 6
        color: aberto ? Tema.pressionado : (area.containsMouse ? Tema.realce : "transparent")
        Item {
            id: dentro
            anchors.centerIn: parent
            width: childrenRect.width; height: childrenRect.height
        }
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: (m) => m.button === Qt.RightButton ? botao.clicadoDireito() : botao.clicado()
            onDoubleClicked: (m) => { if (m.button === Qt.LeftButton) botao.duploClicado() }
        }
    }

    component MenuDaBarra: BotaoDaBarra {
        id: tituloMenu
        property int indice: 0
        property string texto: ""
        property bool negrito: false
        property real larguraMaxima: 200
        painel: "appmenu" + indice
        Accessible.role: Accessible.MenuItem
        Accessible.name: texto
        onClicado: sistema.abrirMenuDoAplicativo(indice, barra.ancoraDe(tituloMenu))
        HoverHandler {
            onHoveredChanged: if (hovered && sistema.painel.indexOf("appmenu") === 0 && sistema.painel !== tituloMenu.painel)
                                  sistema.abrirMenuDoAplicativo(tituloMenu.indice, barra.ancoraDe(tituloMenu))
        }
        Text {
            text: tituloMenu.texto
            color: Tema.texto
            elide: Text.ElideRight
            width: Math.min(implicitWidth, tituloMenu.larguraMaxima)
            font { family: Tema.fonteTexto; pixelSize: 13; weight: tituloMenu.negrito ? Font.Bold : Font.Normal }
        }
    }

    component Indicador: BotaoDaBarra {
        id: ind
        required property string modelData
        painel: modelData
        Accessible.role: Accessible.Button
        Accessible.name: ({ wise: "Wise", wifi: "Wi-Fi", som: "Som", bateria: "Bateria", bluetooth: "Bluetooth",
                            brilho: "Brilho", luz: "Luz noturna" })[modelData] || modelData
        onClicado: barra.abrir(modelData, ind)
        // Botão direito no Wise: abrir, configurações e desligar (ADR 063)
        aberto: (painel !== "" && sistema.painel === painel) || (modelData === "wise" && sistema.painel === "appmenuwise")
        onClicadoDireito: if (modelData === "wise") sistema.abrirMenuDoWise(barra.ancoraDe(ind))
        Row {
            spacing: 5
            Image {
                id: imagemWise
                visible: ind.modelData === "wise" && status === Image.Ready
                source: ind.modelData === "wise" ? "file:///usr/share/icons/hicolor/scalable/apps/duiaos-wise.svg" : ""
                width: 18; height: 18; sourceSize: Qt.size(36, 36)
                opacity: sistema.wiseEstado === "descansando" || sistema.wiseEstado === "" ? 0.55 : 1.0
                Behavior on opacity { NumberAnimation { duration: 200 } }
                anchors.verticalCenter: parent.verticalCenter
            }
            Icone {
                visible: ind.modelData !== "bateria" && !imagemWise.visible
                anchors.verticalCenter: parent.verticalCenter
                tamanho: 17
                cor: (ind.modelData === "wifi" && !controles.wifiLigado && rede.icone !== "rede" && rede.icone !== "rede-alerta")
                     || (ind.modelData === "bluetooth" && !controles.bluetoothLigado)
                     || (ind.modelData === "luz" && controles.luzNoturna === "desligada") ? Tema.textoApagado : Tema.texto
                nome: {
                    switch (ind.modelData) {
                    case "wise": return "ia"
                    case "wifi":
                        // rede.icone: cabo, sem internet, sem conexão; "" = Wi-Fi conectada (o sinal decide)
                        if (rede.vpnAtiva !== "" && rede.icone === "" && controles.wifiRede !== "") return "wifi-" + controles.nivelWifi
                        if (rede.icone !== "" && rede.icone !== "wifi-0") return rede.icone
                        if (!controles.wifiLigado) return rede.temWifi || !rede.temPlaca ? "wifi-desligado" : "rede-desligada"
                        return controles.wifiRede !== "" ? "wifi-" + controles.nivelWifi : "wifi-0"
                    case "som":
                        if (controles.mudo || controles.volume === 0) return "som-mudo"
                        return controles.volume < 34 ? "som-0" : (controles.volume < 67 ? "som-1" : "som-2")
                    case "bluetooth": return "bluetooth"
                    case "brilho": return "brilho"
                    case "luz": return "lua"
                    }
                    return "ponto"
                }
            }
            Text {
                visible: ind.modelData === "bateria" && barra.horizontal
                anchors.verticalCenter: parent.verticalCenter
                text: controles.bateria + "%"
                color: Tema.texto
                font { family: Tema.fonteTexto; pixelSize: 12 }
            }
            IconeBateria {
                visible: ind.modelData === "bateria"
                anchors.verticalCenter: parent.verticalCenter
                nivel: controles.bateria
                carregando: controles.carregando
            }
        }
    }

    // ---------------------------------------------------- barra horizontal
    Item {
        anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
        visible: barra.horizontal

        Row {
            anchors { left: parent.left; verticalCenter: parent.verticalCenter }
            spacing: 4
            BotaoDaBarra {
                id: botaoMenu
                painel: "menu"
                width: 34
                Accessible.role: Accessible.ButtonMenu
                Accessible.name: "Menu do DuiaOS"
                onClicado: barra.abrir("menu", botaoMenu)
                Simbolo { width: 17; height: 17 }
            }
            // Menu do aplicativo em foco (ADR 057): o nome dele (ações da janela) e os menus dele
            // (Arquivo, Editar…), lidos pela acessibilidade. Com um menu aberto, passar o mouse em
            // outro título abre esse, como no macOS.
            MenuDaBarra {
                id: menuNome
                visible: sistema.aplicativoEmFoco !== ""
                indice: -1
                negrito: true
                texto: sistema.aplicativoEmFoco
                larguraMaxima: barra.width * 0.2
            }
            Repeater {
                model: sistema.titulosDoMenu
                delegate: MenuDaBarra {
                    required property string modelData
                    required property int index
                    indice: index
                    texto: modelData
                    // Só os que cabem antes do centro da barra (o resto fica escondido, sem sobrepor o aviso)
                    visible: x + width < barra.width * 0.5 - 60
                }
            }
        }

        Aviso {
            id: aviso
            anchors.centerIn: parent
            height: 24
        }

        Row {
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            spacing: 2
            BotaoDaBarra {
                id: botaoBalao
                visible: barra.ocultos.length > 0
                painel: "balao"
                width: 26
                Accessible.name: "Mostrar os outros ícones"
                onClicado: barra.abrir("balao", botaoBalao)
                Icone { nome: sistema.painel === "balao" ? "seta-cima" : "seta-baixo"; tamanho: 14; cor: Tema.textoSecundario }
            }
            Repeater {
                model: barra.visiveis
                delegate: Indicador {}
            }
            BotaoDaBarra {
                id: botaoCentral
                painel: "central"
                Accessible.name: "Central de Controle"
                onClicado: barra.abrir("central", botaoCentral)
                Icone { nome: "controles"; tamanho: 17 }
            }
            // Atualizações (ADR 058): aparece quando há atualizações ou quando falta reiniciar
            BotaoDaBarra {
                id: botaoAtualizacao
                visible: sistema.atualizacaoIcone
                Accessible.role: Accessible.Button
                Accessible.name: sistema.atualizacaoDica || "Atualizações"
                Accessible.description: "Um clique mostra o aviso; dois cliques abrem o resumo das atualizações"
                // Um clique: o balão de novo. Dois cliques: Configurações › Atualizações já com o resumo.
                onClicado: barra.mostrarBalaoAtualizacao()
                onDuploClicado: barra.verResumoDasAtualizacoes()
                Item {
                    width: 18; height: 18
                    Icone { anchors.centerIn: parent; nome: "atualizacao"; tamanho: 17; cor: Tema.texto }
                    Rectangle { x: 12; y: -1; width: 7; height: 7; radius: 3.5; color: Tema.azulDuia
                                border { color: Tema.barra; width: 1 } }
                }
            }
            BotaoDaBarra {
                id: botaoRelogio
                painel: "calendario"
                Accessible.name: "Data e hora"
                onClicado: barra.abrir("calendario", botaoRelogio)
                Text {
                    text: barra.agora.toLocaleDateString(barra.local, "ddd d 'de' MMM").replace(/\./g, "") + "   " + barra.agora.toLocaleTimeString(barra.local, "HH:mm")
                    color: Tema.texto
                    font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Medium }
                }
            }
        }
    }

    // ------------------------------------------------------ barra vertical
    Item {
        anchors { fill: parent; topMargin: 8; bottomMargin: 8 }
        visible: !barra.horizontal

        Column {
            anchors { top: parent.top; horizontalCenter: parent.horizontalCenter }
            spacing: 6
            BotaoDaBarra {
                id: botaoMenuV
                painel: "menu"
                height: 34
                onClicado: barra.abrir("menu", botaoMenuV)
                Simbolo { width: 20; height: 20 }
            }
            BotaoDaBarra {
                visible: sistema.wise
                id: botaoWise
                onClicado: sistema.abrirWise()
                onClicadoDireito: sistema.abrirMenuDoWise(barra.ancoraDe(botaoWise))
                Text { text: "Wise"; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.Bold } }
            }
        }
        Column {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter }
            spacing: 4
            BotaoDaBarra {
                id: botaoBalaoV
                visible: barra.ocultos.length > 0
                painel: "balao"
                onClicado: barra.abrir("balao", botaoBalaoV)
                Icone { nome: "seta-cima"; tamanho: 14; cor: Tema.textoSecundario }
            }
            Repeater { model: barra.visiveis; delegate: Indicador {} }
            BotaoDaBarra {
                id: botaoCentralV
                painel: "central"
                onClicado: barra.abrir("central", botaoCentralV)
                Icone { nome: "controles"; tamanho: 18 }
            }
            BotaoDaBarra {
                id: botaoRelogioV
                painel: "calendario"
                onClicado: barra.abrir("calendario", botaoRelogioV)
                Column {
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: barra.agora.toLocaleTimeString(barra.local, "HH:mm")
                           color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: barra.agora.toLocaleDateString(barra.local, "d MMM").replace(/\./g, "")
                           color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
                }
            }
        }
    }

    Connections {
        target: controles
        function onAviso(mensagem) { aviso.mostrar(mensagem) }
    }
}
