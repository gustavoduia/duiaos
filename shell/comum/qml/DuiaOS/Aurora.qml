// Degradê aurora (ciano → azul → violeta) do estilo futurista; no estilo padrão, azul Duia liso.
// Use como fundo de botões principais, itens selecionados e interruptores ligados.
import QtQuick

Rectangle {
    property real forca: 1            // 0–1: quanto do degradê aparece (1 = cheio)
    property bool vertical: false
    color: Tema.azulDuia
    gradient: Tema.futurista ? degrade : null
    Gradient {
        id: degrade
        orientation: vertical ? Gradient.Vertical : Gradient.Horizontal
        GradientStop { position: 0.0; color: Tema.aurora1 }
        GradientStop { position: 0.5; color: Tema.aurora2 }
        GradientStop { position: 1.0; color: Tema.aurora3 }
    }
}
