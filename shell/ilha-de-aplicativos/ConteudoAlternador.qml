// DuiaOS — conteúdo do alternador de aplicativos (Alt+Tab, ADR 077): painel de vidro no centro da tela com
// os ícones dos aplicativos abertos (o último usado primeiro) e, sobre o escolhido, um balão discreto com o
// nome. Tab/→ e Shift+Tab/← andam; soltar o Alt ou Enter troca; Esc cancela; clique escolhe.
import QtQuick
import DuiaOS

Item {
    id: raiz
    readonly property int lado: ilha.alternador.length > 7 ? 64 : 80
    readonly property int passo: lado + 28

    Rectangle {
        id: painel
        anchors.centerIn: parent
        width: Math.min(raiz.width - 80, linha.width + 40)
        height: raiz.lado + 74
        radius: 26
        color: Tema.escuro ? Qt.rgba(0.08, 0.10, 0.16, 0.86) : Qt.rgba(0.97, 0.98, 1, 0.88)
        border { width: 1; color: Tema.escuro ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(0.06, 0.09, 0.2, 0.10) }
        scale: ilha.alternadorVisivel ? 1 : 0.94
        opacity: ilha.alternadorVisivel ? 1 : 0
        Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: 110 } }
        clip: true

        Row {
            id: linha
            anchors { verticalCenter: parent.verticalCenter; verticalCenterOffset: 8 }
            // Muitos aplicativos: a fila corre para manter o escolhido à vista
            x: Math.min(20, Math.max(painel.width - width - 20, painel.width / 2 - (ilha.alternadorIndice + 0.5) * raiz.passo))
            Behavior on x { NumberAnimation { duration: 120 } }
            Repeater {
                model: ilha.alternador
                delegate: Item {
                    id: celula
                    required property var modelData
                    required property int index
                    readonly property bool escolhido: index === ilha.alternadorIndice
                    width: raiz.passo; height: raiz.lado + 20
                    Rectangle {
                        anchors.centerIn: icone
                        width: raiz.lado + 18; height: raiz.lado + 18
                        radius: 20
                        color: Tema.escuro ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0.24, 0.36, 1, 0.12)
                        border { width: 1.5; color: Qt.rgba(0.24, 0.36, 1, 0.55) }
                        visible: celula.escolhido
                    }
                    Item {
                        id: icone
                        anchors.centerIn: parent
                        width: raiz.lado; height: raiz.lado
                        scale: celula.escolhido ? 1.04 : 1
                        Behavior on scale { NumberAnimation { duration: 100 } }
                        Ladrilho { anchors.fill: parent; visible: (celula.modelData.iconeDuia || "") !== ""
                                   icone: celula.modelData.iconeDuia || "pasta"
                                   estilo: celula.modelData.iconeDuia === "engrenagem" ? "cinza" : "azul"; tamanho: raiz.lado }
                        IconeApp { anchors.fill: parent; visible: (celula.modelData.iconeDuia || "") === ""
                                   icone: celula.modelData.icone || ""; nome: celula.modelData.nome || ""; tamanho: raiz.lado }
                        Rectangle {
                            visible: (celula.modelData.contador || 0) > 0
                            anchors { right: parent.right; top: parent.top; rightMargin: -6; topMargin: -6 }
                            height: 22; width: Math.max(22, numero.implicitWidth + 12); radius: 11
                            color: "#EF4444"; border { width: 2; color: painel.color }
                            Text { id: numero; anchors.centerIn: parent; color: "white"
                                   text: celula.modelData.contador > 99 ? "99+" : String(celula.modelData.contador || "")
                                   font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.Bold } }
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: if (!celula.escolhido) ilha.alternadorMover(celula.index - ilha.alternadorIndice)
                        onClicked: ilha.alternadorEscolher(celula.index)
                    }
                }
            }
        }

        // Balão com o nome do escolhido, logo acima do ícone
        Rectangle {
            id: balao
            readonly property var item: ilha.alternador[ilha.alternadorIndice] || ({})
            y: 10
            x: Math.max(10, Math.min(painel.width - width - 10, linha.x + (ilha.alternadorIndice + 0.5) * raiz.passo - width / 2))
            Behavior on x { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
            width: Math.min(painel.width - 20, nomeBalao.implicitWidth + 22)
            height: 24; radius: 12
            color: Tema.escuro ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(0.06, 0.09, 0.2, 0.78)
            Text {
                id: nomeBalao
                anchors.centerIn: parent
                width: Math.min(implicitWidth, parent.width - 22)
                elide: Text.ElideRight
                text: balao.item.nome || ""
                color: "white"
                font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
            }
        }
    }
}
