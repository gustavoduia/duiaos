// DuiaOS — símbolo Órbita: o "D" aberto e o ponto em órbita.
import QtQuick
import "estilo.js" as Estilo

Canvas {
    id: simbolo
    property color corTraco: Estilo.azulNoite
    property color corPonto: Estilo.azulDuia
    width: 22; height: 22

    onCorTracoChanged: requestPaint()
    onCorPontoChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        ctx.scale(width / 104, height / 104)
        ctx.translate(-12, -8)
        ctx.lineWidth = 14
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.strokeStyle = corTraco
        ctx.beginPath()
        ctx.moveTo(58, 100)
        ctx.lineTo(28, 100)
        ctx.lineTo(28, 20)
        ctx.lineTo(58, 20)
        ctx.arc(58, 60, 40, -Math.PI / 2, 20 * Math.PI / 180, false)
        ctx.stroke()
        ctx.fillStyle = corPonto
        ctx.beginPath()
        ctx.arc(80.94, 92.77, 8, 0, 2 * Math.PI)
        ctx.fill()
    }
}
