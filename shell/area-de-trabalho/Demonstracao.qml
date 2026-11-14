// DuiaOS — Área de Trabalho numa janela comum, com ícones de exemplo
// (main.py --demonstracao [--menu fundo|item] [--captura ARQUIVO]).
import QtQuick
import QtQuick.Window

Window {
    id: janela
    width: 1280; height: 800
    visible: true
    title: "Área de Trabalho — demonstração"
    ConteudoArea {
        id: conteudo
        anchors.fill: parent

    }
    Timer {
        interval: 500; running: true
        onTriggered: {
            if (menuInicial === "fundo") conteudo.abrirMenu("fundo", 520, 220)
            if (menuInicial === "item") { var s = ({}); s[area.itens[2].caminho] = true; conteudo.selecao = s; conteudo.abrirMenu("item", 960, 260) }
            if (capturaArquivo !== "") salvar.start()
        }
    }
    Timer { id: salvar; interval: 400; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
