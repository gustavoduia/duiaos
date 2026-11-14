// DuiaOS — conteúdo da Ilha de Aplicativos (sem a janela, para servir também à demonstração).
// Central de Aplicativos · fixados (Wise e Explorador de Arquivos primeiro) · abertos
// | pasta Aplicativos · pilha de Downloads · Lixeira
import QtQuick
import DuiaOS

Rectangle {
    id: ilhaFundo
    readonly property int tamanhoIcone: 46
    property real deslocamentoX: 0          // onde a Ilha começa na tela (para a pilha de Downloads)
    width: linha.width + 16
    height: tamanhoIcone + 22
    radius: 22
    color: "#EBF7F9FC"
    border { color: Qt.rgba(1, 1, 1, 0.9); width: 1 }
    Rectangle { anchors { fill: parent; margins: -1 } radius: parent.radius + 1; color: "transparent"; border { color: Tema.borda; width: 1 } }

    // Ponto de aplicativo aberto
    component PontoAberto: Rectangle {
        width: 4; height: 4; radius: 2
        color: Tema.azulNoite
    }

    // Espaço de um ícone: realce, crescimento ao passar o mouse e clique
    component Vaga: Item {
        id: vaga
        property bool aberto: false
        property string nome: ""
        default property alias desenho: dentro.data
        signal clicado()
        width: ilhaFundo.tamanhoIcone + 6
        height: ilhaFundo.tamanhoIcone + 16
        Accessible.role: Accessible.Button
        Accessible.name: nome
        Item {
            id: dentro
            width: ilhaFundo.tamanhoIcone; height: width
            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 5 }
            scale: area.pressed ? 0.9 : (area.containsMouse ? 1.12 : 1.0)
            transform: Translate { y: area.containsMouse && !area.pressed ? -3 : 0; Behavior on y { NumberAnimation { duration: 120 } } }
            Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        }
        PontoAberto { visible: vaga.aberto; anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 2 } }
        MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; onClicked: vaga.clicado() }
    }

    component Divisoria: Rectangle {
        width: 1; height: ilhaFundo.tamanhoIcone - 6
        anchors.verticalCenter: parent ? parent.verticalCenter : undefined
        color: Tema.bordaForte
    }

    Row {
        id: linha
        anchors.centerIn: parent
        spacing: 2

        Vaga {
            nome: "Central de Aplicativos"
            onClicado: ilha.alternarCentral()
            Ladrilho { anchors.fill: parent; icone: "aplicativos"; estilo: "noite"; tamanho: ilhaFundo.tamanhoIcone }
        }

        Repeater {
            model: ilha.itens
            delegate: Row {
                required property var modelData
                required property int index
                spacing: 2
                // Divisória entre os fixados e os abertos não fixados
                Divisoria { visible: !modelData.fixado && (index === 0 || ilha.itens[index - 1].fixado) }
                Vaga {
                    nome: modelData.nome
                    aberto: modelData.aberto
                    onClicado: ilha.ativar(index)
                    Ladrilho {
                        visible: (modelData.iconeDuia || "") !== ""
                        anchors.fill: parent
                        icone: modelData.iconeDuia || "pasta"
                        estilo: modelData.iconeDuia === "engrenagem" ? "cinza" : "azul"
                        tamanho: ilhaFundo.tamanhoIcone
                    }
                    IconeApp {
                        visible: (modelData.iconeDuia || "") === ""
                        anchors.fill: parent
                        icone: modelData.icone; nome: modelData.nome; tamanho: ilhaFundo.tamanhoIcone
                    }
                }
            }
        }

        Item { width: 4; height: 1 }
        Divisoria {}
        Item { width: 4; height: 1 }

        Vaga {
            nome: "Aplicativos"
            onClicado: ilha.abrirPasta("aplicativos")
            Ladrilho { anchors.fill: parent; icone: "pasta-aplicativos"; estilo: "azul"; tamanho: ilhaFundo.tamanhoIcone }
        }
        Vaga {
            id: vagaDownloads
            nome: "Downloads"
            onClicado: {
                var p = vagaDownloads.mapToItem(null, vagaDownloads.width / 2, 0)
                ilha.alternarDownloads(p.x + ilhaFundo.deslocamentoX)
            }
            Ladrilho { anchors.fill: parent; icone: "pasta-downloads"; estilo: "azul"; tamanho: ilhaFundo.tamanhoIcone }
        }
        Vaga {
            nome: "Lixeira"
            onClicado: ilha.abrirPasta("lixeira")
            Ladrilho { anchors.fill: parent; icone: ilha.lixeiraCheia ? "lixeira-cheia" : "lixeira"; estilo: "claro"; tamanho: ilhaFundo.tamanhoIcone }
        }
    }
}
