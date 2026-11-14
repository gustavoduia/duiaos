// DuiaOS — cores, fontes e medidas da interface (identidade visual em branding/README.md),
// nos modos claro e escuro. O modo vem de "aparencia" (shell/comum/interface.py), que lê as
// preferências (Configurações › Aparência) e avisa todas as janelas na hora.
pragma Singleton
import QtQuick

QtObject {
    readonly property bool escuro: typeof aparencia !== "undefined" && aparencia !== null && aparencia.escuro

    readonly property color fundo: escuro ? "#1B1F27" : "#F7F9FC"           // Branco gelo
    readonly property color cartao: escuro ? "#262B34" : "#FFFFFF"
    readonly property color vidro: escuro ? "#F2262B35" : "#F2F4F7FB"         // painéis flutuantes
    readonly property color barra: escuro ? "#F01B1F27" : "#F2F7F9FC"         // Barra de Recursos
    readonly property color ilha: escuro ? "#E81F232B" : "#EBF7F9FC"          // Ilha de Aplicativos
    readonly property color lateral: escuro ? "#20242C" : "#EEF2F7"           // barras laterais dos aplicativos
    readonly property color listra: escuro ? "#22272F" : "#F1F4F8"            // linhas alternadas
    readonly property color destaque: escuro ? "#22355A" : "#E8F0FE"          // Azul névoa
    readonly property color azulDuia: "#2E6BE6"                               // Primária
    readonly property color azulEscuro: "#255BC7"
    readonly property color azulNoite: escuro ? "#A9C4F7" : "#1A3A73"         // títulos
    readonly property color azulProfundo: "#0F1724"
    readonly property color texto: escuro ? "#E6EAF0" : "#1F2933"
    readonly property color textoSecundario: escuro ? "#A3ADBB" : "#5B6675"
    readonly property color textoApagado: escuro ? "#7A8494" : "#8A94A3"
    readonly property color borda: escuro ? "#353B46" : "#DDE3EC"
    readonly property color bordaForte: escuro ? "#4A5363" : "#C9D2DE"
    readonly property color controleDesligado: escuro ? "#363C47" : "#E4E9F0"
    readonly property color trilhaCheia: escuro ? "#58627A" : "#FFFFFF"       // parte cheia do deslizante
    readonly property color realce: escuro ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(0.06, 0.09, 0.14, 0.05)   // passar o mouse
    readonly property color pressionado: escuro ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0.06, 0.09, 0.14, 0.11)
    readonly property color selecao: escuro ? Qt.rgba(0.18, 0.42, 0.90, 0.30) : Qt.rgba(0.18, 0.42, 0.90, 0.14)
    readonly property color sombra: escuro ? Qt.rgba(0, 0, 0, 0.30) : Qt.rgba(0.06, 0.09, 0.14, 0.05)
    readonly property color sucesso: "#2FA67A"
    readonly property color aviso: "#E8A33D"
    readonly property color erro: "#D9534F"

    readonly property string fonteTitulo: "Manrope"
    readonly property string fonteTexto: "Inter"
    readonly property string fonteCodigo: "JetBrains Mono"

    readonly property int raio: 12
    readonly property int raioGrande: 18
    readonly property int animacao: 140

    // Cor em hex sem "#" para o provedor de ícones (image://duia/NOME/COR)
    function hex(cor) {
        var c = Qt.color(cor)
        function d(v) { var s = Math.round(v * 255).toString(16); return s.length < 2 ? "0" + s : s }
        return d(c.r) + d(c.g) + d(c.b)
    }
}
