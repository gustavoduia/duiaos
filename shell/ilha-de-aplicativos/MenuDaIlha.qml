// DuiaOS — menu do botão direito na Ilha de Aplicativos (acima do ícone clicado).
import QtQuick
import DuiaOS

Item {
    id: camada
    readonly property var m: ilha.menu
    property bool confirmarEsvaziar: false
    onMChanged: confirmarEsvaziar = false
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton; onClicked: ilha.fecharMenu() }
    focus: true
    Keys.onEscapePressed: ilha.fecharMenu()
    Cartao {
        width: 240
        height: coluna.implicitHeight + 12
        x: Math.max(8, Math.min(camada.width - width - 8, ilha.ancoraDownloads - width / 2))
        y: camada.height - height - 10
        raio: 10
        cor: Tema.cartao
        MouseArea { anchors.fill: parent }
        Column {
            id: coluna
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 6 }
            Text { visible: camada.m.tipo === "app"; leftPadding: 10; topPadding: 4; bottomPadding: 4; text: camada.m.nome || ""
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
            ItemDeMenu { texto: camada.m.aberto ? "Mostrar" : "Abrir"; icone: "abrir"; onClicado: ilha.acaoMenu("abrir") }
            ItemDeMenu { visible: camada.m.tipo === "app" && camada.m.aberto; texto: "Nova janela"; icone: "mais"; onClicado: ilha.acaoMenu("nova-janela") }
            Separador { visible: camada.m.tipo === "app" && (camada.m.podeFixar || camada.m.aberto) }
            ItemDeMenu { visible: camada.m.tipo === "app" && camada.m.podeFixar; texto: camada.m.fixado ? "Tirar da Ilha" : "Manter na Ilha"
                         icone: "estrela"; onClicado: ilha.acaoMenu("fixar") }
            ItemDeMenu { visible: camada.m.tipo === "app" && camada.m.aberto; texto: "Fechar"; icone: "fechar"; onClicado: ilha.acaoMenu("fechar") }
            Separador { visible: camada.m.tipo === "lixeira" }
            ItemDeMenu { visible: camada.m.tipo === "lixeira" && !camada.confirmarEsvaziar; texto: "Esvaziar a Lixeira…"; icone: "lixeira"
                         ativo: camada.m.lixeiraCheia === true; perigo: true; onClicado: camada.confirmarEsvaziar = true }
            ItemDeMenu { visible: camada.m.tipo === "lixeira" && camada.confirmarEsvaziar; texto: "Apagar tudo de vez"; icone: "check"; perigo: true
                         onClicado: ilha.acaoMenu("esvaziar") }
        }
    }
}
