// Calendário do mês, com o dia de hoje marcado e setas para os outros meses.
import QtQuick

Item {
    id: raiz
    property date hoje: new Date()
    property int ano: hoje.getFullYear()
    property int mes: hoje.getMonth()
    readonly property var local: Qt.locale("pt_BR")
    width: 252
    height: cabecalho.height + grade.height + 34

    function primeiroDiaDaSemana() { return new Date(ano, mes, 1).getDay() }
    function diasNoMes() { return new Date(ano, mes + 1, 0).getDate() }
    function mudarMes(delta) {
        var d = new Date(ano, mes + delta, 1)
        ano = d.getFullYear(); mes = d.getMonth()
    }

    Item {
        id: cabecalho
        width: parent.width; height: 30
        Text {
            anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
            text: { var t = raiz.local.standaloneMonthName(raiz.mes, Locale.LongFormat); return t.charAt(0).toUpperCase() + t.slice(1) + " de " + raiz.ano }
            color: Tema.texto
            font { family: Tema.fonteTitulo; pixelSize: 15; weight: Font.Bold }
        }
        Row {
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            BotaoIcone { icone: "seta-esquerda"; width: 26; height: 26; tamanhoIcone: 14; onClicado: raiz.mudarMes(-1) }
            BotaoIcone { icone: "ponto"; width: 26; height: 26; tamanhoIcone: 10; corIcone: Tema.azulDuia
                         onClicado: { raiz.ano = raiz.hoje.getFullYear(); raiz.mes = raiz.hoje.getMonth() } }
            BotaoIcone { icone: "seta-direita"; width: 26; height: 26; tamanhoIcone: 14; onClicado: raiz.mudarMes(1) }
        }
    }
    Row {
        id: semana
        anchors { top: cabecalho.bottom; topMargin: 6 }
        Repeater {
            model: ["D", "S", "T", "Q", "Q", "S", "S"]
            Text { required property string modelData; width: 36; horizontalAlignment: Text.AlignHCenter; text: modelData
                   color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
        }
    }
    Grid {
        id: grade
        anchors { top: semana.bottom; topMargin: 4 }
        columns: 7
        Repeater {
            model: 42
            Item {
                required property int index
                readonly property int dia: index - raiz.primeiroDiaDaSemana() + 1
                readonly property bool valido: dia >= 1 && dia <= raiz.diasNoMes()
                readonly property bool eHoje: valido && dia === raiz.hoje.getDate() && raiz.mes === raiz.hoje.getMonth() && raiz.ano === raiz.hoje.getFullYear()
                visible: index < 35 || raiz.primeiroDiaDaSemana() + raiz.diasNoMes() > 35
                width: 36; height: 30
                Rectangle { anchors.centerIn: parent; width: 28; height: 28; radius: 14; color: parent.eHoje ? Tema.azulDuia : "transparent" }
                Text {
                    anchors.centerIn: parent
                    text: parent.valido ? parent.dia : ""
                    color: parent.eHoje ? "white" : Tema.texto
                    font { family: Tema.fonteTexto; pixelSize: 13; weight: parent.eHoje ? Font.Bold : Font.Normal }
                }
            }
        }
    }
}
