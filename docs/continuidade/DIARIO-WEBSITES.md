# Site e documentação — Diário de sessões

Uma entrada por sessão, a mais nova em cima. Só acrescentar.


## 12–13/10/2026 (noite) · Claude (conta do Gustavo) · #8, #9, #10
- #8: `/api/relatorios` (F3 de "Ajude a melhorar o DuiaOS"), lote por hora no `duiaos-diagnosticos`, issue
  semanal das falhas; 8 testes com D1 real em memória; testado no `wrangler dev` com relatório do coletor.
- #9: aplicativos que não existem para o DuiaOS e Wi-Fi/Bluetooth pelo Wise.
- #10 (rascunho): retira os avisos "Na próxima versão" — o Wise vai instalado na 0.3.0 (ADR 042 do DuiaOS).
## 12/10/2026 (18h30) · Claude (conta do Gustavo) · fechamento do bloco
- PRs #1, #2, #4, #5 e #6 na main e publicados. Páginas novas acompanham o sistema (PR irmão); tudo o que a
  0.2.0 não tem leva "Na próxima versão" — tirar quando sair a 0.3.0.

## 12/10/2026 (noite) · Claude (conta do Gustavo) · PR #6
- Irmão do Wise #8 (W19): "Quando o Wise erra" passa a falar do registro do sistema.

## 12/10/2026 (noite) · Claude (conta do Gustavo) · PR #5
- Irmão do duiaos #10 (logs do sistema, ADR 040): páginas "Ajude a melhorar o DuiaOS" e comando
  `duiaos-relatorios`; privacidade cita o envio opcional.

## 12/10/2026 (tarde) · Claude (conta do Gustavo) · PR #3
- Irmão do duiaos-wise #6 (W17/W18): página "Quando o Wise erra", níveis com energia e Ilha, programas de
  terminal que não aparecem na Central.

## 12/10/2026 (noite) · Claude (conta do Gustavo) · PR #2
- Gustavo publicou e aprovou o site e a documentação (merge do PR #1, segredos criados, workflows rodando).
- Revisão: a documentação descrevia o Wise e a Central de IA, que a 0.2.0 publicada ainda não tem. Acrescentado
  o aviso `Na próxima versão` (regra deste repositório) em 14 páginas e no atalho Super+W.

## 12/10/2026 · Claude (conta do Gustavo) · PR #1
- Site e documentação criados (no `duiaos`, PR #9) e trazidos para este repositório, a pedido do Gustavo: um
  repositório, dois aplicativos (`site/` e `documentacao/`), como as distribuições fazem (site e documentação em
  endereços separados). Endereços: duiaos.gustavoduia.workers.dev e duiaos-docs.gustavoduia.workers.dev
  ("docs.duiaos.gustavoduia.workers.dev" não é possível no workers.dev; com domínio: docs.duiaos.com.br).
- Combinado: documentação atualizada no mesmo fluxo das mudanças do sistema (PR irmão, mesmo nome de branch);
  versões e novidades automáticas pelos lançamentos, sem token entre repositórios.
