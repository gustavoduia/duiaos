"""DuiaOS — Configurações: cópia de fundos importados e foto da conta (sem interface; testado)."""
import shutil
from pathlib import Path

LADO_FOTO = 256


def copiar_sem_sobrescrever(origem, pasta):
    """Copia para a pasta; se já existe um arquivo igual (mesmo nome e tamanho), reaproveita."""
    origem, pasta = Path(origem), Path(pasta)
    alvo = pasta / origem.name
    if alvo.exists() and alvo.stat().st_size == origem.stat().st_size:
        return alvo
    numero = 2
    while alvo.exists():
        alvo = pasta / f"{origem.stem} ({numero}){origem.suffix}"
        numero += 1
    shutil.copy2(origem, alvo)
    return alvo


def foto_redonda(origem, nome=""):
    """PNG 256×256 redondo (fundo transparente) a partir de uma imagem ou de uma cor "#RRGGBB" com a inicial."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath
    imagem = QImage(LADO_FOTO, LADO_FOTO, QImage.Format.Format_ARGB32_Premultiplied)
    imagem.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagem)
    pintor.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    caminho = QPainterPath()
    caminho.addEllipse(QRectF(0, 0, LADO_FOTO, LADO_FOTO))
    pintor.setClipPath(caminho)
    if origem.startswith("#"):
        cor = QColor(origem)
        if not cor.isValid():
            pintor.end()
            raise ValueError("Cor inválida.")
        degrade = QLinearGradient(0, 0, 0, LADO_FOTO)
        degrade.setColorAt(0, cor.lighter(130))
        degrade.setColorAt(1, cor)
        pintor.fillRect(0, 0, LADO_FOTO, LADO_FOTO, degrade)
        fonte = QFont("Manrope", 110)
        fonte.setBold(True)
        pintor.setFont(fonte)
        pintor.setPen(QColor("white"))
        pintor.drawText(QRectF(0, 0, LADO_FOTO, LADO_FOTO), Qt.AlignmentFlag.AlignCenter, (nome or "?")[:1].upper())
    else:
        arquivo = origem[7:] if origem.startswith("file://") else origem
        from urllib.parse import unquote
        foto = QImage(unquote(arquivo))
        if foto.isNull():
            pintor.end()
            raise ValueError("Não foi possível abrir esta imagem.")
        lado = min(foto.width(), foto.height())
        foto = foto.copy((foto.width() - lado) // 2, (foto.height() - lado) // 2, lado, lado)
        pintor.drawImage(QRectF(0, 0, LADO_FOTO, LADO_FOTO), foto)
    pintor.end()
    dados = QByteArray()
    buffer = QBuffer(dados)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    imagem.save(buffer, "PNG")
    return bytes(dados.data())
