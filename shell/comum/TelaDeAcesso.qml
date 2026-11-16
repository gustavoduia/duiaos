// DuiaOS — a Tela de Entrada e a Tela de Bloqueio: o estado, o fundo e o desenho do estilo escolhido
// (TelaDeAcessoPadrao.qml ou TelaDeAcessoAurora.qml).
//
// É a mesma tela nos dois momentos; muda só o texto que descreve o que
// está acontecendo:
//   modo "entrada"  — iniciar uma sessão (depois de ligar ou de encerrar a sessão)
//   modo "bloqueio" — desbloquear uma sessão aberta, porém bloqueada
import QtQuick
import "estilo.js" as Estilo

Item {
    id: tela

    property string modo: "entrada"
    readonly property bool emBloqueio: modo === "bloqueio"
    property var usuarios: []            // [{usuario, nome}]
    property int usuarioAtual: 0
    property bool ocupado: false         // verificando a senha
    property string mensagem: ""         // erro ou aviso da autenticação
    property var opcoesEnergia: []       // [{id, titulo, descricao}]
    property string versao: "DuiaOS"
    property string papelDeParede: ""
    property string ajusteFundo: "preencher"     // shell/comum/papel.py
    property color corFundo: Estilo.fundo
    property bool desfocar: false
    property bool somenteFundo: false    // monitores extras: só o fundo e o relógio
    // Estilo futurista: o tom azul por cima do papel de parede e o brilho (shell/comum/papel.py: acesso)
    property var acesso: ({})
    readonly property int transparenciaDoVeu: acesso.veu !== undefined ? acesso.veu : 15
    readonly property string brilho: acesso.brilho || "radial"
    readonly property bool brilhoNasOutrasTelas: acesso.brilho_extra === true

    signal entrar(string usuario, string senha)
    signal acaoEnergia(string id)

    readonly property var pessoa: usuarios.length > 0
        ? usuarios[Math.min(usuarioAtual, usuarios.length - 1)]
        : ({ usuario: "", nome: "" })

    // O desenho vem de um dos dois arquivos, conforme o estilo (Configurações › Aparência, ADR 052)
    property bool futurista: false
    function limparSenha() { if (desenho.item) desenho.item.limparSenha() }
    function avisarErro() { if (desenho.item) desenho.item.avisarErro() }

    // ------------------------------------------------------------ fundo
    Rectangle { anchors.fill: parent; color: tela.corFundo }
    Image {
        id: imagemFundo
        anchors.fill: parent
        source: tela.papelDeParede
        fillMode: tela.ajusteFundo === "ajustar" ? Image.PreserveAspectFit
                  : tela.ajusteFundo === "esticar" ? Image.Stretch
                  : tela.ajusteFundo === "centralizar" ? Image.Pad
                  : tela.ajusteFundo === "lado-a-lado" ? Image.Tile : Image.PreserveAspectCrop
        asynchronous: false
        smooth: true
    }
    // Desfoque por cima da imagem (que continua embaixo: sem placa de vídeo, fica a imagem nítida)
    Loader {
        id: desfoque
        anchors.fill: parent
        active: tela.desfocar && tela.papelDeParede !== ""
        source: active ? Qt.resolvedUrl("FundoDesfocado.qml") : ""
        onLoaded: item.fonte = imagemFundo
    }
    Loader {
        id: desenho
        anchors.fill: parent
        Component.onCompleted: setSource(Qt.resolvedUrl(tela.futurista ? "TelaDeAcessoAurora.qml" : "TelaDeAcessoPadrao.qml"), { tela: tela })
    }
}
