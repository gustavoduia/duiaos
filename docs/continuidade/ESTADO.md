# DuiaOS — Estado atual (todos os repositórios)

> Atualize no FIM de cada chat (`REGRASFIM.md`). Fatos verificáveis: o que está na `main` de cada repositório,
> commits, o que está instalado em cada máquina. Desde 13/10 é o estado de TODO o projeto (ADR 043): o Wise e o
> site não têm mais arquivos de estado próprios.

Atualizado em: 23/11/2026 · por: Claude (conta do Gustavo) · sessão session_017QRdLhyPjUkMHPvLpngyfq
**23/11 (20h): ADR 082, W26, ficha DUIA-2026-0038** — texto junto com a voz (como no modo voz do ChatGPT), fala da nuvem
emendada (sem os silêncios de cada áudio) e o jeito de falar em Configurações › Wise › Voz (voz natural, estilo, velocidade).
O duiaos-voz das ADRs 079 e 081 foi enviado ao `duiaos-fontes-abertas` (`5bec041`, com autorização do Gustavo) e o pacote
subiu para 1.13.8-duiaos4 (ficha DUIA-2026-0039); conferido num build local.
**23/11 (17h30): ADR 081, W25, ficha DUIA-2026-0037** — fala entendida errado e escuta lenta: o microfone do Dell chega
**estourado** (pico > 0 dB) e o ruído aumentado prende o detector de fala (9 s ouvidos para 2 s de fala). Feito: reconhecimento
pela nuvem com o motor ligado (`gpt-transcribe`/Gemini; local de reserva), volume do microfone ajustado sozinho (`wpctl`), fim da
fala também pela energia (duiaos-voz, patch 2), `pacotes.yml` sem publicar envios só de documentação (as "9 atualizações" sem
descrição). **Pendente do Gustavo:** aplicar `duiaos-voz-patches.patch` (2 commits) no `duiaos-fontes-abertas` e REVISAO=4.
**23/11 (17h): ADR 080, W24, ficha DUIA-2026-0036** — o teste do Gustavo às 16:44 rodou `07deaff` (antes da ADR 079) e
o duiaos-voz antigo. Decisões do Gustavo: **voz natural pela nuvem** quando OpenAI ou Gemini estiver ligado (voz local de
reserva; só o texto falado sai) e **medir modelos** para trocar o padrão se houver um mais rápido. O 4B **já roda na Iris Xe**
(Vulkan), mas lê ~70 pedaços/s, como no processador. Feito: `wise/voz_nuvem.py`, `duiaos-wise --medir-modelos [--baixar]`,
"Voz natural pela nuvem" em Configurações › Wise › Voz. **Pendentes:** Gustavo rodar a medição no Dell; trocar o modelo padrão
conforme o resultado; `gpt-4o-mini-tts` sai em 06/01/2027 (Realtime API).
**23/11 (fim da tarde): ADR 079, W23, ficha DUIA-2026-0035 — Wise em tempo real.** Causas nos relatórios do Dell: com o
**9B** ativo o aquecimento do boot desistia (o modelo não fica sempre na memória) e a 1ª pergunta levou 2 min 52 s; o Wise não
reaquecia quando o modelo voltava para a memória; 1ª fala em 11–12 s (Kokoro int8 quase em tempo real, disputando o
processador). Feito: aquecimento sempre pronto (boot, volta à memória, ao abrir a janela/clicar no microfone), resposta falada
de conversa, trechos para a voz (1º em "Claro!"/1ª vírgula), **conversa por voz mãos livres** (Configurações › Wise › Voz),
duiaos-voz com **Kokoro fp32** (2,3× mais rápido; botão "Atualizar" para quem tem o int8), tocador contínuo, pausas por
pontuação, fim de turno em 0,8 s com espera se a pessoa parou em "e", "mas"… **Pendentes:** o `duiaos-fontes-abertas` ainda não tem o duiaos-voz novo (a REVISAO=3 de `df27400` saiu antes dele e gera o
programa antigo): enviar o patch e subir para **REVISAO=4** juntos; medir no Dell;
o Ollama não usa a Iris Xe (llama-server só com o processador); página da documentação no `duiaos-websites`.
**23/11 (noite, 2ª rodada): ADR 077, ficha DUIA-2026-0034** — 8 pontos do Gustavo: Ora compacto e sem a barra do sistema
(botões da janela à direita das abas, arrastar/redimensionar próprios, regra `serverDecoration="no"` no rc.xml), DevTools
encaixado à direita com botão de destacar; Alt+Tab da Ilha com ícones e balão do nome (rc.xml → `alternar-janelas.sh`);
Mail Box com editor formatado (imagens embutidas por cid, anexos separados), IMAP IDLE (aviso na hora, notificação que abre
a mensagem), contador vermelho no ícone (LauncherEntry, `shell/comum/contador.py`); tela preta ao voltar: redesenho de 1 px
ao ativar (não reproduzido aqui); Barra junta o menu de mesmo nome do app. **Conferir no Dell:** Alt+Tab, tela preta, barra do
Ora no labwc, IDLE no Gmail. **Pendente: H.264/AAC** (mesma decisão abaixo).
**23/11 (noite): ADR 076, ficha DUIA-2026-0033** — 18 pontos do Gustavo: Mail Box envia pelo Gmail (login pulado no SMTP_SSL),
Configurações completas (contas/servidores/senhas/teste, assinaturas texto e HTML com modelos, pastas), botão direito, janela
da mensagem, lista sem pular, lida na hora, wizard fecha; Ora com abas em 4 posições, menus em português, favorito com pasta,
mais visitados, última aba, chave de segurança USB; dicas em todos os botões de ícone. **Pendente: H.264/AAC no Ora**
(rodas do Qt sem codecs proprietários; decisão do Gustavo entre compilar o Qt WebEngine ou usar o do Debian). **Sem teste no
Dell nem na VM.**
**23/11 (tarde): ADR 075, ficha DUIA-2026-0032.** Gustavo confirmou: com o token criado, a VM 0.3.1 recebeu a atualização
acumulada. Causa de o Ora e o Mail Box não abrirem na VM (ARM): a roda aarch64 do Qt WebEngine precisa de libsnappy, libwebp,
libopus, liblcms2 e libminizip do sistema (reproduzido num Debian 13 arm64 emulado; motor 6.12.0-duiaos3 com as dependências
e `conferir-dependencias.sh` no `pacotes.yml`, amd64 e arm64). Tab nos campos (`Campo.qml`, Escrever) e botões pelo teclado;
Ora e Mail Box vêm para a frente pelo `wlrctl`. Ora repaginado (trilho de abas lateral, ilha, cartão; `MarcaOra.qml`) e
apresentação da primeira abertura nos dois (Mail Box importa contas do Thunderbird). **Sem teste no Dell nem na VM.**
**23/11: ADR 074, ficha DUIA-2026-0031 — fluxo único de atualizações.** Causa de a VM 0.3.1 não receber nada: ISOs lançadas
gravavam o canal `estavel`, que só mudava em tags; e os envios de 18/11 (bbc557b, 7b2e3fb, 7af88ae) nem publicaram (motor web
de 141 MB > limite de 100 MB do GitHub; depois, 403 no `duiaos-ora` sem o `DUIAOS_TOKEN_APPS`). Agora: canais `estavel` e
`teste` com o mesmo índice e pasta única; lançamento só no commit mais novo da main (`lancar-versao.sh` marca Wise, Ora e
Mail Box); motor web dividido (`duiaos-motor-web` + `duiaos-motor-web-chromium`, 6.12.0-duiaos2); Ora e Mail Box viraram
Depends do `duiaos-desktop`; "Nível de atualização" em Configurações › Atualizações; instalador sem Thunderbird.
**Nada publica até o Gustavo criar o segredo `DUIAOS_TOKEN_APPS`** (`docs/continuidade/TOKEN-DOS-APLICATIVOS.md`).
**Sem teste no Dell nem na VM.**
**18/11 (noite): ADR 073, ficha DUIA-2026-0030** — Ora e Mail Box nos repositórios privados `duiaos-ora` e `duiaos-mailbox`
(código, testes e `pacote/construir.sh`; `pacotes/trazer-apps.sh` com o segredo `DUIAOS_TOKEN_APPS`, que o Gustavo precisa
criar); Ora navegador padrão e Mail Box e-mail padrão (mimeapps, alternativas, uma vez para quem já usava, Ilha); instalador
sem Firefox e Chrome (`duiaos-fontes-abertas`); Ora com modo aplicativo; buscador Google confirmado. **Sem teste no Dell.**
**18/11 (tarde): Ora e Mail Box 0.1 (ADR 072, ficha DUIA-2026-0029)** — estratégia aprovada pelo Gustavo (plano no doc
"Ora e Mail Box — Estratégia e plano de desenvolvimento"): Ora = interface própria sobre o Qt WebEngine (Chromium 140), com o
motor no pacote novo `duiaos-motor-web` (rodas oficiais do PySide6 fixadas pelo sha256, sem o Qt WebEngine do Debian); Mail Box
100% próprio (IMAP, POP3, SMTP, wizard com descoberta, leitura segura, senhas no gnome-keyring). Testado aqui com o motor de
verdade e contra um Dovecot e um SMTP de laboratório (`shell/testes/laboratorio_email.py`). **Sem teste no Dell.** Pendentes:
login da Microsoft (registro no Entra), OAuth do Google (verificação/CASA), codecs H.264/AAC, onde fica o código (público ou
privado), página da documentação no `duiaos-websites` (acesso negado neste chat).
**18/11: Rede e Internet, plano completo (ADRs 069–071, fichas DUIA-2026-0026 a 0028)** — a página Wi-Fi virou Rede e
Internet: cabo, IP fixo, DNS, Detalhes em abas com "Manter?" (F1); agente de senhas, VPN (WireGuard, OpenVPN, OpenConnect),
Wi-Fi corporativo, proxy, ponto de acesso e QR (F2); firewall com redes privada/pública (o postinst põe as redes que já
existem como privadas para o SSH do Dell continuar), celular por USB/Bluetooth, modem 4G, VLAN/ponte/agregação,
diagnóstico e ferramentas de rede do Wise (F3). Testado com NetworkManager e firewalld de verdade no laboratório
(`ferramentas/laboratorio-rede.sh`). **Sem teste no Dell nem numa VM**; páginas da documentação no `duiaos-websites`
pendentes (o acesso ao repositório foi negado neste chat).
**17/11 (tarde): ADR 066, ficha DUIA-2026-0023, notas da 0.3.1** — instalador pelo Xwayland (teclado nos campos QML),
revisão que relê as escolhas, sem bloqueio de tela no pendrive; **uma instalação completa numa VM UEFI (QEMU) funcionou**
e o sistema instalado ligou. Balão do ícone de atualizações (um clique: balão; dois: Atualizações já com o resumo).
**17/11: 0.3.0 lançada pelo Gustavo; ADR 065, ficha DUIA-2026-0022** — voz do Wise refeita (Parakeet v3, `duiaos-voz servir`,
ganho automático, teste do microfone, `firmware-sof-signed`), menu do pendrive com duas opções (o d-i saiu), instalador com uma
página QML por assunto, Chrome em ARM e Telegram pelo Flathub, downloads do site sempre no último lançamento. **Sem teste no Dell
nem no UTM**; o instalador ainda não fez uma instalação completa.
**16/11 (noite): ADRs 063 e 064, ficha DUIA-2026-0021** — Central de IA removida; Configurações › Inteligência
Artificial (IA local + Gemini/OpenAI) e Configurações › Wise; Wise com texto fluido, rosto novo, voz (`duiaos-voz`),
motor e modelo na janela, menu do ícone na barra e Desligar o Wise; instalador próprio (Calamares) com escolha de
programas; papéis de parede paisagem e Lua; site (órbita, celular, maquetes) e documentação da 0.3.0. **Sem teste no
Dell**: a voz nunca foi ouvida e o instalador nunca fez uma instalação de verdade (o d-i fica de reserva).
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
4. ~~Lançar a 0.3.0~~ (17/11); lançar a 0.3.1 (tag `v0.3.1`) com o instalador corrigido.
5. ~~Explorador de arquivos, Configurações e painel de controle~~ feitos em 14/11 (ADR 044); depois: ícones na
   ~~Área de Trabalho, notificações, atualizações, modo escuro~~ feitos (ADR 045); depois: modo escuro nas Telas de
   Entrada/Bloqueio, Central de IA e "Ajude a melhorar"; janelas presas aos cantos.

## 5. Decisões recentes (detalhe nos ADRs)
- 17/11 (noite): **Lixeira de pastas do sistema, listas de limpeza só com arquivos da pessoa, retângulo fluido, Lixeira
  cheia e nitidez** (ADR 068, ficha DUIA-2026-0025): agente `MoverParaLixeira` (polkit), `arquivos_da_pessoa`, retângulo de
  14,6 → 1,2 ms por quadro, ícones no tamanho dos pixels e texto nativo. **Sem teste no Dell**; falta saber a resolução e a
  escala da tela do Dell (`wlr-randr`) para avaliar o que ainda parecer serrilhado.
- 17/11: **Seleção por arraste e Descompactar** (ADR 067, ficha DUIA-2026-0024): retângulo de seleção no Explorador
  e na Área de Trabalho (as vistas do Explorador eram `interactive`: o arraste virava rolagem); Descompactar no botão
  direito e com dois cliques (.zip, .tar.*, .gz/.bz2/.xz, .7z; pacote `7zip`); correção da seleção que se perdia a
  cada recarga da pasta. **Pendentes**: .rar precisa do `7zip-rar` (non-free) — decisão do Gustavo; página da
  documentação no `duiaos-websites` (o ambiente não liberou o repositório nesta sessão). **Sem teste no Dell.**
- 16/11: **Barra do Armazenamento completa (com o livre) e arrastar na Ilha como no Dock do macOS** (ADR 062,
  ficha DUIA-2026-0020). **Sem teste no Dell** (suavidade real só lá).
- 16/11: **Menu do ☰ do GNOME na Barra, Ilha que reorganiza ao arrastar, listas das Configurações, procura a
  cada hora, aquecimento do Wise** (ADR 061, ficha DUIA-2026-0019). Causas achadas: lista com propriedade de
  mesmo nome do campo de busca (nenhum Seletor abria); lista nova recriando o ícone no meio do clique (Ilha
  presa em "arrastando"); procura automática de 6 em 6 h; serviço do Wise sem HOME. **O disco do Dell está
  quase cheio** (aviso de 941 MB livres na foto do Gustavo): pode impedir downloads de atualizações.
- 16/11: **Armazenamento nas Configurações e avisos de disco cheio** (ADR 060) e **menus dos aplicativos do
  DuiaOS + tamanho na loja** (ADR 059), ficha DUIA-2026-0018. Causa dos menus vazios: o VLC não publica a
  acessibilidade e nada do DuiaOS tinha barra de menus; agora Explorador, Configurações e loja publicam menus
  pelo D-Bus (`org.duiaos.Menu1`). **Sem teste no Dell.** Limites dos avisos (10 GB / 1 GB) a confirmar com
  o Gustavo. Os workflows do site e da documentação falhavam desde 13/10 (procuravam o inventário que saiu do
  `duiaos-websites` na ADR 043): agora clonam o `duiaos` e conferem de lá; site e documentação publicados.
- 16/11: **Atualização automática (5 modos), notificações próprias, botões em todos os apps, pulo da Ilha**
  (ADR 058, ficha DUIA-2026-0017). Menus da Barra: no último relatório o Dell ainda estava na 0015 (sem os
  menus); leitor mais robusto e com registro nos relatórios. **Sem teste no Dell.** A confirmar com o Gustavo:
  modo padrão da atualização automática (`baixar`).
- 16/11: **Menus de cada aplicativo na Barra** (ADR 057, ficha DUIA-2026-0016): pela acessibilidade (AT-SPI),
  sem modificar o labwc; leitor em processo à parte. Testado aqui com apps GTK 3 e Qt 6 reais
  (`shell/testes/menus/`, Xvfb + dbus-run-session). Firefox, Electron e apps do DuiaOS ficam só com o menu do
  aplicativo. **Sem teste no Dell** (estado ACTIVE no Wayland e devolução do foco).
- 16/11: **Entrar sem tela preta, gênio sem piscar, modo Automático, tom das telas de acesso** (ADR 056, ficha
  DUIA-2026-0015). Causa da espera ao entrar achada nos relatórios do Dell (Wise aquecendo a IA no login).
  Ambiente de teste novo aqui: `xvfb-run` com `QT_QPA_PLATFORM=xcb` desenha com OpenGL (serve para efeitos que o
  modo offscreen não mostra). **Sem teste no Dell.**
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
