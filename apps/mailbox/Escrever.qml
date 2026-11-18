// DuiaOS — Mail Box: janela de escrever (nova mensagem, resposta e encaminhamento), com anexos.
import QtQuick
import QtQuick.Window
import QtQuick.Dialogs
import DuiaOS

Window {
    id: escrever
    property var campos: ({})
    property string conta: campos.conta || ""
    property var anexos: []
    property bool enviando: false
    property bool mostrarCc: (campos.cc || "") !== ""
    property string erro: ""
    width: 760; height: 680
    minimumWidth: 520; minimumHeight: 420
    visible: true
    color: Tema.fundo
    title: (campoAssunto.texto || "Nova mensagem") + " — Mail Box"

    function enviar() {
        erro = ""
        if (campoPara.texto.trim() === "" && campoCc.texto.trim() === "" && campoCco.texto.trim() === "") { erro = "Escreva pelo menos um destinatário."; return }
        enviando = true
        caixa.enviar({ conta: conta, para: campoPara.texto, cc: campoCc.texto, cco: campoCco.texto, assunto: campoAssunto.texto,
                       corpo: corpo.text, anexos: anexos, em_resposta_a: campos.em_resposta_a || "",
                       referencias: campos.referencias || "", id_respondida: campos.id_respondida || 0 })
    }
    Connections {
        target: caixa
        function onEnviada() { if (escrever.enviando) { escrever.enviando = false; escrever.close() } }
        function onFalhaEnvio(texto) { if (escrever.enviando) { escrever.enviando = false; escrever.erro = texto } }
    }
    Shortcut { sequences: ["Ctrl+Return", "Ctrl+Enter"]; onActivated: escrever.enviar() }
    Shortcut { sequences: ["Escape"]; enabled: !escrever.enviando && corpo.text === "" ; onActivated: escrever.close() }
    onClosing: destroy()

    FileDialog {
        id: escolherAnexos
        title: "Anexar arquivos"
        fileMode: FileDialog.OpenFiles
        onAccepted: { var l = escrever.anexos.slice(); for (var i = 0; i < selectedFiles.length; i++) l.push(selectedFiles[i].toString()); escrever.anexos = l }
    }

    component LinhaCampo: Item {
        property string rotulo: ""
        property alias campo: entradaCampo
        property alias texto: entradaCampo.text
        width: parent ? parent.width : 0
        height: 42
        Text { id: r; anchors { left: parent.left; verticalCenter: parent.verticalCenter } width: 64; text: rotulo
               color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
        TextInput {
            id: entradaCampo
            anchors { left: r.right; right: parent.right; verticalCenter: parent.verticalCenter }
            clip: true
            color: Tema.texto; selectionColor: Tema.azulDuia
            font { family: Tema.fonteTexto; pixelSize: 14 }
            selectByMouse: true
        }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: entradaCampo.activeFocus ? Tema.azulDuia : Tema.borda }
    }

    Rectangle { anchors.fill: parent; color: Tema.fundo }
    Column {
        id: cabecalho
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20; topMargin: 12 }
        // De: as contas, em pílulas
        Item {
            width: parent.width; height: 42
            Text { id: rotuloDe; anchors { left: parent.left; verticalCenter: parent.verticalCenter } width: 64; text: "De"
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
            Row {
                anchors { left: rotuloDe.right; verticalCenter: parent.verticalCenter }
                spacing: 6
                Repeater {
                    model: caixa.contasLista
                    delegate: Rectangle {
                        required property var modelData
                        readonly property bool escolhida: escrever.conta === modelData.id
                        visible: caixa.contasLista.length > 1 || escolhida
                        width: rotuloConta.implicitWidth + 22; height: 28; radius: 14
                        color: escolhida ? Tema.destaque : "transparent"
                        border { width: 1; color: escolhida ? Tema.azulDuia : Tema.borda }
                        Text { id: rotuloConta; anchors.centerIn: parent; text: modelData.email; color: parent.escolhida ? Tema.azulDuia : Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 12; weight: parent.escolhida ? Font.DemiBold : Font.Normal } }
                        MouseArea { anchors.fill: parent; onClicked: escrever.conta = modelData.id }
                    }
                }
            }
            Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda }
        }
        LinhaCampo { id: campoPara; rotulo: "Para"; texto: escrever.campos.para || ""
            Text { anchors { right: parent.right; verticalCenter: parent.verticalCenter } visible: !escrever.mostrarCc
                   text: "Cc e Cco"; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 12 }
                   MouseArea { anchors.fill: parent; anchors.margins: -4; onClicked: escrever.mostrarCc = true } } }
        LinhaCampo { id: campoCc; rotulo: "Cc"; visible: escrever.mostrarCc; height: visible ? 42 : 0; texto: escrever.campos.cc || "" }
        LinhaCampo { id: campoCco; rotulo: "Cco"; visible: escrever.mostrarCc; height: visible ? 42 : 0 }
        LinhaCampo { id: campoAssunto; rotulo: "Assunto"; texto: escrever.campos.assunto || "" }
    }
    Flickable {
        id: rolagem
        anchors { left: parent.left; right: parent.right; top: cabecalho.bottom; bottom: listaAnexos.top; margins: 20; topMargin: 8 }
        contentHeight: corpo.paintedHeight + 20
        clip: true
        TextEdit {
            id: corpo
            width: rolagem.width
            text: escrever.campos.corpo || ""
            wrapMode: TextEdit.Wrap
            color: Tema.texto; selectionColor: Tema.azulDuia
            font { family: Tema.fonteTexto; pixelSize: 14 }
            selectByMouse: true
            textFormat: TextEdit.PlainText
            Component.onCompleted: { if (campoPara.texto === "") campoPara.campo.forceActiveFocus(); else { forceActiveFocus(); cursorPosition = 0 } }
            onCursorRectangleChanged: {
                if (cursorRectangle.y < rolagem.contentY) rolagem.contentY = cursorRectangle.y
                else if (cursorRectangle.y + cursorRectangle.height > rolagem.contentY + rolagem.height)
                    rolagem.contentY = cursorRectangle.y + cursorRectangle.height - rolagem.height
            }
        }
    }
    Flow {
        id: listaAnexos
        anchors { left: parent.left; right: parent.right; bottom: rodape.top; margins: 20; bottomMargin: 8 }
        spacing: 6
        height: escrever.anexos.length ? implicitHeight : 0
        Repeater {
            model: escrever.anexos
            delegate: Rectangle {
                required property var modelData
                required property int index
                height: 30; radius: 15
                width: linhaAnexo.implicitWidth + 20
                color: Tema.cartao
                border { width: 1; color: Tema.borda }
                Row {
                    id: linhaAnexo
                    anchors.centerIn: parent
                    spacing: 6
                    Icone { nome: "documento"; tamanho: 13; cor: Tema.azulDuia; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: decodeURIComponent(modelData.split("/").pop()); color: Tema.texto; anchors.verticalCenter: parent.verticalCenter
                           font { family: Tema.fonteTexto; pixelSize: 12 } }
                    BotaoIcone { width: 20; height: 20; radius: 10; icone: "fechar"; tamanhoIcone: 10; anchors.verticalCenter: parent.verticalCenter
                                 onClicado: { var l = escrever.anexos.slice(); l.splice(index, 1); escrever.anexos = l } }
                }
            }
        }
    }
    Rectangle {
        id: rodape
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 60
        color: Tema.lateral
        Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top } height: 1; color: Tema.borda }
        Row {
            anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
            spacing: 10
            Botao { texto: escrever.enviando ? "Enviando…" : "Enviar"; icone: "seta-direita"; tipo: "primario"; ativo: !escrever.enviando; onClicado: escrever.enviar() }
            BotaoIcone { anchors.verticalCenter: parent.verticalCenter; icone: "documento"; dica: "Anexar arquivos"; onClicado: escolherAnexos.open() }
        }
        Text {
            anchors { left: parent.left; leftMargin: 200; right: descartar.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
            text: escrever.erro; elide: Text.ElideRight; color: Tema.erro; font { family: Tema.fonteTexto; pixelSize: 13 }
        }
        BotaoIcone { id: descartar; anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                     icone: "lixeira"; dica: "Descartar"; ativo: !escrever.enviando; onClicado: escrever.close() }
    }

    Timer {
        interval: 2500
        running: typeof capturaArquivo !== "undefined" && capturaArquivo !== "" && typeof paginaDemonstracao !== "undefined" && paginaDemonstracao === "escrever"
        onTriggered: escrever.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() })
    }
}
