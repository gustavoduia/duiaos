// Ícone próprio do DuiaOS (shell/comum/icones.py), na cor pedida.
import QtQuick

Image {
    property string nome: "arquivo"
    property color cor: Tema.texto
    property int tamanho: 18
    width: tamanho; height: tamanho
    sourceSize: Qt.size(tamanho * 2, tamanho * 2)
    source: nome !== "" ? "image://duia/" + nome + "/" + Tema.hex(cor) : ""
    smooth: true
    asynchronous: false
}
