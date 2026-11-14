// DuiaOS — menu do botão direito na Ilha de Aplicativos (ao lado do ícone clicado).
// Aplicativo: abrir/mostrar, nova janela, minimizar, manter ou tirar da Ilha, fechar.
// Fundo da Ilha: ampliação, ocultar automaticamente, posição, efeito ao minimizar, Configurações.
import QtQuick
import DuiaOS
import "posicao.js" as Posicao

Item {
    id: camada
    readonly property var m: ilha.menu
    readonly property var o: ilha.opcoes
    property bool confirmarEsvaziar: false
    onMChanged: confirmarEsvaziar = false
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton; onClicked: ilha.fecharMenu() }
    focus: true
    Keys.onEscapePressed: ilha.fecharMenu()

    // Opção com marca (✓) à esquerda, para escolhas do menu do fundo
    component Escolha: ItemDeMenu {
        property bool marcada: false
        icone: marcada ? "check" : "vazio"
    }

    Cartao {
        id: cartao
        width: 250
        height: coluna.implicitHeight + 12
        readonly property var lugar: Posicao.balao(camada.o.posicao, camada.width, camada.height, ilha.ancoraDownloads, width, height)
        x: lugar.x
        y: lugar.y
        raio: 10
        cor: Tema.cartao
        MouseArea { anchors.fill: parent }
        Column {
            id: coluna
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 6 }
            readonly property bool app: camada.m.tipo === "app"
            readonly property bool fundo: camada.m.tipo === "ilha"
            Text { visible: coluna.app; leftPadding: 10; topPadding: 4; bottomPadding: 4; text: camada.m.nome || ""
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }

            // ------------------------------------------------ aplicativo e pastas
            ItemDeMenu { visible: !coluna.fundo; texto: camada.m.aberto ? "Mostrar" : "Abrir"; icone: "abrir"; onClicado: ilha.acaoMenu("abrir") }
            ItemDeMenu { visible: coluna.app && camada.m.aberto; texto: "Nova janela"; icone: "mais"; onClicado: ilha.acaoMenu("nova-janela") }
            ItemDeMenu { visible: coluna.app && camada.m.aberto; texto: "Minimizar"; icone: "seta-baixo"; atalho: "Super+M"; onClicado: ilha.acaoMenu("minimizar") }
            Separador { visible: coluna.app && (camada.m.podeFixar || camada.m.aberto || camada.m.recente) }
            ItemDeMenu { visible: coluna.app && camada.m.podeFixar; texto: camada.m.fixado ? "Tirar da Ilha" : "Manter na Ilha"
                         icone: camada.m.fixado ? "fechar" : "estrela"; onClicado: ilha.acaoMenu("fixar") }
            ItemDeMenu { visible: coluna.app && camada.m.recente === true; texto: "Tirar dos recentes"; icone: "recentes"; onClicado: ilha.acaoMenu("esquecer") }
            ItemDeMenu { visible: coluna.app && camada.m.aberto; texto: "Fechar"; icone: "fechar"; perigo: true; onClicado: ilha.acaoMenu("fechar") }
            Separador { visible: camada.m.tipo === "lixeira" }
            ItemDeMenu { visible: camada.m.tipo === "lixeira" && !camada.confirmarEsvaziar; texto: "Esvaziar a Lixeira…"; icone: "lixeira"
                         ativo: camada.m.lixeiraCheia === true; perigo: true; onClicado: camada.confirmarEsvaziar = true }
            ItemDeMenu { visible: camada.m.tipo === "lixeira" && camada.confirmarEsvaziar; texto: "Apagar tudo de vez"; icone: "check"; perigo: true
                         onClicado: ilha.acaoMenu("esvaziar") }
            Separador { visible: !coluna.fundo && !coluna.app }
            ItemDeMenu { visible: !coluna.fundo && !coluna.app; texto: "Opções da Ilha…"; icone: "engrenagem"; onClicado: ilha.acaoMenu("configuracoes") }

            // ------------------------------------------------ fundo da Ilha
            ItemDeMenu { visible: coluna.fundo; texto: camada.o.ampliacao ? "Desligar a ampliação" : "Ligar a ampliação"; icone: "busca"
                         onClicado: ilha.acaoMenu("opcao:ampliacao=" + (camada.o.ampliacao ? "nao" : "sim")) }
            ItemDeMenu { visible: coluna.fundo; texto: camada.o.ocultar ? "Desligar o ocultar automático" : "Ocultar automaticamente"; icone: "olho"
                         onClicado: ilha.acaoMenu("opcao:ocultar=" + (camada.o.ocultar ? "nao" : "sim")) }
            Separador { visible: coluna.fundo }
            Text { visible: coluna.fundo; leftPadding: 10; topPadding: 2; bottomPadding: 2; text: "Posição na tela"
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
            Escolha { visible: coluna.fundo; texto: "Embaixo"; marcada: camada.o.posicao === "base"; onClicado: ilha.acaoMenu("opcao:posicao=base") }
            Escolha { visible: coluna.fundo; texto: "À esquerda"; marcada: camada.o.posicao === "esquerda"; onClicado: ilha.acaoMenu("opcao:posicao=esquerda") }
            Escolha { visible: coluna.fundo; texto: "À direita"; marcada: camada.o.posicao === "direita"; onClicado: ilha.acaoMenu("opcao:posicao=direita") }
            Separador { visible: coluna.fundo }
            Text { visible: coluna.fundo; leftPadding: 10; topPadding: 2; bottomPadding: 2; text: "Efeito ao minimizar"
                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
            Escolha { visible: coluna.fundo; texto: "Gênio"; marcada: camada.o.minimizar === "genio"; onClicado: ilha.acaoMenu("opcao:minimizar=genio") }
            Escolha { visible: coluna.fundo; texto: "Escala (suave)"; marcada: camada.o.minimizar === "escala"; onClicado: ilha.acaoMenu("opcao:minimizar=escala") }
            Escolha { visible: coluna.fundo; texto: "Nenhum"; marcada: camada.o.minimizar === "nenhum"; onClicado: ilha.acaoMenu("opcao:minimizar=nenhum") }
            Separador { visible: coluna.fundo }
            ItemDeMenu { visible: coluna.fundo; texto: "Opções da Ilha…"; icone: "engrenagem"; onClicado: ilha.acaoMenu("configuracoes") }
        }
    }
}
