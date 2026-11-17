#!/usr/bin/env python3
"""DuiaOS — gera o tema do menu de boot da ISO (GRUB, para UEFI e Macs/máquinas virtuais, e o menu BIOS).

Saída (vai para a ISO pelo live-build, em includes.binary):
  build/config/includes.binary/boot/grub/duiaos/   theme.txt, fundo.jpg, marca.png, ícones, fontes .pf2
  build/config/includes.binary/isolinux/duiaos-fundo.png   fundo do menu BIOS (1024x768)

Precisa de: Pillow, cairosvg, grub-mkfont (pacote grub-common) e as fontes Inter e Manrope instaladas.
  python3 branding/grub/gerar-tema.py [--chroot /srv/trixie]
O menu (as duas opções) é escrito no build por build/config/hooks/normal/0600-duiaos-menu-boot.hook.binary.
"""
import argparse
import io
import shlex
import subprocess
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "build/config/includes.binary/boot/grub/duiaos"
ISOLINUX = RAIZ / "build/config/includes.binary/isolinux"
LUA = RAIZ / "pacotes/duiaos-identidade/raiz/usr/share/duiaos/papel-de-parede/lua.jpg"
FONTES = {
    "inter-regular": "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
    "inter-semibold": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "manrope-extrabold": "/usr/share/fonts/truetype/manrope/Manrope-ExtraBold.ttf",
}
SIMBOLO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="12 8 104 104">
  <defs><linearGradient id="t" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#C9D6FF"/></linearGradient>
  <radialGradient id="p" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#7DF3FF"/><stop offset="1" stop-color="#3D7BFF"/></radialGradient></defs>
  <path d="M58 100H28V20H58A40 40 0 0 1 95.59 73.68" fill="none" stroke="url(#t)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="80.94" cy="92.77" r="8" fill="url(#p)"/></svg>"""
ICONES = {
    # Instalar: um disco com a seta entrando
    "instalar": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3v9M8.5 8.5L12 12l3.5-3.5"/><rect x="3.5" y="14" width="17" height="6.5" rx="2"/><path d="M16.5 17.3h.01"/></g></svg>""",
    # Carregar: o símbolo de "experimentar" (um play dentro do círculo)
    "carregar": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="8.5"/><path d="M10.2 8.8l5 3.2-5 3.2z"/></g></svg>""",
}


def svg_png(svg, tamanho):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=tamanho, output_height=tamanho))).convert("RGBA")


def fundo(largura, altura, escurecer=0.58):
    """A Lua, recortada para a tela, escurecida e com as bordas mais escuras."""
    foto = Image.open(LUA).convert("RGB")
    escala = max(largura / foto.width, altura / foto.height)
    foto = foto.resize((round(foto.width * escala), round(foto.height * escala)), Image.LANCZOS)
    x, y = (foto.width - largura) // 2, (foto.height - altura) // 2
    foto = foto.crop((x, y, x + largura, y + altura))
    noite = Image.new("RGB", (largura, altura), (7, 11, 24))
    foto = Image.blend(foto, noite, escurecer)
    # vinheta: escurece em cima e embaixo, para o texto ficar legível
    mascara = Image.new("L", (largura, altura), 0)
    d = ImageDraw.Draw(mascara)
    for i in range(altura):
        t = i / altura
        v = int(255 * max(0.0, (abs(t - 0.52) - 0.18) / 0.34) ** 1.4) if abs(t - 0.52) > 0.18 else 0
        d.line([(0, i), (largura, i)], fill=min(255, v))
    return Image.composite(noite, foto, mascara.filter(ImageFilter.GaussianBlur(30)))


def marca(destino):
    """O símbolo e o nome DuiaOS, numa imagem só (o GRUB não desenha SVG)."""
    simbolo = svg_png(SIMBOLO, 132)
    fonte = ImageFont.truetype(FONTES["manrope-extrabold"], 58)
    caixa = fonte.getbbox("DuiaOS")
    largura = max(simbolo.width, caixa[2]) + 40
    imagem = Image.new("RGBA", (largura, 132 + 26 + 72), (0, 0, 0, 0))
    imagem.alpha_composite(simbolo, ((largura - simbolo.width) // 2, 0))
    ImageDraw.Draw(imagem).text(((largura - caixa[2]) // 2, 132 + 22), "DuiaOS", font=fonte, fill=(255, 255, 255, 255))
    imagem.save(destino)
    return imagem.size


def caixa_9(prefixo, raio, preenchimento, borda, largura_borda):
    """Uma caixa de cantos redondos em 9 pedaços (o GRUB estica as bordas e o meio)."""
    lado = raio * 2 + 4
    img = Image.new("RGBA", (lado * 4, lado * 4), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=raio * 4,
                                          fill=preenchimento, outline=borda, width=largura_borda * 4)
    img = img.resize((lado, lado), Image.LANCZOS)
    c = raio + 1
    partes = {"nw": (0, 0, c, c), "n": (c, 0, lado - c, c), "ne": (lado - c, 0, lado, c),
              "w": (0, c, c, lado - c), "c": (c, c, lado - c, lado - c), "e": (lado - c, c, lado, lado - c),
              "sw": (0, lado - c, c, lado), "s": (c, lado - c, lado - c, lado), "se": (lado - c, lado - c, lado, lado)}
    for nome, area in partes.items():
        img.crop(area).save(DESTINO / f"{prefixo}_{nome}.png")


def fontes_pf2(grub_mkfont, raiz_chroot=""):
    """Fontes do GRUB (.pf2). Com --chroot, o grub-mkfont roda dentro dele (fontes e saída lá dentro)."""
    for nome, tamanho, arquivo in (("Inter Regular", 16, "inter-regular"), ("Inter Regular", 18, "inter-regular"),
                                   ("Inter SemiBold", 24, "inter-semibold")):
        final = DESTINO / f"{arquivo}-{tamanho}.pf2"
        saida = f"/tmp/{final.name}" if raiz_chroot else str(final)
        comando = (["chroot", raiz_chroot] if raiz_chroot else []) + shlex.split(grub_mkfont)
        subprocess.run(comando + ["-s", str(tamanho), "-n", nome, "-o", saida, FONTES[arquivo]], check=True)
        if raiz_chroot:
            Path(raiz_chroot + saida).replace(final)


TEMA = """# DuiaOS — tema do menu de boot da ISO (gerado por branding/grub/gerar-tema.py)
title-text: ""
desktop-image: "fundo.jpg"
desktop-image-scale-method: "crop"
desktop-color: "#070B18"
message-font: "Inter Regular 18"
message-color: "#EEF2FF"
terminal-font: "Inter Regular 16"
terminal-box: "terminal_*.png"

+ image {
    file = "marca.png"
    left = 50%-{meia_marca}
    top = 50%-{acima_marca}
}

+ boot_menu {
    left = 50%-310
    top = 50%+22
    width = 620
    height = 200
    item_font = "Inter SemiBold 24"
    selected_item_font = "Inter SemiBold 24"
    item_color = "#B9C3E6"
    selected_item_color = "#FFFFFF"
    item_height = 52
    item_spacing = 48
    item_padding = 4
    icon_width = 36
    icon_height = 36
    item_icon_space = 20
    item_pixmap_style = "item_*.png"
    selected_item_pixmap_style = "escolhido_*.png"
    scrollbar = false
}

+ label {
    id = "__timeout__"
    left = 0
    top = 100%-92
    width = 100%
    align = "center"
    font = "Inter Regular 18"
    color = "#A7B2D6"
    text = "Começa sozinho em %d s"
}

+ label {
    left = 0
    top = 100%-58
    width = 100%
    align = "center"
    font = "Inter Regular 16"
    color = "#6F7AA3"
    text = "Use as setas para escolher e Enter para começar"
}
"""


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--grub-mkfont", default="grub-mkfont", help="comando do grub-mkfont")
    argumentos.add_argument("--chroot", default="", help="roda o grub-mkfont dentro deste chroot (ex.: /srv/trixie)")
    opcoes = argumentos.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "icons").mkdir(exist_ok=True)
    ISOLINUX.mkdir(parents=True, exist_ok=True)

    fundo(1920, 1080).save(DESTINO / "fundo.jpg", quality=86, optimize=True, progressive=False)
    largura, altura = marca(DESTINO / "marca.png")
    for nome, svg in ICONES.items():
        svg_png(svg, 36).save(DESTINO / "icons" / f"{nome}.png")
    caixa_9("item", 18, (255, 255, 255, 14), (255, 255, 255, 34), 1)
    caixa_9("escolhido", 18, (61, 91, 255, 70), (125, 160, 255, 230), 2)
    caixa_9("terminal", 12, (7, 11, 24, 235), (60, 72, 120, 255), 1)
    fontes_pf2(opcoes.grub_mkfont, opcoes.chroot)
    (DESTINO / "theme.txt").write_text(TEMA.replace("{meia_marca}", str(largura // 2)).replace("{acima_marca}", str(altura + 40)))

    # Menu BIOS (isolinux/vesamenu): 1024x768, com a marca no alto
    bios = fundo(1024, 768, 0.62).convert("RGBA")
    m = Image.open(DESTINO / "marca.png").convert("RGBA")
    m = m.resize((m.width * 2 // 3, m.height * 2 // 3), Image.LANCZOS)
    bios.alpha_composite(m, ((1024 - m.width) // 2, 150))
    bios.convert("RGB").save(ISOLINUX / "duiaos-fundo.png", optimize=True)
    print("tema gerado em", DESTINO.relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
