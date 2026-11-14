// Vídeo de fundo, sem som e em laço (precisa do qml6-module-qtmultimedia).
import QtQuick
import QtMultimedia

Item {
    property string fonte: ""
    property bool tocando: true
    onTocandoChanged: tocando ? jogador.play() : jogador.pause()
    onFonteChanged: if (tocando && fonte !== "") jogador.play()
    MediaPlayer {
        id: jogador
        source: parent.fonte
        loops: MediaPlayer.Infinite
        videoOutput: saida
        audioOutput: null
        Component.onCompleted: if (parent.tocando) play()
    }
    VideoOutput { id: saida; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectCrop }
}
