// DuiaOS — Central de IA: modelo ativo do sistema, download e catálogo.
// Dados: central.estadoJson (JSON do serviço duiaos-ia); ações: central.baixar,
// ativar, remover e cancelar. Um só modelo ativo para o sistema inteiro.
import QtQuick
import QtQuick.Window
import QtQuick.Controls

ApplicationWindow {
    id: janela
    width: 920
    height: 720
    minimumWidth: 560
    minimumHeight: 480
    visible: true
    title: "Central de IA"
    color: cores.fundo

    QtObject {
        id: cores
        readonly property color fundo: "#F7F9FC"
        readonly property color cartao: "#FFFFFF"
        readonly property color destaque: "#E8F0FE"
        readonly property color azul: "#2E6BE6"
        readonly property color azulEscuro: "#255BC7"
        readonly property color noite: "#1A3A73"
        readonly property color texto: "#1F2933"
        readonly property color secundario: "#5B6675"
        readonly property color borda: "#DDE3EC"
        readonly property color sucesso: "#2FA67A"
        readonly property color aviso: "#E8A33D"
        readonly property color avisoFundo: "#FDF4E5"
        readonly property color erro: "#D9534F"
        readonly property color erroFundo: "#FBECEB"
    }
    readonly property string fonteTitulo: "Manrope"
    readonly property string fonte: "Inter"

    property var estado: ({})
    function atualizar() {
        try { estado = JSON.parse(central.estadoJson) } catch (e) { estado = ({}) }
    }
    Connections {
        target: central
        function onMudou() { janela.atualizar() }
        function onErro(mensagem) { aviso.mostrar(mensagem) }
    }
    Component.onCompleted: atualizar()

    readonly property var tarefa: estado.tarefa || null
    readonly property var familias: estado.familias || []
    readonly property var modeloAtivo: {
        for (const f of familias)
            for (const m of f.modelos)
                if (m.ativo) return m
        return null
    }
    function nomeModelo(id) {
        for (const f of familias)
            for (const m of f.modelos)
                if (m.id === id) return f.nome + " " + m.tamanho
        return id
    }
    function gb(bytes) { return (bytes / 1073741824).toLocaleString(Qt.locale("pt_BR"), "f", 1) + " GB" }
    function numero(valor) { return Number(valor).toLocaleString(Qt.locale("pt_BR"), "f", 1) }

    // ------------------------------------------------------------ componentes
    component Rotulo: Text {
        color: cores.texto
        font { family: janela.fonte; pixelSize: 14 }
        wrapMode: Text.WordWrap
    }

    component Etiqueta: Rectangle {
        property alias texto: rotuloEtiqueta.text
        property color corTexto: cores.noite
        property color corFundo: cores.destaque
        height: 22
        width: rotuloEtiqueta.implicitWidth + 16
        radius: 11
        color: corFundo
        Text {
            id: rotuloEtiqueta
            anchors.centerIn: parent
            color: parent.corTexto
            font { family: janela.fonte; pixelSize: 11; weight: Font.DemiBold }
        }
    }

    component Botao: Rectangle {
        id: botao
        property alias texto: rotuloBotao.text
        property bool principal: true
        property bool perigo: false
        property bool habilitado: true
        signal clicado()
        width: rotuloBotao.implicitWidth + 28
        height: 34
        radius: 17
        opacity: habilitado ? 1 : 0.45
        color: !principal ? (areaBotao.containsMouse && habilitado ? cores.destaque : cores.cartao)
                          : (areaBotao.pressed ? cores.noite : (areaBotao.containsMouse && habilitado ? cores.azulEscuro : cores.azul))
        border { width: principal ? 0 : 1; color: perigo ? cores.erro : cores.borda }
        Behavior on color { ColorAnimation { duration: 120 } }
        Text {
            id: rotuloBotao
            anchors.centerIn: parent
            color: botao.principal ? "white" : (botao.perigo ? cores.erro : cores.noite)
            font { family: janela.fonte; pixelSize: 13; weight: Font.DemiBold }
        }
        MouseArea {
            id: areaBotao
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: botao.habilitado ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (botao.habilitado) botao.clicado()
        }
    }

    component Cartao: Rectangle {
        width: parent ? parent.width : 0
        radius: 16
        color: cores.cartao
        border { width: 1; color: cores.borda }
    }

    // ------------------------------------------------------------ conteúdo
    ScrollView {
        id: rolagem
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true

        Column {
            id: coluna
            width: Math.min(rolagem.availableWidth - 48, 840)
            x: (rolagem.availableWidth - width) / 2
            topPadding: 32
            bottomPadding: 40
            spacing: 18

            // Cabeçalho
            Column {
                width: parent.width
                spacing: 6
                Text {
                    text: "Central de IA"
                    color: cores.noite
                    font { family: janela.fonteTitulo; pixelSize: 28; weight: Font.ExtraBold }
                }
                Rotulo {
                    width: parent.width
                    color: cores.secundario
                    text: "Um modelo de IA ativo para o sistema inteiro: o Wise e os outros programas usam o mesmo. "
                          + "Tudo roda neste computador, sem enviar nada para a internet."
                }
            }

            // Avisos: serviço ou Ollama parados, último download com erro
            Rectangle {
                width: parent.width
                visible: !central.servicoOk || janela.estado.ollama === false
                height: visible ? textoParado.implicitHeight + 24 : 0
                radius: 12
                color: cores.erroFundo
                Rotulo {
                    id: textoParado
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                    color: cores.erro
                    text: !central.servicoOk
                          ? "O serviço de IA do sistema não está respondendo. Tente abrir a Central de novo em instantes."
                          : "A IA local (Ollama) não está respondendo. Reinicie o computador ou veja: systemctl status ollama"
                }
            }
            Rectangle {
                readonly property var ultima: janela.estado.ultima || null
                width: parent.width
                visible: !janela.tarefa && ultima !== null && ultima.resultado === "erro"
                height: visible ? textoUltima.implicitHeight + 24 : 0
                radius: 12
                color: cores.avisoFundo
                Rotulo {
                    id: textoUltima
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                    text: parent.ultima ? "Não deu para baixar " + janela.nomeModelo(parent.ultima.modelo) + ": " + parent.ultima.mensagem : ""
                }
            }

            // Modelo ativo
            Cartao {
                height: 104
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: cores.noite }
                    GradientStop { position: 1; color: cores.azul }
                }
                border.width: 0
                Row {
                    anchors { left: parent.left; leftMargin: 24; verticalCenter: parent.verticalCenter }
                    spacing: 18
                    Rectangle {
                        width: 56; height: 56; radius: 28
                        color: Qt.rgba(1, 1, 1, 0.16)
                        anchors.verticalCenter: parent.verticalCenter
                        // Pulso suave: a IA está ligada
                        Rectangle {
                            anchors.centerIn: parent
                            width: 18; height: 18; radius: 9
                            color: janela.modeloAtivo ? "#7CE0B5" : "#FFFFFF"
                            SequentialAnimation on scale {
                                running: janela.modeloAtivo !== null
                                loops: Animation.Infinite
                                NumberAnimation { to: 1.35; duration: 900; easing.type: Easing.InOutSine }
                                NumberAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutSine }
                            }
                        }
                    }
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 4
                        Text {
                            text: "MODELO ATIVO"
                            color: Qt.rgba(1, 1, 1, 0.7)
                            font { family: janela.fonte; pixelSize: 11; weight: Font.Bold; letterSpacing: 1 }
                        }
                        Text {
                            text: janela.modeloAtivo ? janela.modeloAtivo.familia + " " + janela.modeloAtivo.tamanho
                                                     : (janela.tarefa ? "Preparando a IA…" : "Nenhum modelo ativo")
                            color: "white"
                            font { family: janela.fonteTitulo; pixelSize: 22; weight: Font.ExtraBold }
                        }
                        Text {
                            text: janela.estado.calibrando
                                  ? "Medindo a velocidade deste computador para ajustar a IA (cerca de 1 minuto)…"
                                  : janela.modeloAtivo
                                  ? janela.modeloAtivo.descricao + " · licença " + janela.modeloAtivo.licenca.nome
                                  : "Escolha um modelo abaixo para ligar a IA do sistema."
                            color: Qt.rgba(1, 1, 1, 0.82)
                            font { family: janela.fonte; pixelSize: 13 }
                        }
                    }
                }
            }

            // Download em andamento
            Cartao {
                visible: janela.tarefa !== null
                height: visible ? 96 : 0
                Column {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                    spacing: 10
                    Item {
                        width: parent.width
                        height: 34
                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            Text {
                                text: janela.tarefa ? "Baixando " + janela.nomeModelo(janela.tarefa.modelo) : ""
                                color: cores.noite
                                font { family: janela.fonte; pixelSize: 15; weight: Font.DemiBold }
                            }
                            Text {
                                text: janela.tarefa
                                      ? Math.round(janela.tarefa.fracao * 100) + "% · " + janela.gb(janela.tarefa.concluido)
                                        + " de " + janela.gb(janela.tarefa.total)
                                        + (janela.tarefa.automatico ? " · modelo padrão do DuiaOS" : "")
                                      : ""
                                color: cores.secundario
                                font { family: janela.fonte; pixelSize: 12 }
                            }
                        }
                        Botao {
                            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                            texto: "Cancelar"
                            principal: false
                            onClicado: central.cancelar()
                        }
                    }
                    Rectangle {
                        width: parent.width
                        height: 8
                        radius: 4
                        color: cores.destaque
                        Rectangle {
                            width: parent.width * (janela.tarefa ? janela.tarefa.fracao : 0)
                            height: parent.height
                            radius: 4
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: cores.azul }
                                GradientStop { position: 1; color: "#5B8DEF" }
                            }
                            Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                        }
                    }
                }
            }

            Text {
                text: "Modelos disponíveis"
                topPadding: 8
                color: cores.noite
                font { family: janela.fonteTitulo; pixelSize: 18; weight: Font.ExtraBold }
            }
            Rotulo {
                width: parent.width
                color: cores.secundario
                font.pixelSize: 13
                text: "Este computador tem " + janela.numero(janela.estado.memoria_gb || 0) + " GB de memória. "
                      + "Modelos maiores respondem melhor, mas pedem mais memória e são mais lentos."
            }

            // Famílias
            Repeater {
                model: janela.familias
                delegate: Cartao {
                    id: cartaoFamilia
                    required property var modelData
                    height: colunaFamilia.implicitHeight + 8
                    Column {
                        id: colunaFamilia
                        width: parent.width
                        Item {
                            width: parent.width
                            height: cabecalhoFamilia.implicitHeight + 32
                            Column {
                                id: cabecalhoFamilia
                                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20; topMargin: 18 }
                                spacing: 6
                                Row {
                                    spacing: 10
                                    Text {
                                        text: cartaoFamilia.modelData.nome
                                        color: cores.noite
                                        font { family: janela.fonteTitulo; pixelSize: 17; weight: Font.ExtraBold }
                                    }
                                    Text {
                                        anchors.bottom: parent.bottom
                                        bottomPadding: 3
                                        text: cartaoFamilia.modelData.autor
                                        color: cores.secundario
                                        font { family: janela.fonte; pixelSize: 12 }
                                    }
                                }
                                Rotulo {
                                    width: parent.width
                                    font.pixelSize: 13
                                    color: cores.secundario
                                    text: cartaoFamilia.modelData.descricao
                                }
                            }
                        }
                        Repeater {
                            model: cartaoFamilia.modelData.modelos
                            delegate: Item {
                                id: linha
                                required property var modelData
                                readonly property var m: modelData
                                readonly property bool baixando: janela.tarefa !== null && janela.tarefa.modelo === m.id
                                width: colunaFamilia.width
                                height: Math.max(64, infoModelo.implicitHeight + 24)
                                Rectangle {
                                    anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 20; rightMargin: 20 }
                                    height: 1
                                    color: cores.borda
                                }
                                Rectangle {
                                    anchors { fill: parent; leftMargin: 8; rightMargin: 8; topMargin: 4; bottomMargin: 4 }
                                    radius: 10
                                    color: linha.m.ativo ? cores.destaque : "transparent"
                                }
                                Column {
                                    id: infoModelo
                                    anchors { left: parent.left; leftMargin: 20; right: acoes.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                    spacing: 4
                                    opacity: linha.m.cabe ? 1 : 0.6
                                    Flow {
                                        width: parent.width
                                        spacing: 8
                                        Text {
                                            text: linha.m.tamanho
                                            color: cores.texto
                                            font { family: janela.fonte; pixelSize: 15; weight: Font.DemiBold }
                                        }
                                        Etiqueta { visible: linha.m.ativo; texto: "Ativo"; corFundo: cores.sucesso; corTexto: "white" }
                                        Etiqueta { visible: linha.m.padrao; texto: "Recomendado" }
                                        Etiqueta { visible: linha.m.instalado && !linha.m.ativo; texto: "Baixado"; corFundo: "#EEF1F5"; corTexto: cores.secundario }
                                        Etiqueta {
                                            visible: !linha.m.licenca.livre
                                            texto: "Licença não livre"
                                            corFundo: cores.avisoFundo
                                            corTexto: "#9A6412"
                                        }
                                    }
                                    Rotulo {
                                        width: parent.width
                                        font.pixelSize: 12
                                        color: cores.secundario
                                        text: linha.m.descricao + " · download de " + janela.numero(linha.m.download_gb)
                                              + " GB · usa cerca de " + janela.numero(linha.m.memoria_gb) + " GB de memória"
                                    }
                                    Rotulo {
                                        visible: linha.m.aviso !== ""
                                        width: parent.width
                                        font.pixelSize: 12
                                        color: linha.m.cabe ? "#9A6412" : cores.erro
                                        text: "⚠ " + linha.m.aviso
                                    }
                                }
                                Row {
                                    id: acoes
                                    anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                                    spacing: 8
                                    Botao {
                                        visible: linha.m.instalado && !linha.m.ativo
                                        texto: "Remover"
                                        principal: false
                                        perigo: true
                                        onClicado: confirmacao.perguntar("remover", linha.m)
                                    }
                                    Botao {
                                        visible: linha.m.instalado && !linha.m.ativo
                                        texto: "Usar este"
                                        onClicado: central.ativar(linha.m.id)
                                    }
                                    Botao {
                                        visible: !linha.m.instalado && !linha.baixando
                                        texto: "Baixar"
                                        principal: false
                                        habilitado: linha.m.cabe && janela.tarefa === null
                                        onClicado: {
                                            if (!linha.m.licenca.livre) confirmacao.perguntar("licenca", linha.m)
                                            else central.baixar(linha.m.id)
                                        }
                                    }
                                    Text {
                                        visible: linha.baixando
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: "Baixando…"
                                        color: cores.azul
                                        font { family: janela.fonte; pixelSize: 13; weight: Font.DemiBold }
                                    }
                                    Text {
                                        visible: linha.m.ativo
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: "Em uso"
                                        color: cores.sucesso
                                        font { family: janela.fonte; pixelSize: 13; weight: Font.DemiBold }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // IA na nuvem (próximo passo da ADR 029)
            Cartao {
                height: textoNuvem.implicitHeight + 36
                color: "transparent"
                border.color: cores.borda
                Column {
                    id: textoNuvem
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                    spacing: 4
                    Text {
                        text: "IA na nuvem"
                        color: cores.noite
                        font { family: janela.fonte; pixelSize: 14; weight: Font.DemiBold }
                    }
                    Rotulo {
                        width: parent.width
                        font.pixelSize: 13
                        color: cores.secundario
                        text: "Em breve aqui. Por enquanto, a chave do Gemini fica nas configurações do Wise, e só é usada com a sua permissão."
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------ confirmação
    Rectangle {
        id: confirmacao
        property string tipo: ""
        property var modelo: null
        function perguntar(t, m) { tipo = t; modelo = m; visible = true }
        anchors.fill: parent
        visible: false
        color: Qt.rgba(0.06, 0.12, 0.25, 0.45)
        MouseArea { anchors.fill: parent; onClicked: confirmacao.visible = false }
        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 460)
            height: conteudoConfirmacao.implicitHeight + 48
            radius: 18
            color: cores.cartao
            MouseArea { anchors.fill: parent }
            Column {
                id: conteudoConfirmacao
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 14
                Text {
                    text: confirmacao.tipo === "remover" ? "Remover este modelo?" : "Licença do modelo"
                    color: cores.noite
                    font { family: janela.fonteTitulo; pixelSize: 19; weight: Font.ExtraBold }
                }
                Rotulo {
                    width: parent.width
                    text: !confirmacao.modelo ? "" : confirmacao.tipo === "remover"
                          ? confirmacao.modelo.familia + " " + confirmacao.modelo.tamanho + " sai deste computador e libera cerca de "
                            + janela.numero(confirmacao.modelo.download_gb) + " GB. Dá para baixar de novo quando quiser."
                          : confirmacao.modelo.familia + " " + confirmacao.modelo.tamanho + " usa a " + confirmacao.modelo.licenca.nome
                            + ". Ela não é uma licença livre: tem regras de uso próprias, definidas pela Meta. "
                            + "Ao baixar, você concorda com esses termos."
                }
                Text {
                    visible: confirmacao.tipo === "licenca" && confirmacao.modelo !== null && confirmacao.modelo.licenca.url !== ""
                    text: "Ler a licença"
                    color: cores.azul
                    font { family: janela.fonte; pixelSize: 14; weight: Font.DemiBold; underline: true }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: central.abrirEndereco(confirmacao.modelo.licenca.url)
                    }
                }
                Row {
                    anchors.right: parent.right
                    spacing: 10
                    Botao { texto: "Cancelar"; principal: false; onClicado: confirmacao.visible = false }
                    Botao {
                        texto: confirmacao.tipo === "remover" ? "Remover" : "Aceitar e baixar"
                        onClicado: {
                            if (confirmacao.tipo === "remover") central.remover(confirmacao.modelo.id)
                            else central.baixar(confirmacao.modelo.id)
                            confirmacao.visible = false
                        }
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------ aviso rápido
    Rectangle {
        id: aviso
        property string texto: ""
        function mostrar(t) { texto = t; opacity = 1; temporizador.restart() }
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 24 }
        width: Math.min(parent.width - 48, textoAviso.implicitWidth + 40)
        height: textoAviso.implicitHeight + 24
        radius: 14
        color: cores.noite
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        Rotulo {
            id: textoAviso
            anchors.centerIn: parent
            width: Math.min(implicitWidth, janela.width - 88)
            color: "white"
            text: aviso.texto
        }
        Timer { id: temporizador; interval: 5000; onTriggered: aviso.opacity = 0 }
    }

    // Captura para testes (main.py --demonstracao --captura ARQUIVO)
    Timer {
        running: capturaArquivo !== ""
        interval: 900
        onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() })
    }
}
