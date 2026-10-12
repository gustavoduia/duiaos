# DuiaOS — Diário de sessões

Uma entrada por sessão, a mais nova em cima. Só acrescentar; nunca apagar.
Formato: data · quem/conta · branches/PRs · o que foi feito · decisões · o que ficou pendente.

## 12/10/2026 (noite) · Claude (conta do Gustavo) · duiaos #10, duiaos-websites #5, duiaos-diagnosticos #1
- Merge de duiaos #9, Wise #5 e site #2. O `--delete-branch` apagou as bases de Wise #6 e site #3, que o GitHub
  fechou: refeitos sobre a main como Wise #7 e site #4. Lição: PR empilhado → mudar a base para a main
  antes do merge do PR de baixo (ou não apagar a branch).
- Pedido do Gustavo: logs do sistema inteiro como nas distribuições, centralizados no `duiaos-diagnosticos`.
  Estudo (journald, apport/whoopsie, ABRT, systemd-coredump, Ubuntu Insights, eos-metrics, KUserFeedback,
  popcon) → ADR 040. Decisões: pergunta sem padrão na 1ª entrada; usuários pelo Worker do site; nome
  "Ajude a melhorar o DuiaOS".
- F1: `duiaos_registro` (todos os programas), coletor `duiaos-relatorios`, journal persistente, coredump,
  catálogo, envio Git, `ler-relatorios.py`. Testado com um systemd-journald real no ambiente do Claude.
- Dell configurado (`configurar-relatorios.sh`; 1º erro: cópia da chave no /tmp com sticky bit — corrigido).
  1º relatório chegou ao `duiaos-diagnosticos`. Ele mostrou: `zramswap.service` falha em todo boot (causa ainda
  não visível → o relatório passa a levar as últimas linhas do serviço que falhou), `gkr-pam` na Tela de Entrada
  (normal: o cofre abre logo depois), limite da 1ª coleta pulava registros (corrigido) e `estado` sem sudo
  quebrava (situacao.json público).

## 12/10/2026 (noite) · Claude (conta do Gustavo) · duiaos #9, duiaos-websites #2
- Gustavo publicou e aprovou o site e a documentação (duiaos-websites #1 na main, segredos criados).
- Revisão do histórico: faltam o teste no Dell e o merge de duiaos #9 e Wise #5 (risco da carinha antiga
  continua); documentação ganhou avisos "Na próxima versão" (duiaos-websites #2).

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
  Cloudflare Workers (ADRs 037–038). A pedido do Gustavo, site e documentação foram para o repositório privado
  `duiaos-websites`, como dois aplicativos (ADR 039), com PR irmão exigido quando algo visível muda.

## 11–12/10/2026 · Claude (conta do Gustavo) · duiaos #1–#8, duiaos-wise #1–#4
- P3 (Tela de Entrada/Bloqueio, boot, papel de parede, Menu de Energia), P3b (pacotes .deb e apt assinado),
  Wise W1 (consultas), presença na sessão, IA do sistema (duiaos-ia, Central de IA, duiaos-ollama), carinha de
  robô e resposta rápida (W10–W12), calibração por computador (ADRs 017–033).
