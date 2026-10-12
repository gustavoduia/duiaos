---
title: Comando duiaos-ia
description: A IA do sistema pelo terminal.
---

```
duiaos-ia [comando] [modelo]
```

| Comando | O que faz |
| --- | --- |
| `estado` (padrão) | Mostra o modelo ativo, downloads e a última ação |
| `catalogo` | Lista os modelos que dá para baixar, com tamanho e licença |
| `baixar MODELO` | Baixa um modelo do catálogo (ex.: `qwen3.5:2b`) |
| `ativar MODELO` | Torna um modelo baixado o modelo ativo do sistema |
| `remover MODELO` | Apaga um modelo baixado (não o ativo) |
| `cancelar` | Cancela o download em andamento |
| `diagnostico` | Mede leitura e escrita da IA neste computador (com `sudo`, inclui a memória) |
| `calibrar` | Mede de novo o jeito mais rápido de rodar o modelo ativo |
| `ajuda` | Mostra esta lista |

Pela sessão no computador, as mudanças não pedem senha. Por acesso remoto (SSH), use `sudo`.
