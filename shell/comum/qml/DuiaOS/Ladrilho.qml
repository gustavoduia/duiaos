// Ícone de aplicativo do próprio DuiaOS: quadrado arredondado com degradê e o desenho em branco.
import QtQuick

Rectangle {
    id: raiz
    property string icone: "pasta"
    property string estilo: "azul"          // azul, cinza, claro, noite
    property int tamanho: 44
    width: tamanho; height: tamanho
    radius: tamanho * (Tema.futurista ? 0.3 : 0.25)
    readonly property var cores: Tema.futurista ? ({
        azul: [Tema.escuro ? "#38BDF8" : "#22B8E6", Tema.escuro ? "#6366F1" : "#3D5BFF", "white"],
        noite: [Tema.escuro ? "#7C83FF" : "#5B5FEF", Tema.escuro ? "#A855F7" : "#7C3AED", "white"],
        cinza: Tema.escuro ? ["#3A4676", "#1C2545", "#EEF2FF"] : ["#FFFFFF", "#D5DBF2", "#0E1430"],
        claro: Tema.escuro ? ["#27325C", "#161D3A", "#EEF2FF"] : ["#FFFFFF", "#E6EAF8", "#0E1430"]
    }) : ({
        azul: ["#6FA0F7", "#2E6BE6", "white"],
        noite: ["#3D5F9E", "#1A3A73", "white"],
        cinza: Tema.escuro ? ["#535B68", "#363C47", "#E6EAF0"] : ["#F3F5F8", "#C9D1DC", "#1F2933"],
        claro: Tema.escuro ? ["#3A404B", "#2B3039", "#E6EAF0"] : ["#FFFFFF", "#E4EAF2", "#1F2933"]
    })
    readonly property var c: cores[estilo] || cores.azul
    gradient: Gradient {
        GradientStop { position: 0; color: raiz.c[0] }
        GradientStop { position: 1; color: raiz.c[1] }
    }
    border { color: Tema.futurista ? Qt.rgba(1, 1, 1, Tema.escuro ? 0.16 : 0.5) : Qt.rgba(0.06, 0.09, 0.14, 0.10); width: 1 }
    Icone { anchors.centerIn: parent; nome: raiz.icone; tamanho: Math.round(raiz.tamanho * 0.55); cor: raiz.c[2] }
}
