// DuiaOS — o que abre a partir da Barra de Recursos: Menu do DuiaOS, balão dos ícones
// ocultos, Central de Controle, balões de cada ícone (Wi-Fi, som, brilho, bateria,
// Bluetooth, luz noturna), calendário e a confirmação de Reiniciar/Desligar/Encerrar.
//
// Ocupa a área de trabalho inteira (abaixo da barra): um clique fora do cartão ou
// Esc fecha. sistema.ancora diz onde, ao longo da barra, o cartão deve nascer.
import QtQuick
import DuiaOS

Item {
    id: painel
    property string posicao: configuracao.posicao
    readonly property bool horizontal: posicao === "topo" || posicao === "base"
    readonly property string aberto: sistema.painel
    readonly property bool temAlgo: aberto !== "" || sistema.confirmacao !== ""
    focus: true
    Keys.onEscapePressed: sistema.fecharPainel()

    onAbertoChanged: {
        if (aberto === "wifi") controles.buscarRedes(true)
        if (aberto === "bluetooth") controles.buscarBluetooth(false)
        senhaPara = ""
    }
    property string senhaPara: ""

    // Clique fora fecha
    MouseArea { anchors.fill: parent; enabled: painel.temAlgo; onClicked: sistema.fecharPainel() }

    // Posição do cartão junto à barra
    property real deslocamento: 0          // reservado (a camada já começa depois da barra)
    function posicionar(cartao, alinharInicio) {
        var m = 6
        var a = sistema.ancora          // ao longo da barra, a camada começa junto com ela
        if (horizontal) {
            cartao.x = alinharInicio ? Math.max(m, a - 17) : Math.max(m, Math.min(width - cartao.width - m, a - cartao.width / 2))
            cartao.y = posicao === "topo" ? m : height - cartao.height - m
        } else {
            cartao.y = alinharInicio ? Math.max(m, a - 17) : Math.max(m, Math.min(height - cartao.height - m, a - cartao.height / 2))
            cartao.x = posicao === "esquerda" ? m : width - cartao.width - m
        }
    }

    component Balao: Cartao {
        id: balao
        property string nome: ""
        property bool alinharInicio: false
        default property alias corpo: coluna.data
        property alias coluna: coluna
        visible: painel.aberto === nome
        width: 300
        height: coluna.implicitHeight + 24
        onVisibleChanged: if (visible) painel.posicionar(balao, alinharInicio)
        onHeightChanged: if (visible) painel.posicionar(balao, alinharInicio)
        opacity: visible ? 1 : 0
        scale: visible ? 1 : 0.97
        Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        MouseArea { anchors.fill: parent }     // clique dentro não fecha
        Column {
            id: coluna
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            spacing: 6
        }
    }

    component Cabecalho: Item {
        property string texto: ""
        property bool comInterruptor: false
        property bool ligado: false
        signal alternado(bool v)
        width: parent.width; height: 30
        Text {
            anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
            text: parent.texto
            color: Tema.texto
            font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.Bold }
        }
        Interruptor {
            visible: parent.comInterruptor
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            ligado: parent.ligado
            onAlternado: (v) => parent.alternado(v)
        }
    }

    component Subtitulo: Text {
        width: parent.width
        leftPadding: 4; topPadding: 4
        color: Tema.textoSecundario
        font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold }
    }

    // ============================================================ Menu do aplicativo em foco
    MenuDoAplicativo { posicionar: painel.posicionar; z: 5 }

    // ============================================================ Menu do DuiaOS
    Balao {
        nome: "menu"
        alinharInicio: true
        width: 300
        coluna.spacing: 0
        ItemDeMenu { texto: "Sobre este computador"; icone: "info"; onClicado: sistema.abrir("sobre") }
        Separador {}
        ItemDeMenu { texto: "Configurações…"; icone: "engrenagem"; onClicado: sistema.abrir("configuracoes") }
        ItemDeMenu { texto: "Central de Aplicativos"; icone: "aplicativos"; atalho: "Super Espaço"; onClicado: sistema.abrir("central") }
        ItemDeMenu { texto: "Explorador de Arquivos"; icone: "pasta"; onClicado: sistema.abrir("explorador") }
        ItemDeMenu { visible: sistema.wise; texto: "Wise"; icone: "ia"; atalho: "Super W"; onClicado: sistema.abrirWise() }
        Separador {}
        ItemDeMenu { texto: "Repousar"; icone: "lua"; onClicado: sistema.pedirEnergia("suspender") }
        ItemDeMenu { texto: "Reiniciar…"; icone: "reiniciar"; onClicado: sistema.pedirEnergia("reiniciar") }
        ItemDeMenu { visible: sistema.windows; texto: "Reiniciar no Windows…"; icone: "monitor"; onClicado: sistema.pedirEnergia("windows") }
        ItemDeMenu { texto: "Desligar…"; icone: "energia"; atalho: "Ctrl Alt Del"; onClicado: sistema.pedirEnergia("desligar") }
        Separador {}
        ItemDeMenu { texto: "Bloquear tela"; icone: "cadeado"; atalho: "Super L"; onClicado: sistema.pedirEnergia("bloquear") }
        ItemDeMenu { texto: "Encerrar sessão de " + sistema.usuario + "…"; icone: "sair"; onClicado: sistema.pedirEnergia("encerrar") }
    }

    // ================================================ balão dos ícones ocultos
    Balao {
        id: balaoOcultos
        nome: "balao"
        width: Math.max(160, gradeOcultos.implicitWidth + 24)
        Flow {
            id: gradeOcultos
            width: Math.min(4, painel.ocultos.length) * 66
            spacing: 2
            Repeater {
                model: painel.ocultos
                Rectangle {
                    required property string modelData
                    width: 64; height: 62; radius: 10
                    color: areaOculto.containsMouse ? Tema.destaque : "transparent"
                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Item {
                            width: 24; height: 22
                            anchors.horizontalCenter: parent.horizontalCenter
                            Icone {
                                anchors.centerIn: parent
                                visible: modelData !== "bateria"
                                tamanho: 20
                                nome: ({ wise: "ia", wifi: controles.wifiLigado ? "wifi-" + Math.max(1, controles.nivelWifi) : "wifi-desligado",
                                         som: controles.mudo ? "som-mudo" : "som-2", bluetooth: "bluetooth", brilho: "brilho", luz: "lua" })[modelData] || "ponto"
                            }
                            IconeBateria { anchors.centerIn: parent; visible: modelData === "bateria"; nivel: controles.bateria; carregando: controles.carregando }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: ({ wise: "Wise", wifi: "Wi-Fi", som: "Som", bateria: controles.bateria + "%", bluetooth: "Bluetooth",
                                     brilho: "Brilho", luz: "Luz noturna" })[modelData] || modelData
                            color: Tema.texto
                            font { family: Tema.fonteTexto; pixelSize: 11 }
                        }
                    }
                    MouseArea {
                        id: areaOculto
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: modelData === "wise" ? sistema.abrirWise() : sistema.abrirPainel(modelData, sistema.ancora)
                    }
                }
            }
        }
    }
    property var ocultos: []

    // ======================================================== Central de Controle
    component Quadro: Rectangle {
        radius: 14
        color: Tema.cartao
        border { color: Tema.borda; width: 1 }
    }
    component BotaoRedondo: Rectangle {
        property string icone: ""
        property bool ligado: false
        signal clicado()
        width: 30; height: 30; radius: 15
        color: ligado ? Tema.azulDuia : Tema.controleDesligado
        Icone { anchors.centerIn: parent; nome: parent.icone; tamanho: 16; cor: parent.ligado ? "white" : Tema.texto }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: parent.clicado() }
    }
    component LinhaDeControle: Item {
        id: linhaControle
        property string icone: ""
        property string titulo: ""
        property string detalhe: ""
        property bool ligado: false
        property string abre: ""
        signal alternado()
        width: parent.width; height: 40
        BotaoRedondo { id: redondo; anchors.verticalCenter: parent.verticalCenter; icone: linhaControle.icone; ligado: linhaControle.ligado; onClicado: linhaControle.alternado() }
        Column {
            anchors { left: redondo.right; leftMargin: 9; right: parent.right; verticalCenter: parent.verticalCenter }
            Text { width: parent.width; text: linhaControle.titulo; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
            Text { width: parent.width; text: linhaControle.detalhe; elide: Text.ElideRight; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
        }
        MouseArea {
            anchors { left: redondo.right; right: parent.right; top: parent.top; bottom: parent.bottom }
            enabled: linhaControle.abre !== ""
            cursorShape: Qt.PointingHandCursor
            onClicked: sistema.abrirPainel(linhaControle.abre, sistema.ancora)
        }
    }
    component QuadroPequeno: Quadro {
        id: qp
        property string icone: ""
        property string texto: ""
        property bool ligado: false
        signal clicado()
        color: ligado ? Tema.azulDuia : (areaQp.containsMouse ? Tema.realce : Tema.cartao)
        Column {
            anchors.centerIn: parent
            spacing: 5
            Icone { anchors.horizontalCenter: parent.horizontalCenter; nome: qp.icone; tamanho: 20; cor: qp.ligado ? "white" : Tema.texto }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: qp.texto; horizontalAlignment: Text.AlignHCenter
                   color: qp.ligado ? "white" : Tema.texto; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.Medium } }
        }
        MouseArea { id: areaQp; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: qp.clicado() }
    }

    Balao {
        nome: "central"
        width: 364
        coluna.spacing: 10

        Row {
            width: parent.width
            spacing: 10
            Quadro {
                width: (parent.width - 10) * 0.52
                height: 146
                Column {
                    anchors { fill: parent; margins: 10 }
                    spacing: 4
                    LinhaDeControle {
                        // Sem placa Wi-Fi (máquina virtual, computador só com cabo): o quadro vira "Rede" (ADR 069)
                        icone: !rede.temWifi && rede.temPlaca ? (rede.icone || "rede") : (controles.wifiLigado ? "wifi-3" : "wifi-desligado")
                        titulo: !rede.temWifi && rede.temPlaca ? "Rede" : "Wi-Fi"
                        detalhe: !rede.temWifi && rede.temPlaca ? rede.resumo.split(" · ")[0]
                                 : (!controles.wifiLigado ? "Desligado" : (controles.wifiRede !== "" ? controles.wifiRede : (rede.temCabo ? "Cabo conectado" : "Sem rede")))
                        ligado: rede.temWifi ? controles.wifiLigado : rede.icone === "rede"
                        abre: "wifi"
                        onAlternado: if (rede.temWifi) controles.ligarWifi(!controles.wifiLigado)
                    }
                    LinhaDeControle {
                        icone: "bluetooth"
                        titulo: "Bluetooth"
                        detalhe: !controles.bluetoothExiste ? "Indisponível" : (!controles.bluetoothLigado ? "Desligado"
                                 : (controles.bluetoothConectados.length > 0 ? controles.bluetoothConectados[0].nome : "Ligado"))
                        ligado: controles.bluetoothLigado
                        abre: controles.bluetoothExiste ? "bluetooth" : ""
                        onAlternado: if (controles.bluetoothExiste) controles.ligarBluetooth(!controles.bluetoothLigado)
                    }
                    LinhaDeControle {
                        icone: "aviao"
                        titulo: "Modo avião"
                        detalhe: controles.modoAviaoLigado ? "Ligado" : "Desligado"
                        ligado: controles.modoAviaoLigado
                        onAlternado: controles.modoAviao(!controles.modoAviaoLigado)
                    }
                }
            }
            Column {
                width: (parent.width - 10) * 0.48
                spacing: 10
                Quadro {
                    width: parent.width; height: 68
                    LinhaDeControle {
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
                        width: undefined
                        icone: "lua"
                        titulo: "Luz noturna"
                        detalhe: ({ desligada: "Desligada", ligada: "Ligada", programada: "Programada" })[controles.luzNoturna]
                        ligado: controles.luzNoturna !== "desligada"
                        abre: "luz"
                        onAlternado: controles.definirLuzNoturna(controles.luzNoturna === "desligada" ? "ligada" : "desligada")
                    }
                }
                Quadro {
                    width: parent.width; height: 68
                    LinhaDeControle {
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
                        width: undefined
                        icone: "sino-desligado"
                        titulo: "Não perturbe"
                        detalhe: sistema.naoPerturbe ? "Ligado" : "Desligado"
                        ligado: sistema.naoPerturbe
                        onAlternado: sistema.definirNaoPerturbe(!sistema.naoPerturbe)
                    }
                }
            }
        }

        Quadro {
            visible: controles.brilho >= 0
            width: parent.width; height: 66
            Text { x: 12; y: 9; text: "Tela"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
            Deslizante {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 10 }
                valor: controles.brilho
                icone: "brilho"; iconeBaixo: "brilho-baixo"
                onMovido: (v) => controles.definirBrilho(v)
            }
        }
        Quadro {
            visible: controles.volume >= 0
            width: parent.width; height: 66
            Text { x: 12; y: 9; text: "Som"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
            BotaoIcone { anchors { right: parent.right; top: parent.top; margins: 5 } width: 24; height: 24; icone: "seta-direita"; tamanhoIcone: 14
                         onClicado: sistema.abrirPainel("som", sistema.ancora) }
            Deslizante {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 10 }
                valor: controles.mudo ? 0 : controles.volume
                icone: controles.mudo ? "som-mudo" : "som-2"; iconeBaixo: controles.mudo ? "som-mudo" : "som-0"
                onMovido: (v) => controles.definirVolume(v)
                onIconeClicado: controles.alternarMudo()
            }
        }
        Quadro {
            visible: controles.bateria >= 0 || controles.perfis.length > 0
            width: parent.width; height: 74
            Row {
                x: 12; y: 10; spacing: 8
                IconeBateria { visible: controles.bateria >= 0; anchors.verticalCenter: parent.verticalCenter; nivel: controles.bateria; carregando: controles.carregando }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: controles.bateria >= 0 ? controles.bateria + "%" + (controles.carregando ? " · carregando" : (controles.tomada ? " · na tomada" : (controles.tempoBateria !== "" ? " · " + controles.tempoBateria : ""))) : "Modo de energia"
                    color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
                }
            }
            Row {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 10 }
                spacing: 6
                visible: controles.perfis.length > 0
                Repeater {
                    model: controles.perfis
                    Rectangle {
                        required property string modelData
                        width: (parent.width - 12) / 3; height: 26; radius: 8
                        color: controles.perfil === modelData ? Tema.azulDuia : Tema.controleDesligado
                        Text { anchors.centerIn: parent; text: controles.nomesPerfis[modelData]
                               color: controles.perfil === modelData ? "white" : Tema.texto; font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.Medium } }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: controles.definirPerfil(modelData) }
                    }
                }
            }
        }
        Row {
            id: linhaPequenos
            width: parent.width; spacing: 10
            readonly property int quantos: sistema.wise ? 4 : 3
            readonly property real lado: (width - (quantos - 1) * 10) / quantos
            QuadroPequeno { width: linhaPequenos.lado; height: 62; icone: "cadeado"; texto: "Bloquear"; onClicado: sistema.pedirEnergia("bloquear") }
            QuadroPequeno { width: linhaPequenos.lado; height: 62; icone: "captura"; texto: "Capturar"
                            onClicado: { sistema.fecharPainel(); controles.capturarTela() } }
            QuadroPequeno { visible: sistema.wise; width: linhaPequenos.lado; height: 62; icone: "ia"; texto: "Wise"; onClicado: sistema.abrirWise() }
            QuadroPequeno { width: linhaPequenos.lado; height: 62; icone: "engrenagem"; texto: "Ajustes"; onClicado: sistema.abrir("configuracoes") }
        }
    }

    // ================================================================= Wi-Fi
    Balao {
        nome: "wifi"
        // Rede e Internet (ADR 069): o estado em uma frase, o cabo e as VPNs, depois a Wi-Fi
        Cabecalho { texto: rede.temWifi ? "Wi-Fi" : "Rede"; comInterruptor: rede.temWifi; ligado: controles.wifiLigado; onAlternado: (v) => controles.ligarWifi(v) }
        Subtitulo { text: rede.resumo; wrapMode: Text.WordWrap }
        Repeater {
            model: rede.dispositivos.filter(function (d) { return d.tipo === "cabo" || d.tipo === "celular" || d.tipo === "bluetooth" })
            LinhaDeLista {
                required property var modelData
                icone: modelData.tipo === "cabo" ? "rede" : (modelData.tipo === "celular" ? "celular" : "bluetooth")
                texto: modelData.tipo === "cabo" ? "Cabo de rede" : (modelData.tipo === "celular" ? "Rede celular" : "Celular pelo Bluetooth")
                marcada: modelData.estado === "conectado"
                detalhe: ({ conectado: "Conectado", conectando: "Conectando…", desconectado: "Desconectado", indisponivel: "Sem cabo" })[modelData.estado] || ""
                onClicada: modelData.estado === "conectado" ? rede.desconectarDispositivo(modelData.dispositivo) : rede.conectarDispositivo(modelData.dispositivo)
            }
        }
        Repeater {
            model: rede.conexoes.filter(function (c) { return c.tipo === "vpn" })
            LinhaDeLista {
                required property var modelData
                icone: "vpn"
                texto: modelData.nome
                marcada: modelData.ativa
                detalhe: modelData.ativa ? "VPN ligada" : "VPN"
                onClicada: modelData.ativa ? rede.desativar(modelData.uuid) : rede.ativar(modelData.uuid)
            }
        }
        Subtitulo { visible: rede.temWifi && controles.wifiLigado; text: controles.buscandoRedes ? "Procurando redes…" : "Redes Wi-Fi" }
        Column {
            width: parent.width
            visible: rede.temWifi && controles.wifiLigado
            Repeater {
                model: controles.redes
                Column {
                    required property var modelData
                    width: parent.width
                    LinhaDeLista {
                        icone: "wifi-" + (modelData.sinal >= 67 ? 3 : (modelData.sinal >= 34 ? 2 : 1))
                        texto: modelData.ssid
                        marcada: modelData.conectada
                        detalhe: modelData.conectada ? "Conectada" : (controles.redeSalva(modelData.ssid) ? "Salva" : "")
                        onClicada: {
                            if (modelData.conectada) return
                            if (!modelData.segura || controles.redeSalva(modelData.ssid)) controles.conectarWifi(modelData.ssid, "")
                            else painel.senhaPara = modelData.ssid
                        }
                        Icone { visible: modelData.segura; nome: "cadeado"; tamanho: 13; cor: Tema.textoApagado; anchors.verticalCenter: parent.verticalCenter }
                    }
                    Row {
                        visible: painel.senhaPara === modelData.ssid
                        width: parent.width
                        spacing: 6
                        leftPadding: 6; topPadding: 2; bottomPadding: 6
                        Campo {
                            id: campoSenha
                            width: parent.width - botaoConectar.width - 18
                            senha: true
                            dica: "Senha"
                            onVisibleChanged: if (visible) entrada.forceActiveFocus()
                            onConfirmado: { controles.conectarWifi(modelData.ssid, texto); painel.senhaPara = "" }
                        }
                        Botao {
                            id: botaoConectar
                            texto: "Conectar"; tipo: "primario"
                            onClicado: { controles.conectarWifi(modelData.ssid, campoSenha.texto); painel.senhaPara = "" }
                        }
                    }
                }
            }
        }
        Separador {}
        ItemDeMenu { texto: "Configurações de rede…"; onClicado: sistema.abrir("configuracoes:rede") }
    }

    // =================================================================== Som
    Balao {
        nome: "som"
        Cabecalho { texto: "Som" }
        Deslizante {
            width: parent.width
            valor: controles.mudo ? 0 : controles.volume
            icone: controles.mudo ? "som-mudo" : "som-2"; iconeBaixo: controles.mudo ? "som-mudo" : "som-0"
            onMovido: (v) => controles.definirVolume(v)
            onIconeClicado: controles.alternarMudo()
        }
        Subtitulo { text: "Saída"; visible: controles.saidas.length > 0 }
        Repeater {
            model: controles.saidas
            LinhaDeLista {
                required property var modelData
                icone: "som-2"; texto: modelData.nome; marcada: modelData.padrao
                onClicada: controles.escolherDispositivoDeSom(modelData.id)
            }
        }
        Subtitulo { text: "Microfone"; visible: controles.microfone >= 0 }
        Deslizante {
            visible: controles.microfone >= 0
            width: parent.width
            valor: controles.microfoneMudo ? 0 : controles.microfone
            icone: "microfone"
            onMovido: (v) => controles.definirMicrofone(v)
            onIconeClicado: controles.alternarMicrofoneMudo()
        }
        Separador {}
        ItemDeMenu { texto: "Configurações de som…"; onClicado: sistema.abrir("configuracoes:som") }
    }

    // ================================================================ Brilho
    Balao {
        nome: "brilho"
        Cabecalho { texto: "Tela" }
        Deslizante {
            width: parent.width
            valor: controles.brilho
            icone: "brilho"; iconeBaixo: "brilho-baixo"
            onMovido: (v) => controles.definirBrilho(v)
        }
        Item {
            width: parent.width; height: 34
            Text { anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter } text: "Luz noturna"
                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
            Interruptor { anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                          ligado: controles.luzNoturna !== "desligada"
                          onAlternado: (v) => controles.definirLuzNoturna(v ? "ligada" : "desligada") }
        }
        Separador {}
        ItemDeMenu { texto: "Configurações da tela…"; onClicado: sistema.abrir("configuracoes:tela") }
    }

    // =============================================================== Bateria
    Balao {
        nome: "bateria"
        Item {
            width: parent.width; height: 38
            Text { anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
                   text: "Bateria"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.Bold } }
            Text { anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                   text: controles.bateria + "%"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 20; weight: Font.Bold } }
        }
        Rotulo {
            width: parent.width; leftPadding: 4
            secundario: true
            text: controles.carregando ? "Carregando" + (controles.tempoBateria !== "" ? " · cheia em " + controles.tempoBateria : "")
                  : (controles.tomada ? "Na tomada" : (controles.tempoBateria !== "" ? "Restam cerca de " + controles.tempoBateria : "Usando a bateria"))
        }
        Subtitulo { text: "Modo de energia"; visible: controles.perfis.length > 0 }
        Repeater {
            model: controles.perfis
            Opcao {
                required property string modelData
                texto: controles.nomesPerfis[modelData]
                descricao: ({ "power-saver": "Mais horas de bateria", balanced: "Para o dia a dia", performance: "Mais rápido, gasta mais" })[modelData]
                marcada: controles.perfil === modelData
                onEscolhida: controles.definirPerfil(modelData)
            }
        }
        Separador {}
        ItemDeMenu { texto: "Configurações de bateria…"; onClicado: sistema.abrir("configuracoes:energia") }
    }

    // ============================================================= Bluetooth
    Balao {
        nome: "bluetooth"
        Cabecalho { texto: "Bluetooth"; comInterruptor: true; ligado: controles.bluetoothLigado; onAlternado: (v) => controles.ligarBluetooth(v) }
        Subtitulo { visible: controles.bluetoothLigado; text: "Dispositivos" }
        Repeater {
            model: controles.bluetoothLigado ? controles.bluetoothPareados : []
            LinhaDeLista {
                required property var modelData
                icone: "bluetooth"; texto: modelData.nome
                marcada: modelData.conectado
                detalhe: modelData.conectado ? "Conectado" : "Não conectado"
                onClicada: modelData.conectado ? controles.desconectarBluetooth(modelData.endereco) : controles.conectarBluetooth(modelData.endereco)
            }
        }
        Rotulo {
            visible: controles.bluetoothLigado && controles.bluetoothPareados.length === 0
            width: parent.width; leftPadding: 4; secundario: true
            text: "Nenhum dispositivo pareado."
        }
        Separador {}
        ItemDeMenu { texto: "Configurações de Bluetooth…"; onClicado: sistema.abrir("configuracoes:bluetooth") }
    }

    // =========================================================== Luz noturna
    Balao {
        nome: "luz"
        Cabecalho { texto: "Luz noturna" }
        Rotulo { width: parent.width; leftPadding: 4; secundario: true; text: "Cores mais quentes na tela, que cansam menos a vista à noite." }
        Opcao { texto: "Desligada"; marcada: controles.luzNoturna === "desligada"; onEscolhida: controles.definirLuzNoturna("desligada") }
        Opcao { texto: "Ligada agora"; marcada: controles.luzNoturna === "ligada"; onEscolhida: controles.definirLuzNoturna("ligada") }
        Opcao { texto: "Programada"; descricao: "Das 19:00 às 6:30 (mude nas Configurações)"; marcada: controles.luzNoturna === "programada"
                onEscolhida: controles.definirLuzNoturna("programada") }
        Separador {}
        ItemDeMenu { texto: "Configurações da tela…"; onClicado: sistema.abrir("configuracoes:tela") }
    }

    // ============================================================ Calendário
    Balao {
        nome: "calendario"
        width: 300
        Text {
            width: parent.width; leftPadding: 4
            text: { var t = new Date().toLocaleDateString(Qt.locale("pt_BR"), "dddd, d 'de' MMMM 'de' yyyy"); return t.charAt(0).toUpperCase() + t.slice(1) }
            color: Tema.textoSecundario
            font { family: Tema.fonteTexto; pixelSize: 12 }
        }
        Calendario { anchors.horizontalCenter: parent.horizontalCenter; hoje: new Date() }
        Separador {}
        Item {
            width: parent.width; height: 26
            Text { anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter } text: "Notificações"
                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Bold } }
            Text {
                visible: sistema.historico.length > 0
                anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                text: "Limpar"; color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
                MouseArea { anchors { fill: parent; margins: -6 } cursorShape: Qt.PointingHandCursor; onClicked: sistema.limparNotificacoes() }
            }
        }
        Rotulo { visible: sistema.historico.length === 0; width: parent.width; leftPadding: 4; secundario: true
                 text: sistema.naoPerturbe ? "Não perturbe está ligado. As notificações novas ficam aqui." : "Nenhuma notificação." }
        Flickable {
            visible: sistema.historico.length > 0
            width: parent.width
            height: Math.min(colunaNotificacoes.height, 260)
            contentHeight: colunaNotificacoes.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: colunaNotificacoes
                width: parent.width
                spacing: 6
                Repeater {
                    model: sistema.historico
                    Rectangle {
                        required property var modelData
                        width: colunaNotificacoes.width
                        height: textosNotificacao.implicitHeight + 16
                        radius: 10
                        color: Tema.cartao
                        border { color: Tema.borda; width: 1 }
                        Column {
                            id: textosNotificacao
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8; rightMargin: 28 }
                            Text { text: modelData.app + "  ·  " + modelData.quando; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
                            Text { width: parent.width; text: modelData.titulo; elide: Text.ElideRight; color: Tema.texto
                                   font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.Bold } }
                            Text { width: parent.width; visible: modelData.texto !== ""; text: modelData.texto; wrapMode: Text.WordWrap
                                   maximumLineCount: 2; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        }
                        BotaoIcone { anchors { right: parent.right; top: parent.top; margins: 4 } width: 20; height: 20; icone: "fechar"; tamanhoIcone: 11
                                     corIcone: Tema.textoSecundario; onClicado: sistema.removerNotificacao(modelData.id) }
                    }
                }
            }
        }
        Separador {}
        ItemDeMenu { texto: "Configurações de data e hora…"; onClicado: sistema.abrir("configuracoes:data") }
    }

    // ============================================ confirmação de energia
    Rectangle {
        id: confirmacao
        anchors.fill: parent
        visible: sistema.confirmacao !== ""
        color: Qt.rgba(0.06, 0.09, 0.14, 0.35)
        MouseArea { anchors.fill: parent; onClicked: sistema.fecharPainel() }
        readonly property var textos: ({
            reiniciar: ["reiniciar", "Deseja reiniciar o computador agora?", "Os aplicativos abertos serão fechados.", "Reiniciar"],
            windows: ["monitor", "Deseja reiniciar no Windows agora?", "O Windows abre uma vez; depois o computador volta ao DuiaOS.", "Reiniciar no Windows"],
            desligar: ["energia", "Deseja desligar o computador agora?", "Os aplicativos abertos serão fechados.", "Desligar"],
            encerrar: ["sair", "Deseja encerrar a sessão de " + sistema.usuario + "?", "Os aplicativos abertos serão fechados e a Tela de Entrada aparece.", "Encerrar sessão"]
        })
        readonly property var texto: textos[sistema.confirmacao] || ["energia", "", "", ""]
        Cartao {
            anchors.centerIn: parent
            width: 360; height: colunaConfirmar.implicitHeight + 40
            raio: 20
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Column {
                id: colunaConfirmar
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 10
                Rectangle {
                    width: 48; height: 48; radius: 24; color: Tema.destaque
                    anchors.horizontalCenter: parent.horizontalCenter
                    Icone { anchors.centerIn: parent; nome: confirmacao.texto[0]; tamanho: 24; cor: Tema.azulNoite }
                }
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
                       text: confirmacao.texto[1]; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 16; weight: Font.Bold } }
                Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
                       text: confirmacao.texto[2]; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
                Item { width: 1; height: 4 }
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10
                    Botao { texto: "Cancelar"; width: 130; onClicado: sistema.fecharPainel() }
                    Botao { texto: confirmacao.texto[3]; tipo: "primario"; width: 150; onClicado: sistema.confirmarEnergia() }
                }
            }
        }
        focus: visible
        Keys.onReturnPressed: sistema.confirmarEnergia()
        Keys.onEscapePressed: sistema.fecharPainel()
    }
}
