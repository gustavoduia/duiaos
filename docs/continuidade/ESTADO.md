# DuiaOS — Estado atual (todos os repositórios)

> Atualize no FIM de cada chat (`REGRASFIM.md`). Fatos verificáveis: o que está na `main` de cada repositório,
> commits, o que está instalado em cada máquina. Desde 13/10 é o estado de TODO o projeto (ADR 043): o Wise e o
> site não têm mais arquivos de estado próprios.

Atualizado em: 12/10/2026 (22h20) · por: Claude (conta do Gustavo) · sessão session_01CiC8yo8v1GpMMnY2gZUjqx
**Chat encerrando com 3 PRs finais esperando merge do Gustavo** (seção 1) — os últimos: dali em diante, só `main`.

## 1. O que está na main e o que falta entrar
- **Na `main`** (12/10 18h30): duiaos até #11 (ADRs 001–040); Wise até #9 (W01–W19); site até #7;
  diagnosticos com os relatórios do Dell; fontes-abertas com EULA, licenças, ISOs 0.2.0 e o apt.
- **Falta entrar (PRs finais, merge pelo Gustavo, nesta ordem)**:
  1. **duiaos #12** — F2/F3 de "Ajude a melhorar o DuiaOS" (ADR 041), Wise na ISO e no apt (ADR 042),
     notas da 0.3.0, organização dos repositórios e só-`main` (ADR 043): REGRASINI/REGRASFIM, memórias em
     `docs/continuidade/`, inventários e diários do Wise e do site aqui, `publico/` substituída pelo
     `duiaos-fontes-abertas`, `ferramentas/organizar-repositorios.sh`.
  2. **duiaos-wise #10** — W20 (aquecimento antes do login, agir sem anunciar, Wi-Fi/Bluetooth, aplicativos fora
     do apt, uso agregado); sai o CLAUDE.md e `docs/continuidade/` (a conferência de recursos lê
     `duiaos/docs/continuidade/RECURSOS-WISE.md`).
  3. **duiaos-websites #8** — `/api/relatorios`, cron para o `duiaos-diagnosticos`, documentação de F2/F3 e do
     W20 (conteúdo do antigo #9); sai o CLAUDE.md e `docs/continuidade/` (workflows clonam o `duiaos` para a
     conferência).
  Depois dos três: `bash ferramentas/organizar-repositorios.sh` (🍎 MAC) apaga todas as branches `claude/*` e
  tira as instruções do `duiaos-diagnosticos` e o aviso de cópia do README do `duiaos-fontes-abertas`.
- Fechados sem merge neste chat: duiaos #13 (memória, foi para o #12), Wise #11 (memória no repositório
  errado), site #9 (foi para o #8) e site #10 (retirar avisos — virou pendência para depois da 0.3.0).
- **Versão publicada**: 0.2.0 (12/10 02h17). A 0.3.0 está preparada e não lançada.

## 2. O que está instalado em cada máquina
| Máquina | duiaos | duiaos-wise | Como conferir |
| --- | --- | --- | --- |
| Dell | pacotes de `f75b9bc` (igual à main de 12/10); relatórios no nível desenvolvimento, máquina `dell`, deploy key "DuiaOS dell (relatórios, escrita)" | main de 12/10 (#8) | 🔗 DELL: `dpkg -l 'duiaos*' \| grep ^ii` e `duiaos-relatorios estado` |
| Mac | — (repositórios e `gh`) | — | — |
- Deploy key antiga "Wise dell (escrita)" pode existir no `duiaos-diagnosticos`: se existir, remover.
- Desde 13/10 o build precisa do `duiaos-fontes-abertas` clonado ao lado (`~/Projetos/duiaos-fontes-abertas`).

## 3. Em andamento
- Nenhuma frente aberta (ver as pendências na memória do chat mais recente).

## 4. Próximos passos (detalhes na memória mais recente)
1. Gustavo: merges da seção 1 (ordem), `organizar-repositorios.sh`, segredos `DUIAOS_TOKEN_WISE` (duiaos) e
   `GITHUB_DIAGNOSTICOS` (duiaos-websites).
2. Teste no Dell (aquecimento antes do login, janela "Ajude a melhorar", Wi-Fi pelo Wise) e leitura dos
   relatórios pelo Claude.
3. Lançar a 0.3.0 (`lancar-versao.sh 0.3.0`) e, depois de publicada, retirar os avisos "Na próxima versão" da
   documentação (direto na `main` do `duiaos-websites`).
4. Explorador de arquivos, Configurações e painel de controle (nomes e escopo com o Gustavo).
5. Antes da 1.0: Wise compilado (ADR 042), Google/Microsoft na agenda, W3 voz, W4 gateway da nuvem, P4
   instalador próprio (BitLocker).

## 5. Decisões recentes (detalhe nos ADRs)
- 13/10: **organização** (ADR 043): o `duiaos` é o repositório oficial e guarda toda instrução; só `main`, sem
  branches nem PRs; `duiaos-fontes-abertas` é a fonte do código aberto; início/fim de chat por REGRASINI/REGRASFIM.
- 13/10: **o Wise vai instalado com o sistema** (ISO e apt; ADR 042). Código continua no repositório privado; o
  build usa o segredo `DUIAOS_TOKEN_WISE`. Lançamento = mesma tag no Wise e no DuiaOS.
- 13/10: "Ajude a melhorar o DuiaOS" F2/F3 (ADR 041): uso só de lista conhecida e somado; janela da 1ª entrada
  sem opção marcada; envio padrão pelo site (sem credencial no computador).
- 13/10 (Wise W20): aquecimento antes do login; instruções para agir sem anunciar e fazer só o pedido;
  descartado mandar só as ferramentas do assunto (quebra o reaproveitamento do começo da conversa).
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
- Explorador de arquivos, Configurações e Painel de controle: nomes visíveis e se Configurações e Painel são um
  aplicativo só.
- Licença da documentação: proprietária (hoje) ou aberta (CC BY-SA, como o Ubuntu)?

## 7. Fila de problemas conhecidos
- `duiaos.local` (mDNS) não resolve a partir do Mac — usar `duiaos` ou o IP.
- BitLocker pede recuperação após o dual boot → instalador próprio deve detectar (P4).
- EULA/oferta de fonte são minutas: revisar com advogado antes da 1.0.
- Tela de Bloqueio sem ext-session-lock (ADR 026). Ponteiro entre monitores: aceito (ADR 027).
- Chave do repositório apt vence em 2036.
- Placas NVIDIA: sem CUDA no duiaos-ollama. `intel-opencl-icd` não existe no Debian 13.
- Programas de terceiros que não mandam as "opcoes" fazem o Ollama recarregar o modelo.
- Wise: 1ª leitura das instruções + ferramentas ~49 s (≈3.700 pedaços a ~77/s no Dell); agora feita antes do
  login (W20) — falta medir no Dell. Escrita ~7–9 pedaços/s: respostas longas continuam lentas.
- `zramswap.service` falhou em 5 boots antes de 12/10 17h29; o relatório agora traz as últimas linhas do
  serviço que falha — conferir se voltar a aparecer.
- `gkr-pam: unable to locate daemon control file` na Tela de Entrada: normal (o cofre abre logo depois).
- Risco das ações na tela avaliado por palavras (pode falhar); Flatpak fora do agente.

## 8. Ambiente do Claude (dicas para a próxima sessão)
- Clonar os repositórios lado a lado em /home/claude (o build e as conferências usam ../duiaos-fontes-abertas,
  ../duiaos-wise, ../duiaos-websites).
- `gh` só via REST. Python 3.13 do container sem `gi`: use `python3.12` para D-Bus/AT-SPI.
- Testes do Wise: `pip install --break-system-packages icalendar python-dateutil` e, para o 3.12,
  `python3.12 -m pip install --break-system-packages PySide6-Essentials`; rodar com `QT_QPA_PLATFORM=offscreen`.
- Captura QML offscreen: `shiboken6.wrapInstance(..., QQuickWindow)` + `grabWindow()`.
- AT-SPI de verdade: Xvfb + dbus-run-session + `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`.
- CalDAV de teste: Radicale com HTTPS (`SSL_CERT_FILE`, `no_proxy=127.0.0.1`).
- Rede: open-meteo bloqueado; api.met.no, nominatim, huggingface, GitHub, npm e PyPI liberados.
- journald de verdade para testes: `/usr/lib/systemd/systemd-journald &` (cria /run/systemd/journal/socket);
  para reiniciar use `kill $(pidof systemd-journald)` (nunca `pkill -f`, que mata o próprio shell).
- O ambiente do Claude bloqueia `git push` direto na `main` (classificador do modo automático) e não deixa
  apagar branches pela API: o Gustavo aprova o envio (modo de permissões manual) ou faz pelo Mac.
- `api.github.com/meta` bloqueado; repositórios novos entram na sessão com `add_repo`.
