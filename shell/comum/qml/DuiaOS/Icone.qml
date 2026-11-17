// Ícone próprio do DuiaOS (shell/comum/icones.py), na cor pedida.
//
// Nitidez (ADR 068): a imagem é desenhada no tamanho exato dos pixels da tela (tamanho × a densidade da
// tela), e o traço é escolhido pelo tamanho em que o ícone aparece. Antes ela era gerada com o dobro do
// tamanho e reduzida pela placa de vídeo, o que deixava as linhas finas borradas e falhadas.
import QtQuick
import QtQuick.Window

Image {
    id: raiz
    property string nome: "arquivo"
    property color cor: Tema.texto
    property int tamanho: 18
    // Lado com que o desenho é gerado. Quem anima o tamanho (a Ilha, na ampliação) fixa este valor no
    // maior tamanho: sem isso, cada mudança de tamanho refaz a imagem e o ícone pisca. A imagem maior,
    // mostrada menor: até o dobro, a redução simples da placa de vídeo fica nítida; acima disso serrilha,
    // e entra o mipmap (que em compensação deixa um pouco mais macio).
    property int resolucao: 0
    // Tamanho em que o ícone costuma aparecer, para escolher o traço quando ele é animado (a Ilha em
    // repouso). Sem animação, é o próprio tamanho.
    property int base: 0
    readonly property real densidade: Screen.devicePixelRatio > 0 ? Screen.devicePixelRatio : 1
    readonly property int lado: Math.max(1, Math.round((resolucao || tamanho) * densidade))
    width: tamanho; height: tamanho
    sourceSize: Qt.size(lado, lado)
    source: nome !== "" ? "image://duia/" + nome + "/" + Tema.hex(cor) + "/" + (resolucao ? (base || resolucao) : tamanho) : ""
    smooth: true
    mipmap: resolucao > 2 * (base || tamanho)
    asynchronous: false
}
