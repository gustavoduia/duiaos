import QtQuick
import QtQuick.Window

Window {
    id: janela
    width: 1280; height: 800
    visible: true
    title: "Tela de Descanso — demonstração"
    ConteudoDescanso { anchors.fill: parent; onSair: if (capturaArquivo === "") Qt.quit() }
    Timer { interval: 600; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
