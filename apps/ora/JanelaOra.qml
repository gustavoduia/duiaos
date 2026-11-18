// DuiaOS — Ora: uma janela do navegador.
// Faixa de abas; barra de ferramentas (voltar, avançar, recarregar, endereço com sugestões e estrela de
// favorito, downloads e o menu); barra de favoritos; conteúdo (página da web ou página interna do Ora:
// início, histórico, favoritos, downloads, configurações). A janela privada usa o perfil sem disco.
import QtQuick
import QtQuick.Window
import QtWebEngine
import DuiaOS

Window {
    id: janela
    property bool privada: false
    property var enderecosIniciais: []
    readonly property string idJanela: "j" + Date.now() + "-" + Math.floor(Math.random() * 100000)
    readonly property var perfil: privada ? perfilPrivado : perfilPadrao
    property int atual: 0
    property bool telaCheia: false
    property var fechadas: []                      // abas fechadas, para reabrir (Ctrl+Shift+T)
    property var permissao: null                   // pedido de permissão pendente do site
    property var pedidoTela: null                  // pedido de compartilhar a tela
    property bool menuAberto: false
    readonly property Item aba: repetidor.count > 0 ? repetidor.itemAt(Math.min(atual, repetidor.count - 1)) : null
    readonly property var web: aba ? aba.web : null
    readonly property bool corPrivada: privada

    width: 1280; height: 820
    minimumWidth: 640; minimumHeight: 420
    visible: true
    color: Tema.fundo
    title: (aba && aba.titulo ? aba.titulo + " — " : "") + (privada ? "Ora (janela privada)" : "Ora")

    // ============================================================ abas
    ListModel { id: abas }
    property int seq: 0

    function novaAba(url, ativar, depoisDe) {
        seq++
        var posicao = depoisDe === undefined ? abas.count : Math.min(depoisDe + 1, abas.count)
        abas.insert(posicao, { uid: "a" + seq, urlInicial: url || "" })
        if (ativar !== false) atual = posicao
        else if (posicao <= atual) atual = atual + 1
        return posicao
    }
    function fecharAba(i) {
        if (i < 0 || i >= abas.count) return
        var item = repetidor.itemAt(i)
        if (item && item.url !== "" && !privada) {
            var lista = fechadas.slice(); lista.push(item.url); fechadas = lista.slice(-20)
        }
        if (abas.count === 1) { janela.close(); return }
        abas.remove(i)
        if (atual >= abas.count) atual = abas.count - 1
        else if (i < atual) atual = atual - 1
        salvarSessao()
    }
    function reabrirFechada() {
        if (fechadas.length === 0) return
        var lista = fechadas.slice(); var url = lista.pop(); fechadas = lista
        novaAba(url, true)
    }
    function abrir(texto, emNovaAba) {
        var url = texto.indexOf("ora://") === 0 ? texto : ora.normalizar(texto)
        if (emNovaAba || !aba) novaAba(url, true, atual)
        else aba.navegar(url)
    }
    function abrirInterna(pagina) {
        // Reaproveita a aba que já mostra essa página interna
        for (var i = 0; i < repetidor.count; i++)
            if (repetidor.itemAt(i).pagina === pagina) { atual = i; return }
        if (aba && aba.pagina === "inicio" && !aba.temWeb) aba.navegar("ora://" + pagina)
        else novaAba("ora://" + pagina, true, atual)
    }
    function salvarSessao() {
        if (privada) return
        var lista = []
        for (var i = 0; i < repetidor.count; i++) {
            var it = repetidor.itemAt(i)
            if (it && it.url !== "" && it.url.indexOf("ora://") !== 0) lista.push({ url: it.url, titulo: it.titulo })
        }
        ora.guardarSessao(idJanela, lista)
    }
    function focarEndereco() { barraEndereco.focar() }

    Component.onCompleted: {
        var lista = enderecosIniciais || []
        if (typeof paginaDemonstracao !== "undefined" && paginaDemonstracao !== "") {
            if (paginaDemonstracao === "web") lista = [enderecoDemonstracao]
            else if (paginaDemonstracao !== "inicio") lista = ["ora://" + paginaDemonstracao]
        }
        if (lista.length === 0) novaAba("", true)
        for (var i = 0; i < lista.length; i++) novaAba(lista[i], i === 0)
        atual = 0
    }
    onActiveChanged: if (active) { ora.janelaAtiva(idJanela); menuDoApp.definirMenus(menusDoApp) }
    onClosing: {
        if (!privada) salvarSessao()
        ora.janelaFechada(idJanela)
    }

    Connections {
        target: ora
        function onAbrirPedido(url, alvo) {
            if (alvo !== janela.idJanela) return
            janela.novaAba(url, true)
            janela.raise(); janela.requestActivate()
        }
        function onAviso(texto) { if (janela.active || ora.ultimaJanela === janela.idJanela) aviso.mostrar(texto) }
    }

    // ============================================================ menus na Barra (ADR 059)
    readonly property var menusDoApp: {
        var it = function (id, rotulo, atalho, ativo, marcado) {
            return { id: id, rotulo: rotulo, tipo: marcado === undefined ? "item" : "marcavel", ativo: ativo !== false,
                     marcado: marcado === true, atalho: atalho || "", itens: [] } }
        var sep = { id: -1, rotulo: "", tipo: "separador", ativo: false, marcado: false, atalho: "", itens: [] }
        var temWeb = janela.web !== null && janela.aba && janela.aba.pagina === ""
        var favs = []
        var barra = ora.favoritosDaBarra
        for (var i = 0; i < Math.min(barra.length, 15); i++) favs.push(it("fav:" + barra[i].url, barra[i].titulo || barra[i].url))
        return [{ rotulo: "Ora", itens: [it("nova-aba", "Nova aba", "Ctrl+T"), it("nova-janela", "Nova janela", "Ctrl+N"),
                                         it("nova-privada", "Nova janela privada", "Ctrl+Shift+N"), sep,
                                         it("reabrir", "Reabrir aba fechada", "Ctrl+Shift+T", janela.fechadas.length > 0),
                                         it("pdf", "Salvar página como PDF", "Ctrl+P", temWeb), sep,
                                         it("configuracoes", "Configurações"), sep,
                                         it("fechar-aba", "Fechar aba", "Ctrl+W"), it("fechar-janela", "Fechar janela", "Ctrl+Shift+W")] },
                { rotulo: "Editar", itens: [it("desfazer", "Desfazer", "Ctrl+Z", temWeb), it("refazer", "Refazer", "Ctrl+Shift+Z", temWeb), sep,
                                            it("recortar", "Recortar", "Ctrl+X", temWeb), it("copiar", "Copiar", "Ctrl+C", temWeb),
                                            it("colar", "Colar", "Ctrl+V", temWeb), it("selecionar-tudo", "Selecionar tudo", "Ctrl+A", temWeb), sep,
                                            it("buscar", "Buscar na página", "Ctrl+F", temWeb), it("endereco", "Ir para o endereço", "Ctrl+L")] },
                { rotulo: "Visualizar", itens: [it("recarregar", "Recarregar", "Ctrl+R", temWeb), sep,
                                                it("zoom-mais", "Aumentar", "Ctrl++", temWeb), it("zoom-menos", "Diminuir", "Ctrl+-", temWeb),
                                                it("zoom-normal", "Tamanho original", "Ctrl+0", temWeb), sep,
                                                it("barra-favoritos", "Barra de favoritos", "Ctrl+Shift+B", true, ora.configuracoes.barra_de_favoritos === true),
                                                it("tela-cheia", "Tela cheia", "F11", true, janela.visibility === Window.FullScreen), sep,
                                                it("codigo-fonte", "Código-fonte da página", "Ctrl+U", temWeb)] },
                { rotulo: "Histórico", itens: [it("voltar", "Voltar", "Alt+←", janela.aba !== null && janela.aba.podeVoltar),
                                               it("avancar", "Avançar", "Alt+→", temWeb && janela.web.canGoForward), sep,
                                               it("historico", "Mostrar todo o histórico", "Ctrl+H")] },
                { rotulo: "Favoritos", itens: [it("favoritar", "Adicionar esta página aos favoritos", "Ctrl+D", temWeb),
                                               it("favoritos", "Mostrar todos os favoritos", "Ctrl+Shift+O")].concat(favs.length ? [sep].concat(favs) : []) },
                { rotulo: "Ferramentas", itens: [it("downloads", "Downloads", "Ctrl+J"),
                                                 it("devtools", "Ferramentas do desenvolvedor", "F12", temWeb)] }]
    }
    onMenusDoAppChanged: if (active) menuDoApp.definirMenus(menusDoApp)
    Connections {
        target: menuDoApp
        function onAcionado(id) {
            if (!janela.active && ora.ultimaJanela !== janela.idJanela) return
            janela.executar(id)
        }
    }

    function executar(id) {
        var w = janela.web
        var temWeb = w !== null && aba && aba.pagina === ""
        if (id.indexOf("fav:") === 0) { abrir(id.slice(4), false); return }
        switch (id) {
        case "nova-aba": novaAba("", true); focarEndereco(); break
        case "nova-janela": ora.novaJanela(false, ""); break
        case "nova-privada": ora.novaJanela(true, ""); break
        case "reabrir": reabrirFechada(); break
        case "pdf": if (temWeb) { var destino = ora.caminhoPdf(aba.titulo); w.printToPdf(destino); aviso.mostrar("PDF salvo em Documentos.") } break
        case "configuracoes": abrirInterna("configuracoes"); break
        case "fechar-aba": fecharAba(atual); break
        case "fechar-janela": janela.close(); break
        case "desfazer": if (temWeb) w.triggerWebAction(WebEngineView.Undo); break
        case "refazer": if (temWeb) w.triggerWebAction(WebEngineView.Redo); break
        case "recortar": if (temWeb) w.triggerWebAction(WebEngineView.Cut); break
        case "copiar": if (temWeb) w.triggerWebAction(WebEngineView.Copy); break
        case "colar": if (temWeb) w.triggerWebAction(WebEngineView.Paste); break
        case "selecionar-tudo": if (temWeb) w.triggerWebAction(WebEngineView.SelectAll); break
        case "buscar": if (temWeb) barraBusca.abrir(); break
        case "endereco": focarEndereco(); break
        case "recarregar": if (temWeb) w.reload(); break
        case "zoom-mais": if (temWeb) w.zoomFactor = Math.min(5, w.zoomFactor + 0.1); break
        case "zoom-menos": if (temWeb) w.zoomFactor = Math.max(0.25, w.zoomFactor - 0.1); break
        case "zoom-normal": if (temWeb) w.zoomFactor = ora.configuracoes.zoom_padrao || 1; break
        case "barra-favoritos": ora.definir("barra_de_favoritos", !ora.configuracoes.barra_de_favoritos); break
        case "tela-cheia": janela.visibility = janela.visibility === Window.FullScreen ? Window.Windowed : Window.FullScreen; break
        case "codigo-fonte": if (temWeb) novaAba("view-source:" + aba.url, true, atual); break
        case "voltar": if (aba) aba.voltar(); break
        case "avancar": if (temWeb) w.goForward(); break
        case "historico": abrirInterna("historico"); break
        case "favoritar": if (temWeb) barraEndereco.alternarFavorito(); break
        case "favoritos": abrirInterna("favoritos"); break
        case "downloads": abrirInterna("downloads"); break
        case "devtools": if (temWeb) abrirDevTools(w); break
        }
    }

    // ============================================================ atalhos de teclado
    Shortcut { sequences: ["Ctrl+T"]; onActivated: janela.executar("nova-aba") }
    Shortcut { sequences: ["Ctrl+N"]; onActivated: janela.executar("nova-janela") }
    Shortcut { sequences: ["Ctrl+Shift+N"]; onActivated: janela.executar("nova-privada") }
    Shortcut { sequences: ["Ctrl+W", "Ctrl+F4"]; onActivated: janela.executar("fechar-aba") }
    Shortcut { sequences: ["Ctrl+Shift+W"]; onActivated: janela.executar("fechar-janela") }
    Shortcut { sequences: ["Ctrl+Shift+T"]; onActivated: janela.executar("reabrir") }
    Shortcut { sequences: ["Ctrl+L", "Alt+D", "F6"]; onActivated: janela.executar("endereco") }
    Shortcut { sequences: ["Ctrl+R", "F5"]; onActivated: janela.executar("recarregar") }
    Shortcut { sequences: ["Ctrl+Shift+R", "Shift+F5"]; onActivated: if (janela.web) janela.web.triggerWebAction(WebEngineView.ReloadAndBypassCache) }
    Shortcut { sequences: ["Ctrl+F", "F3"]; onActivated: janela.executar("buscar") }
    Shortcut { sequences: ["Ctrl+D"]; onActivated: janela.executar("favoritar") }
    Shortcut { sequences: ["Ctrl+H"]; onActivated: janela.executar("historico") }
    Shortcut { sequences: ["Ctrl+J"]; onActivated: janela.executar("downloads") }
    Shortcut { sequences: ["Ctrl+Shift+O"]; onActivated: janela.executar("favoritos") }
    Shortcut { sequences: ["Ctrl+Shift+B"]; onActivated: janela.executar("barra-favoritos") }
    Shortcut { sequences: ["Ctrl+P"]; onActivated: janela.executar("pdf") }
    Shortcut { sequences: ["Ctrl+U"]; onActivated: janela.executar("codigo-fonte") }
    Shortcut { sequences: ["Ctrl++", "Ctrl+="]; onActivated: janela.executar("zoom-mais") }
    Shortcut { sequences: ["Ctrl+-"]; onActivated: janela.executar("zoom-menos") }
    Shortcut { sequences: ["Ctrl+0"]; onActivated: janela.executar("zoom-normal") }
    Shortcut { sequences: ["F11"]; onActivated: janela.executar("tela-cheia") }
    Shortcut { sequences: ["F12", "Ctrl+Shift+I"]; onActivated: janela.executar("devtools") }
    Shortcut { sequences: ["Alt+Left", "Back"]; onActivated: janela.executar("voltar") }
    Shortcut { sequences: ["Alt+Right", "Forward"]; onActivated: janela.executar("avancar") }
    Shortcut { sequences: ["Ctrl+Tab", "Ctrl+PgDown"]; onActivated: janela.atual = (janela.atual + 1) % abas.count }
    Shortcut { sequences: ["Ctrl+Shift+Tab", "Ctrl+PgUp"]; onActivated: janela.atual = (janela.atual + abas.count - 1) % abas.count }
    Shortcut { sequences: ["Ctrl+1"]; onActivated: janela.atual = 0 }
    Shortcut { sequences: ["Ctrl+2"]; onActivated: janela.atual = Math.min(1, abas.count - 1) }
    Shortcut { sequences: ["Ctrl+3"]; onActivated: janela.atual = Math.min(2, abas.count - 1) }
    Shortcut { sequences: ["Ctrl+4"]; onActivated: janela.atual = Math.min(3, abas.count - 1) }
    Shortcut { sequences: ["Ctrl+5"]; onActivated: janela.atual = Math.min(4, abas.count - 1) }
    Shortcut { sequences: ["Ctrl+9"]; onActivated: janela.atual = abas.count - 1 }
    Shortcut { sequences: ["Escape"]; enabled: janela.web !== null && janela.web.loading; onActivated: janela.web.stop() }

    // ============================================================ ferramentas do desenvolvedor e popups
    Component {
        id: componenteDevTools
        Window {
            id: jd
            property var alvo: null
            width: 1000; height: 640
            title: "Ferramentas do desenvolvedor — Ora"
            visible: true
            color: Tema.fundo
            WebEngineView {
                id: vistaDev
                anchors.fill: parent
                profile: janela.perfil
                Component.onCompleted: if (jd.alvo) jd.alvo.devToolsView = vistaDev
            }
            onClosing: { if (alvo) alvo.devToolsView = null; destroy() }
        }
    }
    function abrirDevTools(w) {
        if (w.devToolsView) { w.devToolsView.Window.window.raise(); return }
        componenteDevTools.createObject(janela, { alvo: w })
    }
    // Janelas que o site pede (login com Google/Microsoft, pagamentos): precisam do window.opener
    Component {
        id: componentePopup
        Window {
            id: jp
            property alias vistaDoPopup: vistaPopup
            width: 520; height: 680
            visible: true
            color: Tema.fundo
            title: (vistaPopup.title || "Ora") + " — Ora"
            Rectangle {
                id: faixaPopup
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 32
                color: Tema.lateral
                Icone { id: cadPopup; anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        nome: vistaPopup.url.toString().indexOf("https://") === 0 ? "cadeado" : "globo"; tamanho: 13; cor: Tema.textoSecundario }
                Text { anchors { left: cadPopup.right; leftMargin: 6; right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                       text: ora.paraMostrar(vistaPopup.url.toString()); elide: Text.ElideMiddle
                       font { family: Tema.fonteTexto; pixelSize: 12 } color: Tema.textoSecundario }
            }
            WebEngineView {
                id: vistaPopup
                anchors { left: parent.left; right: parent.right; top: faixaPopup.bottom; bottom: parent.bottom }
                profile: janela.perfil
                onWindowCloseRequested: jp.close()
                onNewWindowRequested: (pedido) => janela.pedidoDeJanela(pedido)
            }
            onClosing: destroy()
        }
    }
    function pedidoDeJanela(pedido) {
        if (pedido.destination === WebEngineNewWindowRequest.InNewDialog) {
            var popup = componentePopup.createObject(janela)
            pedido.openIn(popup.vistaDoPopup)
            return
        }
        var segundoPlano = pedido.destination === WebEngineNewWindowRequest.InNewBackgroundTab
        var i = novaAba("about:blank#ora-nova", !segundoPlano, atual)
        var item = repetidor.itemAt(i)
        item.prepararWeb()
        pedido.openIn(item.web)
    }

    // ============================================================ conteúdo das abas
    Rectangle { anchors.fill: parent; color: Tema.fundo }

    Item {
        id: areaConteudo
        anchors { left: parent.left; right: parent.right; top: janela.visibility === Window.FullScreen && janela.telaCheia ? parent.top : cabecalho.bottom
                  bottom: parent.bottom }
        Repeater {
            id: repetidor
            model: abas
            delegate: Aba { }
        }
    }

    // A aba: a página da web (criada na primeira navegação) e, por cima, a página interna do Ora
    component Aba: Item {
        id: estaAba
        required property int index
        required property string uid
        required property string urlInicial
        anchors.fill: parent
        visible: index === janela.atual
        property string pagina: "inicio"                 // "" = a página da web
        property bool temWeb: false
        property string urlPedida: ""
        property var web: carregadorWeb.item
        property string erroCertificado: ""
        property var pedidoCertificado: null
        property bool processoParou: false
        readonly property string url: pagina !== "" ? (pagina === "inicio" ? "" : "ora://" + pagina)
                                                    : (web ? web.url.toString() : urlPedida)
        readonly property string titulo: pagina !== "" ? ({ inicio: "Nova aba", historico: "Histórico", favoritos: "Favoritos",
                                                             downloads: "Downloads", configuracoes: "Configurações" })[pagina] || "Ora"
                                                       : (web && web.title ? web.title : ora.paraMostrar(url))
        readonly property string icone: pagina === "" && web && web.icon.toString() !== "" ? web.icon.toString() : ""
        readonly property bool carregando: pagina === "" && web !== null && web.loading
        readonly property real progresso: web ? web.loadProgress / 100 : 0
        readonly property bool podeVoltar: (pagina !== "" && temWeb) || (pagina === "" && web !== null && web.canGoBack)
        readonly property bool audivel: web !== null && web.recentlyAudible
        readonly property bool mudo: web !== null && web.audioMuted

        function prepararWeb() { temWeb = true; pagina = "" }
        function navegar(endereco) {
            if (endereco === "") { pagina = "inicio"; return }
            if (endereco.indexOf("ora://") === 0) { pagina = endereco.slice(6); return }
            pagina = ""
            processoParou = false
            if (web) web.url = endereco
            else { urlPedida = endereco; temWeb = true }
        }
        function voltar() {
            if (pagina !== "" && temWeb) pagina = ""
            else if (web && web.canGoBack) web.goBack()
        }
        Component.onCompleted: navegar(urlInicial === "about:blank#ora-nova" ? "" : urlInicial)
        onUrlChanged: janela.salvarSessao()

        Loader {
            id: carregadorWeb
            anchors.fill: parent
            active: estaAba.temWeb
            visible: estaAba.pagina === ""
            sourceComponent: WebEngineView {
                id: vista
                profile: janela.perfil
                url: estaAba.urlPedida !== "" ? estaAba.urlPedida : "about:blank"
                zoomFactor: ora.configuracoes.zoom_padrao || 1
                settings.fullScreenSupportEnabled: true
                settings.pdfViewerEnabled: true
                settings.screenCaptureEnabled: true
                settings.dnsPrefetchEnabled: true
                settings.focusOnNavigationEnabled: true
                settings.localContentCanAccessRemoteUrls: false
                onLoadingChanged: (info) => {
                    if (info.status === WebEngineView.LoadSucceededStatus && !janela.privada)
                        ora.visitou(info.url.toString(), vista.title)
                }
                onTitleChanged: if (!janela.privada && !loading) ora.atualizarTitulo(url.toString(), title)
                onNewWindowRequested: (pedido) => janela.pedidoDeJanela(pedido)
                onWindowCloseRequested: janela.fecharAba(estaAba.index)
                onFullScreenRequested: (pedido) => {
                    pedido.accept()
                    janela.telaCheia = pedido.toggleOn
                    janela.visibility = pedido.toggleOn ? Window.FullScreen : Window.Windowed
                }
                onPermissionRequested: (p) => { janela.permissao = p }
                onDesktopMediaRequested: (pedido) => { janela.pedidoTela = pedido }
                onCertificateError: (erro) => {
                    erro.defer()
                    estaAba.pedidoCertificado = erro
                    estaAba.erroCertificado = erro.description
                }
                onLinkHovered: (endereco) => { bolhaLink.texto = endereco.toString() }
                onRenderProcessTerminated: (estado, codigo) => {
                    if (estado !== WebEngineView.NormalTerminationStatus) estaAba.processoParou = true
                }
                onFindTextFinished: (resultado) => barraBusca.resultado(resultado.numberOfMatches, resultado.activeMatch)
            }
        }

        Loader {
            anchors.fill: parent
            active: estaAba.pagina !== ""
            visible: active
            sourceComponent: {
                switch (estaAba.pagina) {
                case "historico": return componenteHistorico
                case "favoritos": return componenteFavoritos
                case "downloads": return componenteDownloads
                case "configuracoes": return componenteConfiguracoes
                default: return componenteInicio
                }
            }
        }

        // Erro de certificado: a conexão não é segura
        Rectangle {
            anchors.fill: parent
            visible: estaAba.erroCertificado !== "" && estaAba.pagina === ""
            color: Tema.fundo
            Column {
                anchors.centerIn: parent
                width: Math.min(parent.width - 64, 560)
                spacing: 16
                Icone { nome: "escudo"; tamanho: 56; cor: Tema.erro }
                Titulo { text: "A conexão com este site não é segura"; width: parent.width; wrapMode: Text.WordWrap }
                Rotulo { width: parent.width; wrapMode: Text.WordWrap; secundario: true
                         text: "Alguém pode estar tentando roubar as suas informações de " + ora.dominio(estaAba.url) +
                               " (senhas, mensagens ou cartões).\n\nDetalhe técnico: " + estaAba.erroCertificado }
                Row {
                    spacing: 10
                    Botao { texto: "Voltar para a segurança"; tipo: "primario"
                            onClicado: { estaAba.pedidoCertificado.rejectCertificate(); estaAba.erroCertificado = ""; estaAba.voltar() } }
                    Botao { texto: "Continuar mesmo assim"; visible: estaAba.pedidoCertificado && estaAba.pedidoCertificado.overridable
                            onClicado: { estaAba.pedidoCertificado.acceptCertificate(); estaAba.erroCertificado = "" } }
                }
            }
        }
        // A página parou (o processo do site fechou)
        Rectangle {
            anchors.fill: parent
            visible: estaAba.processoParou && estaAba.pagina === ""
            color: Tema.fundo
            Column {
                anchors.centerIn: parent
                spacing: 14
                Icone { anchors.horizontalCenter: parent.horizontalCenter; nome: "info"; tamanho: 48; cor: Tema.textoSecundario }
                Titulo { anchors.horizontalCenter: parent.horizontalCenter; text: "Esta página parou de funcionar" }
                Botao { anchors.horizontalCenter: parent.horizontalCenter; texto: "Recarregar"; tipo: "primario"
                        onClicado: { estaAba.processoParou = false; estaAba.web.reload() } }
            }
        }
    }

    Component { id: componenteInicio; PaginaInicio { janelaOra: janela } }
    Component { id: componenteHistorico; PaginaHistorico { janelaOra: janela } }
    Component { id: componenteFavoritos; PaginaFavoritos { janelaOra: janela } }
    Component { id: componenteDownloads; PaginaDownloads { janelaOra: janela } }
    Component { id: componenteConfiguracoes; PaginaConfiguracoes { janelaOra: janela } }

    // ============================================================ cabeçalho: abas, ferramentas, favoritos
    Rectangle {
        id: cabecalho
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: janela.visibility === Window.FullScreen && janela.telaCheia ? 0 : faixaAbas.height + ferramentas.height + barraFavoritos.height
        visible: height > 0
        clip: true
        color: janela.privada ? (Tema.escuro ? "#1B1530" : "#ECE7FB") : Tema.lateral
        z: 5

        // ---------------------------------------------------- faixa de abas
        Item {
            id: faixaAbas
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 40
            Row {
                id: linhaAbas
                anchors { left: parent.left; leftMargin: 8; bottom: parent.bottom }
                spacing: 2
                readonly property real larguraAba: Math.max(72, Math.min(232, (faixaAbas.width - 64 - (janela.privada ? 110 : 0)) / Math.max(1, abas.count)))
                Repeater {
                    model: abas
                    delegate: Item {
                        id: guia
                        required property int index
                        readonly property Item conteudo: repetidor.count > index ? repetidor.itemAt(index) : null
                        readonly property bool ativa: index === janela.atual
                        width: linhaAbas.larguraAba; height: 34
                        Rectangle {
                            anchors.fill: parent
                            anchors.bottomMargin: -8
                            radius: 10
                            color: guia.ativa ? Tema.fundo : (areaGuia.containsMouse ? Tema.realce : "transparent")
                            border { width: guia.ativa && Tema.futurista ? 1 : 0; color: Tema.borda }
                        }
                        Rectangle {          // separador entre abas inativas
                            visible: !guia.ativa && guia.index + 1 !== janela.atual && guia.index < abas.count - 1
                            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                            width: 1; height: 16; color: Tema.borda
                        }
                        MouseArea {
                            id: areaGuia
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                            onClicked: (m) => { if (m.button === Qt.MiddleButton) janela.fecharAba(guia.index); else janela.atual = guia.index }
                        }
                        // ícone do site, ou o giro do carregamento
                        Item {
                            id: iconeGuia
                            anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                            width: 16; height: 16
                            Image {
                                anchors.fill: parent
                                visible: guia.conteudo && guia.conteudo.icone !== "" && !guia.conteudo.carregando
                                source: guia.conteudo && guia.conteudo.icone !== "" ? guia.conteudo.icone : ""
                                sourceSize: Qt.size(32, 32)
                            }
                            Icone {
                                anchors.centerIn: parent
                                visible: guia.conteudo && guia.conteudo.icone === "" && !guia.conteudo.carregando
                                nome: guia.conteudo && guia.conteudo.pagina !== "" ? ({ historico: "recentes", favoritos: "estrela", downloads: "download",
                                                                                        configuracoes: "engrenagem" })[guia.conteudo.pagina] || "globo" : "globo"
                                tamanho: 14; cor: Tema.textoSecundario
                            }
                            Rectangle {
                                anchors.fill: parent
                                visible: guia.conteudo !== null && guia.conteudo.carregando
                                radius: 8; color: "transparent"
                                border { width: 2; color: Tema.azulDuia }
                                Rectangle { width: 6; height: 6; radius: 3; color: Tema.lateral; x: 10; y: 0 }
                                RotationAnimation on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: parent.visible }
                            }
                        }
                        Text {
                            anchors { left: iconeGuia.right; leftMargin: 8; right: botoesGuia.left; rightMargin: 4; verticalCenter: parent.verticalCenter }
                            text: guia.conteudo ? guia.conteudo.titulo : ""
                            elide: Text.ElideRight
                            color: guia.ativa ? Tema.texto : Tema.textoSecundario
                            font { family: Tema.fonteTexto; pixelSize: 13; weight: guia.ativa ? Font.DemiBold : Font.Normal }
                        }
                        Row {
                            id: botoesGuia
                            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                            spacing: 0
                            BotaoIcone {
                                visible: guia.conteudo !== null && (guia.conteudo.audivel || guia.conteudo.mudo)
                                width: 22; height: 22; radius: 6
                                icone: guia.conteudo && guia.conteudo.mudo ? "som-mudo" : "som-0"
                                tamanhoIcone: 13; corIcone: Tema.textoSecundario
                                dica: "Silenciar a aba"
                                onClicado: guia.conteudo.web.audioMuted = !guia.conteudo.web.audioMuted
                            }
                            BotaoIcone {
                                visible: guia.ativa || areaGuia.containsMouse || linhaAbas.larguraAba > 120
                                width: 22; height: 22; radius: 6
                                icone: "fechar"; tamanhoIcone: 12; corIcone: Tema.textoSecundario
                                dica: "Fechar a aba"
                                onClicado: janela.fecharAba(guia.index)
                            }
                        }
                    }
                }
                BotaoIcone {
                    anchors.verticalCenter: parent.verticalCenter
                    icone: "mais"; tamanhoIcone: 15; corIcone: Tema.textoSecundario
                    dica: "Nova aba"
                    onClicado: { janela.novaAba("", true); janela.focarEndereco() }
                }
            }
            Rectangle {
                visible: janela.privada
                anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                height: 24; width: linhaPrivada.implicitWidth + 18; radius: 12
                color: Tema.escuro ? "#3A2E66" : "#D9CFF8"
                Row {
                    id: linhaPrivada
                    anchors.centerIn: parent
                    spacing: 6
                    Icone { nome: "olho"; tamanho: 13; cor: Tema.escuro ? "#D9CFF8" : "#4B2FB0"; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "Janela privada"; color: Tema.escuro ? "#D9CFF8" : "#4B2FB0"; anchors.verticalCenter: parent.verticalCenter
                           font { family: Tema.fonteTexto; pixelSize: 12; weight: Font.DemiBold } }
                }
            }
        }

        // ---------------------------------------------------- barra de ferramentas
        Rectangle {
            id: ferramentas
            anchors { left: parent.left; right: parent.right; top: faixaAbas.bottom }
            height: 48
            color: Tema.fundo
            Row {
                id: navegacao
                anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                spacing: 2
                BotaoIcone { icone: "seta-esquerda"; dica: "Voltar"; ativo: janela.aba !== null && janela.aba.podeVoltar; onClicado: janela.executar("voltar") }
                BotaoIcone { icone: "seta-direita"; dica: "Avançar"; ativo: janela.web !== null && janela.aba.pagina === "" && janela.web.canGoForward
                             onClicado: janela.executar("avancar") }
                BotaoIcone {
                    icone: janela.aba && janela.aba.carregando ? "fechar" : "reiniciar"
                    dica: janela.aba && janela.aba.carregando ? "Parar" : "Recarregar"
                    ativo: janela.web !== null && janela.aba.pagina === ""
                    onClicado: janela.aba.carregando ? janela.web.stop() : janela.web.reload()
                }
                BotaoIcone { icone: "casa"; dica: "Página inicial"; onClicado: janela.aba.navegar(ora.configuracoes.ao_iniciar === "pagina" && ora.configuracoes.pagina_inicial ? ora.normalizar(ora.configuracoes.pagina_inicial) : "") }
            }
            BarraDeEndereco {
                id: barraEndereco
                anchors { left: navegacao.right; leftMargin: 8; right: acoes.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                janelaOra: janela
            }
            Row {
                id: acoes
                anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                spacing: 2
                Item {
                    width: 30; height: 30
                    BotaoIcone { anchors.fill: parent; icone: "download"; dica: "Downloads"; onClicado: janela.abrirInterna("downloads") }
                    Rectangle {
                        visible: ora.downloadsEmAndamento > 0
                        anchors { right: parent.right; top: parent.top; margins: 2 }
                        width: 14; height: 14; radius: 7; color: Tema.azulDuia
                        Text { anchors.centerIn: parent; text: ora.downloadsEmAndamento; color: "white"; font { family: Tema.fonteTexto; pixelSize: 9; weight: Font.Bold } }
                    }
                }
                BotaoIcone { icone: "lista"; dica: "Menu do Ora"; marcado: janela.menuAberto; onClicado: janela.menuAberto = !janela.menuAberto }
            }
            // barra fina de progresso do carregamento
            Rectangle {
                anchors { left: parent.left; bottom: parent.bottom }
                height: 2
                visible: janela.aba !== null && janela.aba.carregando
                width: parent.width * (janela.aba ? janela.aba.progresso : 0)
                gradient: Gradient { orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Tema.aurora1 } GradientStop { position: 0.5; color: Tema.aurora2 } GradientStop { position: 1; color: Tema.aurora3 } }
                Behavior on width { NumberAnimation { duration: 160 } }
            }
        }

        // ---------------------------------------------------- barra de favoritos
        Rectangle {
            id: barraFavoritos
            anchors { left: parent.left; right: parent.right; top: ferramentas.bottom }
            height: ora.configuracoes.barra_de_favoritos === true && !janela.privada ? 32 : 0
            visible: height > 0
            color: Tema.fundo
            clip: true
            Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda }
            Row {
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 2
                Repeater {
                    model: ora.favoritosDaBarra
                    delegate: Rectangle {
                        required property var modelData
                        height: 26; radius: 7
                        width: Math.min(180, linhaFav.implicitWidth + 16)
                        color: areaFav.pressed ? Tema.pressionado : (areaFav.containsMouse ? Tema.realce : "transparent")
                        Row {
                            id: linhaFav
                            anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                            spacing: 6
                            Favicon { url: modelData.url; titulo: modelData.titulo; tamanho: 14; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: modelData.titulo || modelData.url; width: Math.min(implicitWidth, 140); elide: Text.ElideRight
                                   anchors.verticalCenter: parent.verticalCenter; color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 12 } }
                        }
                        MouseArea { id: areaFav; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                                    onClicked: (m) => janela.abrir(modelData.url, m.button === Qt.MiddleButton || (m.modifiers & Qt.ControlModifier)) }
                    }
                }
            }
        }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Tema.borda
                    visible: barraFavoritos.height === 0 }
    }

    // ============================================================ barras sobre o conteúdo
    // Pedido de permissão do site (câmera, microfone, localização, notificações...)
    Rectangle {
        id: barraPermissao
        visible: janela.permissao !== null
        anchors { top: areaConteudo.top; horizontalCenter: parent.horizontalCenter; topMargin: 10 }
        width: Math.min(parent.width - 32, linhaPermissao.implicitWidth + 32)
        height: 52; radius: Tema.raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        z: 20
        Row {
            id: linhaPermissao
            anchors.centerIn: parent
            spacing: 12
            Icone { nome: "escudo"; tamanho: 18; cor: Tema.azulDuia; anchors.verticalCenter: parent.verticalCenter }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: janela.permissao ? "<b>" + ora.dominio(janela.permissao.origin.toString()) + "</b> quer " +
                                         ora.nomePermissao(janela.permissao.permissionType) : ""
                textFormat: Text.StyledText
                color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 }
            }
            Botao { texto: "Bloquear"; onClicado: { janela.permissao.deny(); janela.permissao = null } }
            Botao { texto: "Permitir"; tipo: "primario"; onClicado: { janela.permissao.grant(); janela.permissao = null } }
        }
    }
    // Compartilhar a tela (Meet, Teams...): a tela inteira, com confirmação
    Rectangle {
        visible: janela.pedidoTela !== null
        anchors { top: areaConteudo.top; horizontalCenter: parent.horizontalCenter; topMargin: 10 }
        width: Math.min(parent.width - 32, linhaTela.implicitWidth + 32)
        height: 52; radius: Tema.raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        z: 21
        Row {
            id: linhaTela
            anchors.centerIn: parent
            spacing: 12
            Icone { nome: "monitor"; tamanho: 18; cor: Tema.azulDuia; anchors.verticalCenter: parent.verticalCenter }
            Text { anchors.verticalCenter: parent.verticalCenter; text: "Compartilhar a tela inteira com este site?"
                   color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
            Botao { texto: "Cancelar"; onClicado: { janela.pedidoTela.cancel(); janela.pedidoTela = null } }
            Botao { texto: "Compartilhar"; tipo: "primario"
                    onClicado: { janela.pedidoTela.selectScreen(janela.pedidoTela.screensModel.index(0, 0)); janela.pedidoTela = null } }
        }
    }
    // Buscar na página
    Rectangle {
        id: barraBusca
        property bool aberta: false
        property int total: 0
        property int ativo: 0
        function abrir() { aberta = true; campoBusca.entrada.forceActiveFocus(); campoBusca.entrada.selectAll() }
        function fechar() { aberta = false; if (janela.web) janela.web.findText(""); total = 0 }
        function resultado(n, a) { total = n; ativo = a }
        function buscar(paraTras) {
            if (!janela.web) return
            janela.web.findText(campoBusca.texto, paraTras ? WebEngineView.FindBackward : 0)
        }
        visible: aberta
        anchors { top: areaConteudo.top; right: parent.right; topMargin: 10; rightMargin: 16 }
        width: 400; height: 46; radius: Tema.raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        z: 22
        Campo {
            id: campoBusca
            anchors { left: parent.left; leftMargin: 8; right: contagem.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            height: 32
            icone: "busca"; dica: "Buscar na página"
            onTextoChanged: barraBusca.buscar(false)
            onConfirmado: barraBusca.buscar(false)
            Keys.onEscapePressed: barraBusca.fechar()
        }
        Text {
            id: contagem
            anchors { right: botoesBusca.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
            text: campoBusca.texto === "" ? "" : (barraBusca.total === 0 ? "Nada" : barraBusca.ativo + " de " + barraBusca.total)
            color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 }
        }
        Row {
            id: botoesBusca
            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
            BotaoIcone { icone: "seta-cima"; tamanhoIcone: 14; dica: "Anterior"; onClicado: barraBusca.buscar(true) }
            BotaoIcone { icone: "seta-baixo"; tamanhoIcone: 14; dica: "Próximo"; onClicado: barraBusca.buscar(false) }
            BotaoIcone { icone: "fechar"; tamanhoIcone: 13; dica: "Fechar"; onClicado: barraBusca.fechar() }
        }
    }
    // Endereço do link sob o mouse
    Rectangle {
        id: bolhaLink
        property string texto: ""
        visible: texto !== "" && janela.aba !== null && janela.aba.pagina === ""
        anchors { left: parent.left; bottom: parent.bottom; margins: 6 }
        width: Math.min(parent.width * 0.6, textoLink.implicitWidth + 20)
        height: 26; radius: 8
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        z: 23
        Text { id: textoLink; anchors { fill: parent; leftMargin: 10; rightMargin: 10 } verticalAlignment: Text.AlignVCenter
               text: bolhaLink.texto; elide: Text.ElideMiddle; color: Tema.textoSecundario; font { family: Tema.fonteTexto; pixelSize: 12 } }
    }
    // Tela cheia: aviso de como sair
    Rectangle {
        id: avisoTelaCheia
        visible: opacity > 0
        opacity: 0
        anchors { top: parent.top; horizontalCenter: parent.horizontalCenter; topMargin: 24 }
        width: textoTelaCheia.implicitWidth + 32; height: 40; radius: 20
        color: Qt.rgba(0, 0, 0, 0.75)
        z: 30
        Text { id: textoTelaCheia; anchors.centerIn: parent; text: "Pressione Esc ou F11 para sair da tela cheia"
               color: "white"; font { family: Tema.fonteTexto; pixelSize: 13 } }
        Behavior on opacity { NumberAnimation { duration: 300 } }
        Timer { id: tempoTelaCheia; interval: 2600; onTriggered: avisoTelaCheia.opacity = 0 }
    }
    onVisibilityChanged: function () {
        if (janela.visibility === Window.FullScreen) { avisoTelaCheia.opacity = 1; tempoTelaCheia.restart() }
        else if (telaCheia) { telaCheia = false; if (web && web.isFullScreen) web.fullScreenCancelled() }
    }
    Shortcut { sequences: ["Escape"]; enabled: janela.visibility === Window.FullScreen; onActivated: janela.visibility = Window.Windowed }

    // ============================================================ menu do Ora (botão ☰)
    MouseArea { anchors.fill: parent; visible: janela.menuAberto; z: 40; onClicked: janela.menuAberto = false }
    Rectangle {
        id: menu
        visible: janela.menuAberto
        z: 41
        anchors { right: parent.right; rightMargin: 10; top: cabecalho.top; topMargin: faixaAbas.height + ferramentas.height - 4 }
        width: 280
        height: colunaMenu.implicitHeight + 16
        radius: Tema.raio
        color: Tema.vidro
        border { color: Tema.borda; width: 1 }
        Column {
            id: colunaMenu
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
            spacing: 1
            ItemDeMenu { width: parent.width; texto: "Nova aba"; icone: "mais"; atalho: "Ctrl+T"; onClicado: { janela.menuAberto = false; janela.executar("nova-aba") } }
            ItemDeMenu { width: parent.width; texto: "Nova janela"; icone: "monitor"; atalho: "Ctrl+N"; onClicado: { janela.menuAberto = false; janela.executar("nova-janela") } }
            ItemDeMenu { width: parent.width; texto: "Nova janela privada"; icone: "olho"; atalho: "Ctrl+Shift+N"; onClicado: { janela.menuAberto = false; janela.executar("nova-privada") } }
            Separador { width: parent.width }
            ItemDeMenu { width: parent.width; texto: "Histórico"; icone: "recentes"; atalho: "Ctrl+H"; onClicado: { janela.menuAberto = false; janela.executar("historico") } }
            ItemDeMenu { width: parent.width; texto: "Favoritos"; icone: "estrela"; atalho: "Ctrl+Shift+O"; onClicado: { janela.menuAberto = false; janela.executar("favoritos") } }
            ItemDeMenu { width: parent.width; texto: "Downloads"; icone: "download"; atalho: "Ctrl+J"; onClicado: { janela.menuAberto = false; janela.executar("downloads") } }
            Separador { width: parent.width }
            Item {
                width: parent.width; height: 34
                Text { anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter } text: "Zoom"
                       color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                Row {
                    anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
                    spacing: 4
                    BotaoIcone { icone: "seta-baixo"; tamanhoIcone: 13; dica: "Diminuir"; ativo: janela.web !== null; onClicado: janela.executar("zoom-menos") }
                    Text { width: 44; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter
                           text: janela.web ? Math.round(janela.web.zoomFactor * 100) + "%" : "100%"
                           color: Tema.texto; font { family: Tema.fonteTexto; pixelSize: 13 } }
                    BotaoIcone { icone: "seta-cima"; tamanhoIcone: 13; dica: "Aumentar"; ativo: janela.web !== null; onClicado: janela.executar("zoom-mais") }
                    BotaoIcone { icone: "monitor"; tamanhoIcone: 13; dica: "Tela cheia"; onClicado: { janela.menuAberto = false; janela.executar("tela-cheia") } }
                }
            }
            ItemDeMenu { width: parent.width; texto: "Buscar na página"; icone: "busca"; atalho: "Ctrl+F"; ativo: janela.web !== null; onClicado: { janela.menuAberto = false; janela.executar("buscar") } }
            ItemDeMenu { width: parent.width; texto: "Salvar como PDF"; icone: "pdf"; atalho: "Ctrl+P"; ativo: janela.web !== null; onClicado: { janela.menuAberto = false; janela.executar("pdf") } }
            ItemDeMenu { width: parent.width; texto: "Ferramentas do desenvolvedor"; icone: "codigo"; atalho: "F12"; ativo: janela.web !== null; onClicado: { janela.menuAberto = false; janela.executar("devtools") } }
            Separador { width: parent.width }
            ItemDeMenu { width: parent.width; texto: "Configurações"; icone: "engrenagem"; onClicado: { janela.menuAberto = false; janela.executar("configuracoes") } }
        }
    }

    Aviso { id: aviso; anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 24 } z: 50 }

    // Captura de tela para os testes e a documentação
    Timer {
        interval: 3500
        running: typeof capturaArquivo !== "undefined" && capturaArquivo !== ""
        onTriggered: janela.contentItem.grabToImage(function (r) { r.saveToFile(capturaArquivo); Qt.quit() })
    }
}
