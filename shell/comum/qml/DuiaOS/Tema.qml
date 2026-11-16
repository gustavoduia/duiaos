// DuiaOS — cores, fontes e medidas da interface (identidade visual em branding/README.md),
// nos modos claro e escuro e em dois estilos (Configurações › Aparência):
//   padrao     o visual de sempre
//   futurista  "Aurora" (ADR 052): azul-noite profundo ou pérola, vidro, cantos mais redondos e o
//              degradê aurora (ciano → azul → violeta) nos controles principais
// O modo e o estilo vêm de "aparencia" (shell/comum/interface.py), que lê as preferências e avisa
// todas as janelas na hora.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool escuro: typeof aparencia !== "undefined" && aparencia !== null && aparencia.escuro
    readonly property bool futurista: typeof aparencia !== "undefined" && aparencia !== null && aparencia.estilo === "futurista"

    // Escolhe a cor pelo estilo e pelo modo: c(padrão claro, padrão escuro, aurora claro, aurora escuro)
    function c(pc, pe, fc, fe) { return futurista ? (escuro ? fe : fc) : (escuro ? pe : pc) }

    readonly property color fundo: c("#F7F9FC", "#1B1F27", "#F2F4FC", "#0A0F1F")
    readonly property color cartao: c("#FFFFFF", "#262B34", "#FFFFFF", "#131A30")
    readonly property color vidro: c("#F2F4F7FB", "#F2262B35", "#E6FAFBFF", "#E0121830")       // painéis flutuantes
    readonly property color barra: c("#F2F7F9FC", "#F01B1F27", "#B8F4F6FF", "#B00A0F1F")       // Barra de Recursos
    readonly property color ilha: c("#EBF7F9FC", "#E81F232B", "#A6FFFFFF", "#99141B33")        // Ilha de Aplicativos
    readonly property color lateral: c("#EEF2F7", "#20242C", "#E8ECF9", "#0D1326")             // barras laterais
    readonly property color listra: c("#F1F4F8", "#22272F", "#EDF0FA", "#10162B")              // linhas alternadas
    readonly property color destaque: c("#E8F0FE", "#22355A", "#E2E8FF", "#1B2752")
    readonly property color azulDuia: c("#2E6BE6", "#2E6BE6", "#3D5BFF", "#5B8CFF")            // primária
    readonly property color azulEscuro: c("#255BC7", "#255BC7", "#2F47D9", "#4A76E8")
    readonly property color azulNoite: c("#1A3A73", "#A9C4F7", "#16205C", "#C7D6FF")           // títulos
    readonly property color azulProfundo: "#0F1724"
    readonly property color texto: c("#1F2933", "#E6EAF0", "#0E1430", "#EEF2FF")
    readonly property color textoSecundario: c("#5B6675", "#A3ADBB", "#56608A", "#9AA6C7")
    readonly property color textoApagado: c("#8A94A3", "#7A8494", "#8C95B5", "#66729A")
    readonly property color borda: c("#DDE3EC", "#353B46", "#DADFF2", "#232C4D")
    readonly property color bordaForte: c("#C9D2DE", "#4A5363", "#BFC8EA", "#35427A")
    readonly property color controleDesligado: c("#E4E9F0", "#363C47", "#E1E6F6", "#1C2545")
    readonly property color trilhaCheia: c("#FFFFFF", "#58627A", "#FFFFFF", "#4A5BA8")
    readonly property color realce: escuro ? Qt.rgba(1, 1, 1, futurista ? 0.07 : 0.06) : Qt.rgba(0.06, 0.09, 0.14, 0.05)
    readonly property color pressionado: escuro ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0.06, 0.09, 0.14, 0.11)
    readonly property color selecao: futurista ? Qt.rgba(0.36, 0.55, 1.0, escuro ? 0.28 : 0.16)
                                               : (escuro ? Qt.rgba(0.18, 0.42, 0.90, 0.30) : Qt.rgba(0.18, 0.42, 0.90, 0.14))
    readonly property color sombra: futurista ? (escuro ? Qt.rgba(0.02, 0.03, 0.10, 0.45) : Qt.rgba(0.11, 0.16, 0.42, 0.08))
                                              : (escuro ? Qt.rgba(0, 0, 0, 0.30) : Qt.rgba(0.06, 0.09, 0.14, 0.05))
    readonly property color sucesso: futurista ? "#2DD4A7" : "#2FA67A"
    readonly property color aviso: "#E8A33D"
    readonly property color erro: futurista ? "#FF5C7A" : "#D9534F"

    // Aurora: as três cores do degradê dos controles principais (no estilo padrão, tudo azul Duia)
    readonly property color aurora1: futurista ? (escuro ? "#22D3EE" : "#06B6D4") : azulDuia
    readonly property color aurora2: azulDuia
    readonly property color aurora3: futurista ? (escuro ? "#A78BFA" : "#7C3AED") : azulDuia
    // Borda luminosa dos painéis de vidro
    readonly property color brilho: futurista ? (escuro ? Qt.rgba(0.55, 0.68, 1, 0.28) : Qt.rgba(1, 1, 1, 0.95)) : Qt.rgba(1, 1, 1, 0.9)

    readonly property string fonteTitulo: "Manrope"
    readonly property string fonteTexto: "Inter"
    readonly property string fonteCodigo: "JetBrains Mono"

    readonly property int raio: futurista ? 16 : 12
    readonly property int raioGrande: futurista ? 24 : 18
    readonly property int raioControle: futurista ? 17 : 10       // botões e campos (17 = cápsula em 34 px)
    readonly property int animacao: futurista ? 180 : 140

    // Cor em hex sem "#" para o provedor de ícones (image://duia/NOME/COR)
    function hex(cor) {
        var c = Qt.color(cor)
        function d(v) { var s = Math.round(v * 255).toString(16); return s.length < 2 ? "0" + s : s }
        return d(c.r) + d(c.g) + d(c.b)
    }
}
