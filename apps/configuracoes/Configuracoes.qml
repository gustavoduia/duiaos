// DuiaOS — Configurações.
// Barra lateral com a pessoa e as seções; à direita, a página da seção em grupos
// (cartões brancos com linhas), no estilo dos Ajustes do Sistema.
import QtQuick
import QtQuick.Window
import QtQuick.Dialogs
import DuiaOS

Window {
    id: janela
    width: 980; height: 680
    minimumWidth: 760; minimumHeight: 480
    visible: true
    color: Tema.fundo
    title: "Configurações"

    // Menus na Barra de Recursos (ADR 059): Configurações e Exibir (todas as seções)
    readonly property var menusDoApp: {
        var it = function (id, rotulo, marcado) { return { id: id, rotulo: rotulo, tipo: marcado === undefined ? "item" : "marcavel",
                                                          ativo: true, marcado: marcado === true, atalho: "", itens: [] } }
        var sep = { id: -1, rotulo: "", tipo: "separador", ativo: false, marcado: false, atalho: "", itens: [] }
        var exibir = []
        for (var i = 0; i < secoes.length; i++) {
            if (i > 0 && secoes[i].grupo !== secoes[i - 1].grupo) exibir.push(sep)
            exibir.push(it("secao:" + secoes[i].id, secoes[i].nome, ajustes.secao === secoes[i].id))
        }
        return [{ rotulo: "Configurações", itens: [it("secao:sobre", "Sobre este computador"), it("secao:atualizacoes", "Atualizações…"), sep,
                                                    it("fechar", "Fechar")] },
                { rotulo: "Exibir", itens: exibir }]
    }
    onMenusDoAppChanged: menuDoApp.definirMenus(menusDoApp)
    Connections {
        target: menuDoApp
        function onAcionado(id) {
            if (id.indexOf("secao:") === 0) ajustes.irPara(id.slice(6))
            else if (id === "fechar") Qt.quit()
        }
    }

    readonly property var secoes: [
        { id: "rede", nome: "Rede e Internet", icone: "globo", cor: "azul", grupo: 0 },
        { id: "bluetooth", nome: "Bluetooth", icone: "bluetooth", cor: "azul", grupo: 0 },
        { id: "notificacoes", nome: "Notificações", icone: "sino", cor: "noite", grupo: 0 },
        { id: "som", nome: "Som", icone: "som-2", cor: "noite", grupo: 1 },
        { id: "tela", nome: "Tela", icone: "brilho", cor: "azul", grupo: 1 },
        { id: "energia", nome: "Bateria e energia", icone: "bateria", cor: "noite", grupo: 1 },
        { id: "aparencia", nome: "Aparência e estilos", icone: "paleta", cor: "noite", grupo: 2 },
        { id: "papel", nome: "Papel de parede", icone: "imagem", cor: "azul", grupo: 2 },
        { id: "descanso", nome: "Tela de Descanso", icone: "monitor", cor: "noite", grupo: 2 },
        { id: "barra", nome: "Barra e Ilha", icone: "barra", cor: "noite", grupo: 2 },
        { id: "usuario", nome: "Usuário e senha", icone: "usuario", cor: "azul", grupo: 3 },
        { id: "data", nome: "Data e hora", icone: "relogio", cor: "noite", grupo: 3 },
        { id: "teclado", nome: "Idioma e teclado", icone: "teclado", cor: "azul", grupo: 3 },
        { id: "padroes", nome: "Aplicativos padrão", icone: "aplicativos", cor: "noite", grupo: 3 },
        { id: "armazenamento", nome: "Armazenamento", icone: "disco", cor: "noite", grupo: 4 },
        { id: "atualizacoes", nome: "Atualizações", icone: "reiniciar", cor: "azul", grupo: 4 },
        { id: "privacidade", nome: "Privacidade", icone: "escudo", cor: "azul", grupo: 4 },
        { id: "ia", nome: "Inteligência Artificial", icone: "ia", cor: "noite", grupo: 5 },
        { id: "wise", nome: "Wise", icone: "wise", cor: "azul", grupo: 5 },
        { id: "sobre", nome: "Sobre este computador", icone: "info", cor: "cinza", grupo: 6 }
    ]
    function nomeDaSecao(id) { for (var i = 0; i < secoes.length; i++) if (secoes[i].id === id) return secoes[i].nome; return "" }
    property string filtro: ""

    // =============================================================== lateral
    Rectangle {
        id: lateral
        width: 248
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        color: Tema.lateral
        Rectangle { anchors { right: parent.right; top: parent.top; bottom: parent.bottom } width: 1; color: Tema.borda }

        Campo {
            id: busca
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            icone: "busca"; dica: "Buscar"
            entrada.onTextChanged: janela.filtro = texto.toLowerCase()
        }
        // A pessoa
        Rectangle {
            id: cartaoPessoa
            anchors { left: parent.left; right: parent.right; top: busca.bottom; margins: 10; topMargin: 10 }
            height: 58; radius: 10
            color: ajustes.secao === "usuario" ? Tema.selecao : (areaPessoa.containsMouse ? Tema.realce : "transparent")
            Rectangle {
                id: avatar
                width: 40; height: 40; radius: 20
                anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                gradient: Gradient { GradientStop { position: 0; color: "#6FA0F7" } GradientStop { position: 1; color: "#1A3A73" } }
                Image { id: fotoLateral; anchors.fill: parent; source: ajustes.fotoConta; sourceSize: Qt.size(80, 80); visible: status === Image.Ready; cache: false }
                Text { visible: !fotoLateral.visible; anchors.centerIn: parent; text: ajustes.usuario.nome.charAt(0).toUpperCase(); color: "white"; font { family: Tema.fonteTitulo; pixelSize: 18; weight: Font.Bold } }
            }
            Column {
                anchors { left: avatar.right; leftMargin: 10; right: parent.right; verticalCenter: parent.verticalCenter }
                Text { text: ajustes.usuario.nome; color: Tema.texto; elide: Text.ElideRight; width: parent.width; font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.DemiBold } }
                Text { text: "Conta neste computador"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
            }
            MouseArea { id: areaPessoa; anchors.fill: parent; hoverEnabled: true; onClicked: ajustes.irPara("usuario") }
        }

        ListView {
            id: listaSecoes
            anchors { left: parent.left; right: parent.right; top: cartaoPessoa.bottom; bottom: parent.bottom; margins: 10 }
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: janela.secoes.filter(function (s) { return janela.filtro === "" || s.nome.toLowerCase().indexOf(janela.filtro) >= 0 })
            delegate: Item {
                required property var modelData
                required property int index
                width: listaSecoes.width
                height: 34 + (espaco ? 12 : 0)
                readonly property bool espaco: index > 0 && listaSecoes.model[index - 1].grupo !== modelData.grupo
                Rectangle {
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                    height: 34; radius: 8
                    color: ajustes.secao === modelData.id ? Tema.azulDuia : (areaSecao.containsMouse ? Tema.realce : "transparent")
                    Aurora { anchors.fill: parent; radius: parent.radius; visible: Tema.futurista && ajustes.secao === modelData.id }
                    Ladrilho { id: ladrilho; anchors { left: parent.left; leftMargin: 6; verticalCenter: parent.verticalCenter }
                               tamanho: 24; radius: 6; icone: modelData.icone; estilo: modelData.cor }
                    Text {
                        anchors { left: ladrilho.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: modelData.nome
                        color: ajustes.secao === modelData.id ? "white" : Tema.texto
                        font { family: Tema.fonteTexto; pixelSize: 13; weight: ajustes.secao === modelData.id ? Font.DemiBold : Font.Normal }
                    }
                    MouseArea { id: areaSecao; anchors.fill: parent; hoverEnabled: true; onClicked: ajustes.irPara(modelData.id) }
                }
            }
        }
    }

    // ========================================================= componentes
    component Grupo: Rectangle {
        default property alias linhas: colunaGrupo.data
        property string titulo: ""
        width: parent ? parent.width : 500
        height: colunaGrupo.implicitHeight + (titulo !== "" ? 26 : 0)
        color: "transparent"
        Text { visible: parent.titulo !== ""; text: parent.titulo; x: 4; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } }
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: colunaGrupo.implicitHeight
            radius: Tema.raio
            color: Tema.cartao
            border { color: Tema.borda; width: 1 }
            Column { id: colunaGrupo; width: parent.width }
        }
    }
    component Linha: Item {
        id: linha
        property string titulo: ""
        property string descricao: ""
        property string icone: ""
        property bool ultima: false
        property bool clicavel: false
        default property alias controle: lado.data
        signal clicada()
        width: parent ? parent.width : 500
        height: Math.max(46, textos.implicitHeight + 20)
        Rectangle { anchors.fill: parent; anchors.margins: 1; radius: 11; color: linha.clicavel && areaLinha.containsMouse ? Tema.realce : "transparent" }
        Icone { id: iconeLinha; visible: linha.icone !== ""; anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter } nome: linha.icone; tamanho: 18; cor: Tema.textoSecundario }
        Column {
            id: textos
            anchors { left: linha.icone !== "" ? iconeLinha.right : parent.left; leftMargin: 14; right: lado.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
            Text { width: parent.width; text: linha.titulo; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
            Text { width: parent.width; visible: linha.descricao !== ""; text: linha.descricao; wrapMode: Text.WordWrap; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
        }
        MouseArea { id: areaLinha; anchors.fill: parent; enabled: linha.clicavel; hoverEnabled: true; onClicked: linha.clicada() }
        Row { id: lado; anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter } spacing: 8 }
        Rectangle { visible: !linha.ultima; anchors { left: textos.left; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda }
    }
    // Lista de opções que abre por cima da página (com busca quando são muitas)
    component Seletor: Rectangle {
        id: seletor
        property var opcoes: []            // [{valor, rotulo}]
        property string valor: ""
        property string vazio: "Escolher"
        signal escolhido(string valor)
        width: 230; height: 30; radius: Tema.futurista ? 15 : 8
        color: areaSeletor.containsMouse ? Tema.realce : Tema.cartao
        border { color: Tema.bordaForte; width: 1 }
        readonly property string rotulo: {
            for (var i = 0; i < opcoes.length; i++) if (opcoes[i].valor === valor) return opcoes[i].rotulo
            return vazio
        }
        Text { anchors { left: parent.left; leftMargin: 10; right: setaSeletor.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
               text: seletor.rotulo; elide: Text.ElideRight; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
        Icone { id: setaSeletor; anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter } nome: "seta-baixo"; tamanho: 13; cor: Tema.textoSecundario }
        MouseArea {
            id: areaSeletor; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: { var p = seletor.mapToItem(null, 0, seletor.height + 4); escolha.abrir(seletor.opcoes, seletor.valor, function (v) { seletor.escolhido(v) }, p.x, p.y, seletor.width) }
        }
    }
    component Pagina: Flickable {
        default property alias corpo: colunaPagina.data
        contentHeight: colunaPagina.implicitHeight + 40
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: colunaPagina
            x: 28; y: 8
            width: parent.width - 56
            spacing: 18
        }
    }
    component Destaque: Row {
        property string icone: ""
        property string estilo: "azul"
        property string titulo: ""
        property string texto: ""
        spacing: 14
        width: parent ? parent.width : 400
        Ladrilho { tamanho: 52; icone: parent.icone; estilo: parent.estilo }
        Column {
            width: parent.width - 66
            anchors.verticalCenter: parent.verticalCenter
            Titulo { nivel: 2; text: parent.parent.titulo }
            Rotulo { width: parent.width; secundario: true; text: parent.parent.texto }
        }
    }

    // ================================================================ página
    Item {
        id: conteudo
        anchors { left: lateral.right; right: parent.right; top: parent.top; bottom: parent.bottom }
        Rectangle { anchors.fill: parent; color: Tema.fundo }
        Titulo {
            id: tituloPagina
            anchors { left: parent.left; top: parent.top; leftMargin: 28; topMargin: 18 }
            text: janela.nomeDaSecao(ajustes.secao)
        }
        Loader {
            anchors { left: parent.left; right: parent.right; top: tituloPagina.bottom; bottom: parent.bottom; topMargin: 10 }
            sourceComponent: ({ rede: paginaRede, bluetooth: paginaBluetooth, notificacoes: paginaNotificacoes, som: paginaSom,
                                tela: paginaTela, energia: paginaEnergia, aparencia: paginaAparencia, papel: paginaPapel,
                                descanso: paginaDescanso, barra: paginaBarra, usuario: paginaUsuario, data: paginaData,
                                teclado: paginaTeclado, padroes: paginaPadroes, armazenamento: paginaArmazenamento, atualizacoes: paginaAtualizacoes,
                                privacidade: paginaPrivacidade, ia: paginaIa, wise: paginaWise, sobre: paginaSobre })[ajustes.secao]
        }
    }

    // --------------------------------------------------------- Rede e Internet (ADR 069)
    // Visão geral (conexões, Wi-Fi, perfis salvos) e, ao clicar em Detalhes, a conexão em abas:
    // Geral, Endereço, DNS, Informações e Privacidade. Mudanças de endereço pedem "Manter?" (rede_interface.py).
    component CampoRede: Column {
        property string rotulo: ""
        property alias texto: campoInterno.texto
        property alias dica: campoInterno.dica
        property bool senha: false
        width: 260
        spacing: 4
        Text { text: parent.rotulo; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
        Campo { id: campoInterno; width: parent.width; senha: parent.senha }
    }
    Component {
        id: paginaRede
        Pagina {
            id: pr
            readonly property string aberta: rede.conexaoAberta     // UUID da conexão com os Detalhes abertos
            property string aba: abaInicialRede || "geral"
            property bool oculta: false               // formulário "Conectar a uma rede oculta"
            property bool novoPerfil: false           // formulário "Novo perfil de cabo"
            property string empresa: ""               // SSID do Wi-Fi corporativo (802.1X) sendo conectado
            property bool novaVpn: false              // formulário "Adicionar VPN"
            property bool compartilhando: false       // formulário "Compartilhar a internet"
            property string qr: ""                    // imagem do QR code da Wi-Fi aberta
            property string formCelular: ""           // "bluetooth" ou "modem"
            property bool avancada: false             // formulário de VLAN, ponte e agregação
            property bool senhaVisivel: false
            property string senhaWifi: ""
            Component.onCompleted: { rede.atualizar(); rede.lerFirewall(); controles.buscarRedes(true) }
            function nomeDoTipo(t) { return ({ cabo: "Cabo de rede", wifi: "Wi-Fi", celular: "Rede celular", bluetooth: "Celular pelo Bluetooth",
                                              vpn: "VPN", ponte: "Ponte", agregacao: "Agregação de placas", vlan: "VLAN" })[t] || t }
            function iconeDoTipo(t) { return ({ cabo: "rede", wifi: "wifi-3", celular: "celular", bluetooth: "bluetooth", vpn: "vpn" })[t] || "rede" }
            function modemDe(d) { return rede.modens.length ? rede.modens[0] : null }
            function textoDoEstado(d) {
                var ip = rede.detalhesDe(d.dispositivo).ipv4 || []
                var e = ({ conectado: "Conectado", conectando: "Conectando…", desconectado: "Desconectado",
                           indisponivel: d.tipo === "cabo" ? "Cabo desconectado" : "Indisponível", desconectando: "Desconectando…" })[d.estado] || d.estado
                return e + (d.estado === "conectado" && d.conexao ? " · " + d.conexao : "") + (ip.length ? " · " + ip[0].split("/")[0] : "")
            }
            function abrir(uuid) { pr.aba = "geral"; pr.senhaVisivel = false; pr.senhaWifi = ""; pr.qr = ""; rede.abrirConexao(uuid) }
            function fechar() { rede.abrirConexao("") }
            Connections { target: rede; function onSenhaLida(uuid, senha) { if (uuid === pr.aberta) { pr.senhaWifi = senha; pr.senhaVisivel = true } }
                                        function onQrPronto(uuid, caminho) { if (uuid === pr.aberta) pr.qr = "file://" + caminho + "?" + Date.now() } }

            // ================================================== visão geral
            Destaque {
                visible: pr.aberta === ""
                icone: rede.icone === "" ? "wifi-3" : (rede.icone || "rede"); estilo: rede.conectividade === "full" ? "azul" : "cinza"
                titulo: rede.resumo
                texto: rede.conectividade === "portal" ? "Abra o navegador para fazer o login desta rede." :
                       (rede.vpnAtiva !== "" ? "O tráfego passa pela VPN " + rede.vpnAtiva + "." : "Cabo, Wi-Fi e as conexões salvas deste computador.")
            }
            Botao {
                visible: pr.aberta === "" && rede.conectividade === "portal"
                texto: "Fazer login na rede"; tipo: "primario"; icone: "globo"
                onClicado: Qt.openUrlExternally("http://connectivity-check.debian.net/")
            }
            // Firewall (ADR 071): toda rede começa pública; a pessoa diz se é de casa/trabalho
            Grupo {
                visible: pr.aberta === "" && rede.firewall.ligado && rede.semTipo.length > 0
                titulo: "Esta rede é de confiança?"
                Repeater {
                    model: rede.semTipo
                    Linha {
                        required property var modelData
                        required property int index
                        icone: "escudo"; titulo: modelData.nome
                        descricao: "Privada: casa ou trabalho (o computador aparece para os outros aparelhos). Pública: café, aeroporto, hotel (nada entra)."
                        ultima: index === rede.semTipo.length - 1
                        Botao { texto: "Privada"; tipo: "primario"; onClicado: rede.definirTipoDeRede(modelData.uuid, "privada") }
                        Botao { texto: "Pública"; onClicado: rede.definirTipoDeRede(modelData.uuid, "publica") }
                    }
                }
            }
            Grupo {
                visible: pr.aberta === ""
                titulo: "Conexões"
                Linha { visible: !rede.temPlaca; titulo: "Nenhuma placa de rede encontrada"; descricao: "Confira se a placa está ligada (ou, numa máquina virtual, se ela tem uma placa de rede)."; ultima: true }
                Repeater {
                    model: rede.dispositivos.filter(function (d) { return d.tipo !== "vpn" })
                    Linha {
                        required property var modelData
                        required property int index
                        readonly property bool varios: rede.dispositivos.filter(function (d) { return d.tipo === modelData.tipo }).length > 1
                        icone: modelData.celularUsb ? "celular" : pr.iconeDoTipo(modelData.tipo)
                        titulo: modelData.celularUsb ? "Celular pelo cabo USB (" + modelData.celularUsb + ")"
                                                     : pr.nomeDoTipo(modelData.tipo) + (varios ? " (" + modelData.dispositivo + ")" : "")
                        descricao: modelData.tipo === "wifi" && !controles.wifiLigado ? "Desligado"
                                   : pr.textoDoEstado(modelData) + (modelData.tipo === "celular" && pr.modemDe(modelData)
                                        ? " · " + [pr.modemDe(modelData).operadora, pr.modemDe(modelData).tecnologia, pr.modemDe(modelData).sinal + "% de sinal"].filter(function (x) { return x }).join(" · ")
                                        : "")
                        ultima: index === rede.dispositivos.filter(function (d) { return d.tipo !== "vpn" }).length - 1
                        Botao { visible: modelData.uuid !== "" && modelData.estado === "conectado"; texto: "Detalhes"; onClicado: pr.abrir(modelData.uuid) }
                        Interruptor {
                            visible: modelData.tipo === "wifi"
                            ligado: controles.wifiLigado; onAlternado: (v) => controles.ligarWifi(v)
                        }
                        Interruptor {
                            visible: modelData.tipo !== "wifi"
                            ativo: modelData.estado !== "indisponivel"
                            ligado: modelData.estado === "conectado" || modelData.estado === "conectando"
                            onAlternado: (v) => v ? rede.conectarDispositivo(modelData.dispositivo) : rede.desconectarDispositivo(modelData.dispositivo)
                        }
                    }
                }
            }

            // Wi-Fi: redes por perto (como antes) + rede oculta
            Grupo {
                visible: pr.aberta === "" && rede.temWifi && controles.wifiLigado
                titulo: controles.buscandoRedes ? "Procurando redes Wi-Fi…" : "Redes Wi-Fi por perto"
                Linha { visible: controles.redes.length === 0 && !controles.buscandoRedes; titulo: "Nenhuma rede encontrada"; ultima: true }
                Repeater {
                    model: controles.redes
                    Column {
                        required property var modelData
                        required property int index
                        width: parent.width
                        property bool pedindoSenha: false
                        Linha {
                            icone: "wifi-" + (modelData.sinal >= 67 ? 3 : (modelData.sinal >= 34 ? 2 : 1))
                            titulo: modelData.ssid
                            descricao: modelData.conectada ? "Conectada" : (controles.redeSalva(modelData.ssid) ? "Salva" : (modelData.segura ? "Protegida por senha" : "Aberta"))
                            ultima: index === controles.redes.length - 1 && !parent.pedindoSenha
                            Icone { visible: modelData.segura; nome: "cadeado"; tamanho: 14; cor: Tema.textoApagado; anchors.verticalCenter: parent.verticalCenter }
                            Botao {
                                visible: !modelData.conectada
                                texto: "Conectar"
                                onClicado: {
                                    if (!modelData.segura || controles.redeSalva(modelData.ssid)) controles.conectarWifi(modelData.ssid, "")
                                    else if (modelData.empresa) pr.empresa = modelData.ssid
                                    else parent.parent.parent.pedindoSenha = true
                                }
                            }
                            Botao { visible: modelData.conectada; texto: "Desconectar"; onClicado: controles.desconectarWifi(modelData.ssid) }
                        }
                        Row {
                            visible: parent.pedindoSenha
                            spacing: 8; leftPadding: 46; bottomPadding: 10
                            Campo { id: senhaPerto; width: 240; senha: true; dica: "Senha da rede"
                                    onConfirmado: { controles.conectarWifi(modelData.ssid, texto); parent.parent.pedindoSenha = false } }
                            Botao { texto: "Conectar"; tipo: "primario"; onClicado: { controles.conectarWifi(modelData.ssid, senhaPerto.texto); parent.parent.pedindoSenha = false } }
                            Botao { texto: "Cancelar"; onClicado: parent.parent.pedindoSenha = false }
                        }
                    }
                }
            }
            Row {
                visible: pr.aberta === "" && rede.temWifi && controles.wifiLigado
                spacing: 8
                Botao { texto: "Procurar de novo"; icone: "reiniciar"; onClicado: controles.buscarRedes(true) }
                Botao { texto: "Conectar a uma rede oculta…"; onClicado: pr.oculta = !pr.oculta }
            }
            Grupo {
                visible: pr.aberta === "" && pr.oculta
                titulo: "Rede oculta (que não anuncia o nome)"
                Column {
                    width: parent.width; padding: 14; spacing: 10
                    Row {
                        spacing: 12
                        CampoRede { id: ssidOculta; rotulo: "Nome da rede"; dica: "Ex.: Escritório" }
                        CampoRede { id: senhaOculta; rotulo: "Senha (vazia se for aberta)"; senha: true }
                    }
                    Row {
                        spacing: 8
                        Botao { texto: "Conectar"; tipo: "primario"; ativo: ssidOculta.texto !== ""
                                onClicado: { rede.conectarOculta(ssidOculta.texto, senhaOculta.texto); pr.oculta = false } }
                        Botao { texto: "Cancelar"; onClicado: pr.oculta = false }
                    }
                }
            }

            // Wi-Fi corporativo ou de faculdade (WPA2/WPA3-Enterprise, 802.1X; ex.: eduroam) — ADR 070
            Grupo {
                visible: pr.aberta === "" && pr.empresa !== ""
                titulo: "Entrar na rede " + pr.empresa
                Column {
                    width: parent.width; padding: 14; spacing: 10
                    Rotulo { width: parent.width - 28; secundario: true
                             text: "Esta rede pede usuário e senha (rede de empresa ou faculdade). Os dados vêm do setor de TI; na dúvida, deixe as opções avançadas como estão." }
                    Column {
                        spacing: 4
                        Text { text: "Método"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        Segmentos { id: metodoEap; valor: "peap"; onEscolhido: (v) => valor = v
                                    opcoes: Object.keys(rede.metodosEap).map(function (k) { return { valor: k, rotulo: rede.metodosEap[k] } }) }
                    }
                    Row {
                        spacing: 12
                        CampoRede { id: usuarioEap; rotulo: metodoEap.valor === "tls" ? "Identidade" : "Usuário"; dica: "nome@empresa.com.br"; width: 230 }
                        CampoRede { id: senhaEap; visible: metodoEap.valor !== "tls"; rotulo: "Senha"; senha: true; width: 200 }
                    }
                    Row {
                        visible: metodoEap.valor === "tls"
                        spacing: 8
                        Botao { texto: certificadoEap.arquivo ? "Certificado: " + certificadoEap.arquivo.split("/").pop() : "Escolher certificado…"
                                onClicado: { certificadoEap.alvo = "certificado"; certificadoEap.open() } }
                        Botao { texto: certificadoEap.chave ? "Chave: " + certificadoEap.chave.split("/").pop() : "Escolher chave…"
                                onClicado: { certificadoEap.alvo = "chave"; certificadoEap.open() } }
                        CampoRede { id: senhaChaveEap; rotulo: "Senha da chave"; senha: true; width: 160 }
                    }
                    Row {
                        spacing: 8
                        Interruptor { id: avancadoEap; ligado: false; onAlternado: (v) => ligado = v }
                        Rotulo { anchors.verticalCenter: parent.verticalCenter; secundario: true; text: "Opções avançadas (certificado do servidor, identidade anônima)" }
                    }
                    Column {
                        visible: avancadoEap.ligado
                        spacing: 10
                        Row {
                            spacing: 12
                            CampoRede { id: anonimaEap; rotulo: "Identidade anônima"; dica: "anonymous@empresa.com.br"; width: 230 }
                            CampoRede { id: dominioEap; rotulo: "Domínio do servidor"; dica: "radius.empresa.com.br"; width: 230 }
                        }
                        Row {
                            spacing: 8
                            Botao { texto: certificadoEap.ca ? "Certificado da rede: " + certificadoEap.ca.split("/").pop() : "Certificado da rede (CA)…"
                                    onClicado: { certificadoEap.alvo = "ca"; certificadoEap.open() } }
                            Interruptor { id: semVerificarEap; ligado: false; onAlternado: (v) => ligado = v }
                            Rotulo { anchors.verticalCenter: parent.verticalCenter; secundario: true; text: "Não verificar o servidor (menos seguro)" }
                        }
                    }
                    Row {
                        spacing: 8
                        Botao {
                            texto: "Conectar"; tipo: "primario"; ativo: usuarioEap.texto !== ""
                            onClicado: {
                                rede.conectarEmpresa({ ssid: pr.empresa, metodo: metodoEap.valor, usuario: usuarioEap.texto, senha: senhaEap.texto,
                                                       anonima: anonimaEap.texto, dominio: dominioEap.texto, ca: certificadoEap.ca,
                                                       certificado: certificadoEap.arquivo, chave: certificadoEap.chave, senhaChave: senhaChaveEap.texto,
                                                       semVerificar: semVerificarEap.ligado })
                                pr.empresa = ""; senhaEap.texto = ""
                            }
                        }
                        Botao { texto: "Cancelar"; onClicado: pr.empresa = "" }
                    }
                    FileDialog {
                        id: certificadoEap
                        property string alvo: "ca"
                        property string ca: ""
                        property string arquivo: ""
                        property string chave: ""
                        title: alvo === "chave" ? "Escolher a chave particular" : "Escolher certificado"
                        nameFilters: ["Certificados e chaves (*.pem *.crt *.cer *.der *.p12 *.pfx *.key)", "Todos os arquivos (*)"]
                        onAccepted: { var f = selectedFile.toString(); if (alvo === "ca") ca = f; else if (alvo === "chave") chave = f; else arquivo = f }
                    }
                }
            }

            // Perfis salvos (Wi-Fi e cabo), com Detalhes e Esquecer; perfil novo para o cabo (ex.: IP fixo)
            Grupo {
                visible: pr.aberta === "" && rede.conexoes.filter(function (c) { return c.tipo === "cabo" || c.tipo === "wifi" }).length > 0
                titulo: "Conexões salvas"
                Repeater {
                    model: rede.conexoes.filter(function (c) { return c.tipo === "cabo" || c.tipo === "wifi" })
                    Linha {
                        required property var modelData
                        required property int index
                        icone: pr.iconeDoTipo(modelData.tipo)
                        titulo: modelData.nome
                        descricao: (modelData.ativa ? "Em uso" : (modelData.automatico ? "Conecta sozinha quando disponível" : "Só quando você escolher"))
                                   + " · " + pr.nomeDoTipo(modelData.tipo)
                        ultima: index === rede.conexoes.filter(function (c) { return c.tipo === "cabo" || c.tipo === "wifi" }).length - 1
                        Botao { visible: !modelData.ativa && modelData.tipo === "cabo"; texto: "Usar"; onClicado: rede.ativar(modelData.uuid) }
                        Botao { texto: "Detalhes"; onClicado: pr.abrir(modelData.uuid) }
                    }
                }
            }
            Botao { visible: pr.aberta === "" && rede.temCabo; texto: "Novo perfil para o cabo…"; icone: "mais"; onClicado: pr.novoPerfil = !pr.novoPerfil }
            Grupo {
                visible: pr.aberta === "" && pr.novoPerfil
                titulo: "Novo perfil para o cabo de rede"
                Column {
                    width: parent.width; padding: 14; spacing: 10
                    Rotulo { width: parent.width - 28; secundario: true
                             text: "Use para redes que pedem endereço fixo (escritório, máquina virtual sem DHCP). Você troca de perfil em Conexões salvas › Usar." }
                    Row {
                        spacing: 12
                        CampoRede { id: nomePerfil; rotulo: "Nome"; dica: "Ex.: Escritório"; width: 200 }
                        Column {
                            spacing: 4
                            Text { text: "Endereço"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Segmentos { id: metodoPerfil; valor: "manual"; opcoes: [{ valor: "auto", rotulo: "Automático (DHCP)" }, { valor: "manual", rotulo: "Fixo" }]
                                        onEscolhido: (v) => valor = v }
                        }
                    }
                    Row {
                        visible: metodoPerfil.valor === "manual"
                        spacing: 12
                        CampoRede { id: ipPerfil; rotulo: "Endereço IP"; dica: "192.168.0.10"; width: 160 }
                        CampoRede { id: mascaraPerfil; rotulo: "Máscara"; texto: "255.255.255.0"; width: 140 }
                        CampoRede { id: gatewayPerfil; rotulo: "Gateway (roteador)"; dica: "192.168.0.1"; width: 160 }
                        CampoRede { id: dnsPerfil; rotulo: "DNS"; dica: "1.1.1.1, 8.8.8.8"; width: 160 }
                    }
                    Row {
                        spacing: 8
                        Botao {
                            texto: "Criar e usar"; tipo: "primario"; ativo: nomePerfil.texto !== ""
                            onClicado: {
                                var cabo = rede.dispositivos.filter(function (d) { return d.tipo === "cabo" })[0]
                                var cfg = metodoPerfil.valor === "manual"
                                    ? { ipv4: { metodo: "manual", enderecos: [{ endereco: ipPerfil.texto, prefixo: mascaraPerfil.texto }], gateway: gatewayPerfil.texto,
                                                dns: dnsPerfil.texto.split(/[,\s]+/).filter(function (x) { return x !== "" }) } }
                                    : { ipv4: { metodo: "auto", dns: [] } }
                                var erros = rede.validar(cfg)
                                if (erros.length) { aviso.mostrar(erros[0]); return }
                                rede.novaConexaoCabo(cabo ? cabo.dispositivo : "", nomePerfil.texto, cfg)
                                pr.novoPerfil = false
                            }
                        }
                        Botao { texto: "Cancelar"; onClicado: pr.novoPerfil = false }
                    }
                }
            }

            // ============================================ VPN (ADR 070)
            Grupo {
                visible: pr.aberta === ""
                titulo: "VPN"
                Linha { visible: rede.conexoes.filter(function (c) { return c.tipo === "vpn" }).length === 0
                        icone: "vpn"; titulo: "Nenhuma VPN"; descricao: "Importe o arquivo que a empresa ou o serviço de VPN mandou (.conf, .ovpn) ou adicione à mão."; ultima: true }
                Repeater {
                    model: rede.conexoes.filter(function (c) { return c.tipo === "vpn" })
                    Linha {
                        required property var modelData
                        required property int index
                        icone: "vpn"; titulo: modelData.nome
                        descricao: modelData.ativa ? "Conectada — o tráfego passa por ela" : "Desligada"
                        ultima: index === rede.conexoes.filter(function (c) { return c.tipo === "vpn" }).length - 1
                        Botao { texto: "Detalhes"; onClicado: pr.abrir(modelData.uuid) }
                        Interruptor { ligado: modelData.ativa; onAlternado: (v) => v ? rede.ativar(modelData.uuid) : rede.desativar(modelData.uuid) }
                    }
                }
            }
            Row {
                visible: pr.aberta === ""
                spacing: 8
                Botao { texto: "Importar arquivo de VPN…"; icone: "pasta"; onClicado: escolherVpn.open() }
                Botao { texto: "Adicionar VPN…"; icone: "mais"; onClicado: pr.novaVpn = !pr.novaVpn }
            }
            FileDialog {
                id: escolherVpn
                title: "Importar arquivo de VPN"
                nameFilters: ["Arquivos de VPN (*.conf *.ovpn)"]
                onAccepted: rede.importarVpn(selectedFile.toString())
            }
            Grupo {
                visible: pr.aberta === "" && pr.novaVpn
                titulo: "Adicionar VPN"
                Column {
                    id: fv
                    width: parent.width; padding: 14; spacing: 10
                    property string publica: ""
                    Segmentos { id: tipoVpn; valor: "wireguard"; onEscolhido: (v) => valor = v
                                opcoes: [{ valor: "wireguard", rotulo: "WireGuard" }, { valor: "openconnect", rotulo: "VPN de empresa (OpenConnect)" }] }
                    Rotulo { width: parent.width - 28; secundario: true
                             text: tipoVpn.valor === "wireguard"
                                   ? "Preencha com os dados do servidor WireGuard. Sem chave? Gere uma aqui e mande a chave pública para quem cuida do servidor."
                                   : "Para VPNs Cisco AnyConnect, GlobalProtect, Fortinet, Pulse e Ivanti. O usuário e a senha são pedidos na hora de conectar. Login pelo navegador (SSO) ainda não é aceito." }
                    CampoRede { id: nomeVpn; rotulo: "Nome"; dica: tipoVpn.valor === "wireguard" ? "Ex.: Casa" : "Ex.: Empresa"; width: 220 }
                    // WireGuard
                    Column {
                        visible: tipoVpn.valor === "wireguard"
                        spacing: 10
                        Row {
                            spacing: 12
                            CampoRede { id: wgEndereco; rotulo: "Endereço na VPN"; dica: "10.0.0.2/32"; width: 170 }
                            CampoRede { id: wgServidor; rotulo: "Servidor (endereço:porta)"; dica: "vpn.exemplo.com.br:51820"; width: 240 }
                            CampoRede { id: wgDns; rotulo: "DNS (opcional)"; dica: "10.0.0.1"; width: 150 }
                        }
                        Row {
                            spacing: 12
                            CampoRede { id: wgChaveServidor; rotulo: "Chave pública do servidor"; width: 330 }
                            CampoRede { id: wgPermitidos; rotulo: "Redes pela VPN"; dica: "Tudo (0.0.0.0/0, ::/0)"; width: 230 }
                        }
                        Row {
                            spacing: 12
                            CampoRede { id: wgPrivada; rotulo: "Sua chave privada"; senha: true; width: 330 }
                            Botao { anchors.bottom: parent.bottom; texto: "Gerar chaves"; icone: "cadeado"
                                    onClicado: { var k = rede.gerarChavesWireguard(); if (k.privada) { wgPrivada.texto = k.privada; fv.publica = k.publica } } }
                        }
                        Linha { visible: fv.publica !== ""; titulo: "Sua chave pública (mande para o servidor)"; descricao: fv.publica; ultima: true
                                Botao { texto: "Copiar"; onClicado: { area.text = fv.publica; area.selectAll(); area.copy(); aviso.mostrar("Chave copiada.") } } }
                        TextEdit { id: area; visible: false }
                    }
                    // OpenConnect
                    Row {
                        visible: tipoVpn.valor === "openconnect"
                        spacing: 12
                        CampoRede { id: ocServidor; rotulo: "Servidor"; dica: "vpn.empresa.com.br"; width: 240 }
                        Column {
                            spacing: 4
                            Text { text: "Tipo"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Seletor { id: ocProtocolo; width: 230; valor: "anyconnect"; onEscolhido: (v) => valor = v
                                      opcoes: Object.keys(rede.protocolosOpenconnect).map(function (k) { return { valor: k, rotulo: rede.protocolosOpenconnect[k] } }) }
                        }
                    }
                    Row {
                        spacing: 8
                        Botao {
                            texto: "Adicionar"; tipo: "primario"
                            ativo: nomeVpn.texto !== "" && (tipoVpn.valor === "wireguard" ? (wgEndereco.texto !== "" && wgServidor.texto !== "" && wgChaveServidor.texto !== "" && wgPrivada.texto !== "") : ocServidor.texto !== "")
                            onClicado: {
                                if (tipoVpn.valor === "wireguard")
                                    rede.novaWireguard({ nome: nomeVpn.texto, endereco: wgEndereco.texto, servidor: wgServidor.texto, dns: wgDns.texto,
                                                         chaveServidor: wgChaveServidor.texto, permitidos: wgPermitidos.texto, privada: wgPrivada.texto })
                                else
                                    rede.novaOpenConnect(nomeVpn.texto, ocServidor.texto, ocProtocolo.valor)
                                pr.novaVpn = false; wgPrivada.texto = ""; fv.publica = ""
                            }
                        }
                        Botao { texto: "Cancelar"; onClicado: pr.novaVpn = false }
                    }
                }
            }

            // ============================== Compartilhar a internet (ponto de acesso)
            Grupo {
                visible: pr.aberta === "" && rede.temWifi
                titulo: "Compartilhar a internet"
                Linha {
                    icone: "ponto-de-acesso"; titulo: "Ponto de acesso Wi-Fi"
                    descricao: rede.pontoDeAcesso ? "Ligado — outros aparelhos podem entrar na rede do computador"
                                                  : "Transforma a Wi-Fi do computador numa rede para o celular e outros aparelhos (use com a internet pelo cabo)"
                    ultima: !pr.compartilhando || rede.pontoDeAcesso
                    Interruptor { ligado: rede.pontoDeAcesso || pr.compartilhando
                                  onAlternado: (v) => { if (!v) { pr.compartilhando = false; if (rede.pontoDeAcesso) rede.desligarPontoDeAcesso() } else pr.compartilhando = true } }
                }
                Column {
                    visible: pr.compartilhando && !rede.pontoDeAcesso
                    width: parent.width; padding: 14; spacing: 10
                    Row {
                        spacing: 12
                        CampoRede { id: nomePonto; rotulo: "Nome da rede"; texto: "DuiaOS"; width: 200 }
                        CampoRede { id: senhaPonto; rotulo: "Senha (8 caracteres ou mais)"; senha: true; width: 200 }
                    }
                    Row {
                        spacing: 8
                        Botao { texto: "Ligar"; tipo: "primario"; ativo: nomePonto.texto !== "" && senhaPonto.texto.length >= 8
                                onClicado: { rede.ligarPontoDeAcesso(nomePonto.texto, senhaPonto.texto); pr.compartilhando = false } }
                        Botao { texto: "Cancelar"; onClicado: pr.compartilhando = false }
                    }
                }
            }

            // ======================================================== Proxy
            Grupo {
                id: gp
                visible: pr.aberta === ""
                titulo: "Proxy"
                property var p: rede.proxyAtual
                property string modo: p.modo || "desligado"
                Connections { target: rede; function onProxyMudou() { gp.modo = rede.proxyAtual.modo || "desligado" } }
                Linha {
                    titulo: "Usar proxy"; descricao: "Só se a rede da empresa ou da escola exigir"
                    ultima: gp.modo === "desligado"
                    Segmentos { valor: gp.modo; onEscolhido: (v) => gp.modo = v
                                opcoes: [{ valor: "desligado", rotulo: "Não" }, { valor: "manual", rotulo: "Manual" }, { valor: "automatico", rotulo: "Automático" }] }
                }
                Column {
                    visible: gp.modo !== "desligado"
                    width: parent.width; padding: 14; spacing: 10
                    CampoRede { id: pacProxy; visible: gp.modo === "automatico"; rotulo: "Endereço da configuração automática (PAC)"; dica: "http://proxy.empresa.com.br/proxy.pac"
                                width: 420; texto: gp.p.pac || "" }
                    Row {
                        visible: gp.modo === "manual"; spacing: 12
                        CampoRede { id: httpProxy; rotulo: "Proxy HTTP"; dica: "proxy.empresa.com.br"; width: 240; texto: (gp.p.http || {}).servidor || "" }
                        CampoRede { id: httpPorta; rotulo: "Porta"; dica: "3128"; width: 80; texto: (gp.p.http || {}).porta ? String(gp.p.http.porta) : "" }
                    }
                    Row {
                        visible: gp.modo === "manual"; spacing: 12
                        CampoRede { id: httpsProxy; rotulo: "Proxy HTTPS (vazio = o mesmo)"; width: 240; texto: (gp.p.https || {}).servidor || "" }
                        CampoRede { id: httpsPorta; rotulo: "Porta"; width: 80; texto: (gp.p.https || {}).porta ? String(gp.p.https.porta) : "" }
                    }
                    Row {
                        visible: gp.modo === "manual"; spacing: 12
                        CampoRede { id: socksProxy; rotulo: "Proxy SOCKS (opcional)"; width: 240; texto: (gp.p.socks || {}).servidor || "" }
                        CampoRede { id: socksPorta; rotulo: "Porta"; width: 80; texto: (gp.p.socks || {}).porta ? String(gp.p.socks.porta) : "" }
                    }
                    CampoRede { id: excecoesProxy; rotulo: "Sem proxy para (separados por vírgula)"; width: 420; texto: (gp.p.excecoes || []).join(", ") }
                    Botao {
                        texto: "Salvar"; tipo: "primario"
                        onClicado: {
                            var hs = httpsProxy.texto || httpProxy.texto, hp = httpsProxy.texto ? httpsPorta.texto : httpPorta.texto
                            rede.gravarProxy({ modo: gp.modo, pac: pacProxy.texto,
                                               http: { servidor: httpProxy.texto, porta: parseInt(httpPorta.texto) || 0 },
                                               https: { servidor: hs, porta: parseInt(hp) || 0 },
                                               socks: { servidor: socksProxy.texto, porta: parseInt(socksPorta.texto) || 0 },
                                               excecoes: excecoesProxy.texto.split(/[,\s]+/).filter(function (x) { return x !== "" }) })
                        }
                    }
                }
                Botao { visible: gp.modo === "desligado" && (gp.p.modo || "desligado") !== "desligado"; texto: "Desligar o proxy"
                        onClicado: rede.gravarProxy({ modo: "desligado", excecoes: gp.p.excecoes || [] }) }
            }

            // ==================================== Celular (USB, Bluetooth, modem) — ADR 071
            Grupo {
                visible: pr.aberta === ""
                titulo: "Internet do celular"
                Linha {
                    icone: "celular"; titulo: "Pelo cabo USB"
                    descricao: "No celular, ligue Ancoragem USB (Android) ou Acesso Pessoal (iPhone) e ele aparece sozinho em Conexões."
                }
                Linha {
                    icone: "bluetooth"; titulo: "Pelo Bluetooth"
                    descricao: controles.bluetoothPareados.length ? "Ligue Ancoragem Bluetooth no celular e escolha qual é." : "Primeiro pareie o celular em Configurações › Bluetooth."
                    ultima: pr.formCelular !== "bluetooth" && !rede.dispositivos.some(function (d) { return d.tipo === "celular" })
                    Botao { visible: controles.bluetoothPareados.length > 0; texto: "Escolher celular…"; onClicado: pr.formCelular = pr.formCelular === "bluetooth" ? "" : "bluetooth" }
                }
                Repeater {
                    model: pr.formCelular === "bluetooth" ? controles.bluetoothPareados : []
                    Linha {
                        required property var modelData
                        icone: "celular"; titulo: modelData.nome; descricao: modelData.endereco
                        Botao { texto: "Usar a internet"; tipo: "primario"; onClicado: { rede.conectarCelularBluetooth(modelData.endereco, modelData.nome); pr.formCelular = "" } }
                    }
                }
                Linha {
                    visible: rede.dispositivos.some(function (d) { return d.tipo === "celular" })
                    icone: "celular"; titulo: "Modem 4G/5G (chip)"
                    descricao: rede.modens.length && rede.modens[0].bloqueado ? "O chip pede o PIN" : "Configure o APN da operadora para conectar"
                    ultima: pr.formCelular !== "modem"
                    Botao { texto: "Configurar…"; onClicado: pr.formCelular = pr.formCelular === "modem" ? "" : "modem" }
                }
                Column {
                    visible: pr.formCelular === "modem"
                    width: parent.width; padding: 14; spacing: 10
                    Row {
                        spacing: 12
                        Column {
                            spacing: 4
                            Text { text: "Operadora"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Seletor { id: operadora; width: 170; valor: ""; vazio: "Outra"
                                      opcoes: Object.keys(rede.operadoras).map(function (k) { return { valor: k, rotulo: k } })
                                      onEscolhido: (v) => { valor = v; var o = rede.operadoras[v]; apn.texto = o.apn; usuarioApn.texto = o.usuario; senhaApn.texto = o.senha } }
                        }
                        CampoRede { id: apn; rotulo: "APN"; dica: "zap.vivo.com.br"; width: 200 }
                        CampoRede { id: pin; rotulo: "PIN do chip (se tiver)"; senha: true; width: 140 }
                    }
                    Row {
                        spacing: 12
                        CampoRede { id: usuarioApn; rotulo: "Usuário (se a operadora pedir)"; width: 200 }
                        CampoRede { id: senhaApn; rotulo: "Senha"; senha: true; width: 160 }
                    }
                    Row {
                        spacing: 8
                        Botao { texto: "Conectar"; tipo: "primario"; ativo: apn.texto !== ""
                                onClicado: { rede.novaCelular({ nome: operadora.valor || "Rede celular", apn: apn.texto, usuario: usuarioApn.texto,
                                                                senha: senhaApn.texto, pin: pin.texto }); pr.formCelular = ""; pin.texto = "" } }
                        Botao { texto: "Cancelar"; onClicado: pr.formCelular = "" }
                    }
                }
            }

            // ============================================ Firewall — ADR 071
            Grupo {
                visible: pr.aberta === "" && rede.firewall.instalado
                titulo: "Firewall"
                Linha {
                    icone: "escudo"; titulo: "Firewall"
                    descricao: rede.firewall.ligado ? "Ligado — bloqueia conexões vindas de fora; nas redes públicas, nada entra" : "Desligado — qualquer aparelho da rede pode tentar se conectar ao computador"
                    Interruptor { ligado: rede.firewall.ligado; onAlternado: (v) => rede.configurarFirewall(v, rede.firewall.ssh) }
                }
                Linha {
                    visible: rede.firewall.ligado
                    icone: "terminal"; titulo: "Acesso remoto (SSH) nas redes privadas"
                    descricao: "Permite entrar neste computador pelo terminal de outro, na mesma rede de casa ou do trabalho"
                    ultima: true
                    Interruptor { ligado: rede.firewall.ssh; onAlternado: (v) => rede.configurarFirewall(true, v) }
                }
            }

            // ============================================ Diagnóstico — ADR 071
            Grupo {
                visible: pr.aberta === ""
                titulo: "Problemas com a internet?"
                Linha {
                    icone: "info"; titulo: "Diagnosticar a rede"
                    descricao: rede.diagnosticando ? "Conferindo…" : "Confere a conexão passo a passo e diz onde está o problema"
                    ultima: rede.diagnostico.length === 0
                    Botao { texto: rede.diagnostico.length ? "De novo" : "Diagnosticar"; ativo: !rede.diagnosticando; onClicado: rede.diagnosticar() }
                }
                Repeater {
                    model: rede.diagnostico
                    Linha {
                        required property var modelData
                        required property int index
                        icone: modelData.ok ? "check" : "rede-alerta"
                        titulo: modelData.nome + (modelData.ok ? "" : " — aqui está o problema")
                        descricao: modelData.explicacao + (modelData.dica ? " " + modelData.dica : "")
                        ultima: index === rede.diagnostico.length - 1
                    }
                }
            }

            // ================================ Avançado: VLAN, ponte, agregação — ADR 071
            Grupo {
                visible: pr.aberta === "" && rede.conexoes.some(function (c) { return ["ponte", "agregacao", "vlan"].indexOf(c.tipo) >= 0 })
                titulo: "Conexões avançadas"
                Repeater {
                    model: rede.conexoes.filter(function (c) { return ["ponte", "agregacao", "vlan"].indexOf(c.tipo) >= 0 })
                    Linha {
                        required property var modelData
                        required property int index
                        icone: "rede"; titulo: modelData.nome
                        descricao: pr.nomeDoTipo(modelData.tipo) + (modelData.ativa ? " · em uso" : "")
                        ultima: index === rede.conexoes.filter(function (c) { return ["ponte", "agregacao", "vlan"].indexOf(c.tipo) >= 0 }).length - 1
                        Botao { texto: "Detalhes"; onClicado: pr.abrir(modelData.uuid) }
                    }
                }
            }
            Botao { visible: pr.aberta === "" && rede.temCabo; texto: "VLAN, ponte ou agregação…"; icone: "mais"; onClicado: pr.avancada = !pr.avancada }
            Grupo {
                visible: pr.aberta === "" && pr.avancada
                titulo: "Nova conexão avançada"
                Column {
                    width: parent.width; padding: 14; spacing: 10
                    readonly property var placas: rede.dispositivos.filter(function (d) { return d.tipo === "cabo" }).map(function (d) { return d.dispositivo })
                    property var escolhidas: []
                    id: fa
                    Segmentos { id: tipoAvancada; valor: "vlan"; onEscolhido: (v) => valor = v
                                opcoes: [{ valor: "vlan", rotulo: "VLAN" }, { valor: "ponte", rotulo: "Ponte" }, { valor: "agregacao", rotulo: "Agregação" }] }
                    Rotulo { width: parent.width - 28; secundario: true
                             text: tipoAvancada.valor === "vlan" ? "Rede virtual com etiqueta (802.1Q) sobre uma placa, para redes de empresa separadas por VLAN."
                                   : tipoAvancada.valor === "ponte" ? "Junta placas numa só rede, como um switch. Útil para máquinas virtuais aparecerem na rede da casa."
                                   : "Usa duas ou mais placas como uma: se uma cair, a outra segura (ou somam velocidade, com o switch certo)." }
                    CampoRede { id: nomeAvancada; rotulo: "Nome"; dica: tipoAvancada.valor === "vlan" ? "Ex.: VLAN da empresa" : "Ex.: Ponte das VMs"; width: 220 }
                    Row {
                        visible: tipoAvancada.valor === "vlan"
                        spacing: 12
                        Column {
                            spacing: 4
                            Text { text: "Placa"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                            Seletor { id: placaVlan; width: 170; valor: fa.placas[0] || ""; onEscolhido: (v) => valor = v
                                      opcoes: fa.placas.map(function (p) { return { valor: p, rotulo: p } }) }
                        }
                        CampoRede { id: numeroVlan; rotulo: "Número da VLAN (1 a 4094)"; dica: "10"; width: 180 }
                    }
                    Column {
                        visible: tipoAvancada.valor !== "vlan"
                        spacing: 6
                        Text { text: "Placas"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        Repeater {
                            model: fa.placas
                            Row {
                                required property string modelData
                                spacing: 8
                                Interruptor { ligado: fa.escolhidas.indexOf(modelData) >= 0
                                              onAlternado: (v) => { var l = fa.escolhidas.filter(function (x) { return x !== modelData }); if (v) l.push(modelData); fa.escolhidas = l } }
                                Rotulo { anchors.verticalCenter: parent.verticalCenter; text: modelData }
                            }
                        }
                        Rotulo { secundario: true; text: "A placa escolhida deixa de ter conexão própria e passa a fazer parte desta." }
                    }
                    Column {
                        visible: tipoAvancada.valor === "agregacao"
                        spacing: 4
                        Text { text: "Modo"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        Seletor { id: modoAgregacao; width: 300; valor: "active-backup"; onEscolhido: (v) => valor = v
                                  opcoes: Object.keys(rede.modosDeAgregacao).map(function (k) { return { valor: k, rotulo: rede.modosDeAgregacao[k] } }) }
                    }
                    Row {
                        spacing: 8
                        Botao {
                            texto: "Criar"; tipo: "primario"
                            ativo: tipoAvancada.valor === "vlan" ? numeroVlan.texto !== "" : (nomeAvancada.texto !== "" && fa.escolhidas.length > 0)
                            onClicado: {
                                rede.novaAvancada({ tipo: tipoAvancada.valor, nome: nomeAvancada.texto, placa: placaVlan.valor, numero: parseInt(numeroVlan.texto) || 0,
                                                    placas: fa.escolhidas, modo: modoAgregacao.valor })
                                pr.avancada = false; fa.escolhidas = []
                            }
                        }
                        Botao { texto: "Cancelar"; onClicado: pr.avancada = false }
                    }
                }
            }

            // ======================================================= detalhes
            Loader {
                id: detalhes
                width: parent.width
                active: pr.aberta !== "" && rede.conexao.uuid === pr.aberta
                visible: pr.aberta !== ""
                sourceComponent: detalhesConexao
                Connections { target: rede; function onConexaoMudou() { if (detalhes.active) { detalhes.active = false; detalhes.active = Qt.binding(function () { return pr.aberta !== "" && rede.conexao.uuid === pr.aberta }) } } }
            }
            Component {
                id: detalhesConexao
                Column {
                    id: dc
                    width: parent ? parent.width : 600
                    spacing: 16
                    readonly property var c: rede.conexao
                    readonly property var info: rede.detalhesDe(c.dispositivo || "")
                    function lista(texto) { return texto.split(/[,\s]+/).filter(function (x) { return x !== "" }) }
                    function configuracao() {
                        var cfg = { uuid: c.uuid, tipo: c.tipo, automatico: automatico.ligado, prioridade: preferir.ligado ? 10 : 0,
                                    limitada: limitada.valor, mac: mac.valor, mtu: mtu.texto }
                        cfg.ipv4 = metodo4.valor === "manual"
                            ? { metodo: "manual", enderecos: [{ endereco: ip4.texto, prefixo: mascara4.texto }], gateway: gw4.texto,
                                dns: dnsModo.valor === "manual" ? lista(dnsServidores.texto) : [], soDnsManual: true, rotas: rotas4.texto }
                            : { metodo: metodo4.valor, enderecos: [], gateway: "", dns: dnsModo.valor === "manual" ? lista(dnsServidores.texto) : [],
                                soDnsManual: true, rotas: rotas4.texto }
                        cfg.ipv6 = metodo6.valor === "manual"
                            ? { metodo: "manual", enderecos: [{ endereco: ip6.texto, prefixo: prefixo6.texto }], gateway: gw6.texto, dns: [], soDnsManual: false }
                            : { metodo: metodo6.valor, enderecos: [], gateway: "", dns: [], soDnsManual: false }
                        if (c.tipo === "wifi") cfg.oculta = c.oculta
                        return cfg
                    }
                    Row {
                        spacing: 10
                        Botao { texto: "Rede e Internet"; icone: "seta-esquerda"; onClicado: pr.fechar() }
                    }
                    Destaque {
                        icone: pr.iconeDoTipo(dc.c.tipo); estilo: "azul"
                        titulo: dc.c.nome || ""
                        texto: pr.nomeDoTipo(dc.c.tipo) + (dc.c.dispositivo ? " · " + dc.c.dispositivo : "") + (dc.c.todos ? " · para todos os usuários" : " · só para você")
                    }
                    Segmentos {
                        valor: pr.aba
                        opcoes: [{ valor: "geral", rotulo: "Geral" }, { valor: "endereco", rotulo: "Endereço" }, { valor: "dns", rotulo: "DNS" },
                                 { valor: "informacoes", rotulo: "Informações" }, { valor: "privacidade", rotulo: "Privacidade" }]
                        onEscolhido: (v) => pr.aba = v
                    }

                    // ----- Geral
                    Grupo {
                        visible: pr.aba === "geral"
                        Linha { titulo: "Conectar automaticamente"; descricao: "Quando esta rede estiver disponível"
                                Interruptor { id: automatico; ligado: dc.c.automatico === true; onAlternado: (v) => ligado = v } }
                        Linha { titulo: "Preferir esta rede"; descricao: "Quando houver mais de uma disponível, esta vem primeiro"
                                Interruptor { id: preferir; ligado: (dc.c.prioridade || 0) > 0; onAlternado: (v) => ligado = v } }
                        Linha {
                            visible: ["cabo", "wifi", "celular", "bluetooth"].indexOf(dc.c.tipo) >= 0
                            titulo: "Tipo de rede"; descricao: "Privada: casa ou trabalho. Pública: café, aeroporto (nada entra no computador)"
                            Segmentos { valor: rede.zonas[dc.c.uuid] || dc.c.zona || "publica"; onEscolhido: (v) => { valor = v; rede.definirTipoDeRede(dc.c.uuid, v) }
                                        opcoes: [{ valor: "privada", rotulo: "Privada" }, { valor: "publica", rotulo: "Pública" }] }
                        }
                        Linha {
                            titulo: "Rede limitada"; descricao: "Numa rede limitada (celular, plano com franquia), o DuiaOS não baixa atualizações sozinho"
                            Seletor { id: limitada; width: 170; valor: dc.c.limitada || "auto"
                                      opcoes: [{ valor: "auto", rotulo: "Automático" }, { valor: "sim", rotulo: "Sim" }, { valor: "nao", rotulo: "Não" }]
                                      onEscolhido: (v) => valor = v }
                        }
                        Linha {
                            visible: dc.c.tipo === "wifi"
                            titulo: "Senha"; descricao: pr.senhaVisivel ? (pr.senhaWifi || "Sem senha") : "••••••••"
                            Botao { texto: pr.senhaVisivel ? "Esconder" : "Mostrar"; icone: "olho"
                                    onClicado: pr.senhaVisivel ? pr.senhaVisivel = false : rede.lerSenha(dc.c.uuid) }
                        }
                        Linha {
                            visible: dc.c.tipo === "wifi" && dc.c.ssid !== ""
                            icone: "qr"; titulo: "Compartilhar esta Wi-Fi"; descricao: "Aponte a câmera do celular para o código e ele entra na rede sem digitar a senha"
                            Botao { texto: pr.qr ? "Esconder" : "Mostrar código"; onClicado: pr.qr ? pr.qr = "" : rede.qrWifi(dc.c.uuid, dc.c.ssid, dc.c.seguranca || "") }
                        }
                        Item {
                            visible: pr.qr !== ""; width: parent.width; height: visible ? 220 : 0
                            Rectangle { anchors.centerIn: parent; width: 200; height: 200; radius: 10; color: "white"
                                        Image { anchors.fill: parent; anchors.margins: 10; source: pr.qr; smooth: false; fillMode: Image.PreserveAspectFit } }
                        }
                        Linha {
                            titulo: "MTU"; descricao: "Tamanho máximo dos pacotes. Deixe vazio para automático (o comum é 1500)"; ultima: true
                            Campo { id: mtu; width: 110; texto: dc.c.mtu || ""; dica: "Automático" }
                        }
                    }

                    // ----- Endereço
                    Grupo {
                        visible: pr.aba === "endereco"
                        titulo: "IPv4"
                        Column {
                            width: parent.width; padding: 14; spacing: 12
                            Segmentos { id: metodo4; valor: (dc.c.ipv4 || {}).metodo === "manual" ? "manual" : ((dc.c.ipv4 || {}).metodo === "desligado" ? "desligado" : "auto")
                                        opcoes: [{ valor: "auto", rotulo: "Automático (DHCP)" }, { valor: "manual", rotulo: "Manual" }, { valor: "desligado", rotulo: "Desligado" }]
                                        onEscolhido: (v) => valor = v }
                            Row {
                                visible: metodo4.valor === "manual"
                                spacing: 12
                                CampoRede { id: ip4; rotulo: "Endereço IP"; dica: "192.168.0.10"; width: 170
                                            texto: ((dc.c.ipv4 || {}).enderecos || [])[0] ? dc.c.ipv4.enderecos[0].endereco : "" }
                                CampoRede { id: mascara4; rotulo: "Máscara"; width: 150
                                            texto: ((dc.c.ipv4 || {}).enderecos || [])[0] ? dc.c.ipv4.enderecos[0].prefixo : "255.255.255.0" }
                                CampoRede { id: gw4; rotulo: "Gateway (roteador)"; dica: "192.168.0.1"; width: 170; texto: (dc.c.ipv4 || {}).gateway || "" }
                            }
                            CampoRede { id: rotas4; rotulo: "Rotas extras (opcional; ex.: 10.0.0.0/8 192.168.0.254)"; width: 420; texto: (dc.c.ipv4 || {}).rotas || "" }
                        }
                    }
                    Grupo {
                        visible: pr.aba === "endereco"
                        titulo: "IPv6"
                        Column {
                            width: parent.width; padding: 14; spacing: 12
                            Segmentos { id: metodo6; valor: (dc.c.ipv6 || {}).metodo === "manual" ? "manual" : ((dc.c.ipv6 || {}).metodo === "desligado" ? "desligado" : "auto")
                                        opcoes: [{ valor: "auto", rotulo: "Automático" }, { valor: "manual", rotulo: "Manual" }, { valor: "desligado", rotulo: "Desligado" }]
                                        onEscolhido: (v) => valor = v }
                            Row {
                                visible: metodo6.valor === "manual"
                                spacing: 12
                                CampoRede { id: ip6; rotulo: "Endereço IPv6"; width: 220
                                            texto: ((dc.c.ipv6 || {}).enderecos || [])[0] ? dc.c.ipv6.enderecos[0].endereco : "" }
                                CampoRede { id: prefixo6; rotulo: "Prefixo"; width: 80
                                            texto: ((dc.c.ipv6 || {}).enderecos || [])[0] ? dc.c.ipv6.enderecos[0].prefixo : "64" }
                                CampoRede { id: gw6; rotulo: "Gateway"; width: 200; texto: (dc.c.ipv6 || {}).gateway || "" }
                            }
                        }
                    }

                    // ----- DNS
                    Grupo {
                        visible: pr.aba === "dns"
                        titulo: "Servidores de nomes (DNS)"
                        Column {
                            width: parent.width; padding: 14; spacing: 12
                            Rotulo { width: parent.width - 28; secundario: true
                                     text: "O DNS traduz nomes de sites em endereços. Automático usa o do roteador; você pode escolher um mais rápido ou com filtro." }
                            Segmentos { id: dnsModo; valor: ((dc.c.ipv4 || {}).dns || []).length ? "manual" : "auto"
                                        opcoes: [{ valor: "auto", rotulo: "Automático" }, { valor: "manual", rotulo: "Escolher" }]
                                        onEscolhido: (v) => valor = v }
                            CampoRede { id: dnsServidores; visible: dnsModo.valor === "manual"; rotulo: "Servidores (separados por vírgula)"; width: 420
                                        texto: ((dc.c.ipv4 || {}).dns || []).join(", ") }
                            Row {
                                visible: dnsModo.valor === "manual"
                                spacing: 8
                                Repeater {
                                    model: Object.keys(rede.dnsConhecidos)
                                    Botao { required property var modelData; texto: modelData; onClicado: dnsServidores.texto = rede.dnsConhecidos[modelData].join(", ") }
                                }
                            }
                        }
                    }

                    // ----- Informações
                    Grupo {
                        visible: pr.aba === "informacoes"
                        Linha { titulo: "Endereço IP"; descricao: (dc.info.ipv4 || []).join(", ") || "—" }
                        Linha { titulo: "Gateway (roteador)"; descricao: dc.info.gateway4 || "—" }
                        Linha { titulo: "DNS em uso"; descricao: (dc.info.dns4 || []).concat(dc.info.dns6 || []).join(", ") || "—" }
                        Linha { titulo: "IPv6"; descricao: (dc.info.ipv6 || []).join(", ") || "—" }
                        Linha { titulo: "Endereço físico (MAC)"; descricao: dc.info.mac || "—" }
                        Linha { visible: (dc.info.velocidade || "") !== ""; titulo: "Velocidade do cabo"; descricao: dc.info.velocidade || "" }
                        Linha { titulo: "Rede limitada agora"; descricao: dc.info.limitada ? "Sim" : "Não"; ultima: true }
                    }

                    // ----- Privacidade
                    Grupo {
                        visible: pr.aba === "privacidade"
                        Linha {
                            titulo: "Endereço físico (MAC)"
                            descricao: "Um endereço diferente para cada rede dificulta que você seja rastreado entre redes (o iPhone e o Windows fazem assim)"
                            ultima: true
                            Seletor { id: mac; width: 250; valor: dc.c.mac || ""
                                      opcoes: [{ valor: "", rotulo: "Padrão do sistema" }, { valor: "stable", rotulo: "Diferente para cada rede" },
                                               { valor: "random", rotulo: "Novo a cada conexão" }, { valor: "permanent", rotulo: "O do equipamento" }]
                                      onEscolhido: (v) => valor = v }
                        }
                    }

                    Row {
                        visible: pr.aba !== "informacoes"
                        spacing: 8
                        Botao { texto: "Salvar"; tipo: "primario"
                                onClicado: { var cfg = dc.configuracao(); var e = rede.validar(cfg); if (e.length) aviso.mostrar(e[0]); else rede.aplicarConexao(cfg) } }
                        Botao { texto: "Cancelar"; onClicado: pr.fechar() }
                        Item { width: 24; height: 1 }
                        Botao { texto: dc.c.tipo === "wifi" ? "Esquecer esta rede" : "Apagar esta conexão"; tipo: "perigo"
                                onClicado: { if (dc.c.tipo === "ponte" || dc.c.tipo === "agregacao") rede.apagarComMembros(dc.c.uuid); else rede.esquecer(dc.c.uuid); pr.fechar() } }
                    }
                }
            }
        }
    }
    // -------------------------------------------------------------- Bluetooth
    Component {
        id: paginaBluetooth
        Pagina {
            Component.onCompleted: controles.buscarBluetooth(false)
            Rotulo { visible: !controles.bluetoothExiste; secundario: true; text: "Este computador não tem Bluetooth, ou ele está desligado no equipamento." }
            Grupo {
                visible: controles.bluetoothExiste
                Linha { icone: "bluetooth"; titulo: "Bluetooth"; descricao: controles.bluetoothLigado ? "Ligado e visível para os seus dispositivos" : "Desligado"; ultima: true
                        Interruptor { ligado: controles.bluetoothLigado; onAlternado: (v) => controles.ligarBluetooth(v) } }
            }
            Grupo {
                visible: controles.bluetoothLigado
                titulo: "Meus dispositivos"
                Linha { visible: controles.bluetoothPareados.length === 0; titulo: "Nenhum dispositivo pareado ainda"; ultima: true }
                Repeater {
                    model: controles.bluetoothPareados
                    Linha {
                        required property var modelData
                        required property int index
                        icone: "bluetooth"; titulo: modelData.nome; descricao: modelData.conectado ? "Conectado" : "Não conectado"
                        ultima: index === controles.bluetoothPareados.length - 1
                        Botao { texto: modelData.conectado ? "Desconectar" : "Conectar"
                                onClicado: modelData.conectado ? controles.desconectarBluetooth(modelData.endereco) : controles.conectarBluetooth(modelData.endereco) }
                        Botao { texto: "Esquecer"; onClicado: controles.esquecerBluetooth(modelData.endereco) }
                    }
                }
            }
            Grupo {
                visible: controles.bluetoothLigado
                titulo: controles.buscandoBluetooth ? "Procurando dispositivos por perto…" : "Dispositivos por perto"
                Linha { visible: controles.bluetoothProximos.length === 0; titulo: controles.buscandoBluetooth ? "Procurando…" : "Clique em Procurar com o dispositivo em modo de pareamento"; ultima: true }
                Repeater {
                    model: controles.bluetoothProximos
                    Linha {
                        required property var modelData
                        required property int index
                        icone: "bluetooth"; titulo: modelData.nome; ultima: index === controles.bluetoothProximos.length - 1
                        Botao { texto: "Parear"; tipo: "primario"; onClicado: controles.conectarBluetooth(modelData.endereco) }
                    }
                }
            }
            Botao { visible: controles.bluetoothLigado; texto: "Procurar"; icone: "busca"; ativo: !controles.buscandoBluetooth; onClicado: controles.buscarBluetooth(true) }
        }
    }

    // -------------------------------------------------------------------- Som
    Component {
        id: paginaSom
        Pagina {
            Grupo {
                titulo: "Saída"
                Linha {
                    icone: controles.mudo ? "som-mudo" : "som-2"; titulo: "Volume"
                    Deslizante { width: 260; valor: controles.mudo ? 0 : controles.volume; icone: "som-2"; iconeBaixo: "som-0"
                                 onMovido: (v) => controles.definirVolume(v); onIconeClicado: controles.alternarMudo() }
                }
                Linha { titulo: "Sem som"; ultima: controles.saidas.length === 0; Interruptor { ligado: controles.mudo; onAlternado: controles.alternarMudo() } }
                Repeater {
                    model: controles.saidas
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData.nome; clicavel: true; ultima: index === controles.saidas.length - 1
                        onClicada: controles.escolherDispositivoDeSom(modelData.id)
                        Icone { visible: modelData.padrao; nome: "check"; tamanho: 16; cor: Tema.azulDuia }
                    }
                }
            }
            Grupo {
                titulo: "Entrada"
                visible: controles.microfone >= 0
                Linha {
                    icone: "microfone"; titulo: "Volume do microfone"
                    Deslizante { width: 260; valor: controles.microfoneMudo ? 0 : controles.microfone; icone: "microfone"
                                 onMovido: (v) => controles.definirMicrofone(v); onIconeClicado: controles.alternarMicrofoneMudo() }
                }
                Repeater {
                    model: controles.entradas
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData.nome; clicavel: true; ultima: index === controles.entradas.length - 1
                        onClicada: controles.escolherDispositivoDeSom(modelData.id)
                        Icone { visible: modelData.padrao; nome: "check"; tamanho: 16; cor: Tema.azulDuia }
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------ Tela
    Component {
        id: paginaTela
        Pagina {
            Grupo {
                visible: controles.brilho >= 0
                Linha { icone: "brilho"; titulo: "Brilho"; ultima: true
                        Deslizante { width: 260; valor: controles.brilho; icone: "brilho"; iconeBaixo: "brilho-baixo"; onMovido: (v) => controles.definirBrilho(v) } }
            }
            Repeater {
                model: ajustes.telas
                Grupo {
                    required property var modelData
                    titulo: modelData.descricao !== "" ? modelData.descricao : modelData.nome
                    Linha {
                        icone: "monitor"; titulo: "Resolução"
                        Seletor { opcoes: modelData.modos.map(function (m) { return { valor: m.valor, rotulo: m.rotulo + (m.preferido ? " · recomendada" : "") } })
                                  valor: modelData.modo; onEscolhido: (v) => ajustes.definirTela(modelData.nome, v, modelData.escala) }
                    }
                    Linha {
                        titulo: "Tamanho do texto e dos itens"; descricao: "Escala da tela"; ultima: true
                        Seletor { width: 160
                                  opcoes: [{ valor: "1", rotulo: "100%" }, { valor: "1.25", rotulo: "125%" }, { valor: "1.5", rotulo: "150%" },
                                           { valor: "1.75", rotulo: "175%" }, { valor: "2", rotulo: "200%" }]
                                  valor: String(modelData.escala); onEscolhido: (v) => ajustes.definirTela(modelData.nome, modelData.modo, parseFloat(v)) }
                    }
                }
            }
            Rotulo { visible: ajustes.telas.length === 0; secundario: true; text: "Não foi possível ler as telas (wlr-randr)." }
            Grupo {
                titulo: "Luz noturna"
                Linha {
                    icone: "lua"; titulo: "Luz noturna"; descricao: "Cores mais quentes, que cansam menos a vista à noite"
                    Seletor { width: 200
                              opcoes: [{ valor: "desligada", rotulo: "Desligada" }, { valor: "ligada", rotulo: "Ligada" }, { valor: "programada", rotulo: "Programada" }]
                              valor: controles.luzNoturna; onEscolhido: (v) => controles.definirLuzNoturna(v) }
                }
                Linha {
                    titulo: "Horário programado"; descricao: "Usado no modo Programada"; ultima: true
                    Campo { id: luzInicio; width: 72; texto: ajustes.luzInicio; entrada.horizontalAlignment: TextInput.AlignHCenter }
                    Text { text: "às"; anchors.verticalCenter: parent.verticalCenter; color: Tema.textoSecundario; font.family: Tema.fonteTexto }
                    Campo { id: luzFim; width: 72; texto: ajustes.luzFim; entrada.horizontalAlignment: TextInput.AlignHCenter }
                    Botao { texto: "Salvar"; onClicado: ajustes.definirHorarioLuz(luzInicio.texto, luzFim.texto) }
                }
            }
        }
    }

    // ------------------------------------------------------- Bateria e energia
    Component {
        id: paginaEnergia
        Pagina {
            Grupo {
                visible: controles.bateria >= 0
                Linha {
                    titulo: "Bateria"
                    descricao: controles.carregando ? "Carregando" + (controles.tempoBateria !== "" ? " · cheia em " + controles.tempoBateria : "")
                               : (controles.tomada ? "Na tomada" : (controles.tempoBateria !== "" ? "Restam cerca de " + controles.tempoBateria : "Usando a bateria"))
                    ultima: true
                    IconeBateria { anchors.verticalCenter: parent.verticalCenter; nivel: controles.bateria; carregando: controles.carregando }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: controles.bateria + "%"; color: Tema.texto; font { family: Tema.fonteTitulo; pixelSize: 18; weight: Font.Bold } }
                }
            }
            Grupo {
                visible: controles.perfis.length > 0
                titulo: "Modo de energia"
                Repeater {
                    model: controles.perfis
                    Linha {
                        required property string modelData
                        required property int index
                        titulo: controles.nomesPerfis[modelData]
                        descricao: ({ "power-saver": "Mais horas de bateria, um pouco mais lento", balanced: "O melhor para o dia a dia", performance: "Mais rápido; gasta mais bateria e esquenta mais" })[modelData]
                        clicavel: true; ultima: index === controles.perfis.length - 1
                        onClicada: controles.definirPerfil(modelData)
                        Icone { visible: controles.perfil === modelData; nome: "check"; tamanho: 16; cor: Tema.azulDuia }
                    }
                }
            }
            Grupo {
                titulo: "Tela de Bloqueio e repouso"
                Linha {
                    icone: "cadeado"; titulo: "Bloquear a tela depois de"
                    Seletor { width: 180
                              opcoes: [{ valor: "2", rotulo: "2 minutos" }, { valor: "5", rotulo: "5 minutos" }, { valor: "10", rotulo: "10 minutos" },
                                       { valor: "15", rotulo: "15 minutos" }, { valor: "30", rotulo: "30 minutos" }, { valor: "60", rotulo: "1 hora" }, { valor: "0", rotulo: "Nunca" }]
                              valor: String(ajustes.bloquearApos); onEscolhido: (v) => ajustes.definirMinutos("bloquear", parseInt(v)) }
                }
                Linha {
                    icone: "lua"; titulo: "Repousar depois de"; descricao: "Sem uso; a tela bloqueia antes"; ultima: true
                    Seletor { width: 180
                              opcoes: [{ valor: "15", rotulo: "15 minutos" }, { valor: "30", rotulo: "30 minutos" }, { valor: "60", rotulo: "1 hora" },
                                       { valor: "120", rotulo: "2 horas" }, { valor: "0", rotulo: "Nunca" }]
                              valor: String(ajustes.repousarApos); onEscolhido: (v) => ajustes.definirMinutos("repousar", parseInt(v)) }
                }
            }
        }
    }

    // ---------------------------------- miniatura de fundo (imagem, GIF, vídeo ou cor)
    component MiniaturaFundo: Rectangle {
        id: mf
        property string arquivo: ""
        property string cor: ""
        property bool atual: false
        signal escolhida()
        readonly property string ext: arquivo.toLowerCase().split(".").pop()
        readonly property bool video: ["mp4", "webm", "mkv", "mov", "m4v"].indexOf(ext) >= 0
        width: 132; height: 82; radius: 10
        color: cor !== "" ? cor : Tema.controleDesligado
        clip: true
        border { color: atual ? Tema.azulDuia : Tema.borda; width: atual ? 3 : 1 }
        Image { anchors.fill: parent; anchors.margins: mf.atual ? 3 : 1; visible: mf.arquivo !== "" && !mf.video
                source: visible ? "file://" + mf.arquivo : ""; fillMode: Image.PreserveAspectCrop; sourceSize.width: 264; asynchronous: true }
        Column {
            visible: mf.video
            anchors.centerIn: parent
            spacing: 2
            Icone { anchors.horizontalCenter: parent.horizontalCenter; nome: "video"; tamanho: 24; cor: Tema.textoSecundario }
            Text { width: mf.width - 16; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideMiddle
                   text: mf.arquivo.split("/").pop(); color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 10 } }
        }
        Rectangle {
            visible: mf.video || mf.ext === "gif" || mf.ext === "webp"
            anchors { right: parent.right; bottom: parent.bottom; margins: 6 }
            width: 22; height: 16; radius: 4; color: Qt.rgba(0, 0, 0, 0.55)
            Text { anchors.centerIn: parent; text: "▶"; color: "white"; font.pixelSize: 9 }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: mf.escolhida() }
    }

    FileDialog {
        id: escolherArquivo
        property string destino: "papel"
        title: destino === "descanso" ? "Escolher imagem ou vídeo da Tela de Descanso" : "Escolher papel de parede"
        nameFilters: ["Imagens e vídeos (*.jpg *.jpeg *.png *.webp *.gif *.mp4 *.webm *.mkv *.mov *.m4v)"]
        onAccepted: ajustes.importarFundo(selectedFile.toString(), destino)
    }
    FileDialog {
        id: escolherFoto
        title: "Escolher foto da conta"
        nameFilters: ["Imagens (*.jpg *.jpeg *.png *.webp)"]
        onAccepted: ajustes.definirFoto(selectedFile.toString())
    }

    // -------------------------------------------------------- Papel de parede
    // Abas de escolha (segmentos), no estilo do macOS
    component Segmentos: Rectangle {
        id: seg
        property var opcoes: []            // [{valor, rotulo}]
        property string valor: ""
        signal escolhido(string valor)
        width: linhaSeg.implicitWidth + 6; height: 32; radius: 9
        color: Tema.controleDesligado
        Row {
            id: linhaSeg
            anchors.centerIn: parent
            spacing: 2
            Repeater {
                model: seg.opcoes
                Rectangle {
                    required property var modelData
                    width: textoSeg.implicitWidth + 28; height: 26; radius: 7
                    color: seg.valor === modelData.valor ? Tema.cartao : (areaSeg.containsMouse ? Tema.realce : "transparent")
                    border { color: seg.valor === modelData.valor ? Tema.borda : "transparent"; width: 1 }
                    Text { id: textoSeg; anchors.centerIn: parent; text: modelData.rotulo; color: Tema.texto
                           font { family: Tema.fonteTexto; pixelSize: 12; weight: seg.valor === modelData.valor ? Font.DemiBold : Font.Normal } }
                    MouseArea { id: areaSeg; anchors.fill: parent; hoverEnabled: true; onClicked: seg.escolhido(modelData.valor) }
                }
            }
        }
    }

    // --------------------------------------------------------- Papel de parede
    Component {
        id: paginaPapel
        Pagina {
            id: pp
            property var imagens: ajustes.imagensDoUsuario()
            readonly property var i: ajustes.papelInfo
            readonly property var a: i.atual || ({})
            readonly property var acesso: a.acesso || ({})
            readonly property bool naArea: i.alvo === "area"
            readonly property bool variasTelas: (i.telas || []).length > 1
            readonly property var opcoesAjuste: [{ valor: "preencher", rotulo: "Preencher a tela" }, { valor: "ajustar", rotulo: "Ajustar à tela" },
                                                 { valor: "esticar", rotulo: "Esticar" }, { valor: "centralizar", rotulo: "Centralizar" },
                                                 { valor: "lado-a-lado", rotulo: "Lado a lado" }]
            function escolher(arquivo) { ajustes.definirPapel(arquivo) }
            function atualEh(arquivo) { return (pp.a.arquivo || "") === arquivo }

            Segmentos {
                opcoes: [{ valor: "area", rotulo: "Área de trabalho" }, { valor: "bloqueio", rotulo: "Tela de Bloqueio" },
                         { valor: "entrada", rotulo: "Tela de Entrada" }]
                valor: pp.i.alvo; onEscolhido: (v) => ajustes.escolherAlvoPapel(v)
            }

            // Telas (área de trabalho com mais de um monitor)
            Grupo {
                visible: pp.naArea
                Linha {
                    icone: "monitor"; titulo: "Com mais de uma tela"
                    descricao: pp.variasTelas ? (pp.i.telas.length + " telas ligadas") : "Só uma tela ligada agora; vale quando ligar outra"
                    ultima: pp.i.modoTelas !== "separado"
                    Seletor { width: 230
                              opcoes: [{ valor: "mesmo", rotulo: "O mesmo em todas" }, { valor: "separado", rotulo: "Um para cada tela" },
                                       { valor: "estender", rotulo: "Uma imagem por todas" }]
                              valor: pp.i.modoTelas; onEscolhido: (v) => ajustes.definirModoTelas(v) }
                }
                Linha {
                    visible: pp.i.modoTelas === "separado"
                    icone: "monitor"; titulo: "Tela que está mudando"; ultima: true
                    Segmentos {
                        anchors.verticalCenter: parent.verticalCenter
                        opcoes: (pp.i.telas || []).map(function (t) { return { valor: t.nome, rotulo: t.rotulo } })
                        valor: pp.i.tela; onEscolhido: (v) => ajustes.escolherTelaPapel(v)
                    }
                }
            }

            // Pré-visualização: as telas como estão na mesa (cada uma com o seu papel)
            Item {
                id: previa
                width: Math.min(parent.width, 560)
                readonly property var telas: pp.naArea && pp.i.modoTelas !== "mesmo" && pp.variasTelas ? pp.i.telas : []
                readonly property real x0: telas.length ? Math.min.apply(null, telas.map(function (t) { return t.x })) : 0
                readonly property real y0: telas.length ? Math.min.apply(null, telas.map(function (t) { return t.y })) : 0
                readonly property real larguraTotal: telas.length ? Math.max.apply(null, telas.map(function (t) { return t.x + t.largura })) - x0 : 16
                readonly property real alturaTotal: telas.length ? Math.max.apply(null, telas.map(function (t) { return t.y + t.altura })) - y0 : 10
                readonly property real escala: telas.length ? Math.min(width / larguraTotal, 260 / alturaTotal) : 1
                height: telas.length ? alturaTotal * escala : Math.min(width, 420) * 0.6
                // Uma tela só (ou o mesmo em todas, ou Bloqueio/Entrada)
                Rectangle {
                    visible: previa.telas.length === 0
                    width: Math.min(previa.width, 420); height: width * 0.6; radius: 14
                    clip: true
                    color: Tema.controleDesligado
                    border { color: Tema.borda; width: 1 }
                    Fundo { anchors.fill: parent; anchors.margins: 1; arquivo: pp.a.arquivo || ""; corFundo: pp.a.cor || "#E8F0FE"
                            ajuste: pp.a.ajuste || "preencher"; escala: width / 1920; tocando: pp.naArea }
                    // Desfoque e o cartão de senha, para dar a ideia das Telas de Entrada e de Bloqueio
                    Loader { anchors.fill: parent; active: !pp.naArea && pp.a.desfocar === true; source: active ? "file://" + caminhoComum + "/FundoDesfocado.qml" : ""
                             onLoaded: item.fonte = parent.children[0] }
                    Rectangle { visible: !pp.naArea; anchors.centerIn: parent; width: parent.width * 0.32; height: parent.height * 0.42; radius: 12
                                color: Qt.rgba(1, 1, 1, 0.82)
                                Rectangle { anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: parent.height * 0.14 }
                                            width: parent.width * 0.3; height: width; radius: width / 2; color: Tema.azulDuia }
                                Rectangle { anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: parent.height * 0.14 }
                                            width: parent.width * 0.8; height: parent.height * 0.14; radius: 4; color: "white"; border.color: Tema.borda } }
                }
                // Várias telas
                Repeater {
                    model: previa.telas
                    Rectangle {
                        required property var modelData
                        readonly property var p: pp.i.porTela[modelData.nome] || pp.a
                        x: (modelData.x - previa.x0) * previa.escala + 2; y: (modelData.y - previa.y0) * previa.escala + 2
                        width: modelData.largura * previa.escala - 4; height: modelData.altura * previa.escala - 4
                        radius: 8; clip: true
                        color: Tema.controleDesligado
                        border { color: pp.i.modoTelas === "separado" && pp.i.tela === modelData.nome ? Tema.azulDuia : Tema.borda
                                 width: pp.i.modoTelas === "separado" && pp.i.tela === modelData.nome ? 3 : 1 }
                        Fundo {
                            anchors.fill: parent; anchors.margins: parent.border.width
                            readonly property var papel: pp.i.modoTelas === "estender" ? pp.a : parent.p
                            arquivo: papel.arquivo || ""; corFundo: papel.cor || "#E8F0FE"; ajuste: papel.ajuste || "preencher"
                            escala: previa.escala; tocando: false
                            estendido: pp.i.modoTelas === "estender" ? { largura: previa.larguraTotal, altura: previa.alturaTotal,
                                                                         dx: modelData.x - previa.x0, dy: modelData.y - previa.y0 } : null
                        }
                        Text { anchors { left: parent.left; bottom: parent.bottom; margins: 8 } text: modelData.rotulo; color: "white"
                               style: Text.Outline; styleColor: Qt.rgba(0, 0, 0, 0.35); font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
                        MouseArea { anchors.fill: parent; enabled: pp.i.modoTelas === "separado"; cursorShape: Qt.PointingHandCursor
                                    onClicked: ajustes.escolherTelaPapel(modelData.nome) }
                    }
                }
            }
            Rotulo { visible: (pp.i.tamanhoImagem || "") !== ""; width: parent.width; secundario: true
                     text: "Imagem de " + pp.i.tamanhoImagem + " pixels" + ((pp.i.telas || []).length ? " · tela de " + pp.i.telas[0].largura + " × " + pp.i.telas[0].altura : "") }

            // Opções do alvo
            Grupo {
                Linha {
                    visible: pp.i.alvo === "bloqueio"
                    icone: "cadeado"; titulo: "Imagem"
                    descricao: pp.i.bloqueioModo === "area" ? "A mesma da área de trabalho" : "Uma imagem só da Tela de Bloqueio"
                    Botao { visible: pp.i.bloqueioModo !== "area"; texto: "Usar o da área de trabalho"; height: 28; onClicado: ajustes.usarPapelDaArea() }
                }
                Linha {
                    visible: pp.i.alvo === "entrada"
                    icone: "usuarios"; titulo: "Imagem"
                    descricao: (pp.a.modo === "padrao" ? "A do DuiaOS" : "Escolhida neste computador") + ". Vale para todas as contas; só um administrador muda."
                    Botao { texto: "Usar o da área de trabalho"; height: 28; onClicado: ajustes.usarPapelDaArea() }
                    Botao { visible: pp.a.modo !== "padrao"; texto: "Voltar ao do DuiaOS"; height: 28; onClicado: ajustes.entradaPadrao() }
                }
                Linha {
                    icone: "imagem"; titulo: "Como a imagem ocupa a tela"
                    descricao: ({ preencher: "Cobre a tela inteira, cortando o que sobra", ajustar: "A imagem inteira aparece; sobra a cor nas bordas",
                                  esticar: "Ocupa a tela, deformando se as proporções forem diferentes", centralizar: "Tamanho original, no meio da tela",
                                  "lado-a-lado": "Repetida, como azulejos" })[pp.a.ajuste || "preencher"]
                    Seletor { width: 200; opcoes: pp.opcoesAjuste; valor: pp.a.ajuste || "preencher"; onEscolhido: (v) => ajustes.definirAjuste(v) }
                }
                Linha {
                    visible: (pp.a.arquivo || "") !== "" && ["ajustar", "centralizar"].indexOf(pp.a.ajuste) >= 0
                    icone: "paleta"; titulo: "Cor em volta da imagem"
                    Row {
                        spacing: 6; anchors.verticalCenter: parent.verticalCenter
                        Repeater { model: ["#E8F0FE", "#FFFFFF", "#1A3A73", "#0F1724", "#000000", "#5B6675"]
                                   Rectangle { required property string modelData; width: 22; height: 22; radius: 11; color: modelData
                                               border { color: (pp.a.cor || "").toUpperCase() === modelData ? Tema.azulDuia : Tema.borda; width: 2 }
                                               MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: ajustes.definirCorDasBordas(modelData) } } }
                    }
                }
                Linha {
                    visible: pp.naArea
                    icone: "recentes"; titulo: "Trocar sozinho"; descricao: "Entre as imagens do DuiaOS e as que você importou"
                    ultima: true
                    Seletor { width: 200
                              opcoes: [{ valor: "0", rotulo: "Nunca" }, { valor: "15", rotulo: "A cada 15 minutos" }, { valor: "30", rotulo: "A cada 30 minutos" },
                                       { valor: "60", rotulo: "A cada hora" }, { valor: "180", rotulo: "A cada 3 horas" }, { valor: "1440", rotulo: "Uma vez por dia" }]
                              valor: String(pp.i.alternar); onEscolhido: (v) => ajustes.definirAlternar(parseInt(v)) }
                }
                Linha {
                    visible: !pp.naArea
                    icone: "olho"; titulo: "Desfocar o fundo"; descricao: "Deixa o cartão da senha em destaque"; ultima: true
                    Interruptor { ligado: pp.a.desfocar === true; onAlternado: (l) => ajustes.definirDesfocar(l) }
                }
            }

            // Tom azul e brilho do estilo futurista nas Telas de Bloqueio e de Entrada (ADR 056)
            Grupo {
                visible: !pp.naArea
                titulo: "Tom azul e brilho"
                Linha {
                    icone: "paleta"; titulo: "Transparência do tom azul"
                    descricao: "0% cobre o papel de parede de azul; 100% mostra só o papel de parede"
                    Row {
                        spacing: 10; anchors.verticalCenter: parent.verticalCenter
                        Deslizante {
                            id: deslizanteVeu
                            width: 200
                            property int escolhido: pp.acesso.veu !== undefined ? pp.acesso.veu : 15
                            valor: escolhido
                            onMovido: (v) => { escolhido = Math.round(v); if (pp.i.alvo === "bloqueio") ajustes.definirAcesso("veu", String(escolhido)) }
                            onSolto: if (pp.i.alvo === "entrada") ajustes.definirAcesso("veu", String(escolhido))   // a Tela de Entrada grava com permissão de administrador: só ao soltar
                        }
                        Rotulo { anchors.verticalCenter: parent.verticalCenter; width: 40; text: deslizanteVeu.escolhido + "%" }
                    }
                }
                Linha {
                    icone: "brilho"; titulo: "Brilho perto da senha"; descricao: "Um clarão no centro da tela"
                    Segmentos { opcoes: [{ valor: "radial", rotulo: "Radial" }, { valor: "linear", rotulo: "Linear" }, { valor: "nenhum", rotulo: "Desligado" }]
                                valor: pp.acesso.brilho || "radial"; onEscolhido: (v) => ajustes.definirAcesso("brilho", v) }
                }
                Linha {
                    icone: "monitor"; titulo: "Brilho no relógio das outras telas"
                    descricao: "Com mais de um monitor, o brilho também aparece atrás do relógio"; ultima: true
                    Interruptor { ligado: pp.acesso.brilho_extra === true; onAlternado: (l) => ajustes.definirAcesso("brilho_extra", l ? "sim" : "nao") }
                }
            }
            Rotulo { visible: !pp.naArea; width: parent.width; secundario: true
                     text: "O tom azul e o brilho aparecem no estilo Futurista. " + (pp.i.alvo === "entrada" ? "A Tela de Entrada muda na próxima vez que ela aparecer." : "Bloqueie a tela (Super + L) para ver.") }

            Botao { texto: pp.naArea ? "Importar imagem ou vídeo…" : "Importar imagem…"; icone: "mais"; tipo: "primario"
                    onClicado: { escolherArquivo.destino = "papel"; escolherArquivo.open() } }
            Rotulo { width: parent.width; secundario: true
                     text: pp.naArea ? "Aceita fotos (JPG, PNG, WebP), imagens com movimento (GIF) e vídeos (MP4, WebM, MKV, MOV), que tocam sem som e em laço."
                                     : "As Telas de Entrada e de Bloqueio usam fotos (JPG, PNG ou WebP)." }
            Titulo { nivel: 3; text: "Do DuiaOS"; visible: ajustes.papeis.length > 0 }
            Flow { width: parent.width; spacing: 12
                   Repeater { model: ajustes.papeis
                              MiniaturaFundo { required property string modelData; arquivo: modelData; atual: pp.atualEh(modelData)
                                               onEscolhida: pp.escolher(modelData) } } }
            Titulo { nivel: 3; text: "Importados"; visible: ajustes.fundosImportados.length > 0 }
            Flow { width: parent.width; spacing: 12
                   Repeater { model: ajustes.fundosImportados
                              MiniaturaFundo { required property string modelData; arquivo: modelData; atual: pp.atualEh(modelData)
                                               visible: pp.naArea || /\.(jpe?g|png|webp)$/i.test(modelData)
                                               onEscolhida: pp.escolher(modelData) } } }
            Titulo { nivel: 3; text: "Cores" }
            Flow {
                width: parent.width; spacing: 12
                Repeater { model: ["#E8F0FE", "#1A3A73", "#0F1724", "#2E6BE6", "#2FA67A", "#F4E9DA", "#E8A33D", "#5B6675"]
                           MiniaturaFundo { required property string modelData; cor: modelData; width: 82
                                            atual: (pp.a.arquivo || "") === "" && (pp.a.cor || "").toUpperCase() === modelData
                                            onEscolhida: pp.escolher(modelData) } }
            }
            Titulo { nivel: 3; text: "Da pasta Imagens"; visible: pp.imagens.length > 0 }
            Flow { width: parent.width; spacing: 12
                   Repeater { model: pp.imagens
                              MiniaturaFundo { required property string modelData; arquivo: modelData; atual: pp.atualEh(modelData)
                                               onEscolhida: pp.escolher(modelData) } } }
        }
    }

    // ------------------------------------------------------- Tela de Descanso
    Component {
        id: paginaDescanso
        Pagina {
            Rectangle {
                width: Math.min(parent.width, 420); height: width * 0.6; radius: 14
                clip: true
                color: "black"
                border { color: Tema.borda; width: 1 }
                Fundo { anchors.fill: parent; anchors.margins: 1; arquivo: ajustes.descansoArquivo !== "" ? ajustes.descansoArquivo : ajustes.papelAtual
                        corFundo: ajustes.corAtual }
                Text { visible: ajustes.descansoRelogio; anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: parent.height * 0.14 }
                       text: Qt.formatTime(new Date(), "HH:mm"); color: "white"; style: Text.Raised; styleColor: Qt.rgba(0, 0, 0, 0.3)
                       font { family: Tema.fonteTitulo; pixelSize: 44; weight: Font.Bold } }
            }
            Grupo {
                Linha {
                    icone: "relogio"; titulo: "Mostrar depois de"; descricao: "Sem uso. Qualquer tecla ou movimento do mouse volta."
                    Seletor { width: 180
                              opcoes: [{ valor: "1", rotulo: "1 minuto" }, { valor: "3", rotulo: "3 minutos" }, { valor: "5", rotulo: "5 minutos" },
                                       { valor: "10", rotulo: "10 minutos" }, { valor: "20", rotulo: "20 minutos" }, { valor: "0", rotulo: "Nunca" }]
                              valor: String(ajustes.descansoMinutos); onEscolhido: (v) => ajustes.definirMinutosDescanso(parseInt(v)) }
                }
                Linha { titulo: "Mostrar o relógio"; Interruptor { ligado: ajustes.descansoRelogio; onAlternado: (v) => ajustes.definirRelogioDescanso(v) } }
                Linha { titulo: "Imagem ou vídeo"; descricao: ajustes.descansoArquivo !== "" ? ajustes.descansoArquivo.split("/").pop() : "O mesmo do papel de parede"
                        ultima: true
                        Botao { texto: "Usar o papel de parede"; visible: ajustes.descansoArquivo !== ""; onClicado: ajustes.definirDescanso("") }
                        Botao { texto: "Importar…"; tipo: "primario"; onClicado: { escolherArquivo.destino = "descanso"; escolherArquivo.open() } } }
            }
            Titulo { nivel: 3; text: "Importados"; visible: ajustes.fundosImportados.length > 0 }
            Flow { width: parent.width; spacing: 12
                   Repeater { model: ajustes.fundosImportados
                              MiniaturaFundo { required property string modelData; arquivo: modelData; atual: ajustes.descansoArquivo === modelData
                                               onEscolhida: ajustes.definirDescanso(modelData) } } }
            Botao { texto: "Ver agora"; icone: "olho"; onClicado: ajustes.testarDescanso() }
            Rotulo { width: parent.width; secundario: true
                     text: "A Tela de Descanso não pede senha. A tela bloqueia no tempo escolhido em Bateria e energia." }
        }
    }

    // -------------------------------------------------------------- Aparência
    Component {
        id: paginaAparencia
        Pagina {
            // Estilos (ADR 052 e 054): o futurista "Aurora" (o inicial) ou o Clássico (id "padrao")
            Titulo { nivel: 3; text: "Estilos" }
            Row {
                spacing: 18
                Repeater {
                    model: [{ id: "futurista", nome: "Futurista", texto: "O visual do DuiaOS: vidro, brilho e o degradê aurora" },
                            { id: "padrao", nome: "Clássico", texto: "O visual anterior, mais sóbrio" }]
                    Column {
                        id: opcaoEstilo
                        required property var modelData
                        readonly property bool atual: aparencia.estilo === modelData.id
                        readonly property bool fut: modelData.id === "futurista"
                        spacing: 8
                        Rectangle {
                            width: 230; height: 146; radius: 18
                            clip: true
                            color: opcaoEstilo.fut ? "#0A0F1F" : "#F7F9FC"
                            border { color: opcaoEstilo.atual ? Tema.azulDuia : Tema.borda; width: opcaoEstilo.atual ? 3 : 1 }
                            // Uma janelinha de exemplo em cada estilo
                            Rectangle {
                                x: 16; y: 16; width: 132; height: 96; radius: opcaoEstilo.fut ? 14 : 8
                                color: opcaoEstilo.fut ? "#131A30" : "#FFFFFF"
                                border { color: opcaoEstilo.fut ? "#35427A" : "#DDE3EC"; width: 1 }
                                Row { x: parent.width - width - 10; y: 10; spacing: 4
                                      Repeater { model: ["#8DB8FF", "#3D7BF2", "#2447A8"]; Rectangle { required property string modelData; width: 7; height: 7; radius: 3.5; color: modelData } } }
                                Rectangle { x: 10; y: 30; width: 84; height: 7; radius: 3.5; color: opcaoEstilo.fut ? "#35427A" : "#C9D2DE" }
                                Rectangle { x: 10; y: 44; width: 56; height: 7; radius: 3.5; color: opcaoEstilo.fut ? "#232C4D" : "#DDE3EC" }
                                Rectangle {
                                    x: 10; y: 64; width: 72; height: 20; radius: opcaoEstilo.fut ? 10 : 5
                                    color: "#2E6BE6"
                                    gradient: opcaoEstilo.fut ? degradeAmostra : null
                                    Gradient { id: degradeAmostra; orientation: Gradient.Horizontal
                                               GradientStop { position: 0; color: "#22D3EE" } GradientStop { position: 0.5; color: "#5B8CFF" } GradientStop { position: 1; color: "#A78BFA" } }
                                }
                            }
                            // E a Ilha
                            Rectangle {
                                anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 8 }
                                width: 104; height: 20; radius: opcaoEstilo.fut ? 10 : 7
                                color: opcaoEstilo.fut ? Qt.rgba(1, 1, 1, 0.10) : "#FFFFFF"
                                border { color: opcaoEstilo.fut ? Qt.rgba(0.55, 0.68, 1, 0.4) : "#DDE3EC"; width: 1 }
                                Row { anchors.centerIn: parent; spacing: 5
                                      Repeater { model: opcaoEstilo.fut ? ["#22D3EE", "#5B8CFF", "#A78BFA", "#7C83FF"] : ["#2E6BE6", "#6FA0F7", "#1A3A73", "#2E6BE6"]
                                                 Rectangle { required property string modelData; width: 12; height: 12; radius: opcaoEstilo.fut ? 4 : 3; color: modelData } } }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: ajustes.definirEstilo(opcaoEstilo.modelData.id) }
                        }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: opcaoEstilo.modelData.nome; color: Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 13; weight: opcaoEstilo.atual ? Font.Bold : Font.Normal } }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: opcaoEstilo.modelData.texto; color: Tema.textoSecundario
                               font { family: Tema.fonteTexto; pixelSize: 11 } }
                    }
                }
            }
            Rotulo { width: parent.width; secundario: true
                     text: "O estilo vale para a Barra, a Ilha, as janelas, os aplicativos do DuiaOS e as Telas de Bloqueio e de Entrada. A Tela de Entrada muda na próxima vez que o computador ligar (só um administrador muda a dela)." }
            Titulo { nivel: 3; text: "Modo" }
            Row {
                spacing: 18
                Repeater {
                    model: [{ id: false, nome: "Claro", modo: "claro" }, { id: true, nome: "Escuro", modo: "escuro" }, { id: false, nome: "Automático", modo: "automatico" }]
                    Column {
                        id: opcaoModo
                        required property var modelData
                        readonly property bool atual: aparencia.modo === modelData.modo
                        readonly property bool auto: modelData.modo === "automatico"
                        spacing: 8
                        Rectangle {
                            width: 180; height: 116; radius: 14
                            color: modelData.id ? "#1B1F27" : "#F7F9FC"
                            border { color: opcaoModo.atual ? Tema.azulDuia : Tema.borda; width: opcaoModo.atual ? 3 : 1 }
                            clip: true
                            // Automático: metade clara (dia), metade escura (noite)
                            Rectangle { visible: opcaoModo.auto; x: parent.width / 2; y: 3; width: parent.width / 2 - 3; height: parent.height - 6; radius: 11; color: "#1B1F27"; z: 0
                                        Rectangle { width: parent.radius; height: parent.height; color: parent.color } }
                            Icone { visible: opcaoModo.auto; nome: "brilho"; tamanho: 30; cor: "#E8A33D"; x: parent.width / 4 - 15; y: parent.height / 2 - 15; z: 2 }
                            Icone { visible: opcaoModo.auto; nome: "lua"; tamanho: 28; cor: "#C9D4F5"; x: parent.width * 3 / 4 - 14; y: parent.height / 2 - 14; z: 2 }
                            Rectangle { visible: !opcaoModo.auto; x: 12; y: 12; width: parent.width - 24; height: 12; radius: 4; color: modelData.id ? "#262B34" : "#FFFFFF"
                                        border { color: modelData.id ? "#353B46" : "#DDE3EC"; width: 1 } }
                            Rectangle { visible: !opcaoModo.auto; x: 12; y: 32; width: 100; height: 64; radius: 8; color: modelData.id ? "#262B34" : "#FFFFFF"
                                        border { color: modelData.id ? "#353B46" : "#DDE3EC"; width: 1 }
                                        Row { x: parent.width - width - 8; y: 8; spacing: 4
                                              Repeater { model: ["#8DB8FF", "#3D7BF2", "#2447A8"]; Rectangle { required property string modelData; width: 7; height: 7; radius: 3.5; color: modelData } } }
                                        Rectangle { x: 8; y: 26; width: 60; height: 6; radius: 3; color: modelData.id ? "#4A5363" : "#C9D2DE" }
                                        Rectangle { x: 8; y: 38; width: 40; height: 6; radius: 3; color: "#2E6BE6" } }
                            Rectangle { visible: !opcaoModo.auto; x: 120; y: 32; width: 48; height: 64; radius: 8; color: modelData.id ? "#20242C" : "#EEF2F7" }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: aparencia.definirModo(modelData.modo) }
                        }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.nome; color: Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 13; weight: opcaoModo.atual ? Font.Bold : Font.Normal } }
                    }
                }
            }
            Rotulo { width: parent.width; secundario: true
                     text: "Vale para a Barra, a Ilha, as janelas e os aplicativos do DuiaOS na hora. Outros aplicativos podem precisar ser abertos de novo. No Automático, o DuiaOS fica claro de dia e escuro à noite, pela hora do nascer e do pôr do sol na região do fuso horário do computador." }
        }
    }

    // ----------------------------------------------------------- Notificações
    Component {
        id: paginaNotificacoes
        Pagina {
            Grupo {
                Linha { icone: "sino-desligado"; titulo: "Não perturbe"; descricao: "Os avisos não aparecem na tela (só os urgentes), mas ficam no histórico do relógio."
                        Interruptor { ligado: ajustes.naoPerturbe; onAlternado: (v) => ajustes.definirNaoPerturbe(v) } }
                Linha { icone: "sino"; titulo: "Ver como fica"; ultima: true
                        Botao { texto: "Enviar um aviso de teste"; onClicado: ajustes.testarNotificacao() } }
            }
            Rotulo { width: parent.width; secundario: true
                     text: "Os avisos aparecem no canto de cima, à direita, e somem sozinhos. Clique no relógio da Barra de Recursos para ver os de hoje." }
        }
    }

    // ----------------------------------------------------------- Atualizações
    // Selo colorido (código, tipo, importância)
    component Selo: Rectangle {
        property string texto: ""
        property color cor: Tema.azulDuia
        property bool mono: false
        width: textoSelo.implicitWidth + 14; height: 20; radius: 6
        color: Qt.rgba(cor.r, cor.g, cor.b, 0.14)
        Text { id: textoSelo; anchors.centerIn: parent; text: parent.texto; color: parent.cor
               font { family: parent.mono ? Tema.fonteCodigo : Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
    }
    // Ficha de uma atualização do DuiaOS (código DUIA-AAAA-NNNN, ADR 046)
    component FichaAtualizacao: Rectangle {
        id: ficha
        property var f: ({})
        property bool aberta: false
        width: parent ? parent.width : 500
        height: colunaFicha.implicitHeight + 24
        radius: 12
        color: Tema.cartao
        border { color: Tema.borda; width: 1 }
        readonly property color corTipo: ({ seguranca: Tema.erro, correcao: Tema.aviso, novidade: Tema.azulDuia, melhoria: Tema.sucesso })[f.tipo] || Tema.azulDuia
        Column {
            id: colunaFicha
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            spacing: 6
            Row {
                spacing: 6
                Selo { texto: ficha.f.codigo || ""; cor: Tema.azulNoite; mono: true }
                Selo { texto: ficha.f.tipoNome || ""; cor: ficha.corTipo }
                Selo { visible: ficha.f.importancia !== "recomendada"; texto: ficha.f.importanciaNome || ""; cor: ficha.f.importancia === "critica" ? Tema.erro : Tema.aviso }
                Text { anchors.verticalCenter: parent.verticalCenter; text: (ficha.f.data || "").split("-").reverse().join("/")
                       color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11 } }
            }
            Text { width: parent.width; text: ficha.f.titulo || ""; wrapMode: Text.WordWrap; color: Tema.texto
                   font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.Bold } }
            Text { width: parent.width; text: ficha.f.resumo || ""; wrapMode: Text.WordWrap; color: Tema.textoSecundario
                   font { family: Tema.fonteTexto; pixelSize: 12 } }
            Column {
                visible: ficha.aberta
                width: parent.width
                spacing: 8
                topPadding: 4
                Text { width: parent.width; text: (ficha.f.descricao || "").split("\n\n").join("\n\n"); wrapMode: Text.WordWrap
                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } lineHeight: 1.15 }
                Text { text: "Detalhes"; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.Bold } }
                Repeater {
                    model: ficha.f.detalhes || []
                    Row {
                        required property string modelData
                        width: parent.width
                        spacing: 8
                        Text { text: "•"; color: ficha.corTipo; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.Bold } }
                        Text { width: parent.width - 16; text: modelData; wrapMode: Text.WordWrap; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
                    }
                }
                Text { visible: (ficha.f.observacoes || "") !== ""; width: parent.width; text: ficha.f.observacoes || ""; wrapMode: Text.WordWrap
                       color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12; italic: true } }
                Grid {
                    columns: 2; columnSpacing: 10; rowSpacing: 3
                    Text { text: "Pacotes"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11 } }
                    Text { text: (ficha.f.pacotes || []).join(", "); color: Tema.textoSecundario; font { family: Tema.fonteCodigo; pixelSize: 11 } }
                    Text { text: "Depois"; color: Tema.textoApagado; font { family: Tema.fonteTexto; pixelSize: 11 } }
                    Text { text: ficha.f.reiniciarNome || ""; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 11 } }
                }
            }
            Text {
                text: ficha.aberta ? "Esconder detalhes" : "Ver detalhes"
                color: Tema.azulDuia; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold }
                MouseArea { anchors { fill: parent; margins: -6 } cursorShape: Qt.PointingHandCursor; onClicked: ficha.aberta = !ficha.aberta }
            }
        }
    }

    // Duração em texto: 75 → "1 min 15 s"; 3600 → "1 h"
    function duracao(segundos) {
        segundos = Math.max(0, Math.round(segundos))
        var h = Math.floor(segundos / 3600), m = Math.floor((segundos % 3600) / 60), s = segundos % 60
        if (h > 0) return h + " h" + (m > 0 ? " " + m + " min" : "")
        if (m > 0) return m + " min" + (s > 0 && m < 10 ? " " + s + " s" : "")
        return s + " s"
    }
    function relogio(segundos) {
        segundos = Math.max(0, Math.round(segundos))
        var m = Math.floor(segundos / 60), s = segundos % 60
        return m + ":" + (s < 10 ? "0" : "") + s
    }

    // ------------------------------------------------------------------ Armazenamento (ADR 060)
    function bytes(n) {
        n = n || 0
        if (n < 1000) return n + " B"
        var u = ["KB", "MB", "GB", "TB"], i = -1
        do { n /= 1000; i++ } while (n >= 1000 && i < u.length - 1)
        return (n >= 100 || i < 2 ? Math.round(n) : n.toFixed(1).replace(".", ",")) + " " + u[i]
    }
    // Cor de cada parte da barra do disco: tons do azul DuiaOS para o que é da pessoa, cinza para o sistema
    function corDoUso(id) {
        // Cores bem diferentes entre si (azuis para o que é do sistema e dos aplicativos, quentes e vivas para os arquivos)
        return ({ aplicativos: "#5B8CFF", videos: "#2447A8", pictures: "#22D3EE", music: "#A78BFA", documents: "#FACC15",
                  download: "#F472B6", desktop: "#4A76E8", ia: "#2DD4A7", cache: "#F97316", lixeira: "#EF4444",
                  pessoal: "#9AA6C7", sistema: Tema.textoApagado })[id] || Tema.bordaForte
    }

    Component {
        id: paginaArmazenamento
        Pagina {
            id: par
            readonly property var ar: ajustes.armazenamento
            readonly property var lista: ar.lista || ({ tipo: "", itens: [] })
            readonly property var sis: ar.sistema || ({})
            property var marcados: ({})
            readonly property int quantosMarcados: Object.keys(marcados).length
            readonly property real tamanhoMarcado: {
                var t = 0
                for (var i = 0; i < lista.itens.length; i++) if (marcados[lista.itens[i].caminho]) t += lista.itens[i].tamanho
                return t
            }
            function marcar(caminho, sim) { var m = Object.assign({}, marcados); if (sim) m[caminho] = true; else delete m[caminho]; marcados = m }
            function marcarTodos(sim) { var m = {}; if (sim) for (var i = 0; i < lista.itens.length; i++) m[lista.itens[i].caminho] = true; marcados = m }
            onListaChanged: marcados = ({})
            Component.onCompleted: ajustes.medirArmazenamento()
            // Uma limpeza em andamento: aviso com o que está fazendo, o andamento e o tempo (para nunca
            // parecer travado), e os outros botões esperam
            readonly property var trabalho: ar.trabalho || ({})
            readonly property bool ocupado: !!trabalho.texto
            property real agora: Date.now() / 1000
            Timer { interval: 1000; repeat: true; running: par.ocupado; onTriggered: par.agora = Date.now() / 1000 }

            Rectangle {
                id: andamentoLimpeza
                visible: par.ocupado
                width: parent.width
                height: colunaLimpeza.implicitHeight + 24
                radius: 12
                color: Tema.cartao
                border { color: Tema.azulDuia; width: 1 }
                Row {
                    id: colunaLimpeza
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                    spacing: 12
                    Item {
                        width: 30; height: 30
                        anchors.verticalCenter: parent.verticalCenter
                        Rectangle { anchors.fill: parent; radius: 15; color: Tema.destaque }
                        Icone {
                            anchors.centerIn: parent; nome: "reiniciar"; tamanho: 18; cor: Tema.azulDuia
                            RotationAnimator on rotation { from: 0; to: 360; duration: 1100; loops: Animation.Infinite; running: par.ocupado }
                        }
                    }
                    Column {
                        width: parent.width - 42
                        spacing: 6
                        Text {
                            width: parent.width; elide: Text.ElideRight; color: Tema.texto
                            text: (par.trabalho.texto || "")
                                  + (par.trabalho.total > 0 ? "  " + (par.trabalho.feito || 0) + " de " + par.trabalho.total : "")
                            font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold }
                        }
                        // Com total conhecido, a barra enche; sem ele, uma luz corre de um lado ao outro
                        Rectangle {
                            width: parent.width; height: 6; radius: 3; color: Tema.controleDesligado; clip: true
                            Rectangle {
                                visible: par.trabalho.total > 0
                                height: parent.height; radius: 3; color: Tema.azulDuia
                                width: par.trabalho.total > 0 ? Math.max(6, parent.width * (par.trabalho.feito || 0) / par.trabalho.total) : 0
                                Behavior on width { NumberAnimation { duration: 200 } }
                            }
                            Rectangle {
                                id: luzCorrendo
                                visible: !(par.trabalho.total > 0)
                                width: parent.width * 0.3; height: parent.height; radius: 3; color: Tema.azulDuia
                                NumberAnimation on x { from: -luzCorrendo.width; to: luzCorrendo.parent.width; duration: 1300
                                                        loops: Animation.Infinite; running: par.ocupado && !(par.trabalho.total > 0) }
                            }
                        }
                        Text {
                            color: Tema.textoSecundario
                            text: "Há " + Math.max(0, Math.round(par.agora - (par.trabalho.inicio || par.agora))) + " s · pode continuar usando o computador"
                            font { family: Tema.fonteTexto; pixelSize: 12 }
                        }
                    }
                }
            }

            // ================= visão geral (some enquanto uma lista está aberta)
            Destaque {
                visible: par.lista.tipo === ""
                icone: "disco"; estilo: par.ar.dispositivos.length && par.sis.total && par.sis.livre / par.sis.total < 0.1 ? "noite" : "azul"
                titulo: par.sis.total ? janela.bytes(par.sis.livre) + " livres no disco do sistema" : (par.ar.carregando ? "Medindo o armazenamento…" : "Armazenamento")
                texto: par.sis.total ? janela.bytes(par.sis.usado) + " usados de " + janela.bytes(par.sis.total)
                                       + (par.ar.carregando ? ". Medindo o que ocupa cada parte…" : ". Veja abaixo o que ocupa espaço e o que dá para liberar.")
                                     : "Os discos deste computador, o que ocupa espaço e o que dá para liberar."
            }

            // Barra do disco do sistema, dividida pelo que ocupa, com o espaço livre no fim. A escala é a
            // maior entre o tamanho do disco e (partes + livre): se as medidas somarem mais que o usado, nenhuma
            // parte é cortada no fim da barra (antes só as primeiras apareciam; 16/11)
            readonly property real somaUso: { var t = 0; for (var i = 0; i < ar.uso.length; i++) t += ar.uso[i].tamanho; return t }
            readonly property real escalaBarra: Math.max(sis.total || 1, (ar.uso.length ? somaUso : (sis.usado || 0)) + (sis.livre || 0))
            Column {
                visible: par.lista.tipo === "" && !!par.sis.total
                width: parent.width
                spacing: 10
                Rectangle {
                    id: barraDisco
                    width: parent.width; height: 22; radius: 11; clip: true
                    color: Tema.controleDesligado
                    // Partes visíveis: as menores que 4 px ganham 4 px (tiradas do livre), para nenhuma sumir
                    readonly property var larguras: {
                        var w = width - (par.ar.uso.length - 1) * 2, lista = [], usado = 0
                        for (var i = 0; i < par.ar.uso.length; i++) {
                            var l = w * par.ar.uso[i].tamanho / par.escalaBarra
                            if (par.ar.uso[i].tamanho > 0) l = Math.max(4, l)
                            lista.push(l); usado += l
                        }
                        return lista
                    }
                    Row {
                        anchors { top: parent.top; bottom: parent.bottom; left: parent.left }
                        spacing: 2                                   // fresta entre as partes
                        Repeater {
                            model: par.ar.uso
                            Rectangle {
                                required property var modelData
                                required property int index
                                height: parent.height
                                width: barraDisco.larguras[index] || 0
                                color: janela.corDoUso(modelData.id)
                            }
                        }
                        // Enquanto mede, só o usado em tom neutro
                        Rectangle { visible: par.ar.uso.length === 0; height: parent.height
                                    width: barraDisco.width * (par.sis.usado || 0) / par.escalaBarra; color: Tema.bordaForte }
                    }
                }
                Flow {
                    width: parent.width
                    spacing: 14
                    Repeater {
                        model: par.ar.uso
                        Row {
                            required property var modelData
                            spacing: 6
                            Rectangle { width: 9; height: 9; radius: 4.5; anchors.verticalCenter: parent.verticalCenter; color: janela.corDoUso(modelData.id) }
                            Text { text: modelData.nome + "  " + janela.bytes(modelData.tamanho); color: Tema.textoSecundario
                                   font { family: Tema.fonteTexto; pixelSize: 12 } }
                        }
                    }
                    Row {
                        spacing: 6
                        Rectangle { width: 9; height: 9; radius: 4.5; anchors.verticalCenter: parent.verticalCenter
                                    color: Tema.controleDesligado; border { color: Tema.bordaForte; width: 1 } }
                        Text { text: "Livre  " + janela.bytes(par.sis.livre); color: Tema.texto
                               font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } }
                    }
                }
            }

            // Recomendações
            Grupo {
                visible: par.lista.tipo === "" && par.ar.recomendacoes.length > 0
                titulo: "Liberar espaço"
                Repeater {
                    model: par.ar.recomendacoes
                    Linha {
                        required property var modelData
                        required property int index
                        icone: ({ lixeira: "lixeira", caches: "reiniciar", antigos: "download", grandes: "arquivo", flatpak: "aplicativos",
                                  duplicados: "copiar", apt: "sacola", registros: "documento" })[modelData.id] || "disco"
                        titulo: modelData.titulo + (modelData.tamanho > 0 ? " · " + janela.bytes(modelData.tamanho) : "")
                        descricao: modelData.texto
                        ultima: index === par.ar.recomendacoes.length - 1
                        Botao { texto: modelData.acao; tipo: modelData.acao === "Revisar" || modelData.acao === "Procurar" ? "secundario" : "primario"
                                ativo: !par.ocupado
                                onClicado: ajustes.limparRecomendacao(modelData.id) }
                    }
                }
            }

            // Arquivos por tipo
            Grupo {
                visible: par.lista.tipo === ""
                titulo: "Gerenciar por tipo"
                Repeater {
                    model: [{ id: "videos", nome: "Vídeos", icone: "video" }, { id: "imagens", nome: "Imagens", icone: "imagem" },
                            { id: "musica", nome: "Música e áudio", icone: "musica" }, { id: "documentos", nome: "Documentos", icone: "documento" },
                            { id: "compactados", nome: "Arquivos compactados", icone: "compactado" },
                            { id: "instaladores", nome: "Instaladores e imagens de disco", icone: "sacola" },
                            { id: "copias", nome: "Cópias de segurança", icone: "escudo" },
                            { id: "grandes", nome: "Arquivos grandes (qualquer tipo)", icone: "arquivo" },
                            { id: "duplicados", nome: "Arquivos repetidos", icone: "copiar" },
                            { id: "programas", nome: "Aplicativos instalados", icone: "aplicativos" }]
                    Linha {
                        required property var modelData
                        required property int index
                        icone: modelData.icone; titulo: modelData.nome; clicavel: true
                        ultima: index === 9
                        onClicada: ajustes.listarArmazenamento(modelData.id)
                        Icone { nome: "seta-direita"; tamanho: 14; cor: Tema.textoApagado }
                    }
                }
            }

            // Dispositivos
            Grupo {
                visible: par.lista.tipo === "" && par.ar.dispositivos.length > 0
                titulo: "Discos e dispositivos"
                Repeater {
                    model: par.ar.dispositivos
                    Linha {
                        required property var modelData
                        required property int index
                        icone: modelData.removivel ? "ejetar" : "disco"
                        titulo: modelData.nome + (modelData.total ? " · " + janela.bytes(modelData.total) : "")
                        descricao: (modelData.montado ? janela.bytes(modelData.livre) + " livres de " + janela.bytes(modelData.total)
                                                       + (modelData.nivel === "cheio" ? " · disco cheio" : (modelData.nivel === "pouco" ? " · pouco espaço" : ""))
                                                     : "Não está aberto neste sistema")
                                   + (modelData.modelo ? " · " + modelData.modelo : "")
                        ultima: index === par.ar.dispositivos.length - 1
                        Rectangle {
                            visible: !!modelData.montado
                            width: 140; height: 8; radius: 4; color: Tema.controleDesligado
                            anchors.verticalCenter: parent ? parent.verticalCenter : undefined
                            Rectangle { height: parent.height; radius: 4
                                        width: modelData.total ? parent.width * modelData.usado / modelData.total : 0
                                        color: modelData.nivel === "cheio" ? Tema.erro : (modelData.nivel === "pouco" ? Tema.aviso : Tema.azulDuia) }
                        }
                    }
                }
            }

            Row {
                visible: par.lista.tipo === ""
                spacing: 8
                Botao { texto: par.ar.carregando ? "Medindo…" : "Medir de novo"; icone: "reiniciar"; ativo: !par.ar.carregando && !par.ocupado
                        onClicado: ajustes.medirArmazenamento() }
            }

            // ================= lista para escolher o que apagar
            Row {
                visible: par.lista.tipo !== ""
                width: parent.width
                spacing: 12
                Botao { texto: "Voltar"; icone: "seta-esquerda"; onClicado: ajustes.listarArmazenamento("") }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - 120
                    Titulo { nivel: 2; text: par.lista.titulo || "" }
                    Rotulo { secundario: true; width: parent.width
                             text: par.lista.carregando ? "Procurando na sua pasta pessoal…"
                                 : (par.lista.itens.length === 0 ? "Nada encontrado."
                                 : par.lista.itens.length + (par.lista.itens.length === 1 ? " item" : " itens") + ", do maior para o menor"
                                   + (par.lista.tipo === "programas" ? ". Para remover um aplicativo, abra-o na Duia App Store."
                                      : (par.lista.tipo === "caches" ? ". Os aplicativos refazem esses arquivos quando precisarem."
                                         : ". O que você marcar vai para a Lixeira."))) }
                }
            }
            Grupo {
                visible: par.lista.tipo !== "" && par.lista.itens.length > 0
                Linha {
                    visible: par.lista.tipo !== "programas"
                    titulo: par.quantosMarcados ? par.quantosMarcados + (par.quantosMarcados === 1 ? " marcado" : " marcados") + " · " + janela.bytes(par.tamanhoMarcado)
                                                : "Marque o que quer apagar"
                    Botao { texto: par.quantosMarcados === par.lista.itens.length ? "Desmarcar todos" : "Marcar todos"
                            onClicado: par.marcarTodos(par.quantosMarcados !== par.lista.itens.length) }
                    Botao { texto: par.lista.tipo === "caches" ? "Apagar" : "Mover para a Lixeira"; tipo: "perigo"; ativo: par.quantosMarcados > 0 && !par.ocupado
                            onClicado: { ajustes.apagarDoArmazenamento(par.lista.tipo, Object.keys(par.marcados)); ajustes.listarArmazenamento("") } }
                }
                Repeater {
                    model: par.lista.itens
                    Linha {
                        id: itemLista
                        required property var modelData
                        required property int index
                        readonly property bool marcado: !!par.marcados[modelData.caminho]
                        titulo: modelData.nome + " · " + janela.bytes(modelData.tamanho)
                        descricao: modelData.detalhe || modelData.pasta || ""
                        clicavel: par.lista.tipo !== "programas"
                        ultima: index === par.lista.itens.length - 1
                        onClicada: par.marcar(modelData.caminho, !marcado)
                        // Caixa de marcar
                        Rectangle {
                            visible: par.lista.tipo !== "programas"
                            width: 20; height: 20; radius: 6
                            color: itemLista.marcado ? Tema.azulDuia : "transparent"
                            border { color: itemLista.marcado ? Tema.azulDuia : Tema.bordaForte; width: 1.5 }
                            Icone { anchors.centerIn: parent; visible: itemLista.marcado; nome: "check"; tamanho: 13; cor: "#FFFFFF" }
                        }
                        BotaoIcone { visible: par.lista.tipo !== "programas" && par.lista.tipo !== "caches"; icone: "pasta"
                                     onClicado: ajustes.mostrarNoExplorador(modelData.pasta || "") }
                        Botao { visible: par.lista.tipo === "programas"; texto: "Abrir na loja"; onClicado: ajustes.abrirNaLoja(modelData.caminho) }
                    }
                }
            }
        }
    }

    Component {
        id: paginaAtualizacoes
        Pagina {
            id: pa
            readonly property var a: ajustes.atualizacao
            property bool verHistorico: false
            property bool verRegistros: false
            property real agora: Date.now() / 1000
            Timer { interval: 1000; running: pa.a.etapa === "atualizando"; repeat: true; onTriggered: pa.agora = Date.now() / 1000 }
            readonly property real decorrido: pa.a.inicio ? Math.max(0, pa.agora - pa.a.inicio) : 0
            // Quanto falta: pela previsão do plano e pelo andamento, o que for maior
            readonly property real restante: {
                var porPrevisao = (pa.a.estimativa || 0) - pa.decorrido
                var f = pa.a.fracao || 0
                var porAndamento = f > 0.08 ? pa.decorrido * (1 - f) / f : porPrevisao
                return Math.max(porPrevisao, porAndamento)
            }
            Component.onCompleted: ajustes.acompanharAgente()

            Destaque { icone: "reiniciar"; titulo: ({ inicio: "Atualizações do sistema", procurando: "Procurando atualizações…",
                                                       pronta: pa.a.quantidade + (pa.a.quantidade === 1 ? " pacote para atualizar" : " pacotes para atualizar"),
                                                       "em-dia": "O sistema está em dia", atualizando: "Atualizando o sistema",
                                                       concluida: "Sistema atualizado", erro: "A atualização não terminou" })[pa.a.etapa] || "Atualizações do sistema"
                       texto: pa.a.etapa === "pronta" ? "Download de " + pa.a.baixar + " · tempo previsto: cerca de " + janela.duracao(pa.a.estimativa || 60)
                                + " · " + pa.a.reiniciarNome
                                + (pa.a.quantidadeSeguranca > 0 ? " · " + pa.a.quantidadeSeguranca + (pa.a.quantidadeSeguranca === 1 ? " correção de segurança" : " correções de segurança") : "")
                              : (pa.a.etapa === "atualizando" ? "Você pode continuar usando o computador. Não desligue até terminar."
                              : (pa.a.mensagem || "O DuiaOS, o Wise e os aplicativos instalados recebem correções e novidades por aqui.")) }

            // ------------------------------------------------ atualização automática (ADR 058)
            Grupo {
                titulo: "Atualização automática"
                Linha {
                    icone: "atualizacao"; titulo: "Quando houver atualizações"
                    descricao: ajustes.explicacaoAtualizacaoAutomatica
                    ultima: true
                    Seletor { width: 300
                              opcoes: [{ valor: "desativado", rotulo: "Desativada" },
                                       { valor: "avisar", rotulo: "Só avisar" },
                                       { valor: "baixar", rotulo: "Avisar e baixar" },
                                       { valor: "instalar-avisando", rotulo: "Avisar, baixar e instalar" },
                                       { valor: "instalar", rotulo: "Baixar e instalar sem avisar" }]
                              valor: ajustes.atualizacaoAutomatica
                              onEscolhido: (v) => ajustes.definirAtualizacaoAutomatica(v) }
                }
            }

            // ------------------------------------------------ andamento ao vivo
            Rectangle {
                visible: pa.a.etapa === "atualizando" || pa.a.etapa === "procurando"
                width: parent.width
                height: colunaAndamento.implicitHeight + 28
                radius: 12
                color: Tema.cartao
                border { color: Tema.borda; width: 1 }
                Column {
                    id: colunaAndamento
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
                    spacing: 10
                    Row {
                        spacing: 12
                        width: parent.width
                        // Sinal de que está trabalhando: gira o tempo todo
                        Item {
                            width: 34; height: 34
                            Rectangle { anchors.fill: parent; radius: 17; color: Tema.destaque }
                            Icone {
                                anchors.centerIn: parent; nome: "reiniciar"; tamanho: 20; cor: Tema.azulDuia
                                RotationAnimator on rotation { from: 0; to: 360; duration: 1200; loops: Animation.Infinite; running: true }
                            }
                        }
                        Column {
                            width: parent.width - 46
                            anchors.verticalCenter: parent.verticalCenter
                            Text { width: parent.width; elide: Text.ElideRight; color: Tema.texto
                                   text: pa.a.etapa === "procurando" ? (pa.a.mensagem || "Procurando…") : (pa.a.etapaAtual || "Instalando")
                                   font { family: Tema.fonteTexto; pixelSize: 14; weight: Font.Bold } }
                            Text { width: parent.width; elide: Text.ElideRight; color: Tema.textoSecundario; visible: pa.a.etapa === "atualizando"
                                   text: pa.a.mensagem || ""; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        }
                    }
                    Rectangle {
                        width: parent.width; height: 8; radius: 4; color: Tema.controleDesligado
                        clip: true
                        Rectangle { visible: pa.a.etapa === "atualizando"; width: parent.width * Math.max(0.02, pa.a.fracao || 0); height: parent.height; radius: 4; color: Tema.azulDuia
                                    Behavior on width { NumberAnimation { duration: 400 } } }
                        // Procurando: faixa que corre de um lado ao outro (sem porcentagem conhecida)
                        Rectangle {
                            visible: pa.a.etapa === "procurando"
                            width: parent.width * 0.3; height: parent.height; radius: 4; color: Tema.azulDuia
                            NumberAnimation on x { from: -parent.width * 0.3; to: parent.width; duration: 1400; loops: Animation.Infinite; running: pa.a.etapa === "procurando" }
                        }
                    }
                    Row {
                        visible: pa.a.etapa === "atualizando"
                        width: parent.width
                        spacing: 18
                        Text { text: "Decorrido " + janela.relogio(pa.decorrido); color: Tema.texto; font { family: Tema.fonteCodigo; pixelSize: 12 } }
                        Text { text: Math.round((pa.a.fracao || 0) * 100) + "%"; color: Tema.texto; font { family: Tema.fonteCodigo; pixelSize: 12 } }
                        Text { color: pa.decorrido > (pa.a.estimativa || 0) * 1.5 && pa.a.estimativa > 0 ? Tema.aviso : Tema.textoSecundario
                               text: pa.restante > 20 ? "Faltam cerca de " + janela.duracao(pa.restante)
                                     : (pa.decorrido > (pa.a.estimativa || 0) ? "Demorando mais que o previsto" : "Quase lá")
                               font { family: Tema.fonteTexto; pixelSize: 12 } }
                    }
                    Rectangle {
                        visible: (pa.a.alerta || "") !== "" && pa.a.etapa === "atualizando"
                        width: parent.width
                        height: textoAlerta.implicitHeight + 16
                        radius: 8
                        color: Qt.rgba(0.91, 0.64, 0.24, 0.16)
                        border { color: Tema.aviso; width: 1 }
                        Text { id: textoAlerta; anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
                               text: pa.a.alerta || ""; wrapMode: Text.WordWrap; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
                    }
                    Row {
                        visible: pa.a.etapa === "atualizando"
                        spacing: 8
                        Botao { texto: "Ver o que está acontecendo"; icone: "documento"; visible: (pa.a.registro || "") !== ""
                                onClicado: ajustes.abrirRegistro(pa.a.registro) }
                        Botao { texto: "Cancelar"; onClicado: ajustes.cancelarAtualizacao() }
                    }
                }
            }

            // ------------------------------------------------ resultado
            Rectangle {
                visible: pa.a.etapa === "concluida" || pa.a.etapa === "erro"
                width: parent.width
                height: colunaResultado.implicitHeight + 24
                radius: 12
                color: pa.a.etapa === "erro" ? Qt.rgba(0.85, 0.33, 0.31, 0.10) : Qt.rgba(0.18, 0.65, 0.48, 0.10)
                border { color: pa.a.etapa === "erro" ? Tema.erro : Tema.sucesso; width: 1 }
                Column {
                    id: colunaResultado
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                    spacing: 6
                    Text { width: parent.width; wrapMode: Text.WordWrap; color: Tema.texto; text: pa.a.mensagem || ""
                           font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                    Text { visible: (pa.a.duracao || 0) > 0; text: "Levou " + janela.duracao(pa.a.duracao || 0)
                           color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
                    Botao { visible: (pa.a.registro || "") !== ""; texto: "Ver registro"; icone: "documento"; onClicado: ajustes.abrirRegistro(pa.a.registro) }
                }
            }

            Row {
                spacing: 8
                Botao { visible: ["inicio", "em-dia", "concluida", "erro"].indexOf(pa.a.etapa) >= 0; texto: "Procurar atualizações"; tipo: "primario"
                        onClicado: ajustes.procurarAtualizacoes() }
                Botao { visible: pa.a.etapa === "pronta"; texto: "Atualizar agora"; tipo: "primario"; onClicado: ajustes.atualizarAgora() }
                Botao { texto: pa.verHistorico ? "Esconder o histórico" : "Histórico"; icone: "relogio"; onClicado: pa.verHistorico = !pa.verHistorico }
                Botao { texto: pa.verRegistros ? "Esconder os registros" : "Registros"; icone: "documento"
                        onClicado: { pa.verRegistros = !pa.verRegistros; if (pa.verRegistros) ajustes.listarRegistros() } }
            }

            // Registros: a saída completa de cada atualização
            Grupo {
                visible: pa.verRegistros
                titulo: "Registros das atualizações"
                Linha { visible: ajustes.registros.length === 0; titulo: "Nenhuma atualização registrada ainda."; ultima: true }
                Repeater {
                    model: pa.verRegistros ? ajustes.registros : []
                    Linha {
                        required property var modelData
                        required property int index
                        icone: modelData.resultado === "ok" ? "check" : (modelData.resultado === "cancelada" ? "fechar" : "info")
                        titulo: new Date(modelData.quando * 1000).toLocaleString(Qt.locale("pt_BR"), "dd/MM/yyyy HH:mm")
                                + "  ·  " + ({ ok: "Concluída", erro: "Com erro", recusada: "Recusada", cancelada: "Cancelada", interrompida: "Interrompida" })[modelData.resultado]
                                + (modelData.duracao_s ? "  ·  " + janela.duracao(modelData.duracao_s) : "")
                        descricao: modelData.mensagem
                        ultima: index === ajustes.registros.length - 1
                        Botao { texto: "Abrir"; height: 28; visible: (modelData.nome || "") !== ""; onClicado: ajustes.abrirRegistro(modelData.nome) }
                    }
                }
            }

            // Do DuiaOS: uma ficha por atualização
            Titulo { nivel: 3; visible: pa.a.etapa === "pronta" && (pa.a.duiaos || []).length > 0
                     text: "Do DuiaOS (" + (pa.a.duiaos || []).length + ")" }
            Repeater { model: pa.a.etapa === "pronta" ? (pa.a.duiaos || []) : []
                       FichaAtualizacao { required property var modelData; required property int index; f: modelData; aberta: ajustes.demonstracao && index === 0 } }
            Rotulo { visible: pa.a.etapa === "pronta" && (pa.a.duiaosSemFicha || []).length > 0; width: parent.width; secundario: true
                     text: "Outros pacotes do DuiaOS nesta atualização: " + (pa.a.duiaosSemFicha || []).join(", ") }

            // Do Debian: pacote a pacote
            Titulo { nivel: 3; visible: pa.a.etapa === "pronta" && (pa.a.debian || []).length > 0
                     text: "Do Debian (" + (pa.a.debian || []).length + ")" }
            Grupo {
                visible: pa.a.etapa === "pronta" && (pa.a.debian || []).length > 0
                Repeater {
                    model: pa.a.etapa === "pronta" ? (pa.a.debian || []).slice(0, 80) : []
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData.pacote + (modelData.seguranca ? "   ·   Segurança" : "")
                        descricao: (modelData.descricao !== "" ? modelData.descricao + "\n" : "") + (modelData.de !== "" ? modelData.de + "  →  " : "novo  ·  ") + modelData.para
                        ultima: index === Math.min(79, pa.a.debian.length - 1)
                        Icone { visible: modelData.seguranca; nome: "escudo"; tamanho: 16; cor: Tema.erro; anchors.verticalCenter: parent.verticalCenter }
                        Botao { texto: "O que mudou"; height: 28; onClicado: ajustes.verMudancas(modelData.pacote) }
                    }
                }
            }
            Rotulo { visible: pa.a.etapa === "pronta" && (pa.a.debian || []).length > 80; width: parent.width; secundario: true
                     text: "E mais " + ((pa.a.debian || []).length - 80) + " pacotes." }

            // Aplicativos do Flathub: atualizam pela Duia App Store
            Grupo {
                visible: ajustes.atualizacoesFlathub > 0
                Linha {
                    icone: "sacola"; ultima: true
                    titulo: ajustes.atualizacoesFlathub === 1 ? "1 aplicativo do Flathub tem versão nova" : ajustes.atualizacoesFlathub + " aplicativos do Flathub têm versão nova"
                    descricao: "Eles se atualizam pela Duia App Store, sem senha."
                    Botao { texto: "Abrir a loja"; height: 28; onClicado: ajustes.abrirLojaAtualizacoes() }
                }
            }

            // Histórico: fichas já instaladas neste computador
            Titulo { nivel: 3; visible: pa.verHistorico; text: "Instaladas neste computador" }
            Rotulo { visible: pa.verHistorico && ajustes.historicoAtualizacoes.length === 0; secundario: true; text: "Nenhuma ficha de atualização instalada ainda." }
            Repeater { model: pa.verHistorico ? ajustes.historicoAtualizacoes : []; FichaAtualizacao { required property var modelData; f: modelData } }

            Rotulo { width: parent.width; secundario: true
                     text: "Quem atualiza é o agente do sistema: ele confere o que vai mudar, não remove nada essencial, conclui sozinho uma instalação que ficou pela metade e, se uma etapa ficar parada por 30 minutos, interrompe essa etapa, repara o sistema e mostra o motivo aqui. Também dá para pedir ao Wise: “atualiza o sistema”." }
        }
    }

    // Registro completo de uma atualização (ao vivo enquanto ela roda)
    Rectangle {
        anchors.fill: parent
        z: 56
        visible: ajustes.registroAberto.titulo !== undefined
        color: Qt.rgba(0.06, 0.09, 0.14, 0.35)
        MouseArea { anchors.fill: parent; onClicked: ajustes.fecharRegistro() }
        Timer {
            interval: 2000; repeat: true
            running: parent.visible && ajustes.atualizacao.etapa === "atualizando" && ajustes.registroAberto.nome === ajustes.atualizacao.registro
            onTriggered: ajustes.abrirRegistro(ajustes.registroAberto.nome)
        }
        Cartao {
            anchors.centerIn: parent
            width: Math.min(parent.width - 60, 820); height: Math.min(parent.height - 60, 560)
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Titulo { id: tituloLog; x: 20; y: 16; nivel: 2; text: ajustes.registroAberto.titulo || "" }
            Flickable {
                id: rolarLog
                anchors { left: parent.left; right: parent.right; top: tituloLog.bottom; bottom: fecharLog.top; margins: 20; topMargin: 12 }
                contentHeight: textoLog.height
                clip: true
                onContentHeightChanged: if (ajustes.atualizacao.etapa === "atualizando") contentY = Math.max(0, contentHeight - height)
                TextEdit { id: textoLog; width: parent.width; readOnly: true; selectByMouse: true; wrapMode: Text.Wrap
                           text: ajustes.registroAberto.texto || ""; color: Tema.texto; font { family: Tema.fonteCodigo; pixelSize: 11 } }
            }
            Botao { id: fecharLog; anchors { right: parent.right; bottom: parent.bottom; margins: 16 } texto: "Fechar"; onClicado: ajustes.fecharRegistro() }
        }
    }

    // Registro de mudanças de um pacote do Debian (Configurações › Atualizações › O que mudou)
    Rectangle {
        anchors.fill: parent
        z: 55
        visible: ajustes.registroDeMudancas.pacote !== undefined
        color: Qt.rgba(0.06, 0.09, 0.14, 0.35)
        MouseArea { anchors.fill: parent; onClicked: ajustes.fecharMudancas() }
        Cartao {
            anchors.centerIn: parent
            width: Math.min(parent.width - 80, 720); height: Math.min(parent.height - 80, 520)
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Titulo { id: tituloRegistro; x: 20; y: 16; nivel: 2; text: "O que mudou em " + (ajustes.registroDeMudancas.pacote || "") }
            Flickable {
                anchors { left: parent.left; right: parent.right; top: tituloRegistro.bottom; bottom: fecharRegistro.top; margins: 20; topMargin: 12 }
                contentHeight: textoRegistro.height
                clip: true
                TextEdit { id: textoRegistro; width: parent.width; readOnly: true; selectByMouse: true; wrapMode: Text.Wrap
                           text: ajustes.registroDeMudancas.texto || ""; color: Tema.texto; font { family: Tema.fonteCodigo; pixelSize: 12 } }
            }
            Botao { id: fecharRegistro; anchors { right: parent.right; bottom: parent.bottom; margins: 16 } texto: "Fechar"; onClicado: ajustes.fecharMudancas() }
        }
    }

    // ----------------------------------------------------------- Barra e Ilha
    Component {
        id: paginaBarra
        Pagina {
            Grupo {
                titulo: "Barra de Recursos"
                Linha {
                    icone: "barra"; titulo: "Posição na tela"; ultima: true
                    Seletor { width: 180
                              opcoes: [{ valor: "topo", rotulo: "No alto" }, { valor: "base", rotulo: "Embaixo" }, { valor: "esquerda", rotulo: "À esquerda" }, { valor: "direita", rotulo: "À direita" }]
                              valor: ajustes.posicaoBarra; onEscolhido: (v) => ajustes.definirPosicaoBarra(v) }
                }
            }
            Grupo {
                titulo: "Ícones da Barra (os 4 primeiros ficam à vista; os outros, no balão da seta)"
                Repeater {
                    model: ajustes.ordemIcones
                    Linha {
                        required property string modelData
                        required property int index
                        icone: ({ wise: "ia", wifi: "wifi-3", som: "som-2", bateria: "bateria", bluetooth: "bluetooth", brilho: "brilho", luz: "lua" })[modelData] || "ponto"
                        titulo: ({ wise: "Wise", wifi: "Wi-Fi", som: "Som", bateria: "Bateria", bluetooth: "Bluetooth", brilho: "Brilho", luz: "Luz noturna" })[modelData] || modelData
                        descricao: index < 4 ? "À vista" : "No balão"
                        ultima: index === ajustes.ordemIcones.length - 1
                        function mover(delta) {
                            var o = ajustes.ordemIcones.slice()
                            var j = index + delta
                            if (j < 0 || j >= o.length) return
                            var t = o[index]; o[index] = o[j]; o[j] = t
                            ajustes.definirOrdemIcones(o)
                        }
                        BotaoIcone { icone: "seta-cima"; ativo: index > 0; onClicado: parent.parent.mover(-1) }
                        BotaoIcone { icone: "seta-baixo"; ativo: index < ajustes.ordemIcones.length - 1; onClicado: parent.parent.mover(1) }
                    }
                }
            }
            Grupo {
                id: grupoIlha
                titulo: "Ilha de Aplicativos"
                readonly property var o: ajustes.opcoesIlha
                Linha {
                    icone: "aplicativos"; titulo: "Tamanho"; descricao: grupoIlha.o.tamanho + " pontos"
                    Deslizante { width: 200; anchors.verticalCenter: parent.verticalCenter
                                 valor: (grupoIlha.o.tamanho - 32) / 48 * 100
                                 onMovido: (v) => ajustes.definirOpcaoIlha("tamanho", Math.round(32 + v / 100 * 48)) }
                }
                Linha {
                    icone: "busca"; titulo: "Ampliação"; descricao: "Os ícones crescem quando o mouse passa por cima"
                    Interruptor { ligado: grupoIlha.o.ampliacao; onAlternado: (l) => ajustes.definirOpcaoIlha("ampliacao", l ? "sim" : "nao") }
                }
                Linha {
                    visible: grupoIlha.o.ampliacao
                    icone: "mais"; titulo: "Tamanho da ampliação"; descricao: grupoIlha.o.tamanho_ampliado + " pontos"
                    Deslizante { width: 200; anchors.verticalCenter: parent.verticalCenter
                                 valor: (grupoIlha.o.tamanho_ampliado - 32) / 96 * 100
                                 onMovido: (v) => ajustes.definirOpcaoIlha("tamanho_ampliado", Math.round(32 + v / 100 * 96)) }
                }
                Linha {
                    icone: "barra"; titulo: "Posição na tela"
                    Seletor { width: 180
                              opcoes: [{ valor: "base", rotulo: "Embaixo" }, { valor: "esquerda", rotulo: "À esquerda" }, { valor: "direita", rotulo: "À direita" }]
                              valor: grupoIlha.o.posicao; onEscolhido: (v) => ajustes.definirOpcaoIlha("posicao", v) }
                }
                Linha {
                    icone: "seta-baixo"; titulo: "Efeito ao minimizar"; descricao: "Botão amarelo da janela ou Super + M"
                    Seletor { width: 180
                              opcoes: [{ valor: "genio", rotulo: "Gênio" }, { valor: "escala", rotulo: "Escala (suave)" }, { valor: "nenhum", rotulo: "Nenhum" }]
                              valor: grupoIlha.o.minimizar; onEscolhido: (v) => ajustes.definirOpcaoIlha("minimizar", v) }
                }
                Linha {
                    icone: "olho"; titulo: "Ocultar e mostrar automaticamente"; descricao: "Aparece quando o mouse encosta na borda da tela"
                    Interruptor { ligado: grupoIlha.o.ocultar; onAlternado: (l) => ajustes.definirOpcaoIlha("ocultar", l ? "sim" : "nao") }
                }
                Linha {
                    icone: "ponto"; titulo: "Mostrar indicadores dos aplicativos abertos"
                    Interruptor { ligado: grupoIlha.o.indicadores; onAlternado: (l) => ajustes.definirOpcaoIlha("indicadores", l ? "sim" : "nao") }
                }
                Linha {
                    icone: "seta-cima"; titulo: "Animar ao abrir aplicativos"; descricao: "O ícone pula enquanto o aplicativo abre"
                    Interruptor { ligado: grupoIlha.o.animar_abrir; onAlternado: (l) => ajustes.definirOpcaoIlha("animar_abrir", l ? "sim" : "nao") }
                }
                Linha {
                    icone: "recentes"; titulo: "Mostrar aplicativos recentes"; descricao: "Até 3 aplicativos usados há pouco, depois dos fixados"
                    Interruptor { ligado: grupoIlha.o.recentes; onAlternado: (l) => ajustes.definirOpcaoIlha("recentes", l ? "sim" : "nao") }
                }
                Linha {
                    icone: "monitor"; titulo: "Clicar no aplicativo da frente minimiza a janela"; descricao: "Como na barra de tarefas do Windows"
                    Interruptor { ligado: grupoIlha.o.clique_minimiza; onAlternado: (l) => ajustes.definirOpcaoIlha("clique_minimiza", l ? "sim" : "nao") }
                }
                Linha { icone: "estrela"; titulo: "Manter, tirar e reordenar aplicativos"; ultima: true
                        descricao: "Botão direito no ícone: Manter na Ilha ou Tirar da Ilha. Arraste um ícone para mudar a ordem, ou para fora da Ilha para tirá-lo. Botão direito no fundo da Ilha: atalhos destas opções." }
            }
        }
    }

    // --------------------------------------------------------------- Usuário
    Component {
        id: paginaUsuario
        Pagina {
            Row {
                spacing: 16
                Rectangle {
                    width: 88; height: 88; radius: 44
                    gradient: Gradient { GradientStop { position: 0; color: "#6FA0F7" } GradientStop { position: 1; color: "#1A3A73" } }
                    Image { id: fotoGrande; anchors.fill: parent; source: ajustes.fotoConta; sourceSize: Qt.size(176, 176); visible: status === Image.Ready; cache: false }
                    Text { visible: !fotoGrande.visible; anchors.centerIn: parent; text: ajustes.usuario.nome.charAt(0).toUpperCase(); color: "white"
                           font { family: Tema.fonteTitulo; pixelSize: 38; weight: Font.Bold } }
                }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    Titulo { nivel: 2; text: ajustes.usuario.nome }
                    Row {
                        spacing: 8
                        Botao { texto: "Escolher foto…"; tipo: "primario"; onClicado: escolherFoto.open() }
                        Repeater {
                            model: ["#2E6BE6", "#1A3A73", "#2FA67A", "#E8A33D", "#D9534F", "#8E5BD9"]
                            Rectangle { required property string modelData; width: 28; height: 28; radius: 14; color: modelData
                                        anchors.verticalCenter: parent.verticalCenter
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: ajustes.definirFoto(modelData) } }
                        }
                    }
                    Rotulo { secundario: true; text: "A foto aparece na Tela de Entrada, na Tela de Bloqueio e aqui." }
                }
            }
            Grupo {
                Linha {
                    icone: "usuario"; titulo: "Nome"; descricao: "Aparece na Tela de Entrada e no Menu do DuiaOS"
                    Campo { id: campoNome; width: 220; texto: ajustes.usuario.nome }
                    Botao { texto: "Salvar"; onClicado: ajustes.definirNome(campoNome.texto) }
                }
                Linha { titulo: "Usuário"; descricao: "Nome de acesso (não muda)"; ultima: true
                        Text { anchors.verticalCenter: parent.verticalCenter; text: ajustes.usuario.usuario; color: Tema.textoSecundario; font { family: Tema.fonteCodigo; pixelSize: 13 } } }
            }
            Grupo {
                titulo: "Trocar a senha"
                Linha { titulo: "Senha atual"; Campo { id: senhaAtual; width: 240; senha: true } }
                Linha { titulo: "Senha nova"; descricao: "Pelo menos 6 caracteres"; Campo { id: senhaNova; width: 240; senha: true } }
                Linha { titulo: "Repita a senha nova"; ultima: true; Campo { id: senhaRepetida; width: 240; senha: true } }
            }
            Botao {
                texto: "Trocar a senha"; tipo: "primario"
                ativo: senhaAtual.texto !== "" && senhaNova.texto !== ""
                onClicado: { ajustes.trocarSenha(senhaAtual.texto, senhaNova.texto, senhaRepetida.texto); senhaAtual.texto = ""; senhaNova.texto = ""; senhaRepetida.texto = "" }
            }
        }
    }

    // ----------------------------------------------------------- Data e hora
    Component {
        id: paginaData
        Pagina {
            id: pd
            property date agora: new Date()
            Timer { interval: 1000; running: true; repeat: true; onTriggered: pd.agora = new Date() }
            Grupo {
                Linha {
                    icone: "relogio"; titulo: "Agora"
                    Text { anchors.verticalCenter: parent.verticalCenter
                           text: pd.agora.toLocaleDateString(Qt.locale("pt_BR"), "dddd, d 'de' MMMM") + "  ·  " + pd.agora.toLocaleTimeString(Qt.locale("pt_BR"), "HH:mm")
                           color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                }
                Linha { titulo: "Acertar automaticamente"; descricao: "Pela internet"
                        Interruptor { ligado: ajustes.data.automatica; onAlternado: (v) => ajustes.definirHoraAutomatica(v) } }
                Linha {
                    icone: "globo"; titulo: "Fuso horário"; ultima: true
                    Seletor { width: 260; vazio: ajustes.data.fuso || "Escolher"
                              opcoes: ajustes.fusos.map(function (f) { return { valor: f, rotulo: f.replace(/_/g, " ").replace("/", " › ") } })
                              valor: ajustes.data.fuso; onEscolhido: (v) => ajustes.definirFuso(v) }
                }
            }
        }
    }

    // ------------------------------------------------------ Idioma e teclado
    Component {
        id: paginaTeclado
        Pagina {
            Grupo {
                Linha { icone: "globo"; titulo: "Idioma do sistema"; descricao: "Português do Brasil"; ultima: true }
            }
            Grupo {
                titulo: "Teclado"
                Linha {
                    icone: "teclado"; titulo: "Tipo de teclado"; descricao: "A troca vale a partir da próxima entrada"; ultima: true
                    Seletor { width: 300
                              opcoes: Object.keys(controles.layouts).map(function (k) { return { valor: k, rotulo: controles.layouts[k] } })
                              valor: controles.teclado; onEscolhido: (v) => ajustes.definirTeclado(v) }
                }
            }
            Grupo {
                titulo: "Atalhos do DuiaOS"
                Repeater {
                    model: [["Super + Espaço", "Central de Aplicativos"], ["Super + W", "Wise"], ["Super + L", "Bloquear a tela"], ["Ctrl + Alt + Delete", "Menu de Energia"],
                            ["Alt + Tab", "Trocar de janela"], ["Ctrl + C · Ctrl + X · Ctrl + V", "Copiar, recortar e colar"]]
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData[1]; ultima: index === 5
                        Text { anchors.verticalCenter: parent.verticalCenter; text: modelData[0]; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } }
                    }
                }
            }
        }
    }

    // ---------------------------------------------------- Aplicativos padrão
    Component {
        id: paginaPadroes
        Pagina {
            Grupo {
                Repeater {
                    model: ajustes.categoriasPadrao
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData.nome
                        ultima: index === ajustes.categoriasPadrao.length - 1
                        Seletor {
                            width: 260
                            vazio: (ajustes.appsPorCategoria[modelData.id] || []).length === 0 ? "Nenhum instalado" : "Escolher"
                            opcoes: (ajustes.appsPorCategoria[modelData.id] || []).map(function (a) { return { valor: a.id, rotulo: a.nome } })
                            valor: ajustes.padroes[modelData.id] || ""
                            onEscolhido: (v) => ajustes.definirPadrao(modelData.id, v)
                        }
                    }
                }
            }
        }
    }

    // ----------------------------------------------------------- Privacidade
    Component {
        id: paginaPrivacidade
        Pagina {
            Destaque { icone: "escudo"; titulo: "Ajude a melhorar o DuiaOS"
                       texto: "Você escolhe se o computador envia relatórios de erros e de uso, sempre somados e sem dados pessoais. Nada sai antes da sua escolha." }
            Botao { texto: "Abrir “Ajude a melhorar o DuiaOS”"; tipo: "primario"; onClicado: ajustes.abrirApp("ajude-a-melhorar") }
            Grupo {
                titulo: "Permissões do Wise"
                visible: ajustes.wise
                Linha { icone: "ia"; titulo: "O Wise pede a sua aprovação"; descricao: "Antes de enviar, apagar, pagar, instalar ou confirmar qualquer coisa por você."; ultima: true }
            }
        }
    }

    // ---------------------------------------------- Inteligência artificial
    // ------------------------------------------------ Inteligência Artificial (ADR 063)
    // Etiqueta pequena (Em uso, Padrão, Livre…)
    component Etiqueta: Rectangle {
        property string texto: ""
        property color cor: Tema.azulDuia
        width: textoEtiqueta.implicitWidth + 14; height: 20; radius: 10
        color: Qt.rgba(cor.r, cor.g, cor.b, 0.14)
        Text { id: textoEtiqueta; anchors.centerIn: parent; text: parent.texto; color: parent.cor
               font { family: Tema.fonteTexto; pixelSize: 11; weight: Font.DemiBold } }
    }
    // Barra de andamento fina
    component Andamento: Rectangle {
        property real fracao: 0
        height: 6; radius: 3; color: Tema.controleDesligado
        Rectangle { height: parent.height; radius: 3; color: Tema.azulDuia; width: parent.width * Math.max(0.02, Math.min(1, parent.fracao))
                    Behavior on width { NumberAnimation { duration: 250 } } }
    }
    function gb(bytes) { return ((bytes || 0) / 1073741824).toFixed(1).replace(".", ",") + " GB" }
    function nomeDoModelo(id) {
        var fs = ia.estado.familias || []
        for (var i = 0; i < fs.length; i++) for (var j = 0; j < fs[i].modelos.length; j++) if (fs[i].modelos[j].id === id) return janela.rotuloDoModelo(fs[i].modelos[j])
        return id || ""
    }
    function rotuloDoModelo(m) { return (m.familia || "") + " " + (m.tamanho || "") }

    Component {
        id: paginaIa
        Pagina {
            id: pia
            readonly property var e: ia.estado
            readonly property var tarefa: e.tarefa || null
            property bool verCatalogo: false
            property string chaveAberta: ""           // motor com o campo de chave aberto
            Component.onCompleted: ia.abrir()
            readonly property var instalados: {
                var lista = [], fs = e.familias || []
                for (var i = 0; i < fs.length; i++) for (var j = 0; j < fs[i].modelos.length; j++) if (fs[i].modelos[j].instalado) lista.push(fs[i].modelos[j])
                return lista
            }

            Destaque { icone: "ia"; estilo: "noite"; titulo: "A IA do DuiaOS"
                       texto: "A IA local roda neste computador e é a mesma para todos os programas. Se quiser, ligue também motores na nuvem com a sua chave." }

            // ============================== IA local
            Grupo {
                titulo: "IA local · neste computador"
                Linha {
                    icone: "computador"
                    titulo: !ia.servicoOk ? "O serviço de IA não respondeu" : (pia.e.ativo ? janela.nomeDoModelo(pia.e.ativo) : "Nenhum modelo em uso")
                    descricao: !ia.servicoOk ? "Reinicie o computador; se continuar, envie um relatório ao suporte."
                             : (!pia.e.ollama ? "O motor de IA local não está rodando."
                             : (pia.e.pausado ? "Pausada: fora da memória até você retomar ou abrir o Wise."
                             : (pia.e.calibrando ? "Ajustando ao seu computador (só na primeira vez)…"
                             : (!pia.e.ativo ? "Escolha um modelo abaixo." : (pia.e.carregado ? "Em uso · pronta na memória" : "Em uso · carregando na memória…")))))
                    ultima: !pia.tarefa
                    Botao { visible: ia.servicoOk && !!pia.e.ativo; texto: pia.e.pausado ? "Retomar" : "Pausar"
                            onClicado: ia.pausar(!pia.e.pausado) }
                }
                // Download em andamento
                Linha {
                    visible: !!pia.tarefa
                    icone: "download"
                    titulo: pia.tarefa ? "Baixando " + janela.nomeDoModelo(pia.tarefa.modelo) : ""
                    descricao: pia.tarefa ? janela.gb(pia.tarefa.concluido) + " de " + janela.gb(pia.tarefa.total) + " · " + Math.round((pia.tarefa.fracao || 0) * 100) + "%" : ""
                    ultima: true
                    Andamento { width: 150; anchors.verticalCenter: parent.verticalCenter; fracao: pia.tarefa ? pia.tarefa.fracao || 0 : 0 }
                    Botao { texto: "Cancelar"; onClicado: ia.cancelar() }
                }
            }

            Grupo {
                visible: pia.instalados.length > 0
                titulo: "Modelos neste computador"
                Repeater {
                    model: pia.instalados
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: janela.rotuloDoModelo(modelData)
                        descricao: modelData.descricao + " · ocupa " + String(modelData.download_gb).replace(".", ",") + " GB"
                        ultima: index === pia.instalados.length - 1
                        Etiqueta { visible: modelData.ativo; texto: "Em uso"; cor: Tema.sucesso; anchors.verticalCenter: parent.verticalCenter }
                        Botao { visible: !modelData.ativo; texto: "Usar"; tipo: "primario"; ativo: modelData.cabe; onClicado: ia.usar(modelData.id) }
                        Botao { visible: !modelData.ativo; texto: "Remover"; onClicado: ia.remover(modelData.id) }
                    }
                }
            }

            Botao { visible: ia.servicoOk; texto: pia.verCatalogo ? "Esconder o catálogo" : "Baixar outros modelos"
                    icone: pia.verCatalogo ? "seta-cima" : "download"; onClicado: pia.verCatalogo = !pia.verCatalogo }
            Rotulo { visible: pia.verCatalogo; width: parent.width; secundario: true
                     text: "Este computador tem " + String(pia.e.memoria_gb || 0).replace(".", ",") + " GB de memória. Modelos maiores respondem melhor, mas são mais lentos; os que não cabem na memória aparecem desativados." }
            Repeater {
                model: pia.verCatalogo ? (pia.e.familias || []) : []
                Grupo {
                    id: grupoFamilia
                    required property var modelData
                    readonly property var faltam: modelData.modelos.filter(function (m) { return !m.instalado })
                    visible: faltam.length > 0
                    titulo: modelData.nome + " · " + (modelData.autor || "")
                    Repeater {
                        model: grupoFamilia.faltam
                        Linha {
                            required property var modelData
                            required property int index
                            titulo: janela.rotuloDoModelo(modelData)
                            descricao: modelData.descricao + " · download de " + String(modelData.download_gb).replace(".", ",") + " GB · usa "
                                       + String(modelData.memoria_gb).replace(".", ",") + " GB de memória"
                                       + (modelData.aviso ? "\n" + modelData.aviso : "")
                                       + (modelData.licenca && !modelData.licenca.livre ? "\nLicença: " + modelData.licenca.nome + " (não é livre)" : "")
                            ultima: index === grupoFamilia.faltam.length - 1
                            opacity: modelData.cabe ? 1 : 0.55
                            Etiqueta { visible: modelData.padrao; texto: "Recomendado"; anchors.verticalCenter: parent.verticalCenter }
                            Botao { texto: "Baixar"; ativo: modelData.cabe && !pia.tarefa; onClicado: ia.baixar(modelData.id) }
                        }
                    }
                }
            }

            // ============================== IA na nuvem
            Repeater {
                model: ia.motores
                Grupo {
                    id: grupoMotor
                    required property var modelData
                    required property int index
                    readonly property var m: modelData
                    readonly property bool editando: pia.chaveAberta === m.id || !m.tem_chave
                    titulo: index === 0 ? "IA na nuvem · com a sua chave" : ""
                    Linha {
                        icone: "globo"
                        titulo: m.titulo
                        descricao: m.esperando && m.ocupado ? m.ocupado
                                 : (m.ativado && m.tem_chave ? "Ligado · " + (m.modelos.length ? m.modelos.length + " modelos disponíveis" : "atualize a lista de modelos")
                                 : (m.tem_chave ? "Desligado: nada é enviado para a " + m.empresa + "." : "Sem chave: cole a sua para ligar."))
                        Interruptor { ligado: m.ativado && m.tem_chave; opacity: m.tem_chave ? 1 : 0.4
                                      onAlternado: (v) => { if (m.tem_chave) ia.ativarMotor(m.id, v) } }
                    }
                    Linha {
                        visible: m.ativado || !m.tem_chave
                        titulo: "Privacidade"
                        descricao: m.aviso + " Desligado, nada sai do computador."
                    }
                    Linha {
                        icone: "cadeado"
                        titulo: "Chave"
                        descricao: grupoMotor.editando ? "Crie a chave no site da " + m.empresa + " e cole aqui. Ela fica no cofre do sistema, nunca em arquivo."
                                                       : "Guardada no cofre do sistema."
                        ultima: !grupoMotor.editando && !(m.tem_chave && m.ativado) && m.mensagem === ""
                        Botao { visible: grupoMotor.editando; texto: "Criar chave"; icone: "abrir"; onClicado: ia.abrirEndereco(m.chave_em) }
                        Botao { visible: !grupoMotor.editando; texto: "Trocar"; onClicado: pia.chaveAberta = m.id }
                        Botao { visible: !grupoMotor.editando; texto: "Remover"; ativo: !m.esperando; onClicado: ia.removerChave(m.id) }
                    }
                    Item {
                        visible: grupoMotor.editando
                        width: parent.width; height: 52
                        Campo { id: campoChave; anchors { left: parent.left; leftMargin: 14; right: botoesChave.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                dica: "Colar a chave de " + m.titulo; senha: true
                                onConfirmado: if (texto.length > 7) { ia.salvarChave(m.id, texto); texto = ""; pia.chaveAberta = "" } }
                        Row {
                            id: botoesChave
                            anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                            spacing: 8
                            Botao { texto: m.esperando ? "Conferindo…" : "Salvar e conferir"; tipo: "primario"; ativo: campoChave.texto.length > 7 && !m.esperando
                                    onClicado: { ia.salvarChave(m.id, campoChave.texto); campoChave.texto = ""; pia.chaveAberta = "" } }
                            Botao { visible: m.tem_chave; texto: "Cancelar"; onClicado: { campoChave.texto = ""; pia.chaveAberta = "" } }
                        }
                        Rectangle { anchors { left: parent.left; leftMargin: 14; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda
                                    visible: m.mensagem !== "" || (m.tem_chave && m.ativado) }
                    }
                    Linha {
                        visible: m.tem_chave && m.ativado
                        icone: "lista"
                        titulo: "Modelo preferido"
                        descricao: "O que os programas usam quando escolhem este motor."
                        ultima: m.mensagem === ""
                        Seletor { width: 220; opcoes: m.modelos.map(function (x) { return { valor: x, rotulo: x } }); valor: m.modelo
                                  vazio: "Nenhum modelo"; onEscolhido: (v) => ia.modeloDoMotor(m.id, v) }
                        BotaoIcone { icone: "reiniciar"; onClicado: ia.atualizarModelos(m.id) }
                    }
                    Linha { visible: m.mensagem !== ""; icone: "info"; titulo: m.mensagem; ultima: true }
                }
            }

            Grupo {
                visible: ia.wiseInstalado
                Linha { icone: "wise"; titulo: "Wise"; descricao: "Motor e modelo padrão, voz, agenda, previsão do tempo e o que o Wise pode fazer."
                        clicavel: true; ultima: true; onClicada: ajustes.irPara("wise")
                        Icone { nome: "seta-direita"; tamanho: 14; cor: Tema.textoApagado } }
            }
        }
    }

    // ------------------------------------------------------------------ Wise (ADR 063)
    Component {
        id: paginaWise
        Pagina {
            id: pw
            readonly property var w: ia.wise
            readonly property var voz: w.voz || ({ vozes: [], pacotes: {}, baixando: {} })
            readonly property var motorPadrao: {
                var ms = w.motores || []
                for (var i = 0; i < ms.length; i++) if (ms[i].id === w.motor_padrao) return ms[i]
                return ({ id: "local", modelos: [], modelo: "" })
            }
            readonly property bool temNuvem: (w.motores || []).some(function (m) { return m.nuvem })
            property bool verCalDav: false
            function baixando(item) { return pw.voz.baixando && pw.voz.baixando[item] !== undefined }
            function mb(bytes) { return Math.round((bytes || 0) / 1000000) + " MB" }
            Component.onCompleted: ia.abrir()

            Destaque { icone: "wise"; estilo: "azul"
                       titulo: !ia.wiseInstalado ? "O Wise não está instalado" : (ia.wiseLigado ? "Wise ligado" : "Wise desligado")
                       texto: !ia.wiseInstalado ? "Instale o Wise pelas Atualizações para usar o assistente do DuiaOS."
                            : (ia.wiseLigado ? "O assistente do DuiaOS. Abra com Super + W, pelo rosto no canto da tela ou pela barra do alto."
                                             : "Desligado, o Wise e a IA local ficam fora da memória. Ligue para mudar as preferências.") }
            Row {
                visible: ia.wiseInstalado
                spacing: 8
                Botao { texto: ia.wiseLigado ? "Abrir o Wise" : "Ligar o Wise"; tipo: "primario"; icone: "wise"; onClicado: ia.abrirWise() }
                Botao { visible: ia.wiseLigado; texto: "Desligar o Wise"; icone: "energia"; onClicado: ia.desligarWise() }
            }

            // ============================== motor e modelo
            Grupo {
                visible: ia.wiseLigado
                titulo: "Motor e modelo padrão"
                Linha {
                    icone: "ia"; titulo: "Motor"
                    descricao: "O que o Wise usa ao abrir. Na janela dele dá para trocar só para aquela conversa."
                    Seletor { width: 220; valor: pw.w.motor_padrao || "local"
                              opcoes: (pw.w.motores || []).map(function (m) { return { valor: m.id, rotulo: m.id === "local" ? "Local (neste computador)" : m.titulo } })
                              onEscolhido: (v) => ia.definirWise("motor_padrao", v) }
                }
                Linha {
                    icone: "lista"; titulo: "Modelo"
                    descricao: pw.w.motor_padrao === "local" ? "O modelo local é o do sistema, igual para todos os programas."
                                                             : "O modelo preferido deste motor."
                    ultima: !(pw.w.motor_padrao === "local" && pw.temNuvem)
                    Text { visible: pw.w.motor_padrao === "local"; anchors.verticalCenter: parent.verticalCenter
                           text: janela.nomeDoModelo(pw.motorPadrao.modelo) || "Nenhum"; color: Tema.textoSecundario
                           font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                    Text { visible: pw.w.motor_padrao !== "local"; anchors.verticalCenter: parent.verticalCenter
                           text: pw.motorPadrao.modelo || "Nenhum"; color: Tema.textoSecundario
                           font { family: Tema.fonteTexto; pixelSize: 13; weight: Font.DemiBold } }
                    Botao { texto: "Trocar"; onClicado: ajustes.irPara("ia") }
                }
                Linha {
                    visible: pw.w.motor_padrao === "local" && pw.temNuvem
                    icone: "globo"; titulo: "Usar a nuvem quando a IA local não estiver pronta"
                    descricao: "Enquanto o modelo local baixa ou carrega, o Wise responde por um motor na nuvem ligado."
                    ultima: true
                    Interruptor { ligado: pw.w.reserva_na_nuvem === true; onAlternado: (v) => ia.definirWise("reserva_na_nuvem", v ? "sim" : "nao") }
                }
            }
            Rotulo { visible: ia.wiseLigado && !pw.temNuvem; width: parent.width; secundario: true
                     text: "Para usar o Gemini ou a OpenAI no Wise, ligue o motor e cole a chave em Inteligência Artificial." }

            // ============================== voz
            Grupo {
                visible: ia.wiseLigado
                titulo: "Voz"
                Linha {
                    visible: !pw.voz.disponivel
                    icone: "som-mudo"; titulo: "A voz do sistema não está instalada"
                    descricao: "Instale as atualizações do DuiaOS para o Wise falar e ouvir."; ultima: true
                }
                Linha {
                    visible: !!pw.voz.disponivel
                    icone: "som-2"; titulo: "Respostas faladas"
                    descricao: "O Wise fala a resposta enquanto escreve. Tudo é feito neste computador."
                    Interruptor { ligado: pw.voz.falar_respostas === true; onAlternado: (v) => ia.definirWise("falar_respostas", v ? "sim" : "nao") }
                }
                Repeater {
                    model: pw.voz.disponivel ? pw.voz.vozes : []
                    Linha {
                        required property var modelData
                        required property int index
                        readonly property bool escolhida: pw.voz.voz === modelData.id
                        readonly property bool descendo: pw.baixando(modelData.pacote)
                        icone: escolhida ? "check" : ""
                        titulo: modelData.nome
                        descricao: descendo ? "Baixando… " + Math.round((pw.voz.baixando[modelData.pacote] || 0) * 100) + "%"
                                 : (modelData.instalada ? (escolhida ? "A voz do Wise" : "Instalada") : "Download de " + pw.mb(modelData.tamanho))
                        clicavel: modelData.instalada && !escolhida
                        onClicada: ia.definirWise("voz", modelData.id)
                        Andamento { visible: descendo; width: 120; anchors.verticalCenter: parent.verticalCenter; fracao: pw.voz.baixando[modelData.pacote] || 0 }
                        Botao { visible: !modelData.instalada && !descendo; texto: "Baixar"; onClicado: ia.acaoWise("baixar_voz", { item: modelData.id }) }
                        Botao { visible: modelData.instalada && !escolhida; texto: "Usar"; onClicado: ia.definirWise("voz", modelData.id) }
                    }
                }
                Linha {
                    visible: !!pw.voz.disponivel
                    icone: "relogio"; titulo: "Velocidade da fala"
                    Segmentos { opcoes: [{ valor: "0.88", rotulo: "Devagar" }, { valor: "1.00", rotulo: "Normal" }, { valor: "1.15", rotulo: "Rápida" }]
                                valor: (pw.voz.velocidade || 1) < 0.95 ? "0.88" : ((pw.voz.velocidade || 1) > 1.07 ? "1.15" : "1.00")
                                onEscolhido: (v) => ia.definirWise("velocidade_da_voz", v) }
                    Botao { texto: "Ouvir"; icone: "som-2"; onClicado: ia.acaoWise("testar_voz", {}) }
                }
                Linha {
                    visible: !!pw.voz.disponivel
                    readonly property var p: pw.voz.pacotes["ouvir"] || ({})
                    icone: "microfone"; titulo: "Falar com o Wise"
                    descricao: pw.baixando("ouvir") ? "Baixando… " + Math.round((pw.voz.baixando["ouvir"] || 0) * 100) + "%"
                             : (p.instalado ? "Ligado: clique no microfone da janela do Wise e fale. O áudio não sai do computador."
                                            : (pw.voz.reconhecimento === "whisper"
                                               ? "Há um reconhecimento novo, bem mais preciso (download de " + pw.mb(p.tamanho) + ")."
                                               : "O Wise entende o que você fala (download de " + pw.mb(p.tamanho) + ")."))
                    Andamento { visible: pw.baixando("ouvir"); width: 120; anchors.verticalCenter: parent.verticalCenter; fracao: pw.voz.baixando["ouvir"] || 0 }
                    Botao { visible: !parent.parent.p.instalado && !pw.baixando("ouvir"); texto: "Baixar"; tipo: "primario"; onClicado: ia.acaoWise("baixar_voz", { item: "ouvir" }) }
                    Botao { visible: !!parent.parent.p.instalado; texto: "Remover"; onClicado: ia.acaoWise("remover_voz", { item: "ouvir" }) }
                }
                // Teste do microfone: o Wise ouve uma frase e mostra o que entendeu (não vai para a conversa)
                Linha {
                    id: linhaTesteMicrofone
                    visible: !!pw.voz.disponivel && !!(pw.voz.pacotes["ouvir"] || {}).instalado
                    readonly property var t: pw.voz.teste_microfone || ({})
                    icone: "microfone"; titulo: "Testar o microfone"
                    descricao: t.estado === "ouvindo" ? "Pode falar: diga uma frase qualquer."
                             : t.estado === "transcrevendo" ? "Entendendo…"
                             : t.estado === "baixando" ? "Preparando o reconhecimento de fala…"
                             : t.estado === "pronto" ? (t.texto ? "Entendi: \u201c" + t.texto + "\u201d" : (t.motivo || "Não ouvi nada."))
                             : "Fale uma frase e veja o que o Wise entende."
                    ultima: (pw.voz.mensagem || "") === ""
                    // Nível do microfone enquanto ouve
                    Rectangle {
                        visible: linhaTesteMicrofone.t.estado === "ouvindo"
                        width: 90; height: 6; radius: 3; color: Tema.controleDesligado
                        anchors.verticalCenter: parent.verticalCenter
                        Rectangle { height: parent.height; radius: 3; color: Tema.azulDuia
                                    width: parent.width * Math.min(1, linhaTesteMicrofone.t.nivel || 0)
                                    Behavior on width { NumberAnimation { duration: 90 } } }
                    }
                    Botao { visible: linhaTesteMicrofone.t.estado !== "ouvindo" && linhaTesteMicrofone.t.estado !== "transcrevendo"
                            texto: linhaTesteMicrofone.t.estado === "pronto" ? "Testar de novo" : "Testar"; icone: "microfone"
                            onClicado: ia.acaoWise("testar_microfone", {}) }
                }
                Linha { visible: (pw.voz.mensagem || "") !== ""; icone: "info"; titulo: pw.voz.mensagem || ""; ultima: true }
            }

            // ============================== saudação
            Grupo {
                visible: ia.wiseLigado
                titulo: "Ao entrar na sessão"
                Linha {
                    icone: "sino"; titulo: "Saudação"
                    descricao: ({ escrita: "Um balão ao lado do rosto do Wise.", fala: "O Wise cumprimenta em voz alta.",
                                  fala_e_escrita: "O balão e a voz.", desativada: "O Wise fica quieto no canto." })[pw.w.saudacao] || ""
                    ultima: true
                    Seletor { width: 180; valor: pw.w.saudacao || "escrita"
                              opcoes: [{ valor: "escrita", rotulo: "Escrita" }, { valor: "fala", rotulo: "Falada" },
                                       { valor: "fala_e_escrita", rotulo: "Falada e escrita" }, { valor: "desativada", rotulo: "Desativada" }]
                              onEscolhido: (v) => ia.definirWise("saudacao", v) }
                    Botao { texto: "Ver agora"; onClicado: ia.acaoWise("testar_saudacao", {}) }
                }
            }

            // ============================== previsão do tempo
            Grupo {
                visible: ia.wiseLigado
                titulo: "Previsão do tempo"
                Linha {
                    icone: "globo"; titulo: pw.w.cidade ? pw.w.cidade : "Nenhuma cidade escolhida"
                    descricao: "A previsão vem do Instituto Meteorológico da Noruega; só a posição da cidade sai do computador."
                    Botao { visible: !!pw.w.cidade; texto: "Esquecer"; onClicado: ia.acaoWise("esquecer_cidade", {}) }
                }
                Item {
                    width: parent.width; height: 52
                    Campo { id: campoCidade; anchors { left: parent.left; leftMargin: 14; right: botaoCidade.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            dica: "Cidade, estado"; icone: "busca"
                            onConfirmado: if (texto.length > 1) ia.acaoWise("definir_cidade", { texto: texto, escolha: 0 }) }
                    Botao { id: botaoCidade; anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                            texto: "Procurar"; tipo: "primario"; ativo: campoCidade.texto.length > 1
                            onClicado: ia.acaoWise("definir_cidade", { texto: campoCidade.texto, escolha: 0 }) }
                }
                Linha { visible: (pw.w.cidade_mensagem || "") !== ""; titulo: pw.w.cidade_mensagem || ""; ultima: (pw.w.cidade_opcoes || []).length === 0 }
                Repeater {
                    model: pw.w.cidade_opcoes || []
                    Linha {
                        required property string modelData
                        required property int index
                        titulo: modelData; clicavel: true; ultima: index === (pw.w.cidade_opcoes || []).length - 1
                        onClicada: ia.acaoWise("definir_cidade", { texto: campoCidade.texto, escolha: index + 1 })
                        Icone { nome: "seta-direita"; tamanho: 14; cor: Tema.textoApagado }
                    }
                }
            }

            // ============================== agenda
            Grupo {
                visible: ia.wiseLigado
                titulo: "Agenda"
                Linha { icone: "recentes"; titulo: "Agenda do computador"; descricao: "Sempre ligada. Conecte outras para o Wise ver tudo junto. Senhas e acessos ficam no cofre e nunca passam pela IA." }
                Repeater {
                    model: pw.w.contas_agenda || []
                    Linha {
                        required property var modelData
                        titulo: modelData.nome; descricao: modelData.tipo
                        Botao { texto: "Remover"; onClicado: ia.acaoWise("remover_conta_agenda", { "id": modelData.id }) }
                    }
                }
                Linha {
                    titulo: "Conectar uma conta"
                    descricao: (pw.w.login_google && pw.w.login_microsoft) ? "O navegador abre para você entrar e autorizar."
                             : "O login com Google e Microsoft ainda não está configurado neste DuiaOS: use o link .ics abaixo."
                    Botao { texto: "Google"; ativo: pw.w.login_google === true && !pw.w.agenda_ocupada; onClicado: ia.acaoWise("conectar_agenda", { provedor: "google" }) }
                    Botao { texto: "Outlook / Teams"; ativo: pw.w.login_microsoft === true && !pw.w.agenda_ocupada; onClicado: ia.acaoWise("conectar_agenda", { provedor: "microsoft" }) }
                }
                Linha { titulo: "Link .ics (só leitura)"; descricao: "No Google: Configurações da agenda › Endereço secreto em formato iCal." }
                Item {
                    width: parent.width; height: 52
                    Campo { id: campoLinkNome; anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter } width: 170; dica: "Nome" }
                    Campo { id: campoLink; anchors { left: campoLinkNome.right; leftMargin: 8; right: botaoLink.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            dica: "https://… ou webcal://…"; senha: true }
                    Botao { id: botaoLink; anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                            texto: "Adicionar"; ativo: campoLink.texto.length > 10 && !pw.w.agenda_ocupada
                            onClicado: { ia.acaoWise("adicionar_link_agenda", { nome: campoLinkNome.texto, url: campoLink.texto }); campoLink.texto = "" } }
                    Rectangle { anchors { left: parent.left; leftMargin: 14; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda }
                }
                Linha { titulo: "CalDAV"; descricao: "iCloud, Nextcloud e provedores próprios."; clicavel: true; onClicada: pw.verCalDav = !pw.verCalDav
                        ultima: !pw.verCalDav && (pw.w.agenda_mensagem || "") === ""
                        Icone { nome: pw.verCalDav ? "seta-cima" : "seta-baixo"; tamanho: 14; cor: Tema.textoApagado } }
                Item {
                    visible: pw.verCalDav
                    width: parent.width; height: 100
                    Grid {
                        anchors { left: parent.left; right: parent.right; margins: 14; verticalCenter: parent.verticalCenter }
                        columns: 2; spacing: 8
                        Campo { id: davNome; width: (parent.width - 8) / 2; dica: "Nome (ex.: iCloud)" }
                        Campo { id: davUrl; width: (parent.width - 8) / 2; dica: "Servidor (https://caldav.icloud.com)" }
                        Campo { id: davUsuario; width: (parent.width - 8) / 2; dica: "Usuário ou e-mail" }
                        Row {
                            width: (parent.width - 8) / 2; spacing: 8
                            Campo { id: davSenha; width: parent.width - botaoDav.width - 8; dica: "Senha de aplicativo"; senha: true }
                            Botao { id: botaoDav; texto: "Conectar"; tipo: "primario"
                                    ativo: davUrl.texto.length > 8 && davUsuario.texto.length > 0 && davSenha.texto.length > 0 && !pw.w.agenda_ocupada
                                    onClicado: { ia.acaoWise("adicionar_caldav", { nome: davNome.texto, url: davUrl.texto, usuario: davUsuario.texto, senha: davSenha.texto }); davSenha.texto = "" } }
                        }
                    }
                }
                Linha { visible: (pw.w.agenda_mensagem || "") !== ""; icone: "info"; titulo: pw.w.agenda_mensagem || ""; ultima: true
                        Botao { visible: pw.w.agenda_ocupada === true; texto: "Cancelar"; onClicado: ia.acaoWise("cancelar_conexao_agenda", {}) } }
            }

            // ============================== usar o computador
            Grupo {
                visible: ia.wiseLigado
                titulo: "Usar o computador"
                Linha {
                    icone: "escudo"; titulo: "Pedir aprovação para toda ação na tela"
                    descricao: "Desligado, o Wise só pede aprovação quando a ação envia, apaga, paga, instala ou confirma algo. Ligado, pede para cada clique e cada texto digitado. Tudo fica registrado."
                    Interruptor { ligado: pw.w.aprovar_toda_acao === true; onAlternado: (v) => ia.definirWise("aprovar_toda_acao", v ? "sim" : "nao") }
                }
                Linha { icone: "teclado"; titulo: "Abrir e fechar o Wise"; ultima: true
                        Text { anchors.verticalCenter: parent.verticalCenter; text: "Super + W"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } } }
            }
            Rotulo { visible: ia.wiseLigado; secundario: true; width: parent.width
                     text: "Wise " + (pw.w.versao || "") + " · Previsão do tempo: MET Norway (CC BY 4.0). Busca de cidades: © colaboradores do OpenStreetMap (ODbL)." }
        }
    }

    // ---------------------------------------------------------------- Sobre
    Component {
        id: paginaSobre
        Pagina {
            Row {
                spacing: 18
                Simbolo { width: 64; height: 64 }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    Titulo { text: ajustes.sobre.sistema || "DuiaOS" }
                    Rotulo { secundario: true; text: "Baseado no Debian 13 · com o Wise" }
                }
            }
            Grupo {
                Linha { icone: "computador"; titulo: "Nome do computador"; descricao: "Como ele aparece na rede"
                        Campo { id: nomePc; width: 180; texto: ajustes.sobre.computador || "" }
                        Botao { texto: "Salvar"; onClicado: ajustes.definirNomeComputador(nomePc.texto) } }
                Repeater {
                    model: [["Processador", ajustes.sobre.processador], ["Memória", ajustes.sobre.memoria], ["Gráficos", ajustes.sobre.graficos],
                            ["Disco", ajustes.sobre.disco], ["Versão do Linux", (ajustes.sobre.nucleo || "") + " · " + (ajustes.sobre.arquitetura || "")]]
                    Linha {
                        required property var modelData
                        required property int index
                        titulo: modelData[0]; ultima: index === 4
                        Text { anchors.verticalCenter: parent.verticalCenter; width: Math.min(implicitWidth, 380); elide: Text.ElideRight
                               text: modelData[1] || "—"; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 13 } }
                    }
                }
            }
            Grupo {
                Linha { icone: "documento"; titulo: "Contrato de licença (EULA)"; clicavel: true; onClicada: Qt.openUrlExternally("file:///usr/share/duiaos/licenca/EULA.md")
                        Icone { nome: "seta-direita"; tamanho: 14; cor: Tema.textoApagado } }
                Linha { icone: "documento"; titulo: "Licenças de terceiros"; clicavel: true; ultima: true; onClicada: Qt.openUrlExternally("file:///usr/share/duiaos/licenca/LICENCAS-DE-TERCEIROS.md")
                        Icone { nome: "seta-direita"; tamanho: 14; cor: Tema.textoApagado } }
            }
        }
    }

    // ============================================== lista de opções (Seletor)
    Item {
        id: escolha
        anchors.fill: parent
        visible: false
        z: 50
        property var opcoes: []
        property string atual: ""
        property var aoEscolher: null
        property string filtro: ""   // não pode se chamar "busca": é o id do campo de busca da lateral
        function abrir(lista, valor, funcao, x, y, largura) {
            escolha.opcoes = lista; escolha.atual = valor; escolha.aoEscolher = funcao; escolha.filtro = ""
            cartaoEscolha.width = Math.max(largura, 220)
            cartaoEscolha.x = Math.min(x, janela.width - cartaoEscolha.width - 8)
            cartaoEscolha.y = Math.min(y, janela.height - cartaoEscolha.height - 8)
            visible = true
            if (lista.length > 12) campoEscolha.entrada.forceActiveFocus()
            for (var i = 0; i < lista.length; i++) if (lista[i].valor === valor) listaEscolha.positionViewAtIndex(i, ListView.Center)
        }
        readonly property var filtradas: filtro === "" ? opcoes : opcoes.filter(function (o) { return o.rotulo.toLowerCase().indexOf(escolha.filtro.toLowerCase()) >= 0 })
        MouseArea { anchors.fill: parent; onClicked: escolha.visible = false }
        Cartao {
            id: cartaoEscolha
            height: Math.min(360, listaEscolha.contentHeight + (campoEscolha.visible ? 52 : 12))
            raio: 10
            cor: Tema.cartao
            MouseArea { anchors.fill: parent }
            Campo {
                id: campoEscolha
                visible: escolha.opcoes.length > 12
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
                icone: "busca"; dica: "Buscar"
                entrada.onTextChanged: escolha.filtro = texto
                onVisibleChanged: texto = ""
            }
            ListView {
                id: listaEscolha
                anchors { left: parent.left; right: parent.right; top: campoEscolha.visible ? campoEscolha.bottom : parent.top; bottom: parent.bottom; margins: 6 }
                clip: true
                model: escolha.filtradas
                boundsBehavior: Flickable.StopAtBounds
                delegate: ItemDeMenu {
                    required property var modelData
                    width: listaEscolha.width
                    texto: modelData.rotulo
                    icone: modelData.valor === escolha.atual ? "check" : ""
                    onClicado: { escolha.visible = false; if (escolha.aoEscolher) escolha.aoEscolher(modelData.valor) }
                }
            }
        }
    }

    Aviso { id: aviso; anchors { horizontalCenter: conteudo.horizontalCenter; bottom: parent.bottom; bottomMargin: 20 } z: 60 }

    // "Manter estas configurações de rede?" — se ninguém responder, a anterior volta (rede_interface.py, ADR 069)
    Rectangle {
        anchors.fill: parent
        z: 70
        visible: rede.confirmando > 0
        color: Qt.rgba(0.06, 0.09, 0.14, 0.28)
        MouseArea { anchors.fill: parent }
        Cartao {
            anchors.centerIn: parent
            width: 420; height: colunaConfirmar.implicitHeight + 40
            raio: 18; cor: Tema.cartao
            Column {
                id: colunaConfirmar
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 10
                Titulo { nivel: 2; width: parent.width; wrapMode: Text.WordWrap; text: "Manter estas configurações de rede?" }
                Rotulo { width: parent.width; secundario: true
                         text: "Se a conexão caiu, não faça nada: a configuração anterior volta em " + rede.confirmando + " segundos." }
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Botao { texto: "Voltar à anterior"; onClicado: rede.desfazer() }
                    Botao { texto: "Manter"; tipo: "primario"; onClicado: rede.manter() }
                }
            }
        }
    }
    Connections { target: ajustes; function onAviso(m) { aviso.mostrar(m) } }
    Connections { target: controles; function onAviso(m) { aviso.mostrar(m) } }

    Timer { interval: 900; running: capturaArquivo !== ""; onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() }) }
}
