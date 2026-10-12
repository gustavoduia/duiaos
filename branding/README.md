# Identidade visual do DuiaOS

Logotipo: conceito **Órbita** — um “D” aberto com um ponto em órbita.

| Arquivo | Uso |
| --- | --- |
| `logo/duiaos-simbolo.svg` | Símbolo para fundos claros |
| `logo/duiaos-simbolo-escuro.svg` | Símbolo para fundos escuros |
| `logo/duiaos-icone-app.svg` | Ícone de aplicativo (quadrado azul) |

## Papel de parede e animação de boot

| Arquivo | Uso |
| --- | --- |
| `papel-de-parede/orbita.svg` | Papel de parede padrão "Órbita" (fonte); `gerar.py` cria o JPEG 4K da ISO |
| `plymouth/*.svg` | Imagens da animação de boot (Plymouth); `gerar.py` cria os PNGs do tema `duiaos` |
| `grub/*.svg` | Menu de boot (GRUB) |

Para regenerar as imagens (precisa de `cairosvg`, ImageMagick e da fonte Manrope):

```bash
python3 branding/papel-de-parede/gerar.py
python3 branding/plymouth/gerar.py
```

## Paleta

| Papel | Nome | Hex |
| --- | --- | --- |
| Primária | Azul Duia | `#2E6BE6` |
| Destaques e seleção | Azul névoa | `#E8F0FE` |
| Títulos e logotipo | Azul noite | `#1A3A73` |
| Fundo | Branco gelo | `#F7F9FC` |
| Janelas e cartões | Branco | `#FFFFFF` |
| Texto principal | Grafite | `#1F2933` |
| Texto secundário | Cinza ardósia | `#5B6675` |
| Bordas | Cinza nuvem | `#DDE3EC` |
| Sucesso | Verde menta | `#2FA67A` |
| Aviso | Âmbar suave | `#E8A33D` |
| Erro | Coral | `#D9534F` |
| Fundo do modo escuro | Azul profundo | `#0F1724` |
| Destaque no modo escuro | Azul claro | `#6E9BF5` |

## Tipografia (licença SIL Open Font License)

- **Manrope** — logotipo e títulos
- **Inter** — interface e textos
- **JetBrains Mono** — terminal e código

O nome DuiaOS e o logotipo são marcas do projeto. Veja [TRADEMARKS.md](../TRADEMARKS.md).
