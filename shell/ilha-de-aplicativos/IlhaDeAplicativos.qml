// DuiaOS — Ilha de Aplicativos.
// Uma faixa arredondada encostada na borda da tela (embaixo, à esquerda ou à direita), com a
// Central de Aplicativos, os aplicativos fixados e os abertos (ponto) e, depois da divisória, a
// pasta Aplicativos, a pilha de Downloads e a Lixeira. Ampliação ao passar o mouse, ocultar
// automaticamente e efeito ao minimizar (EfeitoDeJanela.qml) vêm de ilha.opcoes.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum/telas.js" as Telas

Window {
    id: janela
    // Fica na tela principal (a do notebook, quando houver; comum/telas.js)
    screen: Telas.principal(Qt.application.screens)
    readonly property int distanciaBorda: 8   // espaço entre a Ilha e a borda da tela
    readonly property string posicao: conteudo.posicao
    readonly property bool vertical: conteudo.vertical
    readonly property bool ocultar: ilha.opcoes.ocultar === true
    // Ocultar automaticamente: aparece ao encostar o mouse na borda; some 0,7 s depois de sair
    property bool mostrada: !ocultar
    readonly property bool emUso: conteudo.sobre || bordaSensivel.hovered || ilha.menu.tipo !== undefined
                                  || ilha.downloadsVisivel || conteudo.arrastando
    onEmUsoChanged: if (emUso) { mostrada = true; esconder.stop() } else if (ocultar) esconder.restart()
    onOcultarChanged: { mostrada = !ocultar || emUso }
    Timer { id: esconder; interval: 700; onTriggered: if (!janela.emUso && janela.ocultar) janela.mostrada = false }

    width: vertical ? conteudo.width + distanciaBorda : Math.max(conteudo.width, 120)
    height: vertical ? Math.max(conteudo.height, 120) : conteudo.height + distanciaBorda
    visible: true
    color: "transparent"
    title: "Ilha de Aplicativos"

    LayerShell.Window.anchors: posicao === "esquerda" ? LayerShell.Window.AnchorLeft
                              : (posicao === "direita" ? LayerShell.Window.AnchorRight : LayerShell.Window.AnchorBottom)
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    // A área reservada é só a do fundo (a folga da ampliação fica por cima das janelas)
    LayerShell.Window.exclusionZone: ocultar ? 0 : conteudo.espessuraFundo + distanciaBorda
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.scope: "duiaos-ilha-de-aplicativos"

    // Quanto a Ilha anda para fora da tela quando está escondida
    property real recuo: mostrada ? 0 : conteudo.espessuraFundo + distanciaBorda + 4
    Behavior on recuo { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

    Ilha {
        id: conteudo
        x: janela.posicao === "esquerda" ? janela.distanciaBorda - janela.recuo
           : (janela.posicao === "direita" ? janela.recuo : 0)
        y: janela.vertical ? 0 : janela.recuo
    }

    // Faixa de 3 px na borda da tela: com a Ilha escondida, encostar o mouse aqui a mostra
    Item {
        id: borda
        width: janela.vertical ? 3 : janela.width
        height: janela.vertical ? janela.height : 3
        x: janela.posicao === "direita" ? janela.width - 3 : 0
        y: janela.vertical ? 0 : janela.height - 3
        HoverHandler { id: bordaSensivel }
    }

    // Onde a Ilha recebe cliques (o resto deixa passar para as janelas de baixo):
    // escondida → só a faixa da borda; com o mouse em cima → a janela toda (os ícones ampliados);
    // parada → o fundo da Ilha.
    function atualizarMascara() {
        if (!janela.mostrada && janela.recuo > 0)
            ilha.definirMascara(janela, borda.x, borda.y, borda.width, borda.height)
        else if (conteudo.sobre || conteudo.arrastando)
            ilha.definirMascara(janela, 0, 0, janela.width, janela.height)
        else {
            // O fundo da Ilha, esticado até a borda da tela
            var f = conteudo.faixa
            var x = conteudo.x + f.x, y = conteudo.y + f.y
            if (janela.posicao === "esquerda") ilha.definirMascara(janela, 0, y, x + f.width, f.height)
            else if (janela.posicao === "direita") ilha.definirMascara(janela, x, y, janela.width - x, f.height)
            else ilha.definirMascara(janela, x, y, f.width, janela.height - y)
        }
    }
    Timer { id: mascaraAtrasada; interval: 30; onTriggered: janela.atualizarMascara() }
    Connections { target: conteudo; function onSobreChanged() { mascaraAtrasada.restart() } function onArrastandoChanged() { mascaraAtrasada.restart() }
                  function onFaixaChanged() { mascaraAtrasada.restart() } }
    onMostradaChanged: mascaraAtrasada.restart()
    onRecuoChanged: if (recuo === 0 || !mostrada) mascaraAtrasada.restart()
    onWidthChanged: mascaraAtrasada.restart()
    onHeightChanged: mascaraAtrasada.restart()
    Component.onCompleted: { ilha.definirTela(janela.screen ? janela.screen.name : ""); mascaraAtrasada.restart() }
    onScreenChanged: ilha.definirTela(janela.screen ? janela.screen.name : "")

    // Central de Aplicativos (janela própria, aparece por cima de tudo)
    CentralDeAplicativos {}

    // Pilha de Downloads e menu do botão direito (camada por cima da área de trabalho; clique fora fecha)
    Window {
        screen: janela.screen
        width: Screen.width; height: Screen.height      // o compositor ajusta à área livre
        visible: ilha.downloadsVisivel || ilha.menu.tipo !== undefined
        color: "transparent"
        title: "Downloads"
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                   | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        LayerShell.Window.scope: "duiaos-pilha-de-downloads"
        ConteudoDownloads { anchors.fill: parent; visible: ilha.downloadsVisivel }
        MenuDaIlha { anchors.fill: parent; visible: ilha.menu.tipo !== undefined }
    }

    // Efeito de minimizar e restaurar: camada na tela inteira, por cima de tudo, sem receber cliques
    Window {
        id: janelaEfeito
        screen: janela.screen
        width: Screen.width; height: Screen.height
        visible: efeito.visible
        color: "transparent"
        title: "Efeito de janela"
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                   | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.exclusionZone: -1
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        LayerShell.Window.scope: "duiaos-efeito-de-janela"
        onVisibleChanged: if (visible) ilha.definirMascara(janelaEfeito, 0, 0, 1, 1)
        EfeitoDeJanela {
            id: efeito
            anchors.fill: parent
            visible: false
            lado: janela.posicao
            onTerminou: (appId, direcao) => ilha.efeitoTerminou(appId, direcao)
        }
    }

    // Onde está, na tela, o ícone de um aplicativo (alvo do efeito). A janela da Ilha fica
    // centrada ao longo da borda; a Barra de Recursos de lado desloca pouco (aceitável no efeito).
    function alvoNaTela(appId) {
        var i = conteudo.icone(appId)
        var tela = janela.screen
        var larguraTela = tela ? tela.width : janela.width, alturaTela = tela ? tela.height : janela.height
        var x0 = posicao === "esquerda" ? 0 : (posicao === "direita" ? larguraTela - janela.width : (larguraTela - janela.width) / 2)
        var y0 = vertical ? (alturaTela - janela.height) / 2 : alturaTela - janela.height
        return { x: x0 + conteudo.x + i.x, y: y0 + conteudo.y + i.y, tamanho: i.tamanho }
    }
    Connections {
        target: ilha
        function onEfeito(dados) {
            if (!janela.mostrada) { janela.mostrada = true; esconder.restart() }   // a Ilha aparece para receber a janela
            efeito.iniciar(dados, janela.alvoNaTela(dados.appId))
        }
    }
}
