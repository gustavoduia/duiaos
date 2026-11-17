"""DuiaOS — ícones próprios da interface (traço fino, 24 × 24).

Nitidez (ADR 068): o traço é calculado pelo tamanho em que o ícone APARECE na tela, em pixels, e não
pelo tamanho da imagem gerada. Nos tamanhos pequenos ele fica em pelo menos 1,4 pixel (abaixo disso o
antisserrilhado deixa a linha cinza, falhada); nos grandes cresce bem menos que o desenho (um ícone de
60 pontos com o traço proporcional a um de 18 ficaria com o contorno grosso). Veja traco_px().

A imagem é desenhada no tamanho exato dos pixels da tela (Icone.qml: tamanho × devicePixelRatio), sem
reduzir pela placa de vídeo — reduzir uma imagem do dobro do tamanho é o que deixava as linhas finas
borradas e com falhas.

Os desenhos ficam aqui, em SVG, e o QML os pede ao provedor de imagens com a cor que quiser e o
tamanho em que o ícone aparece:

    Image { source: "image://duia/wifi-3/1F2933/18" }      // nome / cor (hex, sem #) / tamanho visto

Assim o mesmo ícone serve à Barra de Recursos, à Ilha de Aplicativos, ao
Explorador de Arquivos e às Configurações, em qualquer cor. Todos os desenhos
são do DuiaOS (nenhum vem de outro conjunto de ícones).
"""
import math
import re

# Elementos SVG de cada ícone, com "C" no lugar da cor. O contêiner aplica
# traço arredondado (TRACO, afinado nos tamanhos grandes); "fill='C'" pinta por dentro.
TRACO_PX = 1.5                  # espessura, em pixels da tela, de um ícone visto com 18 pontos
TRACO_MINIMO_PX = 1.4           # abaixo disso a linha antisserrilhada fica cinza e falhada
_TRACO_ANTIGO = 1.8             # os traços escritos nos desenhos foram pensados para este


def traco_px(visto):
    """Espessura do traço, em pixels, para um ícone que aparece com `visto` pontos na tela."""
    visto = visto or 18
    return max(TRACO_MINIMO_PX, TRACO_PX * (visto / 18) ** 0.45)


def traco(visto):
    """Espessura do traço em unidades do desenho (24 × 24) para um ícone visto com `visto` pontos."""
    visto = visto or 18
    return round(traco_px(visto) * 24 / visto, 3)

_A = 'stroke-opacity="0.28"'


def _wifi(nivel):
    arcos = ['M8.6 15.6a4.9 4.9 0 0 1 6.8 0', 'M5.6 12.6a9.1 9.1 0 0 1 12.8 0', 'M2.6 9.4a13.4 13.4 0 0 1 18.8 0']
    partes = ['<circle cx="12" cy="19" r="1.4" fill="C" stroke="none"/>']
    for i, d in enumerate(arcos, start=1):
        partes.append(f'<path d="{d}" {"" if i <= nivel else _A}/>')
    return "".join(partes)


def _som(nivel):
    alto = ('<path d="M4 9.5h3.2L12 5.5v13l-4.8-4H4z" fill="C" fill-opacity="0.12"/>')
    ondas = ['M15.5 9.5a3.6 3.6 0 0 1 0 5', 'M18 7a7.2 7.2 0 0 1 0 10']
    partes = [alto]
    for i, d in enumerate(ondas, start=1):
        partes.append(f'<path d="{d}" {"" if i <= nivel else _A}/>')
    return "".join(partes)


def _engrenagem():
    pontos = []
    dentes = 8
    for i in range(dentes * 4):
        angulo = (i / (dentes * 4)) * 2 * math.pi - math.pi / 2
        raio = 9.3 if (i % 4) in (1, 2) else 7.2
        pontos.append(f"{12 + raio * math.cos(angulo):.2f} {12 + raio * math.sin(angulo):.2f}")
    return f'<path d="M{"L".join(pontos)}Z"/><circle cx="12" cy="12" r="3"/>'


def _sol(raio_centro=3.6, curto=False):
    raios = []
    for i in range(8):
        angulo = i * math.pi / 4
        r1, r2 = (6.4, 8.2) if curto else (6.2, 9.2)
        raios.append(f"M{12 + r1 * math.cos(angulo):.2f} {12 + r1 * math.sin(angulo):.2f}"
                     f"L{12 + r2 * math.cos(angulo):.2f} {12 + r2 * math.sin(angulo):.2f}")
    return f'<circle cx="12" cy="12" r="{raio_centro}"/><path d="{" ".join(raios)}"/>'


DESENHOS = {
    "wifi-0": _wifi(0), "wifi-1": _wifi(1), "wifi-2": _wifi(2), "wifi-3": _wifi(3),
    "wifi-desligado": _wifi(0).replace(_A, _A) + '<path d="M4 4l16 16"/>',
    "som-0": _som(0), "som-1": _som(1), "som-2": _som(2),
    "som-mudo": _som(0).replace(f' {_A}', ' stroke-opacity="0"') + '<path d="M15.5 9.5l5 5M20.5 9.5l-5 5"/>',
    "microfone": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
    "bluetooth": '<path d="M7 7.5l10 9-5 4.5V3l5 4.5-10 9"/>',
    "brilho": _sol(),
    "brilho-baixo": _sol(3, True),
    "lua": '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    "aviao": ('<path d="M12 2.8c.8 0 1.4.7 1.4 1.5v5.2l7.1 4.3v1.9l-7.1-2.2v4.6l2 1.5v1.6L12 20.4l-3.4.8v-1.6l2-1.5'
              'v-4.6l-7.1 2.2v-1.9l7.1-4.3V4.3c0-.8.6-1.5 1.4-1.5z"/>'),
    "teclado": ('<rect x="2.5" y="6" width="19" height="12" rx="2.2"/>'
                '<path d="M6.5 10h.01M10 10h.01M14 10h.01M17.5 10h.01M7.5 14h9"/>'),
    "energia": '<path d="M12 3v8"/><path d="M6.4 6.6a8 8 0 1 0 11.2 0"/>',
    "engrenagem": _engrenagem(),
    "controles": ('<rect x="3" y="4.5" width="18" height="6.5" rx="3.25"/><circle cx="8" cy="7.75" r="1.6" fill="C"/>'
                  '<rect x="3" y="13" width="18" height="6.5" rx="3.25"/><circle cx="16" cy="16.25" r="1.6" fill="C"/>'),
    "pasta": '<path d="M3 7.5a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2v7.8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "sino": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15zM10 20.5a2 2 0 0 0 4 0"/>',
    "sino-desligado": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15zM10 20.5a2 2 0 0 0 4 0"/><path d="M4 4l16 16"/>',
    # Pasta dos ícones grandes (Explorador, Área de Trabalho): duas formas cheias, sem contorno
    "pasta-cheia": ('<path d="M3 7.2a2 2 0 0 1 2-2h4c.6 0 1.1.2 1.5.6L12 7.3h7a2 2 0 0 1 2 2V12H3z" fill="C" fill-opacity="0.55" stroke="none"/>'
                    '<path d="M3 10.7a1.9 1.9 0 0 1 1.9-1.9h14.2a1.9 1.9 0 0 1 1.9 1.9v6.6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" fill="C" stroke="none"/>'),
    "pasta-aplicativos": ('<path d="M3 7.5a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2v7.8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
                          '<path d="M9.2 16.8l2.8-6.3 2.8 6.3M10.2 14.6h3.6" stroke-width="1.6"/>'),
    "pasta-downloads": ('<path d="M3 7.5a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2v7.8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
                        '<path d="M12 10.5v6M9.5 14.3l2.5 2.5 2.5-2.5" stroke-width="1.6"/>'),
    # Atualizações do sistema: duas setas em círculo com uma seta para baixo no meio (ADR 058)
    "atualizacao": '<path d="M19.5 9.5A8 8 0 0 0 5.2 7.6M4.5 14.5a8 8 0 0 0 14.3 1.9"/><path d="M5 3.8v4h4M19 20.2v-4h-4"/><path d="M12 8.5v6M9.6 12.3l2.4 2.4 2.4-2.4"/>',
    "download": '<path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/>',
    "documento": '<path d="M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6"/>',
    "imagem": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.7"/><path d="M21 16l-5-5-9 8"/>',
    "musica": '<path d="M9 17.5V6l11-2v11.5"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="15.5" r="2.5"/>',
    "video": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10.5l5-3v9l-5-3"/>',
    "lixeira": '<path d="M4 7h16M9.5 7V4.5h5V7M6 7l1 13h10l1-13M10 11v5.5M14 11v5.5"/>',
    # Cheia: sem a tampa, com papéis amassados saindo pela boca (como a Lixeira cheia do macOS) — dá para
    # ver de longe que há algo dentro; a diferença antiga (dois tracinhos no lugar de outros dois) não se via
    "lixeira-cheia": ('<path d="M4.5 9.5h15M6.2 9.5l1 10.5h9.6l1-10.5M10 13v4M14 13v4"/>'
                      '<path d="M7.4 9.5l1-3.9 3.2 1.4 2.4-3 2.5 3.6 1 1.9" fill="C" fill-opacity="0.22" stroke-linejoin="round"/>'),
    "casa": '<path d="M3 11l9-7 9 7M5.5 9.5V20h4.5v-6h4v6h4.5V9.5"/>',
    "monitor": '<rect x="2.5" y="4" width="19" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "aplicativos": ('<rect x="4" y="4" width="6.5" height="6.5" rx="1.8"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.8"/>'
                    '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1.8"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.8"/>'),
    "busca": '<circle cx="10.5" cy="10.5" r="6.2"/><path d="M20 20l-5-5"/>',
    "seta-esquerda": '<path d="M15 5l-7 7 7 7"/>',
    "seta-direita": '<path d="M9 5l7 7-7 7"/>',
    "seta-cima": '<path d="M5 15l7-7 7 7"/>',
    "seta-baixo": '<path d="M5 9l7 7 7-7"/>',
    "lista": '<path d="M8.5 6H21M8.5 12H21M8.5 18H21M3.8 6h.01M3.8 12h.01M3.8 18h.01"/>',
    "cadeado": '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    "captura": '<path d="M4 8.5h3l2-3h6l2 3h3V19H4z"/><circle cx="12" cy="13.3" r="3.3"/>',
    "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
    "usuarios": ('<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/>'
                 '<path d="M15.5 5.2a3.5 3.5 0 0 1 0 6.6M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>'),
    "sair": '<path d="M14 4H6v16h8M10 12h10M16.5 8.5L20 12l-3.5 3.5"/>',
    "reiniciar": '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4v4h-4"/>',
    "relogio": '<circle cx="12" cy="12" r="8.8"/><path d="M12 7v5l3.3 2"/>',
    "globo": '<circle cx="12" cy="12" r="8.8"/><path d="M3.2 12h17.6M12 3.2c2.6 2.4 3.8 5.4 3.8 8.8s-1.2 6.4-3.8 8.8c-2.6-2.4-3.8-5.4-3.8-8.8s1.2-6.4 3.8-8.8z"/>',
    "disco": '<rect x="3" y="6" width="18" height="12" rx="2.2"/><path d="M3 13.5h18M7 16h.01"/>',
    "ejetar": '<path d="M12 5l7 8H5zM5 18h14"/>',
    "mais": '<path d="M12 5v14M5 12h14"/>',
    "fechar": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "escudo": '<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8-7.5 9.5-4.3-1.5-7.5-4.9-7.5-9.5V6z"/>',
    "wise": ('<rect x="3.5" y="4.5" width="17" height="15" rx="5"/><rect x="6.5" y="8" width="11" height="7" rx="3.2"/>'
             '<path d="M10 10.6v1.8M14 10.6v1.8"/>'),
    "ia": ('<path d="M10.5 4l1.7 4.8L17 10.5l-4.8 1.7L10.5 17l-1.7-4.8L4 10.5l4.8-1.7z"/>'
           '<path d="M18 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/>'),
    "paleta": ('<path d="M12 3.2a8.8 8.8 0 1 0 0 17.6c1 0 1.6-.7 1.6-1.5 0-1.1-1-1.5-1-2.5 0-.9.7-1.5 1.6-1.5H16'
               'a4.8 4.8 0 0 0 4.8-4.8c0-4-3.9-7.3-8.8-7.3z"/>'
               '<circle cx="7.6" cy="11" r="1.1" fill="C"/><circle cx="10.5" cy="7.3" r="1.1" fill="C"/>'
               '<circle cx="15" cy="7.8" r="1.1" fill="C"/>'),
    "bateria": '<rect x="2.5" y="7" width="17" height="10" rx="2.4"/><path d="M22 10.5v3"/><rect x="5" y="9.5" width="9" height="5" rx="1" fill="C" stroke="none"/>',
    "barra": '<rect x="3" y="4" width="18" height="16" rx="2.2"/><path d="M3 8.5h18M8.5 16.5h7"/>',
    "lapis": '<path d="M4 20h4.2L19.5 8.7a2.1 2.1 0 0 0-3-3L5.2 17v3"/>',
    "copiar": ('<rect x="8.5" y="8.5" width="11.5" height="11.5" rx="2"/>'
               '<path d="M15.5 8.5V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5"/>'),
    "recortar": '<circle cx="6.5" cy="6.5" r="2.6"/><circle cx="6.5" cy="17.5" r="2.6"/><path d="M8.6 8l11 10M8.6 16l11-10"/>',
    "colar": '<rect x="5.5" y="4.5" width="13" height="16.5" rx="2"/><path d="M9 4.5V3h6v1.5M9 10h6M9 14h6"/>',
    "info": '<circle cx="12" cy="12" r="8.8"/><path d="M12 11v5.5M12 7.8h.01"/>',
    "restaurar": '<path d="M4.5 12a7.5 7.5 0 1 0 2.3-5.4"/><path d="M4.5 4v4h4"/>',
    "olho": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="2.2"/><path d="M7 9.5l3 2.5-3 2.5M12.5 15H17"/>',
    "abrir": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "vazio": "",                       # espaço de ícone em branco (menus com marca)
    "sacola": ('<path d="M5 8.5h14l-1 11a1.6 1.6 0 0 1-1.6 1.5H7.6A1.6 1.6 0 0 1 6 19.5z"/>'
               '<path d="M9 10.5V7a3 3 0 0 1 6 0v3.5"/>'),
    "verificado": ('<path d="M12 3l2.3 1.7 2.8-.2.9 2.7 2.3 1.6-.9 2.7.9 2.7-2.3 1.6-.9 2.7-2.8-.2L12 21l-2.3-1.7-2.8.2-.9-2.7'
                   '-2.3-1.6.9-2.7-.9-2.7 2.3-1.6.9-2.7 2.8.2z"/><path d="M8.8 12.2l2.2 2.2 4.2-4.4"/>'),
    "estrela": '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 17l-5.2 2.7 1-5.9-4.3-4.1 5.9-.8z"/>',
    "nova-pasta": '<path d="M3 7.5a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2v7.8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM12 11v5M9.5 13.5h5"/>',
    "arquivo": '<path d="M6 3h8l4 4v14H6zM14 3v4h4"/>',
    "compactado": '<path d="M6 3h12v18H6zM11 3v2h2v2h-2v2h2v2h-2"/><rect x="10.5" y="13" width="3" height="3.5" rx=".8"/>',
    "codigo": '<path d="M8.5 7.5L4 12l4.5 4.5M15.5 7.5L20 12l-4.5 4.5"/>',
    "planilha": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 3v18"/>',
    "apresentacao": '<rect x="3" y="4" width="18" height="12" rx="1.8"/><path d="M12 16v4M8.5 20h7"/>',
    "pdf": '<path d="M6 3h8l4 4v14H6zM14 3v4h4"/><path d="M9 16v-4h1.3a1.2 1.2 0 0 1 0 2.4H9"/>',
    "computador": '<rect x="4" y="4.5" width="16" height="11" rx="1.6"/><path d="M2.5 19.5h19"/>',
    "ponto": '<circle cx="12" cy="12" r="4" fill="C" stroke="none"/>',
    "recentes": '<circle cx="12" cy="12" r="8.8"/><path d="M12 7v5l3.3 2"/>',
    "rede": ('<rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/>'
             '<rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-2h12v2"/>'),
}


def svg(nome, cor="1F2933", visto=0):
    """SVG completo do ícone na cor pedida (hex sem '#'), com o traço certo para um ícone visto com `visto`
    pontos (o tamanho da imagem não importa: o SVG é vetorial). None se o nome não existe."""
    desenho = DESENHOS.get(nome)
    if desenho is None:
        return None
    cor = "#" + "".join(c for c in cor if c in "0123456789abcdefABCDEF")[:8]
    if len(cor) not in (4, 7, 9):
        cor = "#1F2933"
    espessura = traco(visto)
    fator = espessura / _TRACO_ANTIGO
    corpo = re.sub(r'stroke-width="([0-9.]+)"', lambda m: f'stroke-width="{round(float(m.group(1)) * fator, 3)}"', desenho)
    corpo = corpo.replace('"C"', f'"{cor}"')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" '
            f'fill="none" stroke="{cor}" stroke-width="{espessura}" stroke-linecap="round" stroke-linejoin="round">'
            f'{corpo}</svg>')


def registrar(engine):
    """Registra o provedor "image://duia/NOME/COR/VISTO" na engine QML."""
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtQuick import QQuickImageProvider
    from PySide6.QtSvg import QSvgRenderer

    class Provedor(QQuickImageProvider):
        def __init__(self):
            super().__init__(QQuickImageProvider.ImageType.Image)

        def requestImage(self, pedido, tamanho, tamanho_pedido):
            nome, _, resto = pedido.partition("/")
            cor, _, visto = resto.partition("/")
            lado_l = tamanho_pedido.width() if tamanho_pedido.width() > 0 else 48
            lado_a = tamanho_pedido.height() if tamanho_pedido.height() > 0 else lado_l
            try:
                visto = float(visto)
            except ValueError:
                visto = lado_l / 2                       # pedidos antigos (sem o tamanho visto): o dobro
            texto = svg(nome, cor or "1F2933", visto) or svg("arquivo", cor or "1F2933", visto)
            imagem = QImage(lado_l, lado_a, QImage.Format.Format_ARGB32_Premultiplied)
            imagem.fill(Qt.GlobalColor.transparent)
            pintor = QPainter(imagem)
            pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
            QSvgRenderer(QByteArray(texto.encode())).render(pintor, QRectF(0, 0, lado_l, lado_a))
            pintor.end()
            if tamanho is not None:
                tamanho.setWidth(lado_l)
                tamanho.setHeight(lado_a)
            return imagem

    engine.addImageProvider("duia", Provedor())
