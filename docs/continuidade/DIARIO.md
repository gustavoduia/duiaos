# DuiaOS — Diário de sessões

Uma entrada por sessão, a mais nova em cima. Só acrescentar; nunca apagar.
Formato: data · quem/conta · branches/PRs · o que foi feito · decisões · o que ficou pendente.



## 13/10/2026 (07h50) · Claude (conta do Gustavo) · encerramento do chat de 12/10 19h51
- O Gustavo fez os merges finais (duiaos #12, Wise #10, site #8) e rodou `organizar-repositorios.sh`: só a `main`
  nos cinco repositórios.
- Memórias dos 4 chats antigos geradas pelo prompt deste chat. Falta o segredo `DUIAOS_TOKEN_WISE` (os builds
  de 13/10 saíram sem o Wise); o Dell ainda está em `f75b9bc`. Próximo chat: relatório de realinhamento.
## 12/10/2026 (22h) · Claude (conta do Gustavo) · organização dos repositórios (ADR 043)
- Gustavo: só a `main`, sem branches; o `duiaos` é o repositório oficial e guarda toda instrução; REGRASINI e
  REGRASFIM para iniciar e encerrar chats; memória única por chat em `docs/continuidade/`.
- Instruções e continuidade do Wise e do site trazidas para cá; `publico/` substituída pelo `duiaos-fontes-abertas`;
  o ambiente bloqueia envio direto à `main` e apagar branches → 3 PRs finais (duiaos #12, Wise #10, site #8) e
  `ferramentas/organizar-repositorios.sh` para o Gustavo. Detalhes na memória
  `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`.
## 12–13/10/2026 (noite) · Claude (conta do Gustavo) · duiaos #12, duiaos-wise #10, duiaos-websites #8–#10
- Pedido do Gustavo: as cinco etapas de uma vez (há muito a fazer depois: explorador de arquivos, Configurações,
  painel de controle).
- Desempenho do Wise medido nos relatórios: o 1º aquecimento (~49 s) é a 1ª leitura de ~3.700 pedaços
  (instruções 600, ferramentas 3.000); depois cada pedido lê só o novo (~1 s). O pedido de 37,7 s esperou o
  aquecimento e escreveu 77 pedaços anunciando a busca. → aquecimento antes do login (serviço do sistema),
  instrução de agir sem anunciar. A remoção das frases de aprovação das ferramentas foi bloqueada (enfraquece a
  segurança) e ficou.
- Reclamações de 12/10: aplicativo fora do apt (catálogo com versão web e equivalentes; o filtro tirava o
  LibreOffice da busca) e "desliga o wifi" virando "desligar o computador" (ferramenta de Wi-Fi/Bluetooth e
  conferência no código).
- F2 (uso agregado, janela de escolha, polkit) e F3 (`/api/relatorios`, lote por hora no GitHub, issue semanal),
  testados com D1 real em memória e no `wrangler dev`.
- 0.3.0: perguntei como o Wise chegaria a quem baixa a ISO e recomendei sair sem ele; o Gustavo corrigiu: o Wise
  é o cérebro do DuiaOS e vai instalado com o sistema (ADR 042). Feito pelo build com token de leitura.

## 12/10/2026 (18h30) · Claude (conta do Gustavo) · fechamento do bloco
- Merge de duiaos #10, Wise #8, site #5/#6 e diagnosticos #1. F1 dos logs completa e testada no Dell: a falha de
  teste, um defeito real do próprio coletor (corrigido) e uma reclamação do Wise chegaram ao
  `duiaos-diagnosticos` com rastro e linha do tempo.
- Resumo do dia inteiro (11–12/10), para quem chega agora: P3 (Tela de Entrada/Bloqueio, boot, papel de parede,
  Menu de Energia) → P3b (pacotes .deb e apt assinado) → Wise W1 e presença → IA do sistema (Ollama empacotado,
  duiaos-ia, Central de IA, resposta rápida) → medição de motores (Ollama mantido) → Wise W2 com duiaos-agente,
  clima, agenda, uso do computador → continuidade no Git para várias contas → documentação para usuários e site
  no Cloudflare (duiaos-websites) → diagnóstico do Wise e correções do log real → registros do sistema e "Ajude a
  melhorar o DuiaOS" (ADR 040) com o Wise integrado. Detalhes em `docs/decisoes.md` (ADRs 001–040) e nas
  entradas abaixo.

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
