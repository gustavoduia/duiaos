// DuiaOS — conteúdo da Ilha de Aplicativos (sem a janela, para servir também à demonstração).
// Central de Aplicativos · fixados (Wise e Explorador de Arquivos primeiro) · abertos · recentes
// | pasta Aplicativos · pilha de Downloads · Lixeira
//
// Opções (ilha.opcoes, Configurações › Barra e Ilha): tamanho, ampliação ao passar o mouse (como
// no macOS), posição (embaixo, à esquerda, à direita), indicadores, ícone que pula ao abrir.
// O item tem o tamanho da janela inteira: comprimento com folga para a ampliação e espessura com
// espaço para os ícones crescerem; o fundo arredondado fica encostado na borda da tela.
import QtQuick
import DuiaOS

Item {
    id: ilhaFundo
    readonly property var o: ilha.opcoes
    readonly property string posicao: o.posicao || "base"
    readonly property bool vertical: posicao !== "base"
    readonly property int base: o.tamanho || 46
    readonly property int maximo: o.ampliacao ? Math.max(base, o.tamanho_ampliado || 72) : base
    readonly property int folgaSalto: o.animar_abrir ? 22 : 0
    readonly property real raioAmpliacao: 3          // quantos ícones de cada lado crescem

    // Espessura do fundo (sem ampliação) e da janela: espaço para a ampliação E o salto juntos — o
    // ícone clicado costuma estar ampliado (o mouse está em cima) quando pula; com só o maior dos
    // dois, o topo do ícone saía da janela e era cortado (16/11)
    readonly property int espessuraFundo: base + 22
    readonly property int espessura: espessuraFundo + (maximo - base) + folgaSalto + 4
    // Comprimento da janela: o da faixa de ícones em repouso (calculado, para não mudar a cada
    // movimento do mouse), mais a folga que a ampliação pode somar
    readonly property int comprimentoBase: {
        var k = ilha.itens.length, divisorias = 0
        for (var i = 0; i < k; i++) if (grupo(i) !== (i === 0 ? 0 : grupo(i - 1))) divisorias++
        return (k + 4) * (base + 6) + 2 * (k + 6) + 9 + divisorias * 3
    }
    readonly property int comprimento: comprimentoBase + 16 + Math.ceil((maximo - base) * raioAmpliacao) + 8

    width: vertical ? espessura : comprimento
    height: vertical ? comprimento : espessura

    // Mouse sobre a Ilha: posição em "vagas" (0 = Central de Aplicativos) para a ampliação.
    // A posição é medida na Ilha EM REPOUSO (como no Dock do macOS), não nos ícones já ampliados:
    // se fosse medida neles, cada ampliação deslocaria os ícones debaixo do mouse, o foco mudaria
    // de novo e a Ilha ficaria tremendo. "forca" faz a onda entrar e sair suavemente.
    property real foco: -100
    property bool sobre: hover.hovered
    property bool arrastando: false
    // Sem ampliação enquanto arrasta: os ícones têm o tamanho de repouso e cada passo do arrasto é exato
    property real forca: sobre && !arrastando && o.ampliacao ? 1 : 0
    Behavior on forca { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
    HoverHandler {
        id: hover
        onPointChanged: {
            if (!hovered || ilhaFundo.arrastando) return
            var p = ilhaFundo.vertical ? point.position.y - ilhaFundo.height / 2 : point.position.x - ilhaFundo.width / 2
            ilhaFundo.foco = ilhaFundo.focoEm(p)
        }
    }

    // Faixa da borda (só o fundo); a janela usa para saber onde recebe cliques
    readonly property rect faixa: Qt.rect(fundo.x, fundo.y, fundo.width, fundo.height)

    // Onde começa cada vaga com a Ilha em repouso, ao longo dela (a mesma conta da grade:
    // vagas de base + 6, espaço de 2, divisórias de 1) e o comprimento total
    readonly property var repouso: {
        var passo = base + 6, k = ilha.itens.length, inicios = [0], pos = passo + 2
        for (var i = 0; i < k; i++) {
            if (grupo(i) !== (i === 0 ? 0 : grupo(i - 1))) pos += 3
            inicios.push(pos); pos += passo + 2
        }
        pos += 15                                    // 4 + divisória + 4, com os espaços
        for (var j = 0; j < 3; j++) { inicios.push(pos); pos += passo + 2 }
        return { inicios: inicios, total: pos - 2, passo: passo }
    }
    // Posição ao longo da Ilha (a partir do centro) → foco em vagas; fora das pontas, continua em linha reta
    function focoEm(p) {
        var r = repouso, x = p + r.total / 2, ultimo = r.inicios.length - 1
        for (var n = ultimo; n > 0; n--) if (x >= r.inicios[n]) break
        var f = (x - r.inicios[n]) / r.passo
        return n + (n < ultimo ? Math.min(1, f) : f)
    }

    function zoom(ordem) {
        if (forca <= 0 || foco < -50) return 0
        var d = Math.abs(ordem + 0.5 - foco)
        return d >= raioAmpliacao ? 0 : forca * (1 + Math.cos(Math.PI * d / raioAmpliacao)) / 2
    }
    // Distância do centro da Ilha até um ponto (para os balões), ao longo da Ilha
    function ancora(item) {
        var p = item.mapToItem(ilhaFundo, item.width / 2, item.height / 2)
        return vertical ? p.y - height / 2 : p.x - width / 2
    }
    // Centro e tamanho do ícone de um aplicativo aberto (para o efeito de minimizar)
    function icone(appId) {
        for (var i = 0; i < repetidor.count; i++) {
            var d = repetidor.itemAt(i)
            if (d && d.dados.appId === appId) {
                var p = d.vaga.mapToItem(ilhaFundo, d.vaga.width / 2, d.vaga.height / 2)
                return { x: p.x, y: p.y, tamanho: base }
            }
        }
        return { x: width / 2, y: height / 2, tamanho: base }
    }

    // Arrastar para reorganizar (como no Dock do macOS): enquanto um fixado é arrastado, os outros
    // abrem espaço na posição em que ele vai cair. "origem" é o índice arrastado (em ilha.itens),
    // "destino" onde ele cai; ao soltar, os ícones ficam onde estão até a lista nova chegar.
    readonly property real passoArrasto: base + 8                 // vaga de repouso (base + 6) + espaço 2
    property int origem: -1
    property int destino: -1
    property bool tirando: false                                  // arrastado para fora: vai sair da Ilha
    // Faixa em que um fixado pode cair: depois do Wise e do Explorador, até o último fixado
    function limitesDoArrasto() {
        var primeiro = 0, ultimo = -1
        for (var i = 0; i < ilha.itens.length; i++) {
            var it = ilha.itens[i]
            if (!it.fixado) break
            if (it.id === "duiaos-wise.desktop" || it.id === "duiaos-explorador-de-arquivos.desktop") primeiro = i + 1
            ultimo = i
        }
        return [primeiro, Math.max(primeiro, ultimo)]
    }
    function arrastou(indice, deslocamento, tirar) {
        var l = limitesDoArrasto()
        origem = indice
        tirando = tirar
        destino = Math.max(l[0], Math.min(l[1], indice + Math.round(deslocamento / passoArrasto)))
    }
    // Quanto o ícone de índice i anda para abrir (ou fechar) espaço
    function desvio(i) {
        if (origem < 0 || i === origem) return 0
        if (tirando) return i > origem ? -passoArrasto : 0         // fecha o buraco de quem sai
        if (origem < destino && i > origem && i <= destino) return -passoArrasto
        if (destino < origem && i >= destino && i < origem) return passoArrasto
        return 0
    }
    function terminarArrasto() { origem = -1; destino = -1; tirando = false }
    // A lista nova chegou (ou não vai chegar: demonstração, nada mudou): volta ao normal
    Connections { target: ilha; function onMudou() { if (!ilhaFundo.arrastando) ilhaFundo.terminarArrasto() } }
    Timer { id: limparArrasto; interval: 700; onTriggered: if (!ilhaFundo.arrastando) ilhaFundo.terminarArrasto() }

    // Fundo arredondado, encostado na borda da tela
    Rectangle {
        id: fundo
        readonly property int comprimentoFundo: (ilhaFundo.vertical ? grade.height : grade.width) + 16
        width: ilhaFundo.vertical ? ilhaFundo.espessuraFundo : comprimentoFundo
        height: ilhaFundo.vertical ? comprimentoFundo : ilhaFundo.espessuraFundo
        x: ilhaFundo.posicao === "esquerda" ? 0 : (ilhaFundo.posicao === "direita" ? ilhaFundo.width - width : (ilhaFundo.width - width) / 2)
        y: ilhaFundo.vertical ? (ilhaFundo.height - height) / 2 : ilhaFundo.height - height
        radius: Tema.futurista ? 26 : 22
        color: Tema.ilha
        border { color: Tema.brilho; width: 1 }
        Rectangle { anchors { fill: parent; margins: -1 } radius: parent.radius + 1; color: "transparent"; border { color: Tema.borda; width: 1 } }
        // Botão direito no fundo: opções da Ilha (como no macOS)
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: (m) => ilha.abrirMenu("ilha", -1, ilhaFundo.vertical ? m.y + fundo.y - ilhaFundo.height / 2 : m.x + fundo.x - ilhaFundo.width / 2)
        }
    }

    // Ponto de aplicativo aberto
    component PontoAberto: Rectangle {
        width: Tema.futurista ? 10 : 4; height: 4; radius: 2      // futurista: um traço de luz
        color: Tema.futurista ? Tema.aurora1 : Tema.azulNoite
    }

    // Espaço de um ícone: ampliação, salto ao abrir, clique, arrastar (fixados) e botão direito
    component Vaga: Item {
        id: vaga
        property int ordem: 0
        property bool aberto: false
        property string nome: ""
        property string idDesktop: ""
        property bool arrastavel: false
        property bool podeTirar: false
        default property alias desenho: dentro.data
        readonly property real tam: ilhaFundo.base + (ilhaFundo.maximo - ilhaFundo.base) * ilhaFundo.zoom(ordem)
        property real salto: 0
        property point arrasto: Qt.point(0, 0)
        property int indice: -1                     // em ilha.itens (-1: Central, pasta, Downloads, Lixeira)
        // Abrindo espaço para o ícone arrastado, com animação (o arrastado segue o mouse, sem animação)
        property real desvio: indice >= 0 ? ilhaFundo.desvio(indice) : 0
        Behavior on desvio { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        signal clicado()
        signal menu(real ancora)
        signal soltou(int destino, bool tirar)
        width: ilhaFundo.vertical ? tam + 16 : tam + 6
        height: ilhaFundo.vertical ? tam + 6 : tam + 16
        z: area.pressed ? 2 : 0
        Accessible.role: Accessible.Button
        Accessible.name: nome

        // Salto ao abrir: o ícone sobe e desce enquanto o aplicativo não abre (até 3 vezes)
        SequentialAnimation {
            id: pulo
            loops: 3
            NumberAnimation { target: vaga; property: "salto"; to: ilhaFundo.folgaSalto * 0.85; duration: 260; easing.type: Easing.OutQuad }
            NumberAnimation { target: vaga; property: "salto"; to: 0; duration: 260; easing.type: Easing.InQuad }
        }
        onAbertoChanged: if (aberto && pulo.running) { pulo.stop(); salto = 0 }
        Connections {
            target: ilha
            function onPulando(id) { if (id !== "" && id === vaga.idDesktop && !vaga.aberto) pulo.restart() }
        }

        Item {
            id: dentro
            width: vaga.tam; height: width
            // Encostado do lado da borda: cresce para longe dela
            x: (ilhaFundo.posicao === "esquerda" ? 11 : (ilhaFundo.posicao === "direita" ? vaga.width - width - 11 : (vaga.width - width) / 2))
               + (ilhaFundo.posicao === "esquerda" ? vaga.salto : (ilhaFundo.posicao === "direita" ? -vaga.salto : 0)) + vaga.arrasto.x
               + (ilhaFundo.vertical ? 0 : vaga.desvio)
            y: (ilhaFundo.vertical ? (vaga.height - height) / 2 : vaga.height - height - 11) - (ilhaFundo.vertical ? 0 : vaga.salto) + vaga.arrasto.y
               + (ilhaFundo.vertical ? vaga.desvio : 0)
            scale: area.pressed && !ilhaFundo.arrastando ? 0.9 : 1.0
            opacity: ilhaFundo.arrastando && area.pressed && vaga.podeTirar && vaga.foraDaIlha ? 0.5 : 1.0
            Behavior on scale { NumberAnimation { duration: 100 } }
        }
        readonly property bool foraDaIlha: ilhaFundo.vertical ? Math.abs(arrasto.x) > 70 : arrasto.y < -70
        PontoAberto {
            visible: vaga.aberto && ilhaFundo.o.indicadores !== false
            x: ilhaFundo.posicao === "esquerda" ? 3 : (ilhaFundo.posicao === "direita" ? vaga.width - 7 : (vaga.width - width) / 2)
            y: ilhaFundo.vertical ? (vaga.height - height) / 2 : vaga.height - 6
        }
        MouseArea {
            id: area
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property point inicio
            property bool movendo: false
            onPressed: (m) => { inicio = Qt.point(m.x, m.y); movendo = false }
            onPositionChanged: (m) => {
                if (!(m.buttons & Qt.LeftButton) || !vaga.arrastavel) return
                var dx = m.x - inicio.x, dy = m.y - inicio.y
                if (!movendo && Math.abs(dx) + Math.abs(dy) > 8) { movendo = true; ilhaFundo.arrastando = true; limparArrasto.stop() }
                if (movendo) {
                    vaga.arrasto = Qt.point(dx, dy)
                    ilhaFundo.arrastou(vaga.indice, ilhaFundo.vertical ? dy : dx, vaga.podeTirar && vaga.foraDaIlha)
                }
            }
            onReleased: (m) => {
                // Primeiro o estado volta ao normal; a mudança da lista vem depois (Qt.callLater), porque
                // ela recria os ícones — inclusive este, no meio do próprio clique. Antes, o "soltou" vinha
                // primeiro, o ícone era destruído e o resto não rodava: a Ilha ficava presa em "arrastando"
                // (recebendo cliques na janela inteira, sem ampliação) até reiniciar a sessão (16/11).
                var eraArrasto = movendo, tirar = vaga.podeTirar && vaga.foraDaIlha, destino = ilhaFundo.destino
                movendo = false
                ilhaFundo.arrastando = false
                if (m.button === Qt.RightButton) {
                    vaga.arrasto = Qt.point(0, 0)
                    vaga.menu(ilhaFundo.ancora(vaga))
                } else if (eraArrasto) {
                    // O ícone fica na vaga onde caiu até a lista nova chegar (sem voltar e pular de novo)
                    var deslocamento = (destino - vaga.indice) * ilhaFundo.passoArrasto
                    vaga.arrasto = tirar ? vaga.arrasto : Qt.point(ilhaFundo.vertical ? 0 : deslocamento, ilhaFundo.vertical ? deslocamento : 0)
                    limparArrasto.restart()
                    var alvo = vaga
                    Qt.callLater(function () { alvo.soltou(destino, tirar) })
                } else {
                    vaga.arrasto = Qt.point(0, 0)
                    if (containsMouse) vaga.clicado()
                }
            }
            onCanceled: { movendo = false; ilhaFundo.arrastando = false; vaga.arrasto = Qt.point(0, 0); ilhaFundo.terminarArrasto() }
        }
        // Quando o arrasto termina (lista nova ou tempo esgotado), o ícone volta para a própria vaga
        Connections { target: ilhaFundo; function onOrigemChanged() { if (ilhaFundo.origem < 0 && !area.pressed) vaga.arrasto = Qt.point(0, 0) } }
    }

    // Divisória: ocupa a espessura de um ícone, com o traço no meio
    component Divisoria: Item {
        width: ilhaFundo.vertical ? ilhaFundo.base + 16 : 1
        height: ilhaFundo.vertical ? 1 : ilhaFundo.base + 16
        Rectangle {
            width: ilhaFundo.vertical ? ilhaFundo.base - 6 : 1
            height: ilhaFundo.vertical ? 1 : ilhaFundo.base - 6
            anchors.centerIn: parent
            color: Tema.bordaForte
        }
    }

    // Quem é de qual grupo: 0 fixados, 1 abertos não fixados, 2 recentes
    function grupo(i) { var it = ilha.itens[i]; return !it ? 0 : (it.fixado ? 0 : (it.recente ? 2 : 1)) }

    Grid {
        id: grade
        rows: ilhaFundo.vertical ? -1 : 1
        columns: ilhaFundo.vertical ? 1 : -1
        spacing: 2
        verticalItemAlignment: Grid.AlignBottom
        horizontalItemAlignment: ilhaFundo.posicao === "direita" ? Grid.AlignRight : (ilhaFundo.posicao === "esquerda" ? Grid.AlignLeft : Grid.AlignHCenter)
        // Encostada na borda, centrada ao longo da Ilha
        x: ilhaFundo.vertical ? (ilhaFundo.posicao === "esquerda" ? 0 : ilhaFundo.width - width) : (ilhaFundo.width - width) / 2
        y: ilhaFundo.vertical ? (ilhaFundo.height - height) / 2 : ilhaFundo.height - height

        Vaga {
            ordem: 0
            nome: "Central de Aplicativos"
            onClicado: ilha.alternarCentral()
            onMenu: (a) => ilha.abrirMenu("central", -1, a)
            Ladrilho { anchors.fill: parent; icone: "aplicativos"; estilo: "noite"; tamanho: parent.width; resolucao: ilhaFundo.maximo }
        }

        Repeater {
            id: repetidor
            model: ilha.itens
            delegate: Grid {
                id: delegado
                required property var modelData
                required property int index
                readonly property var dados: modelData
                property alias vaga: vagaApp
                z: ilhaFundo.origem === index ? 5 : 0           // o ícone arrastado passa por cima dos outros
                rows: ilhaFundo.vertical ? -1 : 1
                columns: ilhaFundo.vertical ? 1 : -1
                spacing: 2
                verticalItemAlignment: Grid.AlignVCenter
                horizontalItemAlignment: Grid.AlignHCenter
                // Divisória quando muda o grupo (fixados | abertos | recentes)
                Divisoria { visible: ilhaFundo.grupo(delegado.index) !== (delegado.index === 0 ? 0 : ilhaFundo.grupo(delegado.index - 1)) }
                Vaga {
                    id: vagaApp
                    ordem: delegado.index + 1
                    indice: delegado.index
                    nome: delegado.modelData.nome
                    idDesktop: delegado.modelData.id || ""
                    aberto: delegado.modelData.aberto
                    arrastavel: delegado.modelData.fixado === true
                    podeTirar: delegado.modelData.fixado === true && delegado.modelData.id !== "duiaos-wise.desktop"
                               && delegado.modelData.id !== "duiaos-explorador-de-arquivos.desktop"
                    opacity: delegado.modelData.recente ? 0.85 : 1
                    onClicado: ilha.ativar(delegado.index)
                    onMenu: (a) => ilha.abrirMenu("app", delegado.index, a)
                    onSoltou: (destino, tirar) => {
                        if (tirar) ilha.alternarFixado(delegado.modelData.id)
                        else if (destino >= 0 && destino !== delegado.index) ilha.moverFixado(delegado.modelData.id, destino)
                    }
                    Ladrilho {
                        visible: (delegado.modelData.iconeDuia || "") !== ""
                        anchors.fill: parent
                        icone: delegado.modelData.iconeDuia || "pasta"
                        estilo: delegado.modelData.iconeDuia === "engrenagem" ? "cinza" : "azul"
                        tamanho: parent.width; resolucao: ilhaFundo.maximo
                    }
                    IconeApp {
                        visible: (delegado.modelData.iconeDuia || "") === ""
                        anchors.fill: parent
                        icone: delegado.modelData.icone; nome: delegado.modelData.nome; tamanho: parent.width; resolucao: ilhaFundo.maximo
                    }
                }
            }
        }

        Item { width: 4; height: 4 }
        Divisoria {}
        Item { width: 4; height: 4 }

        Vaga {
            ordem: ilha.itens.length + 1
            nome: "Aplicativos"
            onClicado: ilha.abrirPasta("aplicativos")
            onMenu: (a) => ilha.abrirMenu("aplicativos", -1, a)
            Ladrilho { anchors.fill: parent; icone: "pasta-aplicativos"; estilo: "azul"; tamanho: parent.width; resolucao: ilhaFundo.maximo }
        }
        Vaga {
            id: vagaDownloads
            ordem: ilha.itens.length + 2
            nome: "Downloads"
            onClicado: ilha.alternarDownloads(ilhaFundo.ancora(vagaDownloads))
            onMenu: (a) => ilha.abrirMenu("downloads", -1, a)
            Ladrilho { anchors.fill: parent; icone: "pasta-downloads"; estilo: "azul"; tamanho: parent.width; resolucao: ilhaFundo.maximo }
        }
        Vaga {
            ordem: ilha.itens.length + 3
            nome: "Lixeira"
            onClicado: ilha.abrirPasta("lixeira")
            onMenu: (a) => ilha.abrirMenu("lixeira", -1, a)
            Ladrilho { anchors.fill: parent; icone: ilha.lixeiraCheia ? "lixeira-cheia" : "lixeira"; estilo: "claro"; tamanho: parent.width; resolucao: ilhaFundo.maximo }
        }
    }
}
