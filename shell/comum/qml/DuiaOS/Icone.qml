// Ícone próprio do DuiaOS (shell/comum/icones.py), na cor pedida.
import QtQuick

Image {
    property string nome: "arquivo"
    property color cor: Tema.texto
    property int tamanho: 18
    // Lado com que o desenho é gerado. Quem anima o tamanho (a Ilha, na ampliação) fixa este valor no
    // maior tamanho: sem isso, cada mudança de tamanho refaz a imagem e o ícone pisca.
    property int resolucao: 0
    width: tamanho; height: tamanho
    sourceSize: Qt.size((resolucao || tamanho) * 2, (resolucao || tamanho) * 2)
    source: nome !== "" ? "image://duia/" + nome + "/" + Tema.hex(cor) : ""
    smooth: true
    asynchronous: false
}
