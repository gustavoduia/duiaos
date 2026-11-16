// DuiaOS — Barra de Recursos numa janela comum, com dados de exemplo
// (main.py --demonstracao [--painel NOME] [--captura ARQUIVO]).
import QtQuick
import QtQuick.Window

Window {
    id: janela
    width: 1280; height: 800
    visible: true
    title: "Barra de Recursos — demonstração"
    color: "#E8F0FE"

    Image { anchors.fill: parent; source: papelDeParede; fillMode: Image.PreserveAspectCrop; visible: papelDeParede !== "" }

    Barra { id: barra; width: parent.width; height: barra.espessura }

    ConteudoPainel {
        id: conteudo
        anchors { fill: parent; topMargin: barra.espessura }
        ocultos: barra.ocultos
        deslocamento: barra.espessura
    }

    // Abre um painel ao iniciar (âncora no ícone certo) e, se pedido, salva a imagem
    Timer {
        interval: 400; running: true
        onTriggered: {
            if (painelInicial.indexOf("confirmar:") === 0) sistema.pedirEnergia(painelInicial.split(":")[1])
            else if (painelInicial.indexOf("appmenu") === 0) sistema.abrirMenuDoAplicativo(parseInt(painelInicial.slice(7)), [100, 190, 250, 305, 365, 425][parseInt(painelInicial.slice(7)) + 1] || 200)
            else if (painelInicial !== "") {
                var ancoras = { menu: 25, central: janela.width - 150, calendario: janela.width - 70, balao: janela.width - 290,
                                wifi: janela.width - 255, som: janela.width - 225, bateria: janela.width - 185, luz: janela.width - 200,
                                bluetooth: janela.width - 200, brilho: janela.width - 200 }
                sistema.abrirPainel(painelInicial, ancoras[painelInicial] || janela.width / 2)
            }
            if (capturaArquivo !== "") salvar.start()
        }
    }
    Timer {
        id: salvar
        interval: 500
        onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() })
    }
}
