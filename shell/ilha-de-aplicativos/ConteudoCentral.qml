// DuiaOS — Central de Aplicativos em tela cheia (como o Launchpad): fundo escurecido,
// busca no alto e a grade com todos os aplicativos.
// Enter abre o primeiro resultado · clique direito fixa/desafixa na Ilha · Esc ou clique fora fecha.
import QtQuick
import DuiaOS

Item {
    id: central
    property alias campo: campo

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(0.06, 0.09, 0.14, 0.62) }
            GradientStop { position: 1; color: Qt.rgba(0.10, 0.23, 0.45, 0.70) }
        }
        MouseArea { anchors.fill: parent; onClicked: ilha.fecharCentral() }
    }

    // Busca
    Rectangle {
        id: caixaBusca
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 56 }
        width: 300; height: 36
        radius: 10
        color: Qt.rgba(1, 1, 1, 0.16)
        border { color: Qt.rgba(1, 1, 1, campo.activeFocus ? 0.55 : 0.28); width: 1 }
        Icone { id: lupa; anchors { left: parent.left; leftMargin: 11; verticalCenter: parent.verticalCenter } nome: "busca"; tamanho: 16; cor: "white" }
        TextInput {
            id: campo
            anchors { left: lupa.right; right: parent.right; leftMargin: 8; rightMargin: 12; verticalCenter: parent.verticalCenter }
            color: "white"
            selectionColor: Tema.azulDuia
            font { family: Tema.fonteTexto; pixelSize: 15 }
            clip: true
            onTextChanged: ilha.buscar(text)
            Keys.onEscapePressed: ilha.fecharCentral()
            Keys.onReturnPressed: abrirPrimeiro()
            Keys.onEnterPressed: abrirPrimeiro()
            function abrirPrimeiro() {
                if (ilha.resultados.length > 0)
                    ilha.abrirAplicativo(ilha.resultados[0].id)
            }
            Text {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                visible: campo.text === ""
                text: "Buscar aplicativos"
                color: Qt.rgba(1, 1, 1, 0.7)
                font: campo.font
            }
        }
    }

    GridView {
        id: grade
        readonly property int colunas: Math.max(3, Math.min(7, Math.floor(width / 150)))
        anchors { top: caixaBusca.bottom; bottom: rodape.top; horizontalCenter: parent.horizontalCenter
                  topMargin: 36; bottomMargin: 16 }
        width: Math.min(parent.width - 120, 7 * 150)
        clip: true
        cellWidth: Math.floor(width / colunas)
        cellHeight: 136
        model: ilha.resultados
        boundsBehavior: Flickable.StopAtBounds

        delegate: Item {
            required property var modelData
            width: grade.cellWidth
            height: grade.cellHeight

            Item {
                id: icone
                width: 72; height: 72
                anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 10 }
                scale: area.pressed ? 0.9 : (area.containsMouse ? 1.06 : 1)
                Behavior on scale { NumberAnimation { duration: 110 } }
                Ladrilho { anchors.fill: parent; visible: (modelData.iconeDuia || "") !== ""; icone: modelData.iconeDuia || "pasta"
                           estilo: modelData.iconeDuia === "engrenagem" ? "cinza" : "azul"; tamanho: 72 }
                IconeApp { anchors.fill: parent; visible: (modelData.iconeDuia || "") === ""; icone: modelData.icone; nome: modelData.nome; tamanho: 72 }
                // Marca de fixado na Ilha
                Rectangle {
                    visible: modelData.fixado
                    anchors { right: parent.right; top: parent.top; rightMargin: -3; topMargin: -3 }
                    width: 12; height: 12; radius: 6
                    color: Tema.azulDuia
                    border { color: "white"; width: 2 }
                }
            }
            Text {
                anchors { left: parent.left; right: parent.right; top: icone.bottom; topMargin: 9; leftMargin: 6; rightMargin: 6 }
                text: modelData.nome
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
                color: "white"
                style: Text.Raised; styleColor: Qt.rgba(0, 0, 0, 0.25)
                font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Medium }
            }
            MouseArea {
                id: area
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: (evento) => {
                    if (evento.button === Qt.RightButton)
                        ilha.alternarFixado(modelData.id)
                    else
                        ilha.abrirAplicativo(modelData.id)
                }
            }
        }
    }

    Text {
        anchors.centerIn: grade
        visible: ilha.resultados.length === 0
        text: "Nenhum aplicativo encontrado"
        color: "white"
        font { family: Tema.fonteTexto; pixelSize: 15 }
    }

    Text {
        id: rodape
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 110 }
        text: "Enter abre o primeiro  ·  clique direito fixa/desafixa na Ilha  ·  Esc fecha"
        color: Qt.rgba(1, 1, 1, 0.75)
        font { family: Tema.fonteTexto; pixelSize: 12 }
    }
}
