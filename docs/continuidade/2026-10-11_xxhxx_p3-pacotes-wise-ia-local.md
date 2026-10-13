# Chat 2026-10-11 (hora xxhxx) — P3, pacotes .deb, Wise W1/presença e IA local nativa

> Terceiro chat do projeto, logo depois de `2026-10-11_18h12_licenca-runners-e-build-no-github.md`.
> Memória escrita em 13/10/2026, a pedido do Gustavo, a partir da conversa inteira. **Atenção:** a parte inicial
> do chat (de "Continuar o DuiaOS: P3" até ~01h15 de 12/10) foi resumida automaticamente pelo ambiente durante a
> conversa; ela é descrita aqui a partir desse resumo e dos commits/PRs. Detalhes finos dessa parte podem faltar.
>
> **As regras do projeto mudaram depois deste chat.** Hoje vale: trabalho só na `main`, **sem branches e sem pull
> requests**; instruções e memórias só em `duiaos/docs/continuidade/`; cada repositório com a sua finalidade
> (`duiaos`, `duiaos-fontes-abertas`, `duiaos-wise`, `duiaos-diagnosticos`, `duiaos-websites`). Este chat
> trabalhou com **branches `claude/...` + pull requests** (ADR 022) e guardava a memória no Project do Claude
> (`claude/contexto.md` e `claude/estado-atual.md`). Isso está registrado como aconteceu, mas **não vale mais**.

## 1. Identificação
- **Início:** 2026-10-11, hora não confirmada (**xxhxx**). Não há aviso de horário na primeira mensagem
  preservada. Limites conhecidos: depois das 20:52 de 11/10 (fim do chat anterior) e antes das 21:27 de 11/10
  (criação do PR #1 do `duiaos`, `2026-10-12T00:27Z`). Horário de Brasília.
- **Fim do trabalho:** 2026-10-12 11:34 (o Gustavo encerrou o bloco: "vamos abrir um novo chat e encerrar esse
  aqui"). Pedido desta memória: 2026-10-12 22:34; retomado em 2026-10-13 07:29.
- **Conta e sessão:** conta do Gustavo (GitHub `gustavoduia`), Project "DuiaOS" do Claude. Sessão claude.ai/code
  `session_01RyL6GUeYHjnofruaFibJNT`.
- **Chat anterior:** `2026-10-11_18h12_licenca-runners-e-build-no-github.md`. **Chats posteriores conhecidos:**
  o do `duiaos` #9 / Wise #5 ("três frentes", 12/10), o de fechamento 12/10 18h30 e
  `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`.
- **Repositórios mexidos:**
  - `gustavoduia/duiaos` (público nesta fase): PRs #1 a #8.
  - `gustavoduia/duiaos-wise` (privado, criado pelo Gustavo neste chat): PRs #1 a #4.
  - Project "DuiaOS" do Claude: `claude/contexto.md` e `claude/estado-atual.md` (hoje só histórico).

## 2. O que o Gustavo pediu (em ordem)
1. **"Continuar o DuiaOS: P3."** Pediu orientação sobre o nome da tela de login e confirmou: "Sim, o Wise só
   aparece após a tela de login."
2. Nomes e comportamento: **"1 - Vamos chamar tela de entrada e tela de bloqueio. 2 - Vamos ter uma tela só com o
   mesmo visual, apenas descrevendo quando estiver iniciando uma sessão ou desbloqueando a tela de uma sessão
   aberta, porém bloqueada."**
3. **"Melhor tudo em um pull request só, para ser mais prático."**
4. Perguntou se precisava baixar a ISO ou se dava para atualizar o sistema já instalado (daí nasceu a P3b:
   código próprio em pacotes `.deb` + repositório apt).
5. Regra de comandos: **"Já estou conectado via SSH no Dell. Mantenha o que eu pedi para descrever se o script deve
   ser rodado no terminal do Mac, no SSH conectado no Dell ou direto no terminal do Dell. [...] não precisa de
   código para conectar no SSH."**
6. Relatou, com o monitor externo: o cartão de senha ficava entre as duas telas e o ponteiro batia numa "parede"
   entre telas de tamanhos diferentes. Escolheu ponteiro livre, perguntou o esforço de mexer no labwc e decidiu:
   **"não quero ter esse trabalho todo em ter um labwc próprio... manter o labwc padrão do debian"**.
7. "Pronto, deu tudo certo. Pode seguir." Ativou o GitHub Pages (houve erros 422/409 da API no caminho).
8. Pergunta só para responder: se ainda havia dependência de Mac e Dell ligados para gerar versões. Depois: "Ok,
   pode corrigir na próxima pull request. [...] Deixa que o teste do release eu faço mais pra frente."
9. **Wise:** Gemini + um modelo local leve; abrir pela Barra, pela Ilha e por atalho; repositório `duiaos-wise`.
10. Teste da W1 (só com o modelo local): a janela não redimensionava e a 2ª pergunta repetia a resposta da 1ª.
    Diretriz: **"A IA precisa ser um recurso universal pertencente ao sistema operacional"**, com uma central de
    configuração de IA no sistema.
11. Presença do Wise: iniciar com o sistema; botão flutuante no canto inferior direito; maximizar; saudação
    **"Olá, [nome do usuário]. Que bom te ver por aqui! Se precisar de ajuda, pode contar comigo. Boa
    navegação!"** em balão que some sozinho e pode ser fechado; no futuro, saudação falada (opções fala, escrita,
    fala e escrita, desativada); **sempre em segundo plano, sem poder finalizar**; ao fechar, o balão mostra
    "descansando" e há um ícone perto da bateria. "Pode seguir com o W2 e com o restante do seu plano."
12. **Ollama no sistema + catálogo de modelos:** "Pode seguir com a transformação do Ollama." Pediu ao menos mais um
    modelo: Gemma 4 (12B e 4B), Qwen 3 e 3.5 (8B e 14B), Llama 3, 3.1, 3.2, 3.3 (1B, 3B, 8B, 70B), Phi-3, 3.5 e 4
    (3.8B e 14B), "em repositório e no painel de configuração de IA [...] download, instala e configura
    automaticamente [...] apenas um modelo de IA ativo". Queria o Llama como padrão; depois de perguntado,
    escolheu **padrão Qwen3.5 4B**, **baixado no 1º login** (o Wise avisa e mostra o progresso) e **modelos de
    70B mostrados no catálogo, mas desativados com aviso** quando falta memória.
13. **Carinha do Wise:** "carinha tipo de robô mais bem feita e alegre. Com animação no balão de boas vindas, e
    com efeitos mais bonitos."
14. Erro na Central de IA: "Sem autorização para mudar a IA do sistema" até ao ativar o 4B já baixado; ficou sem
    modelo ativo.
15. Pergunta: os pacotes não deveriam vir pelo `apt` depois do repositório de atualizações? (só responder)
16. Central de IA não atualizava a lista ao remover um modelo ("Seria legal o sistema entender as alterações em
    tempo real"); campo de digitação do Wise escondia a linha nova; com a janela fechada, a resposta deveria vir
    num balão ("como se estivesse falando comigo"), e clicar no balão, na carinha ou no atalho abre a conversa.
17. **Velocidade:** "otimizar o algoritmo dos modelos [...] a primeira pergunta [...] demora muito [...] respostas
    instantâneas e precisas, sendo um ótimo assistente pessoal com menos delay possível."
18. **"Cara, parece que piorou. Está extremamente lento agora até na segunda resposta em diante."** Pediu análise
    técnica profunda de como LLMs locais funcionam num hardware básico e como gerar as saídas de diagnóstico.
19. **Correção de termos:** "Porque você fala Ollama e depois fala Qwen? [...] Ou é um modelo, ou é outro."
20. "Mas precisamos ter o Ollama como motor de IA? Achei que precisava só do modelo e o sistema teria o seu motor
    próprio mais leve e rápido."
21. Mandou três diagnósticos (`sudo duiaos-ia diagnostico`) e relatos de uso real (tempos abaixo).
22. Erro na Tela de Entrada: "Não foi possível entrar: a session is already being configured" (tinha apertado
    Enter sem senha antes).
23. **"Pode executar os 3 passos na mesma atualização. Mesmo que demore mais ou fique grande [...] vamos abrir um
    novo chat e encerrar esse aqui."** (os 3 passos: motor mais rápido, clima/agenda no Wise, W2).

## 3. Visão e regras do produto ditas neste chat
- **Nomes dados pelo Gustavo:** **Tela de Entrada** (login) e **Tela de Bloqueio** — uma tela só, mesmo visual,
  só o texto muda ("Digite a senha para iniciar a sessão" / "Sessão bloqueada. Digite a senha para
  desbloquear"); **Central de IA**. Mantidos: Barra de Recursos, Ilha de Aplicativos, Central de Aplicativos,
  Menu de Energia (com "Reiniciar no Windows").
- O Wise **só existe depois do login**; **inicia com a sessão**, **cumprimenta pelo primeiro nome**, **não pode ser
  finalizado** (fechar = descansar), tem **botão flutuante com carinha** no canto inferior direito e ícone perto
  da bateria; abre pelo botão, pela Barra, pela Ilha e por **Super+W**; a janela pode ser maximizada.
- **"A IA precisa ser um recurso universal pertencente ao sistema operacional"** (ADR 029): serviço do sistema +
  Central de IA; o Wise é cliente. **Um só modelo de IA ativo** para o sistema inteiro.
- Modelos não vão na ISO: ficam no repositório/online e o sistema baixa, instala e configura sozinho.
- Carinha do Wise: **robô bem feito e alegre**; balão de boas-vindas animado, com efeitos bonitos.
- Respostas **o mais instantâneas possível**: "um ótimo assistente pessoal com menos delay possível".
- labwc do Debian **sem modificações**, mesmo com a "parede" do ponteiro entre monitores.
- **Correção do Gustavo sobre termos:** o Claude chamava o Ollama de "IA local" em mensagens do sistema; o certo é
  **Ollama = motor** (programa que roda modelos) e **Qwen3.5 4B etc. = modelo**. Llama (Meta) não tem relação com
  o Ollama.
- Achava que o sistema teria "motor próprio mais leve e rápido": explicado que um motor é obrigatório e que o
  pesado é o llama.cpp (que o Ollama usa por dentro); a troca só se justificaria por medição.

## 4. Decisões
| Decisão | Quem | Por quê | Descartado | Onde ficou |
| --- | --- | --- | --- | --- |
| Tela de Entrada e Tela de Bloqueio: uma tela, mesmo visual; greetd + cage; bloqueio por overlay layer-shell + PAM, com swaylock de reserva; Plymouth próprio | Gustavo (nomes/visual), Claude (técnica) | Nomes descritivos; Qt 6.8 do Debian sem `ext-session-lock` | Duas telas diferentes | ADR 026 |
| labwc do Debian sem modificações; telas estendidas; ponteiro com comportamento padrão | Gustavo | Esforço de manter um labwc próprio (GPL, a cada atualização) | labwc modificado para "ponteiro livre"; espelhamento | ADR 027 |
| Código próprio em `.deb` (duiaos-identidade, duiaos-shell, duiaos-desktop) e repositório apt assinado no GitHub Pages (`duiaos-fontes-abertas`, `gh-pages`), canais `estavel`/`teste`; ISO feita dos mesmos pacotes | Claude, aprovado pelo Gustavo | Atualizar sem reinstalar | Só ISO | ADRs 023 e 028 |
| Um PR único por entrega ("tudo em um pull request só") | Gustavo | Praticidade | Vários PRs | (fluxo da época) |
| Wise: Gemini + modelo local leve; repositório privado `duiaos-wise`; ferramentas tipadas N0 na W1 | Gustavo (provedores, repo), Claude (arquitetura) | Proteger o Wise; segurança | — | `duiaos-wise/docs/decisoes.md` (W01–W09) |
| IA é do sistema: serviço `duiaos-ia` + Central de IA; Wise cliente | Gustavo | "recurso universal" | Gateway só no Wise (ADR 014) | ADR 029 |
| Presença do Wise (autostart em laço, bolha em processo separado, estado em `$XDG_RUNTIME_DIR`) | Gustavo (comportamento), Claude (técnica) | Wise sempre disponível | Poder fechar o Wise | W09, `shell/README.md` |
| Ollama empacotado pelo DuiaOS (`duiaos-ollama`, do release oficial com sha256, **sem CUDA**: 19 MB amd64 / 11 MB arm64 em vez de ~1,5 GB) | Claude, aprovado | Tamanho; atualização pelo apt | Instalador oficial em `/usr/local` | ADR 030 |
| Padrão **Qwen3.5 4B**, baixado no 1º login; modelos grandes visíveis e desativados com aviso; um só ativo | Gustavo (escolheu entre opções) | Licença permissiva (Llama não é livre) e tamanho | Llama como padrão (licença conflita com ADR 019) | ADR 030 |
| Serviço `duiaos-ia` em Python + Gio, D-Bus `org.duiaos.IA1`, polkit `org.duiaos.ia.gerenciar` (sessão ativa sem senha; SSH com sudo); Central de IA em PySide6 + QtDBus | Claude | Padrões do Linux; a sessão não tem agente de senha do polkit | — | ADR 031 |
| Resposta rápida: modelo ativo sempre na memória (se ≤ 50% da RAM), contexto fixo 8192, 1 modelo/1 pedido no Ollama, abertura fixa + aquecimento no Wise, resposta em partes | Claude | Medido: 1ª palavra de ~11 s para ~0,4 s | — | ADR 032, W11 |
| Calibração por computador (threads e placa integrada Vulkan, `OLLAMA_IGPU_ENABLE=1`), opções publicadas a todos; `duiaos-ia diagnostico/calibrar` | Claude | Medição no Dell | Escolha fixa | ADR 033 |
| Wise não disputa o processador com a IA (texto parcial 4x/s, carinha sem redesenho contínuo), resultados compactos | Claude | Causa da lentidão relatada | — | W12 |
| Manter o Ollama por enquanto; trocar de motor só se medição mostrar ganho (comparar llama.cpp direto, "rascunho" e OpenVINO) | Gustavo aceitou a proposta | Medido: escrita já a ~87% do limite da RAM | Motor próprio do zero | (decidido depois: ADR 036, outro chat) |
| `duiaos-ia` sobe com o computador | Claude | 19 s do login à 1ª resposta | Só abrir no login | ADR 033 (texto), commit `a7587ae` |
| Juntar PRs empilhados no de cima (#8 e Wise #4), porque os merges são por squash | Claude | Squash quebra PR empilhado | Merge em sequência | Comentários nos PRs #6, #7, Wise #3 |

## 5. O que foi feito, removido e concluído
### `gustavoduia/duiaos`
| PR | Branch | Conteúdo | Situação |
| --- | --- | --- | --- |
| #1 | `claude/p3` | P3: Tela de Entrada/Bloqueio, animação de boot (Plymouth "Órbita"), papel de parede "Órbita", Menu de Energia com "Reiniciar no Windows" | **Merge** (squash) em 11/10 ~22h02, testado no Dell |
| #2 | (P3b) | Pacotes `.deb`, `pacotes/construir.sh`, `versao.sh`, `publicar.sh`, `instalar-local.sh`, workflow `pacotes.yml`, ISO dos pacotes | **Merge** em 11/10 ~22h44, testado (`verificar-instalacao`: 31 e 33 OK) |
| #3 | — | Pontos de entrada do Wise (Barra, Ilha, Super+W) + mensagem do `lancar-versao.sh` | **Merge** em 11/10 ~23h43 |
| #4 | — | Barra/Ilha não vazam `QT_WAYLAND_SHELL_INTEGRATION`; ADR 029 | **Merge** em 12/10 ~00h04 |
| #5 | — | Wise na sessão (autostart em laço), ícone perto da bateria, contrato no `shell/README.md` | **Merge** em 12/10 ~00h53 |
| #6 | `claude/ollama` | Pacote `duiaos-ollama`; `publicar.sh` por arquitetura e sem sobrescrever versão; ADR 030 | **Fechado sem merge** (conteúdo foi para o #8) |
| #7 | `claude/central-de-ia` | `ia/` (serviço, catálogo, cliente), `apps/central-de-ia/`, pacote `duiaos-ia`, ADR 031; correção do polkit (anotação `org.freedesktop.policykit.owner`); Central em tempo real | **Fechado sem merge** (conteúdo foi para o #8) |
| #8 | `claude/ia-agil` | Reúne #6, #7 + ADRs 032–033, calibração, diagnóstico, `duiaos-ia` no boot, termos "motor"/"modelo", correção da Tela de Entrada (`cancel_session`) | **Fechado sem merge**; o conteúdo entrou na `main` pelo **#9** (`claude/tres-frentes`, merge em 12/10 17h20, outro chat). Testado no Dell (branch instalada à mão) |

Commits do #8 (todos na branch `claude/ia-agil`): `99e5423` (Ollama), `be096ed` (duiaos-ia e Central), `3248750`
(polkit), `f17ac50` (Central em tempo real), `2cbeab1` (ADR 032), `92976d0` (ADR 033), `ca9eb41` (termos),
`047d8ed` e `3a3d179` (calibração), `a7587ae` (serviço no boot), `2a859d2` (Tela de Entrada).

### `gustavoduia/duiaos-wise`
| PR | Conteúdo | Situação |
| --- | --- | --- |
| #1 | W1: Wise textual, 7 ferramentas N0, gateway (Ollama local + Gemini com consentimento), auditoria SQLite, chave do Gemini no cofre do sistema | **Merge** (12/10 ~00h04), testado no Dell (só com o modelo local) |
| #2 | Presença: bolha com carinha (aberto/descansando/pensando), saudação, descanso | **Merge** (12/10 ~00h53), aprovado no Dell |
| #3 | W10: modelo do sistema, progresso do 1º login, **carinha de robô**, **balão animado**, resposta no balão com a janela fechada, campo de texto | **Fechado sem merge** (foi para o #4) |
| #4 | Reúne #3 + W11 (abertura fixa, aquecimento, resposta em partes) + W12 (sem disputa de CPU, lista de aplicativos, regras de não inventar) | **Fechado sem merge**; o conteúdo seguiu no **Wise #5** (`claude/wise-tres-frentes`, merge em 12/10 17h20, outro chat — não confirmado em detalhe) |

Removido neste chat: `ferramentas/instalar-ia-local.sh` do `duiaos-wise` (a IA local passou a vir dos pacotes).

## 6. Testes e medições
- **Ambiente do Claude:**
  - `duiaos-ollama` gerado do release real e instalado num contêiner; `publicar.sh` testado com chave descartável.
  - Serviço `duiaos-ia` testado com D-Bus de sessão e Ollama falso (até 18 testes) e com **polkit e D-Bus do
    sistema reais** (reproduziu "Only trusted callers ... CheckAuthorization()" e confirmou a correção).
  - **Ollama real** com `qwen3.5:0.8b` e `qwen3:0.6b` (2 núcleos, sem GPU), pedido do Wise de ~970 pedaços:
    1ª palavra ~11 s (frio) e ~6 s (carregado) → **~0,4 s** com aquecimento + abertura fixa. O Qwen3.5 (atenção
    híbrida) só reaproveita o que leu em pontos de parada criados no fim de cada pedido; o Qwen3 reaproveita o
    começo normalmente. Mudar `num_ctx` entre pedidos recarrega o modelo (+5 s). Cancelar o aquecimento: de
    11,6 s para 1,0 s depois de trocar `urllib` por `http.client`.
  - Wise: 35 testes; capturas offscreen da carinha, do balão e da Central.
- **Dell (i5-1135G7, Iris Xe, 16 GB):**
  - Qwen3.5 **9B**, só processador: ler 31 pedaços/s, escrever ~5/s; repetido: 0,4 s.
  - Qwen3.5 **4B**, processador (diagnóstico): ler 70/s, escrever 12/s (~87% do limite da RAM).
  - Calibração com a Iris Xe: processador 43,5/8,7; **placa 137,4 ler / 9,8 escrever**; escolhida a placa
    (`{'num_gpu': 999, 'num_thread': 4}`); diagnóstico: ler 132/s, escrever 10/s.
  - Uso real relatado pelo Gustavo: do login à 1ª resposta ~19 s (antes da correção do boot) e depois "quase
    instantânea"; hora na 1ª pergunta após reiniciar ~4 s; perguntas simples ~4 s; lista de programas de 17–18 s
    para ~8–10 s. **"Está ficando muito bom."**
  - Tela de Entrada: senha vazia + senha certa → entra (correção confirmada no Dell).

## 7. Estado das máquinas ao fim do chat (12/10, 11h34)
- **Dell:** `duiaos` na branch `claude/ia-agil` (até `2a859d2`) instalado por `pacotes/instalar-local.sh`
  (duiaos-ollama `0.40.3-duiaos3`, duiaos-ia, Central de IA, Tela de Entrada corrigida); `duiaos-wise` na branch
  `claude/wise-agil` (até `fa4d8db`) por `pacote/instalar-local.sh`. Modelo ativo **Qwen3.5 4B** na Iris Xe;
  Qwen3.5 9B também baixado (removível). Instalação oficial antiga do Ollama em `/usr/local` removida pelo
  pacote. Pentes de RAM: DIMM1 3200 MT/s + DIMM2 2667 MT/s → rodam a 2667.
- **Mac:** sem mudanças registradas neste chat (chave privada do apt em `~/Projetos/duiaos-chaves`, fora dos
  repositórios).
- O que aconteceu depois (outros chats; não confirmado aqui): o conteúdo foi para a `main` pelo `duiaos` #9 e
  Wise #5, e o Dell foi atualizado nesses chats.

## 8. Pendências (ao fim deste chat)
1. **Três frentes numa atualização só** (pedido do Gustavo em 12/10 11h34): (a) motor mais rápido — medir
   Ollama x llama.cpp direto x "rascunho" (Qwen3.5 0.8B rascunhando o 4B) x OpenVINO e trocar só se ganhar;
   (b) clima e agenda no Wise; (c) W2 (`duiaos-agente` com ações aprovadas). **Provavelmente já resolvido** no
   chat seguinte (`duiaos` #9 e Wise #5: ADR 034 agente, ADR 036 "manter o Ollama", clima MET Norway, agenda) —
   não confirmado por este chat. Próximo chat: conferir em `docs/decisoes.md` e `ESTADO.md` antes de qualquer coisa.
2. **Merge do #8 e do Wise #4**: não aconteceu como PR; o conteúdo seguiu nos PRs seguintes (ver seção 5).
   Nada a fazer, salvo conferir que `ia/`, `apps/central-de-ia/` e as ADRs 030–033 estão na `main` (estão).
3. **Pente de memória**: trocar o DIMM2 por DDR4-3200 SODIMM 8 GB daria ~20% mais velocidade de escrita da IA.
   Decisão e compra do Gustavo (💻 DELL LOCAL: troca física). Pode ainda estar em aberto.
4. **Ferramentas de clima e agenda** que este chat só prometeu: ver pendência 1.
5. **Titular dos direitos** (pessoa física ou CNPJ): pergunta em aberto desde chats anteriores.

## 9. Perguntas que ficaram em aberto para o Gustavo
- Fonte da agenda: agenda do próprio sistema, Google Agenda ou as duas (resolvido depois? não confirmado).
- Titular dos direitos do DuiaOS (PF ou CNPJ).
- Se troca o pente de memória de 2667 por um de 3200.

## 10. Erros, correções e lições
- **Comando com `ssh` na frente**: o Gustavo teve de lembrar que nunca se escreve `ssh gustavo@duiaos '...'`;
  virou regra reforçada (🔗 DELL sem `ssh`).
- **Polkit recusava tudo**: o serviço rodava como `duiaos-ia` e o polkit só aceita consultas em nome de outro
  usuário se a ação declarar o dono (`org.freedesktop.policykit.owner`). Os testes usavam `--sem-polkit` e não
  pegaram. Lição: testar com polkit e D-Bus do sistema reais.
- **"Ficou mais lento"** depois da 1ª otimização: a janela do Wise refazia a lista inteira de mensagens a cada
  pedaço da resposta, e a carinha era redesenhada 60x/s com desfoque — isso tirava processador do llama.cpp. O
  9B ativo e uma lista de atualizações de ~1.200 pedaços pioravam. Lição: medir no Dell real, com a interface
  aberta, antes de afirmar ganho.
- **Calibração enviesada**: medidas seguidas esquentam o notebook (processador medido a 35/s, depois 70/s) e o
  "pedido típico" ignorava o reaproveitamento; corrigido com pausa de 10 s e pedido típico 150/100. A placa
  integrada ficou de fora por um limite de 40% da RAM (o 4B pede 42%).
- **Regra de "3 frases"** fez o Wise resumir um diagnóstico pedido em lista; trocada por "conversa curta, lista
  completa com números". A lista de programas usava `%CPU` do `ps` (média desde a abertura) e processos soltos;
  passou a somar por aplicativo e medir na hora.
- **Termos misturados** ("IA local (Ollama)") confundiram o Gustavo; padronizado "motor" x "modelo".
- **Tela de Entrada travava** depois de um erro (faltava `cancel_session` no greetd) — defeito da P3, achado neste
  chat.
- **PRs empilhados com merge por squash**: resolvido juntando tudo no PR de cima e fechando os de baixo.
- Cancelar o aquecimento quando chegava uma pergunta jogava fora o que já tinha sido lido; passou a esperar.

## 11. Forma de trabalho (preferências do Gustavo neste chat)
- Comandos sempre marcados 🍎 MAC, 🔗 DELL (sessão SSH já aberta, sem `ssh` na frente) ou 💻 DELL LOCAL.
- "Melhor tudo em um pull request só" (na época). Hoje: só `main`, sem PR.
- Responder só quando ele diz "só responda" / "não altere nada".
- Explicações técnicas profundas quando pedidas, mas com números medidos; ele testa no Dell e manda saídas.
- Termos consistentes (motor x modelo).
- Chats longos ficam caros: encerrar e abrir chat novo com memória salva.

## 12. Arquivos salvos em cada repositório
- **`duiaos`** (via PRs; #1–#5 na `main` por squash; #6–#8 fechados, conteúdo levado pelo #9):
  - `shell/entrada/`, `shell/bloqueio/`, `shell/comum/` (TelaDeAcesso), `shell/menu-de-energia/`,
    `shell/barra-de-recursos/` (botão e ícone do Wise), `shell/ilha-de-aplicativos/`, `shell/sessao/autostart`
    (Wise em laço, `duiaos-ia garantir-padrao`), `shell/README.md`.
  - `pacotes/` (duiaos-identidade, duiaos-shell, duiaos-desktop, **duiaos-ollama**, **duiaos-ia**),
    `pacotes/construir.sh`, `versao.sh`, `publicar.sh` (índice por arquitetura), `instalar-local.sh`,
    `pacotes/README.md`; `build/build.sh`; `.github/workflows/pacotes.yml`; `verificar-instalacao` (seção IA).
  - `ia/` (catalogo.json, catalogo.py, motor_ollama.py, hardware.py, servico.py, cliente.py, testes/, README.md),
    `apps/central-de-ia/` (main.py, CentralDeIA.qml), `apps/README.md`.
  - `publico/LICENCAS-DE-TERCEIROS.md` (Ollama e componentes; nota sobre modelos); `docs/decisoes.md`
    (ADRs 026–033).
- **`duiaos-wise`** (privado; #1–#2 na `main`, #3–#4 fechados, conteúdo levado pelo #5): núcleo do Wise, interface
  (janela, bolha, carinha, balão), leitura da IA do sistema, empacotamento, testes e `docs/decisoes.md`
  (W01–W12). Removido `ferramentas/instalar-ia-local.sh`. O código não é descrito aqui (repositório privado).
- **Project do Claude** (hoje só histórico): `claude/contexto.md` e `claude/estado-atual.md`, atualizados ao longo
  do chat.

## 13. Orientação para o próximo chat
- Este chat é a origem de: Tela de Entrada/Bloqueio, pacotes `.deb` + apt, Wise W1 e presença, IA do sistema
  (`duiaos-ollama`, `duiaos-ia`, Central de IA), carinha de robô e a otimização de velocidade (ADRs 026–033,
  W01–W12). Tudo isso já está na `main` (pelo `duiaos` #9 e Wise #5).
- Não repita os erros: sempre `cancel_session` no greetd; polkit com anotação de dono; não refazer a tela a cada
  pedaço da resposta; medir no Dell antes de afirmar ganho; "motor" (Ollama) x "modelo" (Qwen3.5 4B).
- As opções do Ollama (`num_thread`, `num_gpu`) são medidas por computador pelo `duiaos-ia` e todos os programas
  devem mandá-las iguais; mudar contexto/opções entre pedidos recarrega o modelo.
- No Dell, o 4B na Iris Xe lê ~135 pedaços/s e escreve ~10/s; o gargalo é escrever.
- As regras deste chat sobre branches/PRs e Project do Claude **não valem mais**: hoje só `main`, memória em
  `docs/continuidade/`. Comece pelo `REGRASINI.md`, `ESTADO.md` e as memórias mais novas, que trazem o que veio
  depois (três frentes, logs, site, organização dos repositórios).
