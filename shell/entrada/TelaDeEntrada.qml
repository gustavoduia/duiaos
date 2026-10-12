// DuiaOS — Tela de Entrada (iniciar uma sessão).
// Roda no compositor cage, aberto pelo greetd. Com mais de um monitor, o cage
// estende uma única janela sobre todos; por isso esta tela desenha uma área
// por monitor: o cartão de senha fica só na tela principal (a do notebook,
// quando houver) e os outros monitores mostram o fundo e o relógio.
import QtQuick
import QtQuick.Window
import "../comum"
import "../comum/telas.js" as Telas

Window {
    id: janela
    visible: true
    visibility: entrada.demonstracao ? Window.Windowed : Window.FullScreen
    width: 1280; height: 800
    color: "#F7F9FC"
    title: "Tela de Entrada"

    readonly property var monitores: Qt.application.screens
    readonly property int indicePrincipal: Telas.indicePrincipal(monitores)
    // Com um monitor só (ou na demonstração), a tela ocupa a janela inteira.
    readonly property bool variosMonitores: monitores.length > 1 && !entrada.demonstracao
    // Canto superior esquerdo do conjunto de monitores (origem da janela no cage)
    readonly property int origemX: Math.min.apply(null, monitores.map(m => m.virtualX))
    readonly property int origemY: Math.min.apply(null, monitores.map(m => m.virtualY))

    Repeater {
        model: janela.variosMonitores ? janela.monitores : [null]
        delegate: TelaDeAcesso {
            id: tela
            required property var modelData
            required property int index
            readonly property bool principal: !janela.variosMonitores || index === janela.indicePrincipal

            x: modelData ? modelData.virtualX - janela.origemX : 0
            y: modelData ? modelData.virtualY - janela.origemY : 0
            width: modelData ? modelData.width : janela.width
            height: modelData ? modelData.height : janela.height

            modo: "entrada"
            somenteFundo: !principal
            usuarios: entrada.usuarios
            usuarioAtual: entrada.usuarioInicial
            ocupado: entrada.ocupado
            opcoesEnergia: entrada.opcoesEnergia
            versao: entrada.versao
            papelDeParede: entrada.papelDeParede
            onEntrar: (usuario, senha) => entrada.entrar(usuario, senha)
            onAcaoEnergia: (id) => entrada.energia(id)

            Connections {
                target: entrada
                enabled: tela.principal
                function onFalhou(mensagem) {
                    tela.mensagem = mensagem
                    tela.avisarErro()
                }
            }
        }
    }
}
