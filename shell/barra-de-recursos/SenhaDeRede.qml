// DuiaOS — janela "Senha da rede" (ADR 070): o NetworkManager pediu uma senha (Wi-Fi, rede corporativa,
// VPN, chip do celular). Enter confirma, Esc cancela.
import QtQuick
import QtQuick.Window
import DuiaOS

Window {
    id: janela
    width: 440; height: coluna.implicitHeight + 48
    minimumWidth: 380
    visible: true
    color: Tema.fundo
    title: pedido.titulo || "Senha da rede"
    flags: Qt.Dialog
    property var valores: ({})
    property bool lembrar: true
    function confirmar() {
        var v = {}
        for (var i = 0; i < campos.count; i++) v[pedido.campos[i].chave] = campos.itemAt(i).texto
        resposta.confirmar(v, janela.lembrar)
    }
    onClosing: resposta.cancelar()
    Component.onCompleted: {
        requestActivate()
        if (campos.count > 0) campos.itemAt(0).entrada.forceActiveFocus()
    }
    Timer { interval: 700; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
    Column {
        id: coluna
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
        spacing: 14
        Row {
            spacing: 14
            width: parent.width
            Ladrilho { tamanho: 48; icone: "cadeado"; estilo: "azul" }
            Column {
                width: parent.width - 62
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                Titulo { nivel: 2; width: parent.width; text: pedido.titulo || "Senha da rede"; wrapMode: Text.WordWrap }
                Rotulo { width: parent.width; secundario: true; text: pedido.texto || ""; wrapMode: Text.WordWrap }
            }
        }
        Repeater {
            id: campos
            model: pedido.campos || []
            Column {
                required property var modelData
                property alias texto: campo.texto
                property alias entrada: campo.entrada
                width: coluna.width
                spacing: 4
                Text { text: modelData.rotulo; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                Campo { id: campo; width: parent.width; senha: modelData.senha === true; onConfirmado: janela.confirmar()
                        entrada.Keys.onEscapePressed: resposta.cancelar() }
            }
        }
        Item {
            visible: pedido.lembrar === true
            width: parent.width; height: 26
            Interruptor { id: chave; ligado: janela.lembrar; onAlternado: (v) => janela.lembrar = v; anchors.verticalCenter: parent.verticalCenter }
            Text { anchors { left: chave.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                   text: "Lembrar neste computador"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
        }
        Row {
            anchors.right: parent.right
            spacing: 8
            Botao { texto: "Cancelar"; onClicado: resposta.cancelar() }
            Botao { texto: "Conectar"; tipo: "primario"; onClicado: janela.confirmar() }
        }
    }
}
