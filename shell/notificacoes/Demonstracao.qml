import QtQuick
import QtQuick.Window
import DuiaOS

Window {
    id: janela
    width: 420; height: 460
    visible: true
    color: Tema.destaque
    title: "Notificações — demonstração"
    Baloes { x: 30; y: 20 }
    Timer { interval: 600; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
