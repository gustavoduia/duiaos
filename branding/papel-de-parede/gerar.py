#!/usr/bin/env python3
"""DuiaOS — gera a imagem do papel de parede a partir de orbita.svg.

Requer: pip install cairosvg  (ou o pacote python3-cairosvg) e ImageMagick.
Resultado: pacotes/duiaos-identidade/raiz/usr/share/duiaos/papel-de-parede/orbita.jpg
"""
import subprocess
from pathlib import Path

import cairosvg

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
DESTINO = RAIZ / "pacotes/duiaos-identidade/raiz/usr/share/duiaos/papel-de-parede/orbita.jpg"
DESTINO.parent.mkdir(parents=True, exist_ok=True)
png = PASTA / "orbita.tmp.png"
cairosvg.svg2png(url=str(PASTA / "orbita.svg"), write_to=str(png))
# JPEG de alta qualidade: o degradê suave fica leve (cerca de 230 KB em 4K).
subprocess.run(["convert", str(png), "-quality", "92", "-sampling-factor", "4:4:4",
                "-strip", str(DESTINO)], check=True)
png.unlink()
print("Papel de parede gerado:", DESTINO)
