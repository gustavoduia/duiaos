import QtQuick

Text {
    property bool secundario: false
    color: secundario ? Tema.textoSecundario : Tema.texto
    font { family: Tema.fonteTexto; pixelSize: secundario ? 12 : 13 }
    wrapMode: Text.WordWrap
}
