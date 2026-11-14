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

    // Espessura do fundo (sem ampliação) e da janela (com espaço para a ampliação e o salto)
    readonly property int espessuraFundo: base + 22
    readonly property int espessura: espessuraFundo + Math.max(maximo - base, folgaSalto)
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

    // Mouse sobre a Ilha: posição em "vagas" (0 = Central de Aplicativos) para a ampliação
    property real foco: -100
    property bool sobre: hover.hovered
    property bool arrastando: false
    onSobreChanged: if (!sobre && !arrastando) foco = -100
    HoverHandler { id: hover }

    // Faixa da borda (só o fundo); a janela usa para saber onde recebe cliques
    readonly property rect faixa: Qt.rect(fundo.x, fundo.y, fundo.width, fundo.height)

    function zoom(ordem) {
        if (!o.ampliacao || foco < -1) return 0
        var d = Math.abs(ordem + 0.5 - foco)
        return d >= raioAmpliacao ? 0 : (1 + Math.cos(Math.PI * d / raioAmpliacao)) / 2
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

    // Fundo arredondado, encostado na borda da tela
    Rectangle {
        id: fundo
        readonly property int comprimentoFundo: (ilhaFundo.vertical ? grade.height : grade.width) + 16
        width: ilhaFundo.vertical ? ilhaFundo.espessuraFundo : comprimentoFundo
        height: ilhaFundo.vertical ? comprimentoFundo : ilhaFundo.espessuraFundo
        x: ilhaFundo.posicao === "esquerda" ? 0 : (ilhaFundo.posicao === "direita" ? ilhaFundo.width - width : (ilhaFundo.width - width) / 2)
        y: ilhaFundo.vertical ? (ilhaFundo.height - height) / 2 : ilhaFundo.height - height
        radius: 22
        color: Tema.ilha
        border { color: Qt.rgba(1, 1, 1, 0.9); width: 1 }
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
        width: 4; height: 4; radius: 2
        color: Tema.azulNoite
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
        signal clicado()
        signal menu(real ancora)
        signal soltou(int passos, bool tirar)
        width: ilhaFundo.vertical ? tam + 16 : tam + 6
        height: ilhaFundo.vertical ? tam + 6 : tam + 16
        Behavior on width { enabled: !ilhaFundo.sobre; NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        Behavior on height { enabled: !ilhaFundo.sobre; NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
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

        HoverHandler {
            onPointChanged: {
                if (!hovered || ilhaFundo.arrastando) return
                var f = ilhaFundo.vertical ? point.position.y / vaga.height : point.position.x / vaga.width
                ilhaFundo.foco = vaga.ordem + Math.max(0, Math.min(1, f))
            }
        }
        Item {
            id: dentro
            width: vaga.tam; height: width
            // Encostado do lado da borda: cresce para longe dela
            x: (ilhaFundo.posicao === "esquerda" ? 11 : (ilhaFundo.posicao === "direita" ? vaga.width - width - 11 : (vaga.width - width) / 2))
               + (ilhaFundo.posicao === "esquerda" ? vaga.salto : (ilhaFundo.posicao === "direita" ? -vaga.salto : 0)) + vaga.arrasto.x
            y: (ilhaFundo.vertical ? (vaga.height - height) / 2 : vaga.height - height - 11) - (ilhaFundo.vertical ? 0 : vaga.salto) + vaga.arrasto.y
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
                if (!movendo && Math.abs(dx) + Math.abs(dy) > 8) { movendo = true; ilhaFundo.arrastando = true }
                if (movendo) vaga.arrasto = Qt.point(dx, dy)
            }
            onReleased: (m) => {
                if (m.button === Qt.RightButton) {
                    vaga.menu(ilhaFundo.ancora(vaga))
                } else if (movendo) {
                    var passo = ilhaFundo.base + 8
                    var passos = Math.round((ilhaFundo.vertical ? vaga.arrasto.y : vaga.arrasto.x) / passo)
                    vaga.soltou(passos, vaga.podeTirar && vaga.foraDaIlha)
                } else if (containsMouse) {
                    vaga.clicado()
                }
                movendo = false
                ilhaFundo.arrastando = false
                vaga.arrasto = Qt.point(0, 0)
                if (!ilhaFundo.sobre) ilhaFundo.foco = -100
            }
        }
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
            Ladrilho { anchors.fill: parent; icone: "aplicativos"; estilo: "noite"; tamanho: parent.width }
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
                    nome: delegado.modelData.nome
                    idDesktop: delegado.modelData.id || ""
                    aberto: delegado.modelData.aberto
                    arrastavel: delegado.modelData.fixado === true
                    podeTirar: delegado.modelData.fixado === true && delegado.modelData.id !== "duiaos-wise.desktop"
                               && delegado.modelData.id !== "duiaos-explorador-de-arquivos.desktop"
                    opacity: delegado.modelData.recente ? 0.85 : 1
                    onClicado: ilha.ativar(delegado.index)
                    onMenu: (a) => ilha.abrirMenu("app", delegado.index, a)
                    onSoltou: (passos, tirar) => {
                        if (tirar) ilha.alternarFixado(delegado.modelData.id)
                        else if (passos !== 0) ilha.moverFixado(delegado.modelData.id, delegado.index + passos)
                    }
                    Ladrilho {
                        visible: (delegado.modelData.iconeDuia || "") !== ""
                        anchors.fill: parent
                        icone: delegado.modelData.iconeDuia || "pasta"
                        estilo: delegado.modelData.iconeDuia === "engrenagem" ? "cinza" : "azul"
                        tamanho: parent.width
                    }
                    IconeApp {
                        visible: (delegado.modelData.iconeDuia || "") === ""
                        anchors.fill: parent
                        icone: delegado.modelData.icone; nome: delegado.modelData.nome; tamanho: parent.width
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
            Ladrilho { anchors.fill: parent; icone: "pasta-aplicativos"; estilo: "azul"; tamanho: parent.width }
        }
        Vaga {
            id: vagaDownloads
            ordem: ilha.itens.length + 2
            nome: "Downloads"
            onClicado: ilha.alternarDownloads(ilhaFundo.ancora(vagaDownloads))
            onMenu: (a) => ilha.abrirMenu("downloads", -1, a)
            Ladrilho { anchors.fill: parent; icone: "pasta-downloads"; estilo: "azul"; tamanho: parent.width }
        }
        Vaga {
            ordem: ilha.itens.length + 3
            nome: "Lixeira"
            onClicado: ilha.abrirPasta("lixeira")
            onMenu: (a) => ilha.abrirMenu("lixeira", -1, a)
            Ladrilho { anchors.fill: parent; icone: ilha.lixeiraCheia ? "lixeira-cheia" : "lixeira"; estilo: "claro"; tamanho: parent.width }
        }
    }
}
