// DuiaOS — Tela de Bloqueio (desbloquear uma sessão aberta).
// Mesmo visual da Tela de Entrada. Uma janela por monitor, na camada mais
// alta do Wayland (layer-shell "overlay"); só a da tela principal (a do
// notebook, quando houver) recebe o teclado e mostra o campo de senha — as
// outras mostram o fundo e o relógio.
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell
import "../comum"
import "../comum/telas.js" as Telas

Item {
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            id: janela
            // modelData (o monitor) e index vêm do Instantiator
            readonly property bool principal: index === Telas.indicePrincipal(Qt.application.screens)

            screen: modelData
            width: modelData.width
            height: modelData.height
            visible: true
            color: "#F7F9FC"
            title: "Tela de Bloqueio"

            LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                                       | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
            LayerShell.Window.layer: LayerShell.Window.LayerOverlay
            LayerShell.Window.exclusionZone: -1
            LayerShell.Window.keyboardInteractivity: principal
                ? LayerShell.Window.KeyboardInteractivityExclusive
                : LayerShell.Window.KeyboardInteractivityNone
            LayerShell.Window.scope: "duiaos-tela-de-bloqueio"

            TelaDeAcesso {
                id: tela
                anchors.fill: parent
                modo: "bloqueio"
                somenteFundo: !janela.principal
                usuarios: [bloqueio.usuario]
                ocupado: bloqueio.ocupado
                opcoesEnergia: bloqueio.opcoesEnergia
                versao: bloqueio.versao
                papelDeParede: bloqueio.papelDeParede
                onEntrar: (usuario, senha) => bloqueio.desbloquear(senha)
                onAcaoEnergia: (id) => bloqueio.energia(id)
            }

            Connections {
                target: bloqueio
                enabled: janela.principal
                function onFalhou(mensagem) {
                    tela.mensagem = mensagem
                    tela.avisarErro()
                }
            }

            Component.onCompleted: if (principal) bloqueio.pronta()
        }
    }
}
