# Wise — Diário de sessões

Uma entrada por sessão, a mais nova em cima. Só acrescentar.

## 12–13/10/2026 (noite) · Claude (conta do Gustavo) · PR #10
- Relatórios de 12/10: 1º aquecimento = 1ª leitura de ~3.700 pedaços (ferramentas 83%); pedido de 37,7 s esperou
  o aquecimento e escreveu 77 pedaços antes de buscar. W20: aquecimento antes do login (serviço do sistema),
  agir sem anunciar, fazer só o pedido (energia recusa ação trocada), `ligar_desligar` (Wi-Fi/Bluetooth),
  catálogo de aplicativos que não existem para o DuiaOS, LibreOffice não é mais filtrado como biblioteca.
- Uso agregado para "Ajude a melhorar o DuiaOS" (F2 do DuiaOS).
- Decisão do Gustavo: o Wise vai instalado com o sistema a partir da 0.3.0 (ADR 042 do DuiaOS).

## 12/10/2026 (18h30) · Claude (conta do Gustavo) · fechamento do bloco
- #8 (W19) testado no Dell e na main. Os relatórios mostraram o próximo trabalho: desempenho (aquecimento ~49 s,
  pedido simples ~38 s) e uma resposta ruim sobre aplicativo que não existe no apt.
- Linha do tempo do Wise (11–12/10): W1 consultas → presença (bolha, saudação) → IA do sistema e robô (W10) →
  resposta rápida (W11–W12) → aprovação + duiaos-agente (W2/W16) → clima (W13), agenda (W14), uso do
  computador (W15) → diagnóstico e correções do log real (W17/W18) → registro do sistema (W19). Decisões em
  `docs/decisoes.md` (W01–W19).

## 12/10/2026 (noite) · Claude (conta do Gustavo) · PR #8
- #7 na main. W19: o Wise passa a registrar pelo `duiaos_registro` (ADR 040 do DuiaOS); conteúdo da pessoa só
  no nível desenvolvimento; "Não ficou bom" pede o envio ao coletor do sistema. Sai o envio próprio (W17).
  Testado com systemd-journald real (nível "erros": só tamanhos e nomes de ferramentas).

## 12/10/2026 (tarde) · Claude (conta do Gustavo) · PR #6
- Gustavo testou o #5 no Dell e mandou a auditoria do dia. Causas achadas: cidade inventada, previsão de hoje
  dita como de amanhã, argumento "início" com acento, título inventado após cancelamento, promessa sem ação,
  7zip sem ícone, sem ferramenta de reiniciar. Corrigidas (W18) com testes do caso real.
- Pedido do Gustavo: log para o Claude analisar falhas. W17: diário técnico + envio ao repositório privado
  `duiaos-diagnosticos` + `ler-diagnosticos.py`; procedimento no CLAUDE.md. 85 testes.
- O modo automático de permissões bloqueou gravações no meio da sessão; o Gustavo passou para o manual.

## 12/10/2026 · Claude (conta do Gustavo) · PR #5
- W2/W16 (aprovação + duiaos-agente), W13 clima, W14 agenda, W15 uso do computador; 59 testes.
- Carinha antiga no Dell: o robô (W10) está só nos PRs #3/#4/#5, sem merge; o Dell tinha o Wise da main.
  Criados `docs/continuidade/` e a conferência de recursos nos testes, para isso não passar despercebido.

## 11–12/10/2026 · Claude (conta do Gustavo) · PRs #1–#4
- W1 consultas; presença (bolha, saudação, estado para a Barra); IA do sistema, carinha de robô e balão (W10);
  resposta rápida (W11–W12).
