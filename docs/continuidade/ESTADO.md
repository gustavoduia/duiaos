# DuiaOS — Estado atual

> Atualize este arquivo no FIM de cada bloco de trabalho, no mesmo PR. Ele é o que a próxima sessão (de
> qualquer conta) lê para continuar. Escreva fatos verificáveis: branch, PR, commit, o que está instalado onde.

Atualizado em: 12/10/2026 (18h30) · por: Claude (conta do Gustavo) · sessão session_01LzmCWyGMx1FKt4d1cuh5R8
**Bloco fechado.** Nenhum PR aberto em nenhum dos quatro repositórios. O próximo chat começa daqui.

## 1. O que está na main e o que está pendente
- **duiaos main**: PRs #1–#5, #9 (IA do sistema, duiaos-agente, acessibilidade, medição, continuidade; ADRs
  030–039) e **#10** (registros do sistema e "Ajude a melhorar o DuiaOS", ADR 040). #6–#8 fechados sem merge.
- **duiaos-wise main**: #1, #2, #5 (robô, aprovação, clima, agenda, uso do computador), #7 (W17/W18) e **#8**
  (W19: o Wise no registro do sistema). #3, #4 e #6 fechados sem merge.
- **duiaos-websites main**: #1, #2, #4, #5, #6 — site e documentação publicados automaticamente.
- **duiaos-diagnosticos main**: #1 (README/CLAUDE.md) + relatórios enviados pelo Dell (`maquinas/dell/`).
- **Versão publicada (ISO/apt estável)**: ainda a 0.2.0 (12/10 02h17). Tudo acima está no canal `teste` e na
  main, à espera da 0.3.0.

## 2. O que está instalado em cada máquina
| Máquina | duiaos | duiaos-wise | Como conferir |
| --- | --- | --- | --- |
| Dell | pacotes de `f75b9bc` (branch do #10, igual ao conteúdo da main); relatórios ligados: nível desenvolvimento, máquina `dell`, deploy key "DuiaOS dell (relatórios, escrita)" no `duiaos-diagnosticos`, chave em `/etc/duiaos/relatorios/` | branch do #8 (igual à main), testado em 12/10 18h20 | 🔗 DELL: `dpkg -l 'duiaos*' \| grep ^ii` e `duiaos-relatorios estado` |
| Mac | — (só repositórios e `gh`) | — | — |
- Ao atualizar o Dell pela main: `git checkout main && git pull` nos dois repositórios + `instalar-local.sh`.
- Deploy key antiga "Wise dell (escrita)" pode existir no `duiaos-diagnosticos` (do script do Wise que saiu na
  W19): se existir, remover no GitHub (Settings › Deploy keys) e apagar `~/.ssh/duiaos-diagnosticos` no Dell.

## 3. Em andamento (quem / branch / PR rascunho)
- Claude (conta do Gustavo) · `claude/registros-f2-f3` · logs F2 (uso agregado + tela "Ajude a melhorar o
  DuiaOS") e F3 (envio pelo site); depois a preparação da 0.3.0. Wise: #10 (desempenho, apps, Wi-Fi).

## 4. Próximos passos (em ordem sugerida)
1. **Desempenho do Wise** (visto nos relatórios de 12/10 18h20): aquecimento de ~49 s depois do boot e ~38 s
   para responder a um pedido simples com 25 ferramentas (uma rodada de ~22 s). Medir com os relatórios e
   atacar (menos ferramentas por pedido, instruções mais curtas, aquecimento antes do login).
2. **Reclamação de 12/10** (Wise): pergunta sobre instalar um aplicativo que não existe no apt (Microsoft 365)
   teve resposta ruim — o Wise deve explicar alternativas (versão web, equivalentes livres). Detalhe no
   `duiaos-diagnosticos` (`ler-relatorios.py --componente duiaos-wise --eventos`).
3. **Logs F2**: eventos de uso agregados (`uso.*`, só lista conhecida) + tela "Ajude a melhorar o DuiaOS" na
   1ª entrada (sem opção marcada) e nas Configurações (polkit para mudar o nível).
4. **Logs F3**: `/api/relatorios` no Worker do site (sem credencial no computador) gravando em lotes no
   `duiaos-diagnosticos`; resumo semanal das falhas como issue.
5. **Lançar a 0.3.0** (ISO + apt estável) e tirar os avisos "Na próxima versão" da documentação; decidir como o
   Wise chega a quem baixa a ISO.
6. Google/Microsoft na agenda (`duiaos-wise/docs/contas-de-agenda.md`); plano: W3 voz, W4 gateway da nuvem no
   duiaos-ia, P4 instalador próprio (BitLocker).

## 5. Decisões recentes (detalhe nos ADRs)
- 12/10 (noite): F1 dos logs entregue e testada no Dell (biblioteca `duiaos_registro` em todos os programas,
  coletor `duiaos-relatorios`, journal persistente, coredump, catálogo; Wise W19). PR empilhado: antes do
  merge do PR de baixo, mudar a base do de cima para a main (o `--delete-branch` fecha o de cima).
- 12/10 (tarde): **logs do sistema** padronizados como nas distribuições (journald + falhas estilo apport/
  coredump + perfil estilo Ubuntu Insights + uso agregado estilo eos-metrics), centralizados no repositório
  privado `duiaos-diagnosticos` para TODO o sistema (não só o Wise). Consentimento: pergunta na 1ª entrada,
  sem opção marcada (nada sai antes). Usuários enviam ao Worker do site, que grava no repositório em lotes;
  computadores de teste enviam pelo Git (nível "Desenvolvimento"). Nome visível: **"Ajude a melhorar o
  DuiaOS"**. Fases: F1 registro + falhas + perfil + coletor `duiaos-relatorios` (Git) e Wise migrado; F2 uso +
  tela de consentimento; F3 Worker + agrupamento de falhas. Começa depois do merge de #9, Wise #5/#6 e site #2/#3.
- 12/10: motor **Ollama mantido** (ADR 036; medição no Dell). Pente de RAM fica para depois.
- 12/10: agenda local + .ics + CalDAV + Google + Microsoft; clima com cidade escolhida (MET Norway).
- 12/10: o Wise opera qualquer aplicativo como a pessoa, com aprovação nas ações arriscadas.
- 12/10: continuidade no Git (várias contas do Claude); documentação para usuários desde já; site no Cloudflare.

## 6. Perguntas em aberto para o Gustavo
- Titular dos direitos (PF ou CNPJ).
- Nome visível do recurso "Wise usando o computador" (hoje "Usar o computador").
- Domínio do site (ex.: duiaos.com.br / duiaos.com).
- Como o Wise chega a quem baixa a ISO (repositório apt privado, pacote fechado no apt público, só no Dell)?
- Licença da documentação: proprietária (hoje) ou aberta (CC BY-SA, como o Ubuntu)?

## 7. Fila de problemas conhecidos
- `duiaos.local` (mDNS) não resolve a partir do Mac — usar `duiaos` ou o IP.
- BitLocker pede recuperação após o dual boot → instalador próprio deve detectar (P4).
- EULA/oferta de fonte são minutas: revisar com advogado antes da 1.0.
- Tela de Bloqueio sem ext-session-lock (ADR 026). Ponteiro entre monitores: aceito (ADR 027).
- Chave do repositório apt vence em 2036. Distribuição pública do Wise não decidida.
- Placas NVIDIA: sem CUDA no duiaos-ollama. `intel-opencl-icd` não existe no Debian 13.
- Programas de terceiros que não mandam as "opcoes" fazem o Ollama recarregar o modelo.
- Wise com 25 ferramentas: aquecimento ~49 s após o boot e respostas de ~38 s (medido em 12/10; próximo passo 1).
- `zramswap.service` falhou em 5 boots antes de 12/10 17h29; o relatório agora traz as últimas linhas do
  serviço que falha — conferir se voltar a aparecer.
- `gkr-pam: unable to locate daemon control file` na Tela de Entrada: normal (o cofre abre logo depois).
- Risco das ações na tela avaliado por palavras (pode falhar); Flatpak fora do agente.

## 8. Ambiente do Claude (dicas para a próxima sessão)
- `gh` só via REST. Python 3.13 do container sem `gi`: use `python3.12` para D-Bus/AT-SPI.
- Captura QML offscreen: `shiboken6.wrapInstance(..., QQuickWindow)` + `grabWindow()`.
- AT-SPI de verdade: Xvfb + dbus-run-session + `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`.
- CalDAV de teste: Radicale com HTTPS (`SSL_CERT_FILE`, `no_proxy=127.0.0.1`).
- Rede: open-meteo bloqueado; api.met.no, nominatim, huggingface, GitHub, npm e PyPI liberados.
- journald de verdade para testes: `/usr/lib/systemd/systemd-journald &` (cria /run/systemd/journal/socket);
  para reiniciar use `kill $(pidof systemd-journald)` (nunca `pkill -f`, que mata o próprio shell).
- Ler relatórios sem sujar uma branch: `git -C ../duiaos-diagnosticos archive origin/main | tar -x -C /tmp/x`.
- `api.github.com/meta` bloqueado; repositórios novos entram na sessão com `add_repo`.
