// DuiaOS — Ora: configurações. Ao abrir, buscador, aparência, downloads, privacidade, importar
// favoritos, navegador padrão e a versão do motor.
import QtQuick
import QtQuick.Dialogs
import DuiaOS

PaginaInterna {
    id: pagina
    titulo: "Configurações"
    icone: "engrenagem"
    larguraMaxima: 760
    readonly property var cfg: ora.configuracoes
    property bool padrao: ora.ehPadrao()
    Connections { target: ora; function onConfiguracoesMudaram() { pagina.padrao = ora.ehPadrao() } }

    component Secao: Column {
        property string nome: ""
        default property alias itens: colunaSecao.data
        width: parent ? parent.width : 0
        spacing: 8
        Text { text: nome; color: Tema.textoSecundario; topPadding: 6
               font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
        Cartao {
            id: cartao
            width: parent.width
            height: colunaSecao.implicitHeight + 24
            Column { id: colunaSecao; anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 } spacing: 4 }
        }
    }
    component LinhaInterruptor: Item {
        property string texto: ""
        property string descricao: ""
        property bool ligado: false
        signal alternado(bool ligado)
        width: parent ? parent.width : 0
        height: Math.max(44, colunaTexto.implicitHeight + 16)
        Column {
            id: colunaTexto
            anchors { left: parent.left; leftMargin: 4; right: chave.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
            spacing: 2
            Text { width: parent.width; text: texto; color: Tema.texto; wrapMode: Text.WordWrap; font { family: Tema.fonteTexto; pixelSize: 14 } }
            Text { width: parent.width; visible: descricao !== ""; text: descricao; color: Tema.textoSecundario; wrapMode: Text.WordWrap
                   font { family: Tema.fonteTexto; pixelSize: 12 } }
        }
        Interruptor { id: chave; anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                      ligado: parent.ligado; onAlternado: (v) => parent.alternado(v) }
    }

    Secao {
        nome: "Ao abrir o Ora"
        Opcao { width: parent.width; texto: "Mostrar a página de nova aba"; marcada: pagina.cfg.ao_iniciar === "inicio"; onEscolhida: ora.definir("ao_iniciar", "inicio") }
        Opcao { width: parent.width; texto: "Continuar de onde parou"; descricao: "Reabre as abas que estavam abertas"
                marcada: pagina.cfg.ao_iniciar === "sessao"; onEscolhida: ora.definir("ao_iniciar", "sessao") }
        Opcao { width: parent.width; texto: "Abrir uma página específica"; marcada: pagina.cfg.ao_iniciar === "pagina"; onEscolhida: ora.definir("ao_iniciar", "pagina") }
        Campo { visible: pagina.cfg.ao_iniciar === "pagina"; width: parent.width; dica: "Endereço da página inicial"
                texto: pagina.cfg.pagina_inicial; onConfirmado: ora.definir("pagina_inicial", texto)
                entrada.onEditingFinished: ora.definir("pagina_inicial", texto) }
    }

    Secao {
        nome: "Buscador"
        Rotulo { secundario: true; text: "Usado na barra de endereço e na página de nova aba."; bottomPadding: 4 }
        Flow {
            width: parent.width
            spacing: 8
            Repeater {
                model: ora.buscadores()
                delegate: Rectangle {
                    required property var modelData
                    readonly property bool escolhido: pagina.cfg.buscador === modelData.id
                    width: rotuloBuscador.implicitWidth + 28; height: 34; radius: 17
                    color: escolhido ? Tema.destaque : (areaBuscador.containsMouse ? Tema.realce : "transparent")
                    border { width: 1; color: escolhido ? Tema.azulDuia : Tema.borda }
                    Text { id: rotuloBuscador; anchors.centerIn: parent; text: modelData.nome
                           color: parent.escolhido ? Tema.azulDuia : Tema.texto
                           font { family: Tema.fonteTexto; pixelSize: 13; weight: parent.escolhido ? Font.DemiBold : Font.Normal } }
                    MouseArea { id: areaBuscador; anchors.fill: parent; hoverEnabled: true; onClicked: ora.definir("buscador", modelData.id) }
                }
            }
        }
    }

    Secao {
        nome: "Aparência"
        LinhaInterruptor { texto: "Mostrar a barra de favoritos"; ligado: pagina.cfg.barra_de_favoritos === true
                           onAlternado: (v) => ora.definir("barra_de_favoritos", v) }
        Item {
            width: parent.width; height: 44
            Text { anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter } text: "Zoom das páginas"
                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14 } }
            Row {
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                spacing: 6
                Repeater {
                    model: [0.8, 0.9, 1.0, 1.1, 1.25, 1.5]
                    delegate: Rectangle {
                        required property var modelData
                        readonly property bool escolhido: Math.abs((pagina.cfg.zoom_padrao || 1) - modelData) < 0.01
                        width: 52; height: 30; radius: 8
                        color: escolhido ? Tema.destaque : (areaZoom.containsMouse ? Tema.realce : "transparent")
                        border { width: 1; color: escolhido ? Tema.azulDuia : Tema.borda }
                        Text { anchors.centerIn: parent; text: Math.round(modelData * 100) + "%"; color: parent.escolhido ? Tema.azulDuia : Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 12 } }
                        MouseArea { id: areaZoom; anchors.fill: parent; hoverEnabled: true; onClicked: ora.definir("zoom_padrao", modelData) }
                    }
                }
            }
        }
        Rotulo { secundario: true; width: parent.width; wrapMode: Text.WordWrap; text: "Modo claro, escuro e o estilo Futurista seguem as Configurações › Aparência do DuiaOS." }
    }

    Secao {
        nome: "Downloads"
        Item {
            width: parent.width; height: 48
            Column {
                anchors { left: parent.left; leftMargin: 4; right: botaoPasta.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                Text { text: "Salvar em"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14 } }
                Text { width: parent.width; elide: Text.ElideMiddle; text: pagina.cfg.pasta_downloads || "Pasta Downloads"
                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
            }
            Botao { id: botaoPasta; anchors { right: parent.right; verticalCenter: parent.verticalCenter } texto: "Mudar…"; onClicado: escolherPasta.open() }
        }
    }
    FolderDialog { id: escolherPasta; title: "Pasta dos downloads"; onAccepted: ora.definir("pasta_downloads", selectedFolder.toString().replace("file://", "")) }

    Secao {
        nome: "Privacidade"
        LinhaInterruptor { texto: "Pedir aos sites que não me rastreiem"; descricao: "Envia os sinais Do Not Track e Global Privacy Control"
                           ligado: pagina.cfg.nao_rastrear === true; onAlternado: (v) => ora.definir("nao_rastrear", v) }
        Item {
            width: parent.width; height: 52
            Column {
                anchors { left: parent.left; leftMargin: 4; right: botaoLimpar.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                Text { text: "Limpar dados de navegação"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14 } }
                Text { width: parent.width; wrapMode: Text.WordWrap; text: "Histórico, cookies (você sai das contas dos sites) e arquivos temporários"
                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
            }
            Botao { id: botaoLimpar; anchors { right: parent.right; verticalCenter: parent.verticalCenter } texto: "Limpar"; tipo: "perigo"
                    onClicado: ora.limparDadosDeNavegacao() }
        }
    }

    Secao {
        nome: "Navegador padrão"
        Item {
            width: parent.width; height: 48
            Text { anchors { left: parent.left; leftMargin: 4; right: botaoPadrao.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                   wrapMode: Text.WordWrap
                   text: pagina.padrao ? "O Ora é o navegador padrão do DuiaOS." : "Os links abertos em outros aplicativos vão para outro navegador."
                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14 } }
            Botao { id: botaoPadrao; visible: !pagina.padrao; anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    texto: "Tornar padrão"; tipo: "primario"; onClicado: ora.tornarPadrao() }
            Icone { visible: pagina.padrao; anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter } nome: "check"; tamanho: 20; cor: Tema.sucesso }
        }
    }

    Secao {
        nome: "Sobre o Ora"
        Rotulo { width: parent.width; wrapMode: Text.WordWrap
                 text: "Ora " + ora.versao + " — o navegador do DuiaOS.\nMotor Qt WebEngine " + ora.versaoMotor + " (Chromium " + ora.versaoChromium + ")." }
    }
}
