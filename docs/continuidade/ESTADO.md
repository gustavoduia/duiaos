# DuiaOS — Estado atual (todos os repositórios)

> Atualize no FIM de cada chat (`REGRASFIM.md`). Fatos verificáveis: o que está na `main` de cada repositório,
> commits, o que está instalado em cada máquina. Desde 13/10 é o estado de TODO o projeto (ADR 043): o Wise e o
> site não têm mais arquivos de estado próprios.

Atualizado em: 14/11/2026 · por: Claude (conta do Gustavo) · sessão session_017QRdLiNuMN3h9iSaFMGT25
**14/11: interface completa (ADR 044) enviada à `main`** — Barra de Recursos nova (Menu do DuiaOS, ícones + balão,
Central de Controle), Ilha com Aplicativos/Downloads/Lixeira, Central de Aplicativos em tela cheia, Explorador de
Arquivos e Configurações, com as páginas da documentação para usuários. **14/11 (tarde): 2ª rodada (ADR 045)** — Área de
Trabalho com ícones e botão direito, barra das janelas com bolinhas, modo escuro, notificações, Tela de Descanso,
fundos com GIF/vídeo, Atualizações nas Configurações, foto da conta, menu da Ilha. Falta o teste no Dell (seção 4).
**Chat encerrado** (memória `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`). Os cinco repositórios só têm a
`main` (o fontes-abertas também a `gh-pages`) e nenhum PR aberto.

## 1. O que está na main
- **duiaos**:
  - até #12 (ADRs 001–043: F2/F3 de "Ajude a melhorar o DuiaOS", Wise na ISO e no apt, organização);
  - memórias dos 5 chats em `docs/continuidade/`, REGRASINI e REGRASFIM.
- **duiaos-wise**: até #10 (W01–W20). Sem instruções (ficam no duiaos).
- **duiaos-websites**: até #8 (`/api/relatorios`, cron, documentação de F2/F3 e W20). Sem instruções.
- **duiaos-diagnosticos**: README e `maquinas/` (último relatório do Dell: 12/10 23h17).
- **duiaos-fontes-abertas**: EULA, licenças, marca, `modificacoes/` (fonte do código aberto desde a ADR 043);
  Releases até a v0.2.0; apt na `gh-pages`.
- **Builds de 13/10**: pacotes no canal teste **sem o Wise**, porque falta o segredo `DUIAOS_TOKEN_WISE`.
- **Versão publicada**: 0.2.0. A 0.3.0 está preparada e não lançada.

## 2. O que está instalado em cada máquina
| Máquina | duiaos | duiaos-wise | Como conferir |
| --- | --- | --- | --- |
| Dell | pacotes de `f75b9bc` (12/10, antes do W20 e do F2/F3; conferido no relatório de 12/10 23h17); relatórios no nível desenvolvimento, máquina `dell`, deploy key "DuiaOS dell (relatórios, escrita)" | main de 12/10 (#8) | 🔗 DELL: `dpkg -l 'duiaos*' \| grep ^ii` e `duiaos-relatorios estado` |
| Mac | — (repositórios e `gh`) | — | — |
- Deploy key antiga "Wise dell (escrita)" pode existir no `duiaos-diagnosticos`: se existir, remover.
- Desde 13/10 o build precisa do `duiaos-fontes-abertas` clonado ao lado (`~/Projetos/duiaos-fontes-abertas`).

## 3. Em andamento
- Interface completa (ADRs 044 e 045): código e documentação na `main`; **sem teste no Dell**.
- Duia App Store (ADR 049, ficha DUIA-2026-0007): loja própria com o Debian (AppStream/DEP-11, pelo duiaos-agente)
  e o Flathub (flatpak --user); testada aqui com os catálogos reais e uma instalação de verdade pelo flatpak;
  **sem teste no Dell**. Depois da atualização: sair e entrar na sessão; o catálogo do Debian só aparece depois do
  próximo `apt update` (o pacote `appstream` liga o download dos metadados).

## 4. Próximos passos (detalhes na seção 6 da memória mais recente)
0. Gustavo: testar a interface nova no Dell — 🔗 DELL: `cd ~/Projetos/duiaos && git pull && bash pacotes/instalar-local.sh`
   (instala também brightnessctl, wlsunset, power-profiles-daemon, pkexec, xdg-user-dirs, xdg-utils, udisks2,
   python3-pyside6.qtsvg; na 2ª rodada também qml6-module-qtmultimedia, qml6-module-qtquick-dialogs, libnotify-bin,
   python3-pyside6.qtdbus); reiniciar e relatar o que falhar.
1. Claude: relatório de realinhamento a partir das 5 memórias (adiado pelo Gustavo em 14/11).
2. Gustavo: segredos `DUIAOS_TOKEN_WISE` (duiaos) e `GITHUB_DIAGNOSTICOS` (duiaos-websites, não confirmado).
3. Teste no Dell (W20, janela "Ajude a melhorar", Wi-Fi pelo Wise) e leitura dos relatórios.
4. Lançar a 0.3.0; depois retirar os avisos "Na próxima versão" da documentação.
5. ~~Explorador de arquivos, Configurações e painel de controle~~ feitos em 14/11 (ADR 044); depois: ícones na
   ~~Área de Trabalho, notificações, atualizações, modo escuro~~ feitos (ADR 045); depois: modo escuro nas Telas de
   Entrada/Bloqueio, Central de IA e "Ajude a melhorar"; janelas presas aos cantos.

## 5. Decisões recentes (detalhe nos ADRs)
- 16/11: **Dell caiu no login em modo texto depois da 0013** (ADR 055, ficha DUIA-2026-0014, crítica): o compositor
  era chamado por `systemd-cat`; agora só redirecionamento do shell, e `test_inicio_da_tela.py` cobre o caso. Causa
  exata no Dell não confirmada (sem relatório daquele boot). **Aguardando o Gustavo aplicar pelo terminal e confirmar.**
- 16/11: **Inicialização limpa, janelas com identidade própria e Futurista como estilo inicial** (ADR 054, ficha
  DUIA-2026-0013): GRUB escondido com F12 para escolher o sistema; logomarca em fundo preto (GRUB e Plymouth, sem
  o nome); núcleo, systemd, sessão e Tela de Entrada sem texto no terminal; Ilha amplia sem piscar (causa: imagem
  refeita a cada tamanho); bolinhas das janelas à direita em azul; ícones de traço fino; o estilo anterior vira
  "Clássico". **Sem teste no Dell** — o boot (F12, logomarca, ausência de texto) só dá para conferir lá.
- 16/11: **Procurar atualizações consulta sempre** (ADR 053, ficha DUIA-2026-0012).
- 16/11: **Estilo futurista "Aurora"** (ADR 052, ficha DUIA-2026-0011): segundo visual ao lado do padrão, em
  Configurações › Aparência e estilos; Telas de Entrada e de Bloqueio redesenhadas. **Sem teste no Dell.**
- 14/11: **Papéis de parede completos** e **testes das janelas reais** (ADR 051; fichas 0009 e 0010). A Ilha
  sumiu no Dell depois da 0008 (QML não carregava: `Behavior` numa propriedade `readonly`); corrigido e coberto
  por `shell/testes/test_janelas_reais.py`. Botão "Wise" da Barra removido.
- 14/11: **Ilha como o Dock do macOS** (ADR 050, ficha DUIA-2026-0008): ampliação, tamanho, posição, ocultar,
  menus, arrastar e minimizar com gênio/escala feito pela própria Ilha (grim + wlrctl), sem animação do labwc.
  **Sem teste no Dell**: conferir o efeito real, a máscara de cliques e o botão amarelo.
- 14/11: **Duia App Store** (ADR 049): o Debian não tem loja própria (só os metadados AppStream que o GNOME Software
  e o KDE Discover leem) e a Snap Store do Ubuntu tem servidor proprietário; loja própria lendo o AppStream do
  Debian e do Flathub; um mesmo aplicativo aparece pelo Flathub, com a versão do Debian como alternativa.
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
- Nomes usados em 14/11 (ADR 044), a confirmar: "Menu do DuiaOS", "Central de Controle", "Explorador de Arquivos",
  "Configurações" (um aplicativo só, com a Central de IA e "Ajude a melhorar" ligados a ele) e "Repousar" (antes
  "Suspender").
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
