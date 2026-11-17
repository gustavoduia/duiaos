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
    // A ampliação continua enquanto arrasta (como no Dock do macOS): o foco segue o ícone arrastado
    property real forca: (sobre || arrastando) && o.ampliacao ? 1 : 0
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

    // Arrastar para reorganizar (como no Dock do macOS): o ícone arrastado segue o mouse, continua
    // ampliado, e os outros abrem espaço, deslizando, na posição em que ele vai cair. "origem" é o índice
    // arrastado (em ilha.itens), "destino" onde ele cai, "passoArrasto" o espaço que ele ocupa (a largura
    // da vaga dele, ampliada). Ao soltar, ele desliza até a vaga e só então a lista muda.
    property real passoArrasto: base + 8
    property int origem: -1
    property int destino: -1
    property bool tirando: false                                  // arrastado para fora: vai sair da Ilha
    property point ponteiro: Qt.point(0, 0)                       // o mouse, em coordenadas da Ilha, durante o arrasto
    // Faixa em que o ícone pode cair: depois do Wise e do Explorador, até o último fixado (um aberto que
    // ainda não está fixado pode ir até uma vaga depois do último fixado: ao soltar, ele passa a ficar na Ilha)
    function limitesDoArrasto(indice) {
        var primeiro = 0, ultimo = -1
        for (var i = 0; i < ilha.itens.length; i++) {
            var it = ilha.itens[i]
            if (!it.fixado) break
            if (it.id === "duiaos-wise.desktop" || it.id === "duiaos-explorador-de-arquivos.desktop") primeiro = i + 1
            ultimo = i
        }
        var fixado = ilha.itens[indice] && ilha.itens[indice].fixado
        return [primeiro, Math.max(primeiro, fixado ? ultimo : ultimo + 1)]
    }
    // O mouse ao longo da Ilha → em que vaga o ícone cai (a mesma conta estável da ampliação)
    function arrastou(indice, ponto, largura, tirar) {
        var l = limitesDoArrasto(indice)
        ponteiro = ponto
        origem = indice
        tirando = tirar
        passoArrasto = largura
        foco = focoEm(vertical ? ponto.y - height / 2 : ponto.x - width / 2)
        destino = Math.max(l[0], Math.min(l[1], Math.floor(foco) - 1))
    }
    // Quanto o ícone de índice i anda para abrir (ou fechar) espaço
    function desvio(i) {
        if (origem < 0 || i === origem) return 0
        if (tirando) return i > origem ? -passoArrasto : 0         // fecha o buraco de quem sai
        if (origem < destino && i > origem && i <= destino) return -passoArrasto
        if (destino < origem && i >= destino && i < origem) return passoArrasto
        return 0
    }
    // Onde a vaga de destino fica em relação à de origem (soma das vagas entre as duas, como estão agora)
    function deslocamentoAte(origemI, destinoI) {
        var total = 0
        if (destinoI > origemI) for (var i = origemI + 1; i <= destinoI; i++) total += (repetidor.itemAt(i) ? (vertical ? repetidor.itemAt(i).height : repetidor.itemAt(i).width) : 0) + grade.spacing
        else for (var j = destinoI; j < origemI; j++) total -= (repetidor.itemAt(j) ? (vertical ? repetidor.itemAt(j).height : repetidor.itemAt(j).width) : 0) + grade.spacing
        return total
    }
    function terminarArrasto() { origem = -1; destino = -1; tirando = false }
    // A lista nova chegou (ou não vai chegar: demonstração, nada mudou): volta ao normal
    Connections { target: ilha; function onMudou() { if (!ilhaFundo.arrastando) ilhaFundo.terminarArrasto() } }
    Timer { id: limparArrasto; interval: 900; onTriggered: if (!ilhaFundo.arrastando) ilhaFundo.terminarArrasto() }
    // Depois de soltar: espera o ícone deslizar até a vaga e só então muda a lista
    property var aoPousar: null
    Timer { id: pousar; interval: 230; onTriggered: { var f = ilhaFundo.aoPousar; ilhaFundo.aoPousar = null; if (f) f() } }

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
        // Arrastado: ampliado por inteiro (está debaixo do mouse). Os outros: pela posição em que estão
        // agora (a vaga mais o deslize), para a onda da ampliação acompanhar quem abriu espaço
        readonly property bool arrastada: ilhaFundo.origem >= 0 && indice === ilhaFundo.origem
        readonly property real ordemVisual: ordem + (ilhaFundo.passoArrasto > 0 ? desvio / ilhaFundo.passoArrasto : 0)
        readonly property real tam: ilhaFundo.base + (ilhaFundo.maximo - ilhaFundo.base) * (arrastada ? ilhaFundo.forca : ilhaFundo.zoom(ordemVisual))
        property real salto: 0
        property point arrasto: Qt.point(0, 0)
        // Ao soltar, o ícone desliza até a vaga (durante o arrasto, segue o mouse sem atraso)
        Behavior on arrasto { enabled: !area.pressed; PropertyAnimation { duration: 220; easing.type: Easing.OutCubic } }
        property int indice: -1                     // em ilha.itens (-1: Central, pasta, Downloads, Lixeira)
        // Abrindo espaço para o ícone arrastado, com animação (o arrastado segue o mouse, sem animação)
        property real desvio: indice >= 0 ? ilhaFundo.desvio(indice) : 0
        Behavior on desvio { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
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
            // Encostado do lado da borda: cresce para longe dela. xBase/yBase: a posição na própria vaga
            readonly property real xBase: (ilhaFundo.posicao === "esquerda" ? 11 : (ilhaFundo.posicao === "direita" ? vaga.width - width - 11 : (vaga.width - width) / 2))
                                          + (ilhaFundo.posicao === "esquerda" ? vaga.salto : (ilhaFundo.posicao === "direita" ? -vaga.salto : 0))
            readonly property real yBase: (ilhaFundo.vertical ? (vaga.height - height) / 2 : vaga.height - height - 11) - (ilhaFundo.vertical ? 0 : vaga.salto)
            x: xBase + vaga.arrasto.x + (ilhaFundo.vertical ? 0 : vaga.desvio)
            y: yBase + vaga.arrasto.y + (ilhaFundo.vertical ? vaga.desvio : 0)
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
            property point pega: Qt.point(0.5, 0.5)        // onde o ícone foi pego (fração da largura e da altura)
            onPressed: (m) => {
                inicio = Qt.point(m.x, m.y); movendo = false
                pega = Qt.point((m.x - dentro.xBase) / dentro.width, (m.y - dentro.yBase) / dentro.height)
            }
            // O ícone arrastado fica sempre debaixo do mouse, mesmo quando a vaga dele anda (a ampliação muda
            // as larguras): a posição é refeita a cada quadro a partir do mouse, não só quando ele se move
            // (o mesmo ponto do ícone fica debaixo do mouse, mesmo com o ícone crescendo)
            function seguir() {
                var p = vaga.mapFromItem(ilhaFundo, ilhaFundo.ponteiro.x, ilhaFundo.ponteiro.y)
                vaga.arrasto = Qt.point(p.x - pega.x * dentro.width - dentro.xBase, p.y - pega.y * dentro.height - dentro.yBase)
            }
            Timer { interval: 16; repeat: true; running: area.movendo && area.pressed; onTriggered: area.seguir() }
            onPositionChanged: (m) => {
                if (!(m.buttons & Qt.LeftButton) || !vaga.arrastavel) return
                var dx = m.x - inicio.x, dy = m.y - inicio.y
                if (!movendo && Math.abs(dx) + Math.abs(dy) > 8) { movendo = true; ilhaFundo.arrastando = true; limparArrasto.stop(); pousar.stop() }
                if (movendo) {
                    var largura = (ilhaFundo.vertical ? vaga.height : vaga.width) + grade.spacing
                    ilhaFundo.arrastou(vaga.indice, area.mapToItem(ilhaFundo, m.x, m.y), largura, vaga.podeTirar && vaga.foraDaIlha)
                    seguir()
                }
            }
            onReleased: (m) => {
                // Primeiro o estado volta ao normal; a mudança da lista vem depois, porque ela recria os ícones
                // — inclusive este, no meio do próprio clique. Antes, o "soltou" vinha primeiro, o ícone era
                // destruído e o resto não rodava: a Ilha ficava presa em "arrastando" (16/11).
                var eraArrasto = movendo, tirar = vaga.podeTirar && vaga.foraDaIlha, destino = ilhaFundo.destino
                var deslocamento = eraArrasto && !tirar ? ilhaFundo.deslocamentoAte(vaga.indice, destino) : 0
                movendo = false
                ilhaFundo.arrastando = false
                if (m.button === Qt.RightButton) {
                    vaga.arrasto = Qt.point(0, 0)
                    vaga.menu(ilhaFundo.ancora(vaga))
                } else if (eraArrasto) {
                    // Desliza até a vaga onde caiu (Behavior) e fica lá até a lista nova chegar
                    if (!tirar) vaga.arrasto = Qt.point(ilhaFundo.vertical ? 0 : deslocamento, ilhaFundo.vertical ? deslocamento : 0)
                    limparArrasto.restart()
                    var alvo = vaga
                    ilhaFundo.aoPousar = function () { alvo.soltou(destino, tirar) }
                    pousar.restart()
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
            Ladrilho { anchors.fill: parent; icone: "aplicativos"; estilo: "noite"; tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base }
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
                    // Fixados e abertos com atalho (um aberto arrastado para os fixados passa a ficar na Ilha)
                    arrastavel: (delegado.modelData.fixado === true || (delegado.modelData.aberto && (delegado.modelData.id || "") !== ""
                                                                        && !delegado.modelData.recente))
                                && delegado.modelData.id !== "duiaos-wise.desktop" && delegado.modelData.id !== "duiaos-explorador-de-arquivos.desktop"
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
                        tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base
                    }
                    IconeApp {
                        visible: (delegado.modelData.iconeDuia || "") === ""
                        anchors.fill: parent
                        icone: delegado.modelData.icone; nome: delegado.modelData.nome; tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base
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
            Ladrilho { anchors.fill: parent; icone: "pasta-aplicativos"; estilo: "azul"; tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base }
        }
        Vaga {
            id: vagaDownloads
            ordem: ilha.itens.length + 2
            nome: "Downloads"
            onClicado: ilha.alternarDownloads(ilhaFundo.ancora(vagaDownloads))
            onMenu: (a) => ilha.abrirMenu("downloads", -1, a)
            Ladrilho { anchors.fill: parent; icone: "pasta-downloads"; estilo: "azul"; tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base }
        }
        Vaga {
            ordem: ilha.itens.length + 3
            nome: "Lixeira"
            onClicado: ilha.abrirPasta("lixeira")
            onMenu: (a) => ilha.abrirMenu("lixeira", -1, a)
            Ladrilho { anchors.fill: parent; icone: ilha.lixeiraCheia ? "lixeira-cheia" : "lixeira"; estilo: "claro"; tamanho: parent.width; resolucao: ilhaFundo.maximo; base: ilhaFundo.base }
        }
    }
}
