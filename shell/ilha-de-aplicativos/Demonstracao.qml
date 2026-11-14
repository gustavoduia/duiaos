// DuiaOS — Ilha de Aplicativos numa janela comum, com dados de exemplo
// (main.py --demonstracao [--central|--downloads|--menu|--menu-ilha|--ampliada|--genio]
//  [--posicao base|esquerda|direita] [--recentes] [--captura ARQUIVO]).
import QtQuick
import QtQuick.Window

Window {
    id: janela
    width: 1280; height: 800
    visible: true
    title: "Ilha de Aplicativos — demonstração"
    color: "#E8F0FE"
    readonly property string posicao: conteudo.posicao
    Image { anchors.fill: parent; source: papelDeParede; fillMode: Image.PreserveAspectCrop; visible: papelDeParede !== "" }
    Ilha {
        id: conteudo
        x: posicao === "esquerda" ? 8 : (posicao === "direita" ? janela.width - width - 8 : (janela.width - width) / 2)
        y: vertical ? (janela.height - height) / 2 : janela.height - height - 8
        Component.onCompleted: if (demoAmpliada) foco = 4.5
    }
    // Área livre (sem a faixa da Ilha), como a camada dos balões no sistema
    Item {
        id: livre
        anchors { fill: parent
                  bottomMargin: conteudo.posicao === "base" ? conteudo.espessuraFundo + 8 : 0
                  leftMargin: conteudo.posicao === "esquerda" ? conteudo.espessuraFundo + 8 : 0
                  rightMargin: conteudo.posicao === "direita" ? conteudo.espessuraFundo + 8 : 0 }
        ConteudoDownloads { anchors.fill: parent; visible: ilha.downloadsVisivel }
        MenuDaIlha { anchors.fill: parent; visible: ilha.menu.tipo !== undefined }
    }
    ConteudoCentral { anchors.fill: parent; visible: ilha.centralVisivel }
    EfeitoDeJanela {
        id: efeito
        anchors.fill: parent
        visible: false
        lado: conteudo.posicao
        Component.onCompleted: if (demoGenio !== "") {
            var i = conteudo.icone("firefox-esr")
            var p = conteudo.mapToItem(janela.contentItem, i.x, i.y)
            quadro({ direcao: "minimizar", efeito: demoEfeito, imagem: demoGenio, appId: "firefox-esr",
                     x: 300, y: 120, w: 640, h: 420 }, { x: p.x, y: p.y, tamanho: i.tamanho }, demoProgresso)
        }
    }
    Timer { interval: 600; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
