#!/usr/bin/env python3
"""DuiaOS — gera as imagens da animação de boot (Plymouth) a partir dos SVGs.

Requer: cairosvg (pip install cairosvg ou python3-cairosvg) e a fonte Manrope.
Resultado: pacotes/duiaos-identidade/raiz/usr/share/plymouth/themes/duiaos/*.png
"""
from pathlib import Path

import cairosvg

PASTA = Path(__file__).resolve().parent
DESTINO = PASTA.parents[1] / "pacotes/duiaos-identidade/raiz/usr/share/plymouth/themes/duiaos"
DESTINO.mkdir(parents=True, exist_ok=True)
for nome in ("simbolo-sem-ponto", "ponto", "nome"):
    cairosvg.svg2png(url=str(PASTA / f"{nome}.svg"), write_to=str(DESTINO / f"{nome}.png"))
    print("Gerado:", DESTINO / f"{nome}.png")
