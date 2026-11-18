// DuiaOS — Ora: favoritos por pasta, com edição, importação de outros navegadores e exportação.
import QtQuick
import QtQuick.Dialogs
import DuiaOS

PaginaInterna {
    id: pagina
    titulo: "Favoritos"
    icone: "estrela"
    property string busca: ""
    property int editando: -1
    property bool importando: false
    property var navegadores: []

    readonly property var grupos: {
        var lista = ora.favoritos, mapa = {}, ordem = []
        var termo = busca.toLowerCase()
        for (var i = 0; i < lista.length; i++) {
            var f = lista[i]
            if (termo !== "" && (f.titulo + " " + f.url).toLowerCase().indexOf(termo) < 0) continue
            var nome = f.pasta === "" ? "Barra de favoritos" : f.pasta
            if (!mapa[nome]) { mapa[nome] = { nome: nome, itens: [] }; ordem.push(nome) }
            mapa[nome].itens.push(f)
        }
        return ordem.map(function (n) { return mapa[n] })
    }

    acoes: [
        Campo { width: 220; icone: "busca"; dica: "Buscar nos favoritos"; onTextoChanged: pagina.busca = texto },
        Botao { texto: "Importar"; icone: "download"; onClicado: { pagina.navegadores = ora.navegadoresParaImportar(); pagina.importando = !pagina.importando } },
        Botao { texto: "Exportar"; icone: "abrir"; onClicado: aviso.mostrar(ora.exportarFavoritos()) }
    ]

    FileDialog {
        id: escolherArquivo
        title: "Arquivo de favoritos (HTML)"
        nameFilters: ["Favoritos (*.html *.htm)"]
        onAccepted: { aviso.mostrar(ora.importar("html", selectedFile.toString())); pagina.importando = false }
    }

    Cartao {
        visible: pagina.importando
        width: parent.width
        height: colunaImportar.implicitHeight + 32
        Column {
            id: colunaImportar
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
            spacing: 10
            Rotulo { text: "Trazer os favoritos de outro navegador:"; font.weight: Font.DemiBold }
            Rotulo { visible: pagina.navegadores.length === 0; secundario: true
                     text: "Nenhum outro navegador com favoritos foi encontrado neste computador." }
            Flow {
                width: parent.width
                spacing: 8
                Repeater {
                    model: pagina.navegadores
                    delegate: Botao { required property var modelData; texto: modelData.nome
                                      onClicado: { aviso.mostrar(ora.importar(modelData.id, modelData.caminho)); pagina.importando = false } }
                }
                Botao { texto: "Arquivo HTML…"; onClicado: escolherArquivo.open() }
            }
        }
    }

    Text {
        visible: pagina.grupos.length === 0
        width: parent.width
        topPadding: 40
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        text: pagina.busca !== "" ? "Nenhum favorito combina com “" + pagina.busca + "”."
                                  : "Nenhum favorito ainda. Clique na estrela da barra de endereço para guardar uma página."
        color: Tema.textoSecundario
        font { family: Tema.fonteTexto; pixelSize: 14 }
    }

    Repeater {
        model: pagina.grupos
        delegate: Column {
            required property var modelData
            width: parent ? parent.width : 0
            spacing: 6
            Row {
                spacing: 8
                topPadding: 8
                Icone { nome: modelData.nome === "Barra de favoritos" ? "estrela" : "pasta"; tamanho: 15; cor: Tema.textoSecundario }
                Text { text: modelData.nome; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
            }
            Cartao {
                width: parent.width
                height: listaPasta.implicitHeight + 8
                Column {
                    id: listaPasta
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                    Repeater {
                        model: modelData.itens
                        delegate: Rectangle {
                            id: linha
                            required property var modelData
                            readonly property bool emEdicao: pagina.editando === modelData.id
                            width: listaPasta.width; height: emEdicao ? 92 : 44; radius: 8
                            color: areaLinha.containsMouse && !emEdicao ? Tema.realce : "transparent"
                            Favicon { id: ic; anchors { left: parent.left; leftMargin: 12; top: parent.top; topMargin: 14 }
                                      url: linha.modelData.url; titulo: linha.modelData.titulo; tamanho: 16 }
                            Column {
                                visible: !linha.emEdicao
                                anchors { left: ic.right; leftMargin: 12; right: botoes.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                Text { width: parent.width; text: linha.modelData.titulo || linha.modelData.url; elide: Text.ElideRight
                                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                                Text { width: parent.width; text: ora.paraMostrar(linha.modelData.url); elide: Text.ElideRight
                                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            }
                            MouseArea { id: areaLinha; anchors.fill: parent; hoverEnabled: true; enabled: !linha.emEdicao
                                        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                                        onClicked: (m) => pagina.janelaOra.abrir(linha.modelData.url, m.button === Qt.MiddleButton || (m.modifiers & Qt.ControlModifier)) }
                            Row {
                                id: botoes
                                visible: !linha.emEdicao && areaLinha.containsMouse
                                anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                                BotaoIcone { icone: "lapis"; tamanhoIcone: 13; corIcone: Tema.textoSecundario; dica: "Editar"; onClicado: pagina.editando = linha.modelData.id }
                                BotaoIcone { icone: "lixeira"; tamanhoIcone: 13; corIcone: Tema.textoSecundario; dica: "Remover"; onClicado: ora.removerFavorito(linha.modelData.url) }
                            }
                            Column {
                                visible: linha.emEdicao
                                anchors { left: ic.right; leftMargin: 12; right: parent.right; rightMargin: 12; top: parent.top; topMargin: 8 }
                                spacing: 6
                                Row {
                                    width: parent.width; spacing: 6
                                    Campo { id: campoTitulo; width: (parent.width - 6) * 0.4; height: 32; texto: linha.modelData.titulo; dica: "Nome" }
                                    Campo { id: campoUrl; width: (parent.width - 6) * 0.6; height: 32; texto: linha.modelData.url; dica: "Endereço" }
                                }
                                Row {
                                    spacing: 6
                                    Botao { texto: "Salvar"; tipo: "primario"; height: 30
                                            onClicado: { ora.editarFavorito(linha.modelData.id, campoTitulo.texto, campoUrl.texto); pagina.editando = -1 } }
                                    Botao { texto: "Cancelar"; height: 30; onClicado: pagina.editando = -1 }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    Aviso { id: aviso; parent: pagina; anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 24 } }
}
