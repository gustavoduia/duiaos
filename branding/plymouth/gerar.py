#!/usr/bin/env python3
"""DuiaOS — gera as imagens da inicialização a partir dos SVGs: a animação de boot (Plymouth),
a tela de espera do F12 e a logomarca do menu de escolha do sistema (GRUB).

Requer: cairosvg (pip install cairosvg ou python3-cairosvg).
"""
from pathlib import Path

import cairosvg

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1] / "pacotes/duiaos-identidade/raiz/usr/share"
IMAGENS = [
    (PASTA / "simbolo-sem-ponto.svg", RAIZ / "plymouth/themes/duiaos/simbolo-sem-ponto.png"),
    (PASTA / "ponto.svg", RAIZ / "plymouth/themes/duiaos/ponto.png"),
    (PASTA.parent / "grub/inicio.svg", RAIZ / "duiaos/grub/duiaos-inicio.png"),
    (PASTA.parent / "grub/logo-grub.svg", RAIZ / "grub/themes/duiaos/logo.png"),
]
for origem, destino in IMAGENS:
    destino.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(origem), write_to=str(destino))
    print("Gerado:", destino)
