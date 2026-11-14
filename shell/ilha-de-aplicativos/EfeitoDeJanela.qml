// DuiaOS — efeito de minimizar e restaurar janelas (gênio ou escala), desenhado pela Ilha por cima
// de tudo, porque o labwc não tem animações. A Ilha captura a janela (main.py) e manda:
//   { direcao: minimizar|restaurar, efeito: genio|escala, imagem, x, y, w, h (lugar da janela) }
// e "alvo" diz onde está o ícone do aplicativo. Gênio: a janela é cortada em faixas que afinam e
// escorrem até o ícone, como no macOS; escala: encolhe e desliza até o ícone, ficando transparente.
import QtQuick

Item {
    id: efeito
    property var dados: ({})
    property var alvo: ({ x: width / 2, y: height, tamanho: 46 })
    property string lado: "base"              // onde está a Ilha: base, esquerda, direita
    property real p: 0                        // 0 = janela no lugar, 1 = dentro do ícone
    readonly property int faixas: 64
    readonly property bool genio: dados.efeito === "genio"
    signal terminou(string appId, string direcao)

    function iniciar(d, a) {
        dados = d
        alvo = a
        animacao.stop()
        animacao.from = d.direcao === "restaurar" ? 1 : 0
        animacao.to = d.direcao === "restaurar" ? 0 : 1
        p = animacao.from
        visible = true
        animacao.start()
    }
    // Mostra um quadro parado (demonstração e testes)
    function quadro(d, a, progresso) { dados = d; alvo = a; p = progresso; visible = true }

    NumberAnimation {
        id: animacao
        target: efeito; property: "p"
        duration: efeito.dados.direcao === "restaurar" ? 420 : 480
        easing.type: Easing.InOutSine
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
    readonly property real alvoA: lado === "esquerda" ? -alvo.x - alvo.tamanho / 2 : (lado === "direita" ? alvo.x - alvo.tamanho / 2 : alvo.y - alvo.tamanho / 2)
    readonly property real alvoC: lado === "base" ? alvo.x : alvo.y

    // Gênio: v de 0 (lado longe da Ilha) a 1 (lado perto); o lado perto começa antes
    function local(v) { var k = 1.0; return Math.max(0, Math.min(1, p * (1 + k) - k * (1 - v))) }
    function posicaoA(v) { return misturar(a0 + v * comprimentoA, alvoA + v * alvo.tamanho, suave(local(v))) }
    function aperto(v) { return suave(Math.min(1, local(v) * 1.7)) }

    // Escala
    Image {
        visible: !efeito.genio
        source: efeito.visible && !efeito.genio ? (efeito.dados.imagem || "") : ""
        readonly property real t: efeito.suave(efeito.p)
        x: efeito.misturar(efeito.dados.x || 0, efeito.alvo.x - efeito.alvo.tamanho / 2, t)
        y: efeito.misturar(efeito.dados.y || 0, efeito.alvo.y - efeito.alvo.tamanho / 2, t)
        width: efeito.misturar(efeito.dados.w || 1, efeito.alvo.tamanho, t)
        height: efeito.misturar(efeito.dados.h || 1, efeito.alvo.tamanho, t)
        opacity: 1 - 0.75 * t
        fillMode: Image.Stretch
        smooth: true
        cache: false
    }

    // Gênio: faixas
    Repeater {
        model: efeito.genio && efeito.visible ? efeito.faixas : 0
        delegate: Item {
            id: faixa
            required property int index
            readonly property real v0: index / efeito.faixas
            readonly property real v1: (index + 1) / efeito.faixas
            readonly property real inicioA: efeito.posicaoA(v0)
            readonly property real fimA: efeito.posicaoA(v1)
            readonly property real s: efeito.aperto((v0 + v1) / 2)
            readonly property real largC: efeito.misturar(efeito.comprimentoC, efeito.alvo.tamanho, s)
            readonly property real centroC: efeito.misturar(efeito.c0 + efeito.comprimentoC / 2, efeito.alvoC, s)
            readonly property real compA: Math.max(0.5, fimA - inicioA + 0.6)
            // Para a tela
            x: efeito.lado === "base" ? centroC - largC / 2 : (efeito.lado === "esquerda" ? -inicioA - compA : inicioA)
            y: efeito.lado === "base" ? inicioA : centroC - largC / 2
            width: efeito.lado === "base" ? largC : compA
            height: efeito.lado === "base" ? compA : largC
            clip: true
            opacity: efeito.p > 0.9 ? (1 - efeito.p) * 10 : 1
            Image {
                source: efeito.dados.imagem || ""
                cache: true
                smooth: true
                fillMode: Image.Stretch
                // A imagem inteira, esticada para que só a fatia desta faixa apareça dentro dela
                readonly property real escalaA: faixa.compA / (efeito.comprimentoA / efeito.faixas)
                readonly property real escalaC: faixa.largC / efeito.comprimentoC
                width: efeito.lado === "base" ? efeito.comprimentoC * escalaC : efeito.comprimentoA * escalaA
                height: efeito.lado === "base" ? efeito.comprimentoA * escalaA : efeito.comprimentoC * escalaC
                x: efeito.lado === "base" ? 0
                   : (efeito.lado === "esquerda" ? -(efeito.faixas - faixa.index - 1) * faixa.compA : -faixa.index * faixa.compA)
                y: efeito.lado === "base" ? -faixa.index * faixa.compA : 0
            }
        }
    }
}
