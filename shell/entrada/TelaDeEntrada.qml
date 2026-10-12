// DuiaOS — Tela de Entrada (iniciar uma sessão).
// Roda no compositor cage, aberto pelo greetd; ocupa a tela inteira.
import QtQuick
import QtQuick.Window
import "../comum"

Window {
    id: janela
    visible: true
    visibility: entrada.demonstracao ? Window.Windowed : Window.FullScreen
    width: 1280; height: 800
    color: "#F7F9FC"
    title: "Tela de Entrada"

    TelaDeAcesso {
        id: tela
        anchors.fill: parent
        modo: "entrada"
        usuarios: entrada.usuarios
        usuarioAtual: entrada.usuarioInicial
        ocupado: entrada.ocupado
        opcoesEnergia: entrada.opcoesEnergia
        versao: entrada.versao
        papelDeParede: entrada.papelDeParede
        onEntrar: (usuario, senha) => entrada.entrar(usuario, senha)
        onAcaoEnergia: (id) => entrada.energia(id)
    }

    Connections {
        target: entrada
        function onFalhou(mensagem) {
            tela.mensagem = mensagem
            tela.avisarErro()
        }
    }
}
