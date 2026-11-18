// DuiaOS — Ora: página de nova aba. A marca, a busca e os atalhos (favoritos da barra e mais visitados).
import QtQuick
import DuiaOS

Rectangle {
    id: pagina
    property var janelaOra
    color: Tema.fundo
    property var maisVisitados: ora.maisVisitados()
    Connections { target: ora; function onMudou() { pagina.maisVisitados = ora.maisVisitados() } }

    // Brilho aurora suave ao fundo (no estilo futurista mais forte), que some para baixo
    Item {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: parent.height * 0.62
        visible: !janelaOra.privada
        Rectangle {
            anchors.fill: parent
            opacity: Tema.futurista ? (Tema.escuro ? 0.24 : 0.18) : 0.09
            gradient: Gradient { orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "transparent" } GradientStop { position: 0.32; color: Tema.aurora1 }
                GradientStop { position: 0.68; color: Tema.aurora3 } GradientStop { position: 1; color: "transparent" } }
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.rgba(Tema.fundo.r, Tema.fundo.g, Tema.fundo.b, 0) }
                GradientStop { position: 1; color: Tema.fundo } }
        }
    }

    Flickable {
        anchors.fill: parent
        contentHeight: Math.max(height, coluna.implicitHeight + 120)
        clip: true
        Column {
            id: coluna
            width: Math.min(parent.width - 64, 760)
            anchors.horizontalCenter: parent.horizontalCenter
            y: Math.max(48, (pagina.height - implicitHeight) * 0.38)
            spacing: 28

            // Marca: "ora" em letras grandes com o degradê aurora
            Item {
                anchors.horizontalCenter: parent.horizontalCenter
                width: marca.implicitWidth; height: marca.implicitHeight
                Text {
                    id: marca
                    text: janelaOra.privada ? "ora privada" : "ora"
                    font { family: Tema.fonteTitulo; pixelSize: janelaOra.privada ? 52 : 72; weight: Font.ExtraBold; letterSpacing: -2 }
                    color: Tema.azulNoite
                }
                Rectangle {
                    anchors { left: marca.left; right: marca.right; top: marca.bottom; topMargin: -6 }
                    height: 4; radius: 2
                    gradient: Gradient { orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: Tema.aurora1 } GradientStop { position: 0.5; color: Tema.aurora2 }
                        GradientStop { position: 1; color: Tema.aurora3 } }
                }
            }
            Text {
                visible: janelaOra.privada
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(parent.width, 560)
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: "Nesta janela, o Ora não guarda histórico, cookies nem o que você digitar em formulários. " +
                      "Os downloads e os favoritos que você criar continuam no computador."
                color: Tema.textoSecundario
                font { family: Tema.fonteTexto; pixelSize: 14 }
            }

            // Busca
            Rectangle {
                id: caixaBusca
                width: parent.width; height: 54
                radius: 27
                color: Tema.cartao
                border { width: campo.activeFocus ? 2 : 1; color: campo.activeFocus ? Tema.azulDuia : Tema.borda }
                Aurora { visible: Tema.futurista; z: -1; anchors { fill: parent; margins: -3 } radius: parent.radius + 3
                         opacity: campo.activeFocus ? 0.35 : 0.12 }
                Icone { id: lupa; anchors { left: parent.left; leftMargin: 22; verticalCenter: parent.verticalCenter }
                        nome: "busca"; tamanho: 18; cor: Tema.textoSecundario }
                TextInput {
                    id: campo
                    anchors { left: lupa.right; leftMargin: 14; right: parent.right; rightMargin: 22; verticalCenter: parent.verticalCenter }
                    font { family: Tema.fonteTexto; pixelSize: 16 }
                    color: Tema.texto
                    selectionColor: Tema.azulDuia
                    clip: true
                    onAccepted: if (text.trim() !== "") janelaOra.abrir(text, false)
                    Text { anchors.fill: parent; verticalAlignment: Text.AlignVCenter; visible: campo.text === ""
                           text: "Pesquise na web ou digite um endereço"; color: Tema.textoApagado; font: campo.font }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.IBeamCursor; onPressed: (m) => { campo.forceActiveFocus(); m.accepted = false } }
            }

            // Atalhos: favoritos da barra e os sites mais visitados
            Flow {
                id: atalhos
                width: parent.width
                spacing: 14
                visible: !janelaOra.privada
                readonly property var itens: {
                    var lista = [], vistos = {}
                    var favs = ora.favoritosDaBarra
                    for (var i = 0; i < favs.length && lista.length < 8; i++) if (!vistos[favs[i].url]) { vistos[favs[i].url] = 1; lista.push(favs[i]) }
                    for (var j = 0; j < pagina.maisVisitados.length && lista.length < 12; j++) {
                        var m = pagina.maisVisitados[j]
                        if (!vistos[m.url]) { vistos[m.url] = 1; lista.push(m) }
                    }
                    return lista
                }
                Repeater {
                    model: atalhos.itens
                    delegate: Rectangle {
                        required property var modelData
                        width: (atalhos.width - 5 * atalhos.spacing) / 6
                        height: 104
                        radius: Tema.raio
                        color: areaAtalho.containsMouse ? Tema.cartao : "transparent"
                        border { width: areaAtalho.containsMouse ? 1 : 0; color: Tema.borda }
                        Rectangle {
                            id: circulo
                            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 14 }
                            width: 48; height: 48; radius: 24
                            color: Tema.cartao
                            border { width: 1; color: Tema.borda }
                            Favicon { anchors.centerIn: parent; url: modelData.url; titulo: modelData.titulo; tamanho: 24 }
                        }
                        Text {
                            anchors { top: circulo.bottom; topMargin: 10; left: parent.left; right: parent.right; margins: 8 }
                            horizontalAlignment: Text.AlignHCenter
                            text: modelData.titulo || ora.dominio(modelData.url)
                            elide: Text.ElideRight
                            color: Tema.texto
                            font { family: Tema.fonteTexto; pixelSize: 13 }
                        }
                        MouseArea { id: areaAtalho; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                                    onClicked: (m) => janelaOra.abrir(modelData.url, m.button === Qt.MiddleButton) }
                    }
                }
            }
        }
    }
    Component.onCompleted: if (!ora.demonstracao) Qt.callLater(janelaOra.focarEndereco)
}
