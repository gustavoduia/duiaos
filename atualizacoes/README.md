# Atualizações do DuiaOS — uma ficha por atualização

Toda mudança que chega aos computadores (sistema, interface, aplicativos, Wise, pacotes) é publicada
com uma **ficha** aqui. A ficha vira o catálogo `atualizacoes.json`, publicado junto com o repositório
apt (GitHub Pages) e instalado em `/usr/share/duiaos/atualizacoes.json`; a tela **Configurações ›
Atualizações** mostra, para cada atualização pendente ou instalada, o código, o título, o tipo, a
importância, a descrição completa e os detalhes (ADR 046).

## Código

`DUIA-AAAA-NNNN` — ano e número em sequência dentro do ano, sem pular nem repetir (como os
boletins de segurança do Debian, DSA-NNNN, e os KB da Microsoft). Nunca reaproveite um código, nem
de uma ficha apagada. A próxima ficha: `python3 ferramentas/atualizacoes.py nova`.

## Formato (`DUIA-AAAA-NNNN.md`)

```
---
codigo: DUIA-2026-0004
titulo: Frase curta do que a pessoa ganha
data: 2026-11-14
tipo: novidade | melhoria | correcao | seguranca
importancia: recomendada | importante | critica
pacotes: duiaos-shell, duiaos-wise
reiniciar: nao | sessao | computador
resumo: Uma ou duas frases para a lista.
publicada: 20261114161951        (opcional; padrão: data do commit que criou a ficha, em UTC)
---

## O que muda
Parágrafos para quem usa o computador: o que mudou e por quê, sem termos técnicos.

## Detalhes
- Um item por mudança, com o nome que aparece na tela.

## Observações
(opcional) O que conferir depois, limitações conhecidas.
```

Regras:
- Português do Brasil, frases curtas, "você". Nomes oficiais dos componentes.
- `pacotes`: os pacotes que mudam (`duiaos-identidade`, `duiaos-shell`, `duiaos-ia`, `duiaos-agente`,
  `duiaos-relatorios`, `duiaos-desktop`, `duiaos-ollama`, `duiaos-wise`).
- `publicada` decide em qual versão a ficha entra: um computador vê como pendentes as fichas
  publicadas depois da versão que tem e até a versão que vai receber (as versões de teste levam a
  data do commit: `X.Y.Z+gitAAAAMMDDhhmmss.SHA`).
- `python3 ferramentas/atualizacoes.py conferir` antes de cada envio (o build recusa ficha malformada).
