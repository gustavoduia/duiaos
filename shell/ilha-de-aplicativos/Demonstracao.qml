// DuiaOS — Ilha de Aplicativos numa janela comum, com dados de exemplo
// (main.py --demonstracao [--central|--downloads] [--captura ARQUIVO]).
import QtQuick
import QtQuick.Window

Window {
    id: janela
    width: 1280; height: 800
    visible: true
    title: "Ilha de Aplicativos — demonstração"
    color: "#E8F0FE"
    Image { anchors.fill: parent; source: papelDeParede; fillMode: Image.PreserveAspectCrop; visible: papelDeParede !== "" }
    Ilha { id: conteudo; anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 8 } }
    ConteudoDownloads { anchors.fill: parent; anchors.bottomMargin: conteudo.height + 8; visible: ilha.downloadsVisivel }
    ConteudoCentral { anchors.fill: parent; visible: ilha.centralVisivel }
    Timer { interval: 600; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
