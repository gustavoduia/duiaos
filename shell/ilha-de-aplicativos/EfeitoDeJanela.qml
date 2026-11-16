// DuiaOS — efeito de minimizar e restaurar janelas (gênio ou escala), desenhado pela Ilha por cima
// de tudo, porque o labwc não tem animações. A Ilha captura a tela (main.py) e manda:
//   { direcao: minimizar|restaurar, efeito: genio|escala, imagem, x, y, w, h (lugar da janela) }
// e "alvo" diz onde está o ícone do aplicativo.
//
// Sem piscar (ADR 056): antes de a janela de verdade sumir, esta camada mostra a tela "congelada"
// (telaCongelada). A janela some por baixo, a Ilha descobre onde ela estava e o efeito começa do
// mesmo quadro que a pessoa já estava vendo.
//
// Gênio, como no macOS: primeiro os lados da janela se curvam na direção do ícone, formando um
// funil; depois a janela escorre por ele até entrar no ícone. A janela é dividida em faixas, e cada
// faixa é um trapézio (transformação projetiva), então as bordas saem inclinadas e contínuas, não
// em degraus. Sem placa de vídeo (testes), as faixas são retângulos finos (GenioFaixas).
import QtQuick

Item {
    id: efeito
    property var dados: ({})
    property var alvo: ({ x: width / 2, y: height, tamanho: 46 })
    property string lado: "base"              // onde está a Ilha: base, esquerda, direita
    property real p: 0                        // 0 = janela no lugar, 1 = dentro do ícone
    readonly property bool genio: dados.efeito === "genio"
    readonly property bool comPlaca: GraphicsInfo.api !== GraphicsInfo.Software
    signal terminou(string appId, string direcao)

    // Tela congelada (antes de o efeito começar)
    property string telaCongelada: ""
    property real opacidadeDaTela: 1
    Image {
        anchors.fill: parent
        visible: efeito.telaCongelada !== ""
        source: efeito.telaCongelada
        opacity: efeito.opacidadeDaTela
        asynchronous: false
        cache: false
    }

    function iniciar(d, a) {
        dados = d
        alvo = a
        animacao.stop()
        animacao.from = d.direcao === "restaurar" ? 1 : 0
        animacao.to = d.direcao === "restaurar" ? 0 : 1
        p = animacao.from
        visible = true
        telaCongelada = ""                    // a imagem da janela já está no lugar (carrega na hora)
        animacao.start()
    }
    function cancelar() { animacao.stop(); telaCongelada = ""; visible = false }
    // Mostra um quadro parado (demonstração e testes)
    function quadro(d, a, progresso) { dados = d; alvo = a; p = progresso; visible = true }

    NumberAnimation {
        id: animacao
        target: efeito; property: "p"
        duration: efeito.genio ? (efeito.dados.direcao === "restaurar" ? 460 : 520) : 380
        easing.type: Easing.Linear             // as curvas do gênio já aceleram e freiam
        onFinished: {
            efeito.terminou(efeito.dados.appId || "", efeito.dados.direcao || "")
            esconder.restart()
        }
    }
    // Ao restaurar, a janela de verdade leva um instante para voltar: o último quadro fica um pouco
    Timer { id: esconder; interval: efeito.dados.direcao === "restaurar" ? 160 : 0; onTriggered: efeito.visible = false }

    function suave(t) { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t) }
    function misturar(a, b, t) { return a + (b - a) * t }

    // Coordenadas "ao longo" (a: na direção da Ilha, crescendo para ela) e "de lado" (c)
    readonly property real a0: lado === "esquerda" ? -((dados.x || 0) + (dados.w || 0)) : (lado === "direita" ? (dados.x || 0) : (dados.y || 0))
    readonly property real comprimentoA: lado === "base" ? (dados.h || 1) : (dados.w || 1)
    readonly property real c0: lado === "base" ? (dados.x || 0) : (dados.y || 0)
    readonly property real comprimentoC: lado === "base" ? (dados.w || 1) : (dados.h || 1)
    // O centro do ícone, ao longo e de lado
    readonly property real alvoA: Math.max(a0 + comprimentoA + 1, lado === "esquerda" ? -alvo.x : (lado === "direita" ? alvo.x : alvo.y))
    readonly property real alvoC: lado === "base" ? alvo.x : alvo.y

    // ---- A forma do gênio
    // 1ª parte (p de 0 a 0,45): o funil se forma. 2ª parte (p de 0,2 a 1): a janela escorre por ele.
    readonly property real funil: suave(p / 0.45)
    readonly property real escorrido: { var t = Math.max(0, (p - 0.2) / 0.8); return (alvoA - a0) * t * t * (3 - 2 * t) * (0.55 + 0.45 * t) }
    // Onde fica (ao longo) a linha v da janela (0 = lado longe da Ilha, 1 = lado perto)
    function posicaoA(v) { return Math.min(a0 + v * comprimentoA + escorrido, alvoA) }
    // As bordas do funil (de lado) na altura a: retas na janela, curvando até a largura do ícone
    function borda(a, direita) {
        var naJanela = direita ? c0 + comprimentoC : c0
        var noIcone = alvoC + (direita ? 0.5 : -0.5) * alvo.tamanho
        var t = (a - a0) / (alvoA - a0)
        var curva = 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, t)))
        return misturar(naJanela, misturar(naJanela, noIcone, curva), funil)
    }
    readonly property real opacidadeFinal: p > 0.93 ? (1 - p) / 0.07 : 1

    // A imagem da janela (a mesma para a escala e para as faixas do gênio)
    Image {
        id: figura
        visible: !efeito.genio && efeito.visible
        source: efeito.visible ? (efeito.dados.imagem || "") : ""
        readonly property real t: efeito.suave(efeito.p)
        x: efeito.misturar(efeito.dados.x || 0, efeito.alvo.x - efeito.alvo.tamanho / 2, t)
        y: efeito.misturar(efeito.dados.y || 0, efeito.alvo.y - efeito.alvo.tamanho / 2, t)
        width: efeito.genio ? (efeito.dados.w || 1) : efeito.misturar(efeito.dados.w || 1, efeito.alvo.tamanho, t)
        height: efeito.genio ? (efeito.dados.h || 1) : efeito.misturar(efeito.dados.h || 1, efeito.alvo.tamanho, t)
        opacity: 1 - 0.75 * t
        fillMode: Image.Stretch
        smooth: true
        mipmap: true
        asynchronous: false
        cache: false
    }

    Loader {
        anchors.fill: parent
        active: efeito.genio && efeito.visible && figura.status === Image.Ready
        sourceComponent: efeito.comPlaca ? malha : faixasSimples
    }

    // Gênio com placa de vídeo: faixas em trapézio
    Component {
        id: malha
        Item {
            id: desenho
            readonly property int faixas: 48
            opacity: efeito.opacidadeFinal
            Repeater {
                model: desenho.faixas
                delegate: ShaderEffectSource {
                    id: faixa
                    required property int index
                    readonly property real v0: index / desenho.faixas
                    readonly property real v1: (index + 1) / desenho.faixas
                    // O pedaço da janela que esta faixa mostra
                    readonly property real fatia: efeito.comprimentoA / desenho.faixas
                    sourceItem: figura
                    sourceRect: efeito.lado === "base" ? Qt.rect(0, index * fatia, efeito.comprimentoC, fatia)
                        : (efeito.lado === "direita" ? Qt.rect(index * fatia, 0, fatia, efeito.comprimentoC)
                           : Qt.rect((desenho.faixas - index - 1) * fatia, 0, fatia, efeito.comprimentoC))
                    width: sourceRect.width; height: sourceRect.height
                    live: false
                    hideSource: false
                    smooth: true
                    mipmap: true
                    // Os quatro cantos na tela: (longe, perto) × (esquerda, direita)
                    readonly property real aL: efeito.posicaoA(v0)
                    readonly property real aP: efeito.posicaoA(v1) + (index < desenho.faixas - 1 ? 0.5 : 0)   // meio ponto a mais: sem frestas
                    visible: aP - aL > 0.05
                    transform: Matrix4x4 {
                        matrix: {
                            var eL = efeito.borda(faixa.aL, false), dL = efeito.borda(faixa.aL, true)
                            var eP = efeito.borda(faixa.aP, false), dP = efeito.borda(faixa.aP, true)
                            // Cantos do item, em ordem: (0,0) (w,0) (w,h) (0,h) → pontos na tela
                            if (efeito.lado === "base")
                                return efeito.projetiva(faixa.width, faixa.height, eL, faixa.aL, dL, faixa.aL, dP, faixa.aP, eP, faixa.aP)
                            if (efeito.lado === "direita")
                                return efeito.projetiva(faixa.width, faixa.height, faixa.aL, eL, faixa.aP, eP, faixa.aP, dP, faixa.aL, dL)
                            return efeito.projetiva(faixa.width, faixa.height, -faixa.aP, eP, -faixa.aL, eL, -faixa.aL, dL, -faixa.aP, dP)
                        }
                    }
                }
            }
        }
    }
    // Matriz que leva o retângulo l × a aos quatro pontos dados (Heckbert, 1989)
    function projetiva(l, a, x0, y0, x1, y1, x2, y2, x3, y3) {
        var dx1 = x1 - x2, dx2 = x3 - x2, sx = x0 - x1 + x2 - x3
        var dy1 = y1 - y2, dy2 = y3 - y2, sy = y0 - y1 + y2 - y3
        var g = 0, h = 0, det = dx1 * dy2 - dx2 * dy1
        if ((Math.abs(sx) > 1e-6 || Math.abs(sy) > 1e-6) && Math.abs(det) > 1e-9) {
            g = (sx * dy2 - dx2 * sy) / det
            h = (dx1 * sy - sx * dy1) / det
        }
        return Qt.matrix4x4((x1 - x0 + g * x1) / l, (x3 - x0 + h * x3) / a, 0, x0,
                            (y1 - y0 + g * y1) / l, (y3 - y0 + h * y3) / a, 0, y0,
                            0, 0, 1, 0,
                            g / l, h / a, 0, 1)
    }

    // Gênio sem placa de vídeo (desenho por software): faixas retangulares finas
    Component {
        id: faixasSimples
        Item {
            id: simples
            readonly property int faixas: Math.max(48, Math.min(160, Math.round(efeito.comprimentoA / 4)))
            opacity: efeito.opacidadeFinal
            Repeater {
                model: simples.faixas
                delegate: Item {
                    id: tira
                    required property int index
                    readonly property real v0: index / simples.faixas
                    readonly property real v1: (index + 1) / simples.faixas
                    readonly property real inicioA: efeito.posicaoA(v0)
                    readonly property real fimA: efeito.posicaoA(v1)
                    readonly property real meio: (inicioA + fimA) / 2
                    readonly property real esq: efeito.borda(meio, false)
                    readonly property real largC: Math.max(1, efeito.borda(meio, true) - esq)
                    readonly property real compA: fimA - inicioA + 0.6
                    visible: fimA - inicioA > 0.05
                    x: efeito.lado === "base" ? esq : (efeito.lado === "esquerda" ? -inicioA - compA : inicioA)
                    y: efeito.lado === "base" ? inicioA : esq
                    width: efeito.lado === "base" ? largC : compA
                    height: efeito.lado === "base" ? compA : largC
                    clip: true
                    Image {
                        source: efeito.dados.imagem || ""
                        cache: true
                        smooth: true
                        fillMode: Image.Stretch
                        // A imagem inteira, esticada para que só a fatia desta tira apareça dentro dela
                        readonly property real escalaA: tira.compA / (efeito.comprimentoA / simples.faixas)
                        readonly property real escalaC: tira.largC / efeito.comprimentoC
                        width: efeito.lado === "base" ? efeito.comprimentoC * escalaC : efeito.comprimentoA * escalaA
                        height: efeito.lado === "base" ? efeito.comprimentoA * escalaA : efeito.comprimentoC * escalaC
                        x: efeito.lado === "base" ? 0
                           : (efeito.lado === "esquerda" ? -(simples.faixas - tira.index - 1) * tira.compA : -tira.index * tira.compA)
                        y: efeito.lado === "base" ? -tira.index * tira.compA : 0
                    }
                }
            }
        }
    }
}
