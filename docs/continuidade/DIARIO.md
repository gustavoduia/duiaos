# DuiaOS — Diário de sessões

Uma entrada por sessão, a mais nova em cima. Só acrescentar; nunca apagar.
Formato: data · quem/conta · branches/PRs · o que foi feito · decisões · o que ficou pendente.

## 12/10/2026 · Claude (conta do Gustavo) · duiaos #9, duiaos-wise #5
- Três frentes numa atualização: medição de motores no Dell (Ollama mantido — ADR 036), clima (MET Norway) e
  agenda (local, .ics, CalDAV, Google, Microsoft) no Wise, W2 (duiaos-agente + aprovação), e o Wise usando o
  computador pela acessibilidade (W15, pedido novo do Gustavo).
- Problema relatado pelo Gustavo: a carinha do Wise voltou à primeira versão. Causa: a carinha de robô (W10)
  existe só nos PRs #3/#4/#5 do Wise, ainda sem merge; o Dell estava com o Wise da `main` (PR #2, carinha
  antiga). Não houve perda de código, mas a memória da sessão não registrava o que estava instalado onde.
- Correção de processo: continuidade no Git (`CLAUDE.md` + `docs/continuidade/`), inventário de recursos com
  conferência automática (`ferramentas/conferir-recursos.py`), seção "instalado em cada máquina", regras para
  várias contas.
- Pedidos novos: documentação para usuários desde o início (como as distros fazem) e site do DuiaOS no
  Cloudflare Workers (ADRs 037–038).

## 11–12/10/2026 · Claude (conta do Gustavo) · duiaos #1–#8, duiaos-wise #1–#4
- P3 (Tela de Entrada/Bloqueio, boot, papel de parede, Menu de Energia), P3b (pacotes .deb e apt assinado),
  Wise W1 (consultas), presença na sessão, IA do sistema (duiaos-ia, Central de IA, duiaos-ollama), carinha de
  robô e resposta rápida (W10–W12), calibração por computador (ADRs 017–033).
