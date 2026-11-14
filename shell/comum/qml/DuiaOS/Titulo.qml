import QtQuick

Text {
    property int nivel: 1
    color: nivel === 1 ? Tema.azulNoite : Tema.texto
    font { family: Tema.fonteTitulo; pixelSize: nivel === 1 ? 22 : (nivel === 2 ? 15 : 13); weight: Font.Bold }
    elide: Text.ElideRight
}
