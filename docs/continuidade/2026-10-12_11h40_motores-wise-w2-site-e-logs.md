# Chat 2026-10-12 11h40 — Medição de motores, Wise W2, site e documentação, registros do sistema

## 1. Identificação
- **Início:** 2026-10-12 ~11h40 (Brasília). Fonte: hora de criação da pasta de trabalho desta sessão no ambiente
  do Claude (11:40:16 -03); o primeiro commit da sessão é de 12:03 (-03). A hora exata da primeira mensagem
  não ficou disponível (o histórico guardado começa na retomada das 16h14) — **hora aproximada**.
- **Fim do trabalho:** 2026-10-12 ~18h30 (fechamento do bloco). Pedido desta memória: 2026-10-13 07h39.
- **Conta e sessão:** conta do Gustavo · `session_01LzmCWyGMx1FKt4d1cuh5R8`. A conversa passou por uma
  compactação de contexto (~16h14); a parte anterior foi reconstruída a partir do resumo da própria sessão.
- **Repositórios mexidos:** `gustavoduia/duiaos` (público), `gustavoduia/duiaos-wise` (privado),
  `gustavoduia/duiaos-websites` (privado, criado pelo Gustavo neste dia), `gustavoduia/duiaos-diagnosticos`
  (privado, criado pelo Gustavo neste dia). Também o Project "DuiaOS" do claude.ai (arquivos-ponteiro).
- **Chat anterior:** 2026-10-11 (P3, pacotes, Wise W1 e IA local). **Chat seguinte:** 2026-10-12 19h51
  (cinco etapas e Wise na ISO), que mudou regras deste chat (ver seção 13).

## 2. O que o Gustavo pediu (em ordem)
1. **"Continuar o DuiaOS"**, com o objetivo de levar "as 3 frentes numa mesma atualização":
   - (1) **IA escrevendo mais rápido**: medir no Dell Ollama × llama-server × decodificação especulativa
     (rascunho/MTP) × OpenVINO e só trocar de motor se ganhar;
   - (2) **clima e agenda** no Wise;
   - (3) **W2**: `duiaos-agente` e ações N2 com aprovação (atualizar, instalar e remover aplicativos), auditadas.
2. Respostas às perguntas sobre agenda e clima (palavras dele): agenda **"Local + link .ics + integração com as
   principais soluções (Teams, Google, provedores privados)"**; e **"Também quero que ele tenha uma inteligência
   de analisar a tela aberta ou de abrir os aplicativos e fazer a leitura independente de ter integração, como se
   fosse o usuário do sistema. O Wise vai substituir o usuário, portanto ele é soberano no sistema operacional e
   pode abrir e usar qualquer aplicativo ou sistema instalado no DuiaOS."** Clima: **"Cidade escolhida"**.
3. Relatou que `sudo apt install -y intel-opencl-icd python3-venv` falhou (o pacote não existe no Debian 13) e
   mandou as saídas das medições de motores (primeira sem e depois com `--placa`).
4. Decisões após a medição: **"Vamos manter o Ollama."**; o teste ngram, se opcional, fica de fora; **"Depois eu
   faço o upgrade na memória. Vamos manter o hardware atual."**
5. **Reclamação:** a continuidade entre chats falhou — "a carinha do Wise voltou para a primeira versão básica".
   Pediu um jeito "totalmente eficiente" de reportar a continuidade, compatível com **mais de uma conta do
   Claude** (todo o histórico em arquivos .md acessíveis por outra conta via pull).
6. Pediu **documentação do DuiaOS em tempo real**, como as grandes distribuições Linux fazem ("Estude isso
   detalhadamente e me diga como vamos fazer").
7. Pediu o **site principal do DuiaOS no Cloudflare Workers** (deploy, banco, storage, KV): downloads,
   atualizações, suporte, base de conhecimento e documentação, com **"layout moderno e sofisticado com efeitos de
   transação entre as sessões do site, bem parecido com os efeitos usado pela Apple"**, usando three.js/WebGL, com
   cara de divulgação de sistema operacional. "Pode seguir."
8. Separação de repositórios: site, documentação, Wise, sistema aberto e fechado **separados**. Criou o
   repositório privado `duiaos-websites`. Escolheu **"um repositório e cada um com sua pasta, igual a opção A"**.
   Endereços: site `duiaos.gustavoduia.workers.dev` (corrigiu: "Eu escrevi errado. O site correto é
   duiaos.gustavoduia.workers.dev"); documentação pedida em `docs.duiaos.gustavoduia.workers.dev` (não é possível
   no workers.dev; ficou `duiaos-docs.gustavoduia.workers.dev`); depois, com domínio: `duiaos.com.br` e
   `docs.duiaos.com.br`. Site e documentação devem se atualizar **sozinhos** junto com o desenvolvimento.
   Perguntou como as distribuições fazem (site e documentação juntos ou separados).
9. Pediu o passo a passo para criar os segredos do Cloudflare no GitHub; depois relatou erro de clone (pasta
   inexistente / endereço SSH errado). Depois: **"Testado e aprovado. Podemos continuar o desenvolvimento do
   DuiaOS de onde paramos. Reveja o histórico para ver se ta faltando alguma coisa"**.
10. Relatou erros nas conversas com o Wise e pediu **um log que guarde tudo**, que o Claude consiga ler — "seja
    integrando no DuiaOS ou o Wise enviando para o Github para uma pasta específica de logs" — "para que você
    possa analisar sempre que eu reclamar de alguma falha do Wise".
11. Anexou o log do dia do Wise (auditoria exportada do Dell) para análise.
12. Trocou o modo de permissões para manual depois que o modo automático bloqueou gravações.
13. Depois: **"O conceito de log precisa ser igual os sistemas operacionais de mercado já fazem. Temos que coletar
    informações de uso mas também de erros. Os logs serão centralizados no repositório que criamos. Ele Não será
    um repositório somente para o Wise, ele vai armazenar todos os logs do sistema."** Pediu para estudar como as
    distribuições Linux fazem e "criar esse mesmo mecanismo no nosso". Perguntou se fazia o merge antes.
14. Respostas às três perguntas de logs: consentimento **"Pergunta sem padrão"**; usuários enviam pelo **site,
    que recebe e grava**; nome visível **"Ajude a melhorar o DuiaOS"**.
15. Rodou `configurar-relatorios.sh` (deu erro, depois funcionou), o teste de falha e o `zramswap`; fez os merges.
16. **"Teste feito. Merge feito também."** e pediu para fechar o bloco registrando tudo para o próximo chat.

## 3. Visão e regras do produto ditas neste chat
- **O Wise é soberano no sistema**: usa qualquer aplicativo como a pessoa, com ou sem integração (ler a tela,
  abrir aplicativos, clicar, digitar). Ações arriscadas (enviar, apagar, pagar, instalar, confirmar) com
  aprovação.
- **Agenda**: local + link .ics + Google, Microsoft/Teams e provedores privados (CalDAV).
- **Clima**: cidade escolhida pela pessoa.
- **Motor da IA**: Ollama (mantido); hardware do Dell fica como está por enquanto.
- **Continuidade**: tem de funcionar entre chats e entre contas do Claude, sem depender da memória de uma conversa.
- **Documentação para usuários** desde já, como as distribuições; **site** com visual moderno estilo Apple
  (three.js), promovendo o sistema.
- **Repositórios separados por finalidade** (site/documentação, Wise, sistema aberto, sistema fechado).
- **Logs**: igual aos sistemas de mercado, de **todo o sistema** (não só do Wise), uso e erros, centralizados no
  repositório `duiaos-diagnosticos`; nome visível **"Ajude a melhorar o DuiaOS"**; consentimento perguntado sem
  opção marcada.
- Correções dele: o endereço do site (`duiaos.gustavoduia.workers.dev`, não `.cloudflare.workers`); o log não é
  só do Wise, é do sistema inteiro.

## 4. Decisões
| Decisão | Quem | Por quê | Alternativas descartadas | Onde |
| --- | --- | --- | --- | --- |
| Manter o **Ollama** como motor | Gustavo (após medição) | Ollama 8,0–8,2 pedaços/s, igual ou melhor que llama-server; MTP/rascunho mais lentos no Dell | llama-server com MTP, rascunho 0.8B, ngram, OpenVINO (GPU sem OpenCL no Debian 13) | ADR 036 |
| `duiaos-agente`: serviço D-Bus de sistema, plano simulado (`apt-get -s`) + polkit + mesma assinatura na execução; lista fechada (atualizar, instalar, remover); protegidos nunca removidos | Claude (pedido W2) | Menor privilégio; o modelo só pede | Dar sudo ao Wise | ADR 034 |
| Acessibilidade ligada na sessão (AT-SPI), `grim`, `wtype` | Claude | Para o Wise usar aplicativos sem integração | Só capturas de tela | ADR 035 |
| Clima pelo **MET Norway** (CC BY 4.0, uso comercial) + Nominatim | Claude | Licença permite produto comercial | Open-Meteo (só uso não comercial) | W13 (Wise) |
| Agenda: local, .ics, CalDAV, Google e Microsoft (OAuth com PKCE, segredos no cofre) | Gustavo (escopo) / Claude (técnica) | Pedido dele | — | W14 (Wise) |
| Wise usando o computador: ler/ver N0, abrir N1, clicar/digitar N2 com aprovação condicional por palavras de risco; senhas nunca lidas | Gustavo (visão) / Claude (níveis) | "Soberano no sistema" com segurança | — | W15 (Wise) |
| Aprovação N2: `preparar()` → cartão "Posso fazer isto?" → `executar()`; 15 min sem resposta = não | Claude | Confirmar o nível N2 | Confirmação em texto pelo modelo | W16 (Wise) |
| **Continuidade no Git**: `CLAUDE.md` + `docs/continuidade/` (CONTEXTO, ESTADO, RECURSOS, DIARIO) em cada repositório e `conferir-recursos.py` (marcadores `arquivo::texto`) | Claude, pelo pedido | A carinha antiga voltou porque o Dell tinha a main e o robô só existia em PRs sem merge | Memória só no Project/chat | ADRs do dia; `CLAUDE.md` |
| Documentação **Diátaxis** (como o Ubuntu), Astro + Starlight, com Pagefind | Claude (estudo) | Padrão das distribuições | Wiki, documentação dentro do site | ADR 037 |
| Site em **Cloudflare Workers** (Astro estático + Worker para `/api/*`, D1, KV), three.js | Gustavo (Cloudflare) / Claude (técnica) | Pedido dele | GSAP (licença própria) | ADR 038 |
| Site e documentação = **dois aplicativos** num repositório privado `duiaos-websites` (`site/`, `documentacao/`), **PR irmão** obrigatório quando algo visível muda | Gustavo ("opção A") | Como Ubuntu/Fedora/Debian: endereços separados | Repositórios separados para cada um; site dentro do `duiaos` | ADR 039 |
| Diagnóstico do Wise (diário técnico, "Não ficou bom") e correções do log real | Claude, pelo pedido | Erros relatados pelo Gustavo | — | W17, W18 (Wise) |
| **Registros do sistema e "Ajude a melhorar o DuiaOS"**: journald persistente, biblioteca `duiaos_registro` em todos os programas, falhas com rastro e assinatura (Python por gancho; nativos pelo systemd-coredump), perfil do computador, coletor `duiaos-relatorios`, níveis (`nao_escolhido` padrão, desligado, erros, erros_e_uso, desenvolvimento), anonimização fora do desenvolvimento, destino único `duiaos-diagnosticos` | Gustavo (conceito, nome, consentimento, transporte) / Claude (técnica) | Estudo: journald, apport/whoopsie (Ubuntu), ABRT (Fedora, abandonado em 2026), systemd-coredump, Ubuntu Insights, eos-metrics, KUserFeedback, popcon | Opt-out (proposta do Fedora, derrubada); Git direto para usuários (exigiria credencial no computador) | ADR 040 |
| O Wise registra pelo `duiaos_registro`; conteúdo da pessoa só no nível desenvolvimento; sai o envio próprio do Wise | Claude | Um mecanismo só para o sistema | Envio próprio do Wise por Git (W17) | W19 (Wise) |

## 5. O que foi feito, removido e concluído (com a situação ao fim do chat)
Fluxo usado neste chat: branch `claude/...` + PR, merge do Gustavo por squash (**isso mudou depois**: ver 13).

**duiaos**
- PR **#9** `claude/tres-frentes` (reuniu #6–#8): duiaos-ollama, duiaos-ia, Central de IA (ADRs 030–033),
  `duiaos-agente` (034), acessibilidade (035), `ferramentas/medir-motores.py`, continuidade, ADRs 036–039,
  workflow `documentacao-irma.yml`. **Merge feito** em 12/10 ~17h20. #6–#8 fechados sem merge. Testado no Dell.
- O site, que nasceu dentro do `duiaos` no PR #9, foi **removido** dele e levado ao `duiaos-websites`.
- PR **#10** `claude/logs-do-sistema`: registros do sistema F1 (ADR 040) — `relatorios/` (biblioteca
  `duiaos_registro`, coletor), pacote `duiaos-relatorios`, ganchos em todos os programas, `ferramentas/
  configurar-relatorios.sh` e `ler-relatorios.py`. **Merge feito** 12/10 18h07. **Testado no Dell.**
- PR **#11** `claude/fechamento-12-10`: só continuidade. Merge feito depois (aparece na main antes do chat
  seguinte).

**duiaos-wise**
- PR **#5** `claude/wise-tres-frentes` (reuniu #3–#4): robô (W10), resposta rápida (W11–W12), aprovação W2/W16,
  clima W13, agenda W14, uso do computador W15, continuidade. **Merge feito.** Testado no Dell.
- PR #6 (W17/W18) **fechado pelo GitHub** quando a branch-base do #5 foi apagada; refeito como **#7**:
  diário técnico, "Não ficou bom", correções do log, ferramentas `energia` e `fixar_na_ilha`. **Merge feito.**
- PR **#8** `claude/wise-no-registro-do-sistema` (W19): o Wise no registro do sistema; **removidos**
  `wise/envio_diagnostico.py`, `ferramentas/configurar-diagnostico.sh`, `ferramentas/ler-diagnosticos.py`.
  **Merge feito.** Testado no Dell (reclamação chegou ao `duiaos-diagnosticos`).
- PR **#9** `claude/fechamento-12-10`: só continuidade (merge feito depois, não confirmado neste chat).

**duiaos-websites**
- Bootstrap da `main` (LICENSE + README), depois PR **#1** (site + documentação, dois aplicativos, workflows de
  publicação). **Merge feito** 12/10 15h57 e **publicado** (o Gustavo testou e aprovou).
- PR **#2**: avisos `:::note[Na próxima versão]` em 14 páginas (a 0.2.0 publicada não tem Wise nem Central de IA).
  Merge feito.
- PR #3 fechado pelo GitHub (base apagada) e refeito como **#4** ("Quando o Wise erra", energia e Ilha). Merge
  feito.
- PR **#5** ("Ajude a melhorar o DuiaOS" e comando `duiaos-relatorios`) e **#6** (Wise no registro do sistema).
  Merges feitos.
- PR **#7** `claude/fechamento-12-10`: só continuidade (merge depois, não confirmado neste chat).

**duiaos-diagnosticos**
- Criado pelo Gustavo (privado). PR **#1**: README e CLAUDE.md (organização `maquinas/<maquina>/<dia>/<hora>.json`
  + `perfil.json`, formato 1, privacidade). Merge feito. Recebe relatórios do Dell direto na `main`.

**Project do claude.ai:** `claude/contexto.md` e `claude/estado-atual.md` viraram ponteiros para o Git.

## 6. Testes e medições
- **Dell — motores (Qwen3.5 4B, Iris Xe, `medir-motores.py`)**: Ollama 8,0–8,2 pedaços/s escritos e 12,4–12,7 s
  no total; llama-server com o mesmo arquivo 7,6–8,2/s; MTP no processador e rascunho 0.8B mais lentos; OpenVINO
  na placa não rodou (sem `intel-opencl-icd` no Debian 13). Resultado: Ollama mantido.
- **Ambiente do Claude**: Wise 59 → 85 testes (W17/W18) → 81 testes (W19); `duiaos` 19 → 22 testes de
  `relatorios/` + ia + agente; CalDAV real com Radicale (HTTPS); MET Norway e Nominatim reais; AT-SPI real com
  Xvfb; **systemd-journald real** no ambiente para provar biblioteca → journal → `journalctl` → coletor → Git;
  `systemd-analyze verify` das unidades; catálogo validado; capturas do QML conferidas.
- **Dell — W2/clima/agenda/computador**: o Gustavo testou ("deu certo tudo"); a análise do log do dia achou 6
  defeitos de conversa (cidade inventada, previsão de hoje dita como de amanhã, argumento com acento repetido,
  título inventado após cancelamento, promessa de ação sem ação, programa de terminal sem ícone) e a falta de
  ferramenta para reiniciar — todos corrigidos no W18.
- **Dell — registros do sistema**: 1º relatório chegou; teste de falha (`ZeroDivisionError` em `duiaos-teste`)
  chegou agrupado com rastro; `journalctl -x` mostrou o catálogo; o próprio coletor teve um defeito real
  (estado sem sudo) que foi registrado e enviado sozinho. Achados: `zramswap.service` falhou em 5 boots
  anteriores (no boot das 17h29 subiu bem); `gkr-pam` na Tela de Entrada é normal.
- **Dell — Wise no registro (18h20)**: aquecimento ~49 s depois do boot; um pedido simples ~38 s (uma rodada
  ~22 s); uma reclamação ("Não ficou bom") chegou com a linha do tempo da tarefa.

## 7. Estado das máquinas ao fim do chat
- **Dell** (`duiaos`, i5-1135G7, 16 GB, Iris Xe, Debian 13): pacotes do DuiaOS do commit `f75b9bc` (conteúdo do
  PR #10); Wise da branch do #8 (conteúdo igual à main). "Ajude a melhorar o DuiaOS" ligado no nível
  **desenvolvimento**, máquina `dell`, transporte Git, chave do sistema em `/etc/duiaos/relatorios/` (privada só
  root), configuração em `/etc/duiaos/relatorios.conf`, deploy key "DuiaOS dell (relatórios, escrita)" no
  `duiaos-diagnosticos`. Journal persistente; coletor a cada hora.
- Talvez exista no `duiaos-diagnosticos` a deploy key antiga **"Wise dell (escrita)"** (script do Wise que saiu
  no W19) — **não confirmado**; se existir, remover e apagar `~/.ssh/duiaos-diagnosticos` no Dell.
- **Mac**: `gh` autenticado; clones em `~/Projetos/` (`duiaos`, `duiaos-wise`, `duiaos-websites`). Segredos
  `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` criados no `duiaos-websites` (valores não registrados aqui).
- **Cloudflare (conta do Gustavo)**: Workers `duiaos` e `duiaos-docs`, D1 `duiaos-site` (tabela `chamados`), KV
  `duiaos-site-cache`; publicação automática a cada merge.

## 8. Pendências
1. **Desempenho do Wise** (aquecimento ~49 s, pedido simples ~38 s). Por quê: a 1ª leitura de instruções + 25
   ferramentas é longa. Fazer: medir pelos eventos `wise.rodada` (métricas do Ollama) e reduzir. Repositório
   `duiaos-wise`. Quem: Claude. **Provavelmente já tratado** no chat de 2026-10-12 19h51 (W20: aquecimento antes do
   login) — não confirmado aqui; leia a memória dele.
2. **Resposta sobre aplicativo que não existe no apt** (reclamação de 12/10): explicar e oferecer alternativas.
   `duiaos-wise`. Claude. **Provavelmente tratado** no chat 19h51 (catálogo de aplicativos) — não confirmado.
3. **Logs F2** (uso agregado + tela "Ajude a melhorar o DuiaOS" na 1ª entrada e nas Configurações com polkit) e
   **F3** (`/api/relatorios` no Worker do site gravando em lotes; resumo semanal das falhas). `duiaos` +
   `duiaos-websites`. Claude. **Provavelmente feito** no chat 19h51 (ADR 041; config já com transporte `https`
   padrão) — conferir.
4. **Lançar a 0.3.0** e tirar os avisos "Na próxima versão"; decidir como o Wise chega na ISO. **Decidido depois**
   pelo Gustavo: o Wise vai instalado na ISO (ADR 042) — conferir se a 0.3.0 saiu.
5. **Registrar os aplicativos no Google e na Microsoft** para a agenda (guia em `duiaos-wise/docs/
   contas-de-agenda.md`; identificadores em `/usr/share/duiaos-wise/contas.json`). Quem: Gustavo (no console do
   Google Cloud e no Entra), depois o Claude ajusta. Pendente.
6. **zramswap**: se voltar a falhar, o relatório agora traz as últimas linhas do serviço; ler com
   `ler-relatorios.py` e corrigir (pacote `zram-tools` vem da lista da ISO em `build/config/package-lists/`).
7. **Deploy key antiga do Wise** (seção 7): Gustavo, no GitHub › `duiaos-diagnosticos` › Settings › Deploy keys;
   no Dell: 🔗 DELL `rm -f ~/.ssh/duiaos-diagnosticos ~/.ssh/duiaos-diagnosticos.pub`.
8. Plano maior: W3 voz, W4 gateway da nuvem no `duiaos-ia`, P4 instalador próprio (detectar BitLocker), remover
   compromissos da agenda, Flatpak no agente, ajuda offline (`duiaos-ajuda`), páginas `man`.

## 9. Perguntas em aberto para o Gustavo
- Titular dos direitos (pessoa física ou CNPJ).
- Nome visível do recurso "Wise usando o computador" (hoje "Usar o computador").
- Domínio do site (`duiaos.com.br` e `docs.duiaos.com.br` foram citados; registro não confirmado).
- Licença da documentação: proprietária (hoje) ou aberta (CC BY-SA, como o Ubuntu)?
- (Respondida depois, no chat 19h51: o Wise vai instalado com o sistema.)

## 10. Erros, correções e lições
- **Carinha antiga do Wise de volta**: o robô estava só em PRs sem merge e o Dell tinha a main → criada a
  continuidade no Git, o inventário de recursos com conferência automática e a seção "instalado em cada máquina".
- **PRs empilhados fechados pelo GitHub**: o `--delete-branch` no merge do PR de baixo apagou a base do PR de cima
  (Wise #6, site #3), refeitos como #7 e #4. Lição registrada (hoje irrelevante: só `main`).
- **Modo automático de permissões** bloqueou gravações no meio do chat; o Gustavo trocou para o manual.
- **`configurar-relatorios.sh`**: a cópia da chave pública feita pelo root no `/tmp` (sticky bit) não podia ser
  apagada pelo usuário e o script parou → a `.pub` passou a ser lida da pasta da chave.
- **`duiaos-relatorios estado` sem sudo** quebrava (pasta só do root) → `situacao.json` público; o próprio
  sistema registrou e enviou esse defeito.
- **1ª coleta** com limite de 60 mil linhas descartava o que vinha depois → para no limite e continua depois.
- Serviço que falhou sem a causa no relatório → o relatório leva as últimas linhas do serviço.
- Site: vários ajustes de visual (profundidade dos objetos 3D, legibilidade, celular); `pkill -f` matou o
  próprio shell do Claude (usar `kill $(pidof …)`); arquivos de relatório copiados para uma branch de
  documentação por engano foram descartados antes de qualquer commit.
- Comando de clone errado dado ao Gustavo (`github.com:` sem `git@`) → trocado por `gh repo clone`.

## 11. Forma de trabalho (preferências do Gustavo vistas aqui)
- Objetividade; passo a passo com comandos completos; cada bloco com 🍎 MAC, 🔗 DELL (sessão SSH, **sem**
  `ssh` na frente) ou 💻 DELL LOCAL; avisar que a sessão SSH cai após `sudo reboot`.
- Medir antes de afirmar ganho; causa raiz, nada paliativo; o Gustavo testa no Dell e faz os merges.
- Decisões de produto e nomes são dele; ele quer ser consultado em escolhas de escopo (consentimento, transporte,
  nome) e aceita a recomendação técnica do Claude quando explicada.
- Quer continuidade à prova de troca de chat e de conta.

## 12. Arquivos salvos em cada repositório (resumo)
- **duiaos**: `agente/` e `pacotes/duiaos-agente/`; `ferramentas/medir-motores.py`; `shell/sessao/` e
  `shell/pacotes.list` (acessibilidade); `relatorios/` (`duiaos_registro/`, `coleta.py`, `config.py`, `envio.py`,
  `perfil.py`, `principal.py`, testes); `pacotes/duiaos-relatorios/` (journald, coredump, catálogo, serviço,
  timer, polkit, known_hosts do GitHub); ganchos `duiaos_registro.ligar` em `shell/*/main.py`,
  `apps/central-de-ia/main.py`, `ia/`, `agente/`; `ferramentas/configurar-relatorios.sh`,
  `ferramentas/ler-relatorios.py`, `ferramentas/conferir-recursos.py`; `.github/workflows/documentacao-irma.yml`;
  `CLAUDE.md`; `docs/continuidade/` (CONTEXTO, ESTADO, RECURSOS, DIARIO); `docs/decisoes.md` (ADRs 034–040).
  Removido: `site/` (foi para o `duiaos-websites`).
- **duiaos-wise**: `wise/ferramentas/` (aplicativos, clima, agenda, computador, energia_e_ilha), `wise/agenda/`,
  `wise/computador/`, `wise/agente_do_sistema.py`, `wise/internet.py`, `wise/diagnostico.py`, orquestrador,
  interface (cartão de aprovação, Configurações, "Não ficou bom"), testes, `docs/decisoes.md` (W13–W19),
  `docs/arquitetura.md`, `docs/contas-de-agenda.md`, `CLAUDE.md` e `docs/continuidade/` (hoje substituídos pelos
  arquivos `*-WISE.md` do `duiaos`). Removidos no W19: `wise/envio_diagnostico.py`,
  `ferramentas/configurar-diagnostico.sh`, `ferramentas/ler-diagnosticos.py`.
- **duiaos-websites**: `site/` (Astro, three.js, Worker `/api/versoes`, `/api/suporte`, D1, KV), `documentacao/`
  (Starlight, ~25 páginas Diátaxis), `compartilhado/`, workflows `site.yml` e `documentacao.yml`, `CLAUDE.md` e
  `docs/continuidade/` (hoje substituídos pelos arquivos `*-WEBSITES.md` e pelo `GUIA-SITE-E-DOCUMENTACAO.md` do
  `duiaos`).
- **duiaos-diagnosticos**: `README.md`, `CLAUDE.md` e os relatórios em `maquinas/dell/` (dados pessoais; não
  copiar para lugar público).

## 13. Orientação para o próximo chat
- **Regras mudaram depois deste chat**: trabalho **só na `main`**, sem branches nem PRs; o `duiaos` é o
  repositório oficial e guarda **todas** as instruções e memórias (`docs/continuidade/`); os `CLAUDE.md` e
  `docs/continuidade/` criados aqui no `duiaos-wise` e no `duiaos-websites` foram substituídos (ADR 043). Onde
  esta memória fala de PRs e branches, é histórico.
- **O Wise é o cérebro do DuiaOS e vai instalado junto com o sistema** (decisão do Gustavo no chat seguinte,
  ADR 042). Não proponha o DuiaOS sem o Wise.
- Leia, depois desta, a memória `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`: ela continua deste ponto e
  provavelmente resolveu as pendências 1–4.
- Falhas relatadas: siga o `CLAUDE.md` do `duiaos` (seção "Quando o Gustavo relatar uma falha") e leia o
  `duiaos-diagnosticos` com `ferramentas/ler-relatorios.py`. Os dados são pessoais.
- Conceitos que nasceram aqui e continuam valendo: aprovação N2 com cartão; agente do sistema com lista fechada;
  registros do sistema com níveis e anonimização; PR irmão virou "página da documentação no mesmo chat".
