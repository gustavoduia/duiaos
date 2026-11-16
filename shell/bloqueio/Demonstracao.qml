// DuiaOS — Tela de Bloqueio em janela comum, para testar o visual
// (main.py --demonstracao). Não bloqueia nada.
import QtQuick
import QtQuick.Window
import "../comum"

Window {
    id: janela
    visible: true
    width: 1280; height: 800
    color: "#F7F9FC"
    title: "Tela de Bloqueio (demonstração)"

    TelaDeAcesso {
        id: tela
        anchors.fill: parent
        modo: "bloqueio"
        usuarios: [bloqueio.usuario]
        ocupado: bloqueio.ocupado
        opcoesEnergia: bloqueio.opcoesEnergia
        versao: bloqueio.versao
        papelDeParede: bloqueio.papelDeParede
        ajusteFundo: bloqueio.ajusteFundo
        corFundo: bloqueio.corFundo
        desfocar: bloqueio.desfocarFundo
        futurista: bloqueio.futurista
        onEntrar: (usuario, senha) => bloqueio.desbloquear(senha)
        onAcaoEnergia: (id) => bloqueio.energia(id)
    }
    Connections {
        target: bloqueio
        function onFalhou(mensagem) {
            tela.mensagem = mensagem
            tela.avisarErro()
        }
    }
    // main.py --demonstracao [--estilo futurista] --captura ARQUIVO: salva a imagem e sai
    Timer { interval: 900; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
