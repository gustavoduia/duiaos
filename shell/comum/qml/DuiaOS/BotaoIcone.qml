// Botão só com ícone (barra de ferramentas, Barra de Recursos).
import QtQuick
import QtQuick.Window

Rectangle {
    id: raiz
    property string icone: ""
    property color corIcone: Tema.texto
    property int tamanhoIcone: 18
    property bool marcado: false
    property bool ativo: true
    property string dica: ""
    signal clicado()
    width: 30; height: 30
    radius: 8
    opacity: ativo ? 1 : 0.35
    color: marcado ? Tema.destaque : (area.pressed ? Tema.pressionado
           : (area.containsMouse ? Tema.realce : "transparent"))
    Icone { anchors.centerIn: parent; nome: raiz.icone; cor: raiz.marcado ? Tema.azulDuia : raiz.corIcone; tamanho: raiz.tamanhoIcone }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: raiz.ativo
        onClicked: raiz.clicado()
    }
    // Dica: o texto do botão aparece num balão depois de meio segundo com o mouse em cima. Fica na camada de
    // cima da janela (não é cortado por quem corta o conteúdo) e não sai da tela.
    property bool _clicado: false            // depois do clique, a dica só volta quando o mouse sai e entra de novo
    Timer { id: esperaDica; interval: 550; running: area.containsMouse && raiz.dica !== "" && !area.pressed && !raiz._clicado
            onTriggered: balaoDica.mostrar() }
    Rectangle {
        id: balaoDica
        parent: raiz.Window.window ? raiz.Window.window.contentItem : raiz
        visible: false
        z: 1000
        width: Math.min(320, textoDica.implicitWidth + 16); height: 26; radius: 7
        color: Tema.escuro ? "#E6E9F0" : "#1B2233"
        function mostrar() {
            var janela = raiz.Window.window
            if (!janela || !raiz.visible) return
            var p = raiz.mapToItem(parent, raiz.width / 2, raiz.height)
            x = Math.max(4, Math.min(parent.width - width - 4, p.x - width / 2))
            y = p.y + 6 + height > parent.height ? raiz.mapToItem(parent, 0, 0).y - height - 6 : p.y + 6
            visible = true
        }
        Text { id: textoDica; anchors { fill: parent; leftMargin: 8; rightMargin: 8 } verticalAlignment: Text.AlignVCenter
               text: raiz.dica; elide: Text.ElideRight; color: Tema.escuro ? "#141823" : "white"
               font { family: Tema.fonteTexto; pixelSize: 12 } }
    }
    Connections { target: area; function onContainsMouseChanged() { if (!area.containsMouse) { balaoDica.visible = false; raiz._clicado = false } }
                  function onPressed() { balaoDica.visible = false; raiz._clicado = true } }
    onVisibleChanged: if (!visible) balaoDica.visible = false
    Accessible.role: Accessible.Button
    Accessible.name: dica
}
