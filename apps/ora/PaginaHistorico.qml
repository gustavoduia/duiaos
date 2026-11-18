// DuiaOS — Ora: histórico, agrupado por dia, com busca e opções para apagar.
import QtQuick
import DuiaOS

PaginaInterna {
    id: pagina
    titulo: "Histórico"
    icone: "recentes"
    property string busca: ""
    property var itens: []
    property bool opcoesApagar: false

    function nomeDoDia(data) {
        var hoje = new Date(); hoje.setHours(0, 0, 0, 0)
        var dia = new Date(data.getTime()); dia.setHours(0, 0, 0, 0)
        var diferenca = Math.round((hoje - dia) / 86400000)
        if (diferenca === 0) return "Hoje"
        if (diferenca === 1) return "Ontem"
        var texto = data.toLocaleDateString(Qt.locale("pt_BR"), "dddd, d 'de' MMMM")
        return texto.charAt(0).toUpperCase() + texto.slice(1)
    }
    function carregar() {
        var lista = ora.historico(busca)
        var grupos = [], atual = null
        for (var i = 0; i < lista.length; i++) {
            var data = new Date(lista[i].ultima * 1000)
            var nome = nomeDoDia(data)
            if (!atual || atual.nome !== nome) { atual = { nome: nome, itens: [] }; grupos.push(atual) }
            var item = lista[i]
            item.hora = data.toLocaleTimeString(Qt.locale("pt_BR"), "HH:mm")
            atual.itens.push(item)
        }
        itens = grupos
    }
    Component.onCompleted: carregar()
    Connections { target: ora; function onMudou() { pagina.carregar() } }

    acoes: [
        Campo { width: 260; icone: "busca"; dica: "Buscar no histórico"
                onTextoChanged: { pagina.busca = texto; pagina.carregar() } },
        Botao { texto: "Apagar histórico"; icone: "lixeira"; onClicado: pagina.opcoesApagar = !pagina.opcoesApagar }
    ]

    Cartao {
        visible: pagina.opcoesApagar
        width: parent.width
        height: linhaApagar.implicitHeight + 32
        Column {
            id: linhaApagar
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
            spacing: 12
            Rotulo { text: "Apagar as páginas visitadas:"; font.weight: Font.DemiBold }
            Row {
                spacing: 8
                Botao { texto: "Última hora"; onClicado: { ora.apagarHistorico("hora"); pagina.opcoesApagar = false } }
                Botao { texto: "Últimas 24 horas"; onClicado: { ora.apagarHistorico("dia"); pagina.opcoesApagar = false } }
                Botao { texto: "Últimos 7 dias"; onClicado: { ora.apagarHistorico("semana"); pagina.opcoesApagar = false } }
                Botao { texto: "Tudo"; tipo: "perigo"; onClicado: { ora.apagarHistorico("tudo"); pagina.opcoesApagar = false } }
            }
        }
    }

    Text {
        visible: pagina.itens.length === 0
        width: parent.width
        topPadding: 40
        horizontalAlignment: Text.AlignHCenter
        text: pagina.busca !== "" ? "Nada no histórico combina com “" + pagina.busca + "”." : "Nenhuma página visitada ainda."
        color: Tema.textoSecundario
        font { family: Tema.fonteTexto; pixelSize: 14 }
    }

    Repeater {
        model: pagina.itens
        delegate: Column {
            required property var modelData
            width: pagina.width > 0 ? parent.width : 0
            spacing: 6
            Text { text: modelData.nome; color: Tema.textoSecundario; topPadding: 8
                   font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
            Cartao {
                width: parent.width
                height: listaDia.implicitHeight + 8
                Column {
                    id: listaDia
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                    Repeater {
                        model: modelData.itens
                        delegate: Rectangle {
                            required property var modelData
                            width: listaDia.width; height: 42; radius: 8
                            color: areaLinha.containsMouse ? Tema.realce : "transparent"
                            Text { id: hora; anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                                   width: 44; text: modelData.hora; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Favicon { id: ic; anchors { left: hora.right; leftMargin: 4; verticalCenter: parent.verticalCenter }
                                      url: modelData.url; titulo: modelData.titulo; tamanho: 16 }
                            Text { id: tit; anchors { left: ic.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                                   width: Math.min(implicitWidth, parent.width * 0.5)
                                   text: modelData.titulo || modelData.url; elide: Text.ElideRight
                                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                            Text { anchors { left: tit.right; leftMargin: 8; right: remover.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                   text: ora.dominio(modelData.url); elide: Text.ElideRight
                                   color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            MouseArea { id: areaLinha; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                                        onClicked: (m) => pagina.janelaOra.abrir(modelData.url, m.button === Qt.MiddleButton || (m.modifiers & Qt.ControlModifier)) }
                            BotaoIcone { id: remover; anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                                         visible: areaLinha.containsMouse || hovered; property bool hovered: false
                                         icone: "fechar"; tamanhoIcone: 12; corIcone: Tema.textoSecundario; dica: "Tirar do histórico"
                                         onClicado: ora.removerDoHistorico(modelData.id) }
                        }
                    }
                }
            }
        }
    }
}
