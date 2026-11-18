// DuiaOS — Ora: downloads em andamento e terminados, com pausar, retomar, cancelar, abrir e mostrar na pasta.
import QtQuick
import DuiaOS

PaginaInterna {
    id: pagina
    titulo: "Downloads"
    icone: "download"

    function tamanho(bytes) {
        if (bytes <= 0) return ""
        var u = ["bytes", "KB", "MB", "GB"], v = bytes, i = 0
        while (v >= 1000 && i < u.length - 1) { v /= 1000; i++ }
        return (i < 2 ? Math.round(v) : v.toFixed(1).replace(".", ",")) + " " + u[i]
    }
    function iconeDoArquivo(nome) {
        var ext = nome.split(".").pop().toLowerCase()
        if (["pdf"].indexOf(ext) >= 0) return "pdf"
        if (["png", "jpg", "jpeg", "gif", "webp", "svg"].indexOf(ext) >= 0) return "imagem"
        if (["mp4", "mkv", "webm", "mov"].indexOf(ext) >= 0) return "video"
        if (["mp3", "ogg", "flac", "wav", "m4a"].indexOf(ext) >= 0) return "musica"
        if (["zip", "gz", "xz", "7z", "rar", "tar", "bz2"].indexOf(ext) >= 0) return "compactado"
        if (["xlsx", "ods", "csv"].indexOf(ext) >= 0) return "planilha"
        if (["deb", "flatpakref", "appimage"].indexOf(ext) >= 0) return "sacola"
        return "documento"
    }

    acoes: [ Botao { texto: "Limpar a lista"; icone: "lixeira"; ativo: ora.downloads.length > 0; onClicado: ora.limparDownloads() } ]

    Text {
        visible: ora.downloads.length === 0
        width: parent.width
        topPadding: 40
        horizontalAlignment: Text.AlignHCenter
        text: "Nenhum download por aqui."
        color: Tema.textoSecundario
        font { family: Tema.fonteTexto; pixelSize: 14 }
    }

    Cartao {
        visible: ora.downloads.length > 0
        width: parent.width
        height: lista.implicitHeight + 8
        Column {
            id: lista
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
            Repeater {
                model: ora.downloads
                delegate: Rectangle {
                    id: linha
                    required property var modelData
                    readonly property bool andando: modelData.estado === "andamento" || modelData.estado === "pausado"
                    width: lista.width; height: 64; radius: 8
                    color: area.containsMouse ? Tema.realce : "transparent"
                    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true
                                onDoubleClicked: if (linha.modelData.estado === "concluido") ora.acaoDownload(linha.modelData.id, "abrir") }
                    Rectangle {
                        id: quadro
                        anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                        width: 40; height: 40; radius: 10
                        color: Tema.destaque
                        Icone { anchors.centerIn: parent; nome: pagina.iconeDoArquivo(linha.modelData.arquivo); tamanho: 20; cor: Tema.azulDuia }
                    }
                    Column {
                        anchors { left: quadro.right; leftMargin: 12; right: botoes.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                        spacing: 4
                        Text { width: parent.width; text: linha.modelData.arquivo; elide: Text.ElideMiddle
                               color: linha.modelData.existe || linha.andando ? Tema.texto : Tema.textoApagado
                               font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold; strikeout: !linha.modelData.existe && !linha.andando && linha.modelData.estado === "concluido" } }
                        Rectangle {
                            visible: linha.andando
                            width: parent.width; height: 4; radius: 2; color: Tema.controleDesligado
                            Rectangle { height: parent.height; radius: 2; color: Tema.azulDuia
                                        width: linha.modelData.total > 0 ? parent.width * linha.modelData.recebido / linha.modelData.total : parent.width * 0.1 }
                        }
                        Text {
                            width: parent.width
                            elide: Text.ElideRight
                            color: linha.modelData.estado === "interrompido" ? Tema.erro : Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 12 }
                            text: {
                                var d = linha.modelData
                                if (d.estado === "andamento") return pagina.tamanho(d.recebido) + (d.total > 0 ? " de " + pagina.tamanho(d.total) : "")
                                if (d.estado === "pausado") return "Pausado — " + pagina.tamanho(d.recebido)
                                if (d.estado === "cancelado") return "Cancelado"
                                if (d.estado === "interrompido") return "Falhou — a conexão caiu ou o site recusou"
                                if (!d.existe) return "Arquivo apagado ou movido"
                                return pagina.tamanho(d.total) + " — " + ora.dominio(d.url)
                            }
                        }
                    }
                    Row {
                        id: botoes
                        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        spacing: 2
                        BotaoIcone { visible: linha.modelData.estado === "andamento"; icone: "relogio"; dica: "Pausar"; onClicado: ora.acaoDownload(linha.modelData.id, "pausar") }
                        BotaoIcone { visible: linha.modelData.estado === "pausado"; icone: "download"; dica: "Continuar"; onClicado: ora.acaoDownload(linha.modelData.id, "retomar") }
                        BotaoIcone { visible: linha.andando; icone: "fechar"; dica: "Cancelar"; onClicado: ora.acaoDownload(linha.modelData.id, "cancelar") }
                        BotaoIcone { visible: linha.modelData.estado === "concluido" && linha.modelData.existe; icone: "abrir"; dica: "Abrir"; onClicado: ora.acaoDownload(linha.modelData.id, "abrir") }
                        BotaoIcone { visible: linha.modelData.estado === "concluido" && linha.modelData.existe; icone: "pasta"; dica: "Mostrar na pasta"; onClicado: ora.acaoDownload(linha.modelData.id, "pasta") }
                    }
                }
            }
        }
    }
}
