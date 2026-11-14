// DuiaOS — cores, fontes e medidas da interface (identidade visual em branding/README.md).
pragma Singleton
import QtQuick

QtObject {
    readonly property color fundo: "#F7F9FC"          // Branco gelo
    readonly property color cartao: "#FFFFFF"
    readonly property color vidro: "#F2F5FAF5"        // painéis flutuantes (quase opacos)
    readonly property color destaque: "#E8F0FE"       // Azul névoa
    readonly property color azulDuia: "#2E6BE6"       // Primária
    readonly property color azulEscuro: "#255BC7"
    readonly property color azulNoite: "#1A3A73"
    readonly property color azulProfundo: "#0F1724"
    readonly property color texto: "#1F2933"
    readonly property color textoSecundario: "#5B6675"
    readonly property color textoApagado: "#8A94A3"
    readonly property color borda: "#DDE3EC"
    readonly property color bordaForte: "#C9D2DE"
    readonly property color controleDesligado: "#E4E9F0"
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
