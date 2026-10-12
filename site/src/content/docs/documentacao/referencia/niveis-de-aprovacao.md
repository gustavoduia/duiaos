---
title: O que o Wise faz sozinho e o que pergunta
description: Os níveis de autonomia do Wise.
---

| Nível | O Wise | Exemplos |
| --- | --- | --- |
| Consultar | Faz sem perguntar; não muda nada | uso do computador, previsão do tempo, agenda, ler uma janela |
| Preparar | Faz sem perguntar; muda só coisas suas, fáceis de desfazer | guardar a cidade, anotar na agenda do computador, abrir um aplicativo |
| Executar com aprovação | Mostra o que vai mudar e só faz depois de **Aprovar** | instalar, remover, atualizar, criar compromisso numa conta, clicar em "Enviar" |

Tudo o que o Wise faz fica registrado no computador, em `~/.local/share/duiaos/wise/auditoria.sqlite`.
As ações do sistema (instalar, remover, atualizar) também ficam em `/var/log/duiaos-agente/acoes.jsonl`.
