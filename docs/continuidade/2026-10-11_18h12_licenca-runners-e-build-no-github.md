# Chat 2026-10-11 18h12 — Licença proprietária, runners próprios e build no GitHub

> Segundo chat do projeto, logo depois do chat fundador (`2026-10-09_16h41_fundacao-iso-shell-dualboot-licenca.md`).
> A memória foi escrita em 12/10/2026 22h31, a pedido do Gustavo, a partir da conversa inteira (nenhum trecho
> se perdeu).
>
> **As regras do projeto mudaram depois deste chat.** Hoje vale: trabalho só na `main` do `duiaos`, **sem
> branches e sem pull requests**; instruções e memórias só em `duiaos/docs/continuidade/`; cada repositório com
> a sua finalidade (`duiaos`, `duiaos-fontes-abertas`, `duiaos-wise`, `duiaos-diagnosticos`, `duiaos-websites`).
> Este chat entregou tudo por **arquivos .patch** e chegou a decidir um fluxo por **branch `claude/...` + pull
> request** (ADR 022). Isso está registrado como aconteceu, mas **não vale mais**. A memória do chat também era
> mantida no Project do Claude (`claude/contexto.md` e `claude/estado-atual.md`), hoje só histórico.

## 1. Identificação
- **Início:** 2026-10-11 18:12 (aviso "Message sent at Sun 2026-10-11 18:12" na primeira mensagem).
- **Fim do trabalho:** 2026-10-11 20:52 (o Gustavo encerrou o bloco). Pedido desta memória: 2026-10-12 22:31.
  Horário de Brasília.
- **Conta e sessão:** conta do Gustavo (GitHub `gustavoduia`), Project "DuiaOS" do Claude. Sessão claude.ai/code
  `session_01LNJv494L2MgxXejDV85Zvu`.
- **Chat anterior:** `2026-10-09_16h41_fundacao-iso-shell-dualboot-licenca.md`. **Chat posterior conhecido:**
  `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md` (já com regras e decisões mais novas).
- **Repositórios mexidos:**
  - `gustavoduia/duiaos`: três patches, aplicados e enviados pelo Gustavo (commits `1f82022`, `bce6a39`,
    `333dd41`). O Claude só leu o repositório: clone anônimo, porque nessa época ele era público.
  - `gustavoduia/duiaos-fontes-abertas`: **criado neste chat** pelo script `ferramentas/criar-repo-publico.sh`,
    rodado pelo Gustavo. O conteúdo é o espelho automático da pasta `publico/`.

## 2. O que o Gustavo pediu (em ordem)
1. **"Continuar o DuiaOS"** (18:12). Pelo `estado-atual.md`, o próximo passo era o **patch de licença**: trocar
   a GPLv3 por licença proprietária, criar o repositório público `duiaos-fontes-abertas` para o que a lei exige e
   resolver o build arm64 (na época se acreditava que os runners ARM gratuitos só existiam em repositório público).
2. **Dúvidas antes de aplicar o patch (18:24):**
   - Repositório privado "é regra ou é só para proteger o meu trabalho desde agora? Posso manter ele aberto para
     usar de forma ilimitada a geração dos releases?"
   - Se dois repositórios (privado com o que é próprio, público com o que é GPL) é a melhor estratégia: "Gostei
     da ideia, assim separamos o que é meu e o que é aberto e não posso me apropriar de forma fechada. Mas
     pensando em uma arquitetura high level [...] é o melhor caminho mesmo ou tem algo melhor?"
   - Processo: "eu assumo tudo que é possível ser feito localmente por mim [...] abrir sempre novas conversas
     para não ter conversas longas que ficam caras, estamos com algum processo ainda engessado que precisa ser
     modificado por um processo mais ágil [...] sem gerar gargalo ou risco?"
3. **Decisões e pedidos (18:35):**
   - "Vamos de repositório privado + runners próprios." Perguntou o que instalar no Mac e no Dell e quanto tempo
     leva um build no MacBook Air M4 de 16 GB.
   - "Vamos de pull requests em branch. Só preciso que me diga o passo a passo."
   - Antecipar o `.deb` para logo depois da P3, "se for melhor".
   - Incluir agora a sincronização da pasta `publico` e o script de verificação, com o repositório
     `duiaos-fontes-abertas` criado por script ("melhor você já me passar o código para eu criar via terminal já
     pronto como precisa estar").
   - Forma de entrega: "cada tarefa e cada etapa bem descrita [...] com os scripts completos para eu apenas copiar
     e colar no terminal".
4. **Correção de forma (18:53):** "Você precisa ser mais claro quando o script é pra rodar no Mac, quando é pra
   rodar no Dell via SSH ou pra rodar no Dell localmente." Ele tinha rodado no Dell um script feito para o Mac.
5. **Correção de forma (19:13):** "Eu sempre estarei conectado no Dell e no Mac ao mesmo tempo. Mantenho duas
   janelas abertas [...] comandos para rodar no Dell via SSH envia identificado para rodar no SSH considerando
   que já estou conectado via SSH sempre".
6. **Entender o novo build (19:21 e 19:27):** se podia fechar a janela do `gh run watch`, e "ta rodando lá no
   github ou aqui na minha maquina? Em qual delas [...]? ai quando termina, a ISO vai para o Github ou fica aqui
   no mac ou fica no dell?"
7. **Flexibilidade e organização (19:39):**
   - Escolher qual arquitetura e em qual computador: as duas no Mac, as duas no Dell, separadas, ou só uma.
   - "A arquitetura M4 ou Core I5 influencia? [...] Posso gerar qualquer versão em qualquer computador?"
   - Padronizar tudo em `/Users/gustavoduia/Projetos/`, inclusive o `duiaos-fontes-abertas` local, e "Padronize
     a pasta Projetos dentro do Dell tbm, vamos manter um padrão de organização igual nos dois computadores."
8. **Teste do `reiniciar-no-windows`** e da amd64 no Mac (20:01). Ele relatou que o Dell reiniciou direto no
   Windows, sem o menu do DuiaOS e sem pedir a chave do BitLocker.
9. **Mudança de estratégia (20:09):**
   - "pode ser a opção A rodando no Dell sempre" (amd64 no Dell); "O arm64 da pra continuar fazendo só pelo Mac?"
   - "Deixar no Dell o que é melhor para ser criado no Dell. Deixar no Mac o que é melhor pra criar no Mac."
   - **"Mas vamos abrir o repositório novamente e vamos utilizar o Github como estávamos usando anteriormente,
     mandando tudo para lá. Ai deixa o ambiente local preparado mas em stand by, onde vamos usar somente quando o
     projeto estiver finalizando, ai fechamos o repositório novamente e passamos a rodar localmente."**
10. **Conferir os runners** (20:22): pediu "um comando só para testar se estão online ou offline".
11. **Encerrar** (20:52): "Agora que o ambiente está fechado, vamos encerrar esse chat aqui e iniciar um novo."
    A mensagem anterior (20:50) começava com "Uma coisa que lembr…" e veio cortada; o assunto não foi retomado.

## 3. Visão e regras do produto ditas pelo Gustavo
- **Código próprio fechado, mas visível por enquanto.** Ele aceitou a separação: o que é dele é proprietário, e o
  que é GPL fica aberto em outro repositório, para não se apropriar de código livre ("não posso me apropriar de
  forma fechada").
- **Repositório `duiaos` público durante o desenvolvimento, privado na fase final** (decisão de 20:09, citada
  acima). Razão dele: usar o GitHub "de forma ilimitada".
- **Cada máquina gera o que faz melhor:** amd64 no Dell, arm64 no Mac, e "Se for tudo melhor no Dell, deixa tudo
  no Dell".
- **Organização:** tudo do projeto dentro de `~/Projetos`, com o mesmo padrão no Mac e no Dell.
- **Público-alvo:** usuários finais. Já estava decidido no chat anterior; aqui entrou na documentação (README,
  `visao.md`).
- Nada novo sobre nomes de componentes; continuam os do chat anterior.

## 4. Decisões
| Decisão | Quem | Por quê | Alternativas descartadas | Onde ficou |
| --- | --- | --- | --- | --- |
| Código próprio proprietário, "todos os direitos reservados"; usuários finais pelo EULA; até `d6526e4`/v0.0.1 continua GPLv3 | Gustavo (no chat anterior); texto do Claude | Proteger o produto | GPLv3 (ADR 005, substituída) | ADR 017, `LICENSE`, `publico/EULA.md` |
| Dois repositórios: `duiaos` (próprio) + `duiaos-fontes-abertas` (público: ISOs, EULA, licenças de terceiros, modificações em código livre); `publico/` é a fonte da verdade | Claude propôs, Gustavo aprovou | Cumprir as licenças sem expor o código próprio; modelo Darwin/macOS, ChromiumOS/ChromeOS, AOSP | Um repositório só | ADR 018, `publico/` |
| Dependências do código próprio só com licença permissiva; GPL só como processo separado | Claude (a partir de regra do Gustavo) | Não ser obrigado a abrir o código próprio | — | ADR 019 |
| Colaboradores só com contrato de cessão de direitos + NDA (substitui o CLA) | Claude (a partir de regra do Gustavo) | Titularidade do código | CLA público | ADR 021, `CONTRIBUTING.md` |
| Fluxo por branch `claude/...` + pull request | Gustavo, a partir de proposta do Claude | Acabar com download/apply de patches | Patch `.patch` | ADR 022. **Revogada depois: hoje é só `main`, sem branch nem PR** |
| Empacotar o código próprio em `.deb` + APT assinado logo após a P3 (fase P3b) | Gustavo aprovou ("se for melhor") | Atualizações pelo apt; licença por pacote; build rápido | Deixar para a P6 | ADR 023, `docs/visao.md` (linha P3b) |
| Runners próprios: Mac M4 (`duiaos-mac`) e Dell (`duiaos-dell`), escolha por arquitetura a cada build | Gustavo pediu; desenho do Claude | Custo zero de minutos; flexibilidade | Só runners do GitHub | ADR 020 (texto revisto 2 vezes) |
| Pastas padrão `~/Projetos/{duiaos, duiaos-fontes-abertas, duiaos-isos, duiaos-runner}` nas duas máquinas | Gustavo | Organização igual | ISOs em `~/duiaos-isos`, runner em `~/actions-runner-duiaos` | ADR 024 |
| amd64 **não** é gerada no Mac | Claude, com a causa raiz medida; Gustavo escolheu "opção A" | Rosetta não roda no chroot do debootstrap sem `/proc` | QEMU no Mac (lento, 40–80 min estimados); GitHub como reserva | ADR 025, `gerar-iso.yml` |
| **Repositório `duiaos` volta a público; build no GitHub; runners próprios em espera até a fase final** | Gustavo | Minutos ilimitados e build rápido | Privado + runners | ADR 025, `ferramentas/README.md` |
| Com o repositório público, runners próprios desligados e o workflow recusa `mac`/`dell` | Claude | Num repositório público, um PR de terceiros poderia rodar código no Dell/Mac | Deixar os runners ligados | ADR 025, `gerar-iso.yml` |
| O Wise deve nascer já em repositório privado | Claude recomendou | O que é publicado enquanto público fica copiável para sempre | Wise no `duiaos` | ADR 025 (atenção). Depois aplicado com o `duiaos-wise` |
| Não reinstalar o Dell agora; reinstalar só depois da P3 | Claude recomendou | Uma reinstalação valida tudo de uma vez, sem perder runner e repositório | Reinstalar já | `estado-atual.md` do Project |

## 5. O que foi feito, removido e concluído
Tudo no `gustavoduia/duiaos`, entregue em patches que o Gustavo aplicou (`git apply`) e enviou à `main`.

### Patch 1 — `duiaos-licenca-runners.patch` → commit `1f82022` (2026-10-11 18:51)
Mensagem: "Licença proprietária, repositório público, runners próprios e verificação da instalação". Substituiu
um patch anterior do mesmo chat (`duiaos-licenca-proprietaria.patch`), que nunca foi aplicado.
- `LICENSE`: GPLv3 → aviso proprietário (titular Gustavo Duia; exceções para componentes de terceiros e para as
  versões GPL até `d6526e4`).
- `publico/` (novo; vira o repositório `duiaos-fontes-abertas`):
  - `EULA.md`, minuta 0.1 com pontos **[REVISAR]**: LGPD, CDC, art. 6º da Lei 9.609, provedores de IA.
  - `LICENCAS-DE-TERCEIROS.md`: componentes, onde obter o código-fonte e a oferta por escrito de 3 anos.
  - `TRADEMARKS.md`, movido da raiz e atualizado (DuiaOS, Zoinho, Wise, logo).
  - `README.md`, `LICENSE`, `logo/duiaos-simbolo.svg`, `modificacoes/README.md`, `.github/ISSUE_TEMPLATE/`
    (formulário "Relatar um problema").
- `README.md` (aviso de repositório interno; público = usuários finais; seção Licença), `CONTRIBUTING.md`
  (cessão + NDA; regras de dependências), `docs/decisoes.md` (005 e 006 substituídas; novas 017–023),
  `docs/visao.md` (público, seção 6, linha P3b no roteiro).
- ISO:
  - `os-release`, `motd` e `--iso-publisher` passam a apontar para o `duiaos-fontes-abertas`.
  - `build.sh` copia o EULA, as licenças e a marca para `/usr/share/duiaos/licenca/` e publica
    `duiaos-VERSÃO-ARQ.packages`.
- `/usr/lib/duiaos/verificar-instalacao` (novo): testa sistema, UEFI/Secure Boot, Windows no firmware e no GRUB,
  SSH, idioma, teclado, fuso, NTP, Wi-Fi, internet, áudio, apt, pacotes da interface, EULA, disco e runner.
  Imprime OK/AVISO/FALHA.
- `.github/workflows/sincronizar-publico.yml` (novo): espelha `publico/` no repositório público (segredo
  `DUIAOS_TOKEN_PUBLICO`).
- `.github/workflows/gerar-iso.yml`: runners próprios, release em rascunho no repositório público.
- `ferramentas/` (novo): `README.md`, `runner-instalar.sh`, `configurar-runners.sh`,
  `configurar-acesso-dell.sh` (deploy key somente leitura), `criar-repo-publico.sh`, `lancar-versao.sh`.

### Patch 2 — `duiaos-escolher-maquina.patch` → commit `bce6a39` (19:47)
Mensagem: "Escolha da máquina por arquitetura, pastas em ~/Projetos e correção de containers órfãos".
- `gerar-iso.yml`:
  - Entradas `amd64`/`arm64` (mac, dell, github, nao) e rótulos por máquina.
  - Emulação automática (Rosetta/QEMU).
  - Containers nomeados `duiaos-build-*`, parados quando o job é cancelado (correção de bug, seção 10).
  - ISOs de teste guardadas em `~/Projetos/duiaos-isos`.
- `runner-instalar.sh` e `configurar-runners.sh` reescritos:
  - Runner em `~/Projetos/duiaos-runner`, com rótulo `duiaos-mac` ou `duiaos-dell`.
  - Removem o runner antigo, movem as ISOs, clonam o público e param containers órfãos.
  - No Mac, Colima com Rosetta.
- Novos: `ferramentas/gerar-iso.sh`, `ferramentas/trazer-isos.sh`. Usuário padrão do Dell trocado para
  `gustavo@duiaos`. ADR 020 revista e ADR 024 nova; `README.md` e `ferramentas/README.md` atualizados.

### Patch 3 — `duiaos-github-agora.patch` → commit `333dd41` (20:19)
Mensagem: "Repositório público com build no GitHub; runners próprios em espera".
- `gerar-iso.yml`:
  - Padrão conforme a visibilidade do repositório: público → `github`; privado → amd64 no Dell e arm64 no Mac.
  - Recusa `mac`/`dell` com o repositório público, recusa `amd64=mac`, e guarda a ISO de teste do GitHub em
    Artifacts por 7 dias.
- Novos: `ferramentas/runners-espera.sh` (`pausar|retomar|estado`) e `ferramentas/baixar-isos.sh` (`[dell]
  [RUN]`). `gerar-iso.sh` atualizado.
- `README.md` (aviso: código proprietário visível publicamente), `CONTRIBUTING.md`, ADR 025 nova,
  `ferramentas/README.md` (tabela de fases e o caminho de volta para a fase final).

### Fora do repositório (feito pelo Gustavo com os scripts)
- `duiaos-fontes-abertas` criado, com token fine-grained no segredo `DUIAOS_TOKEN_PUBLICO`. A existência é
  confirmada pelo clone nas duas máquinas; o token e a primeira sincronização não foram confirmados por saída.
- Deploy key somente leitura do Dell. É **inferido** (não confirmado por saída): o Dell conseguiu `git pull` do
  repositório privado às 19:56.
- Runners registrados e depois pausados; chave SSH do Mac copiada para o Dell.

### Concluído
- Ambiente de build completo e testado, com o fluxo do GitHub funcionando de ponta a ponta.
- `reiniciar-no-windows` validado no Dell, rodando do repositório.

## 6. Testes e medições
| Onde | O quê | Resultado |
| --- | --- | --- |
| Ambiente do Claude | `shellcheck`, `actionlint`, `bash -n`, YAML; simulação do job "Planejar" com todas as combinações; `git apply --check` dos 3 patches | Tudo ok. O `verificar-instalacao` rodou no contêiner só para pegar erros de execução |
| Mac (runner) | ISO arm64 nativa (run 38179393657) | **6 min 6 s** |
| Dell (runner) | ISO amd64 nativa (mesmo run) | Run total **28 min 27 s**; parte do tempo dividindo a CPU com um container órfão |
| GitHub (antes) | Build "Visão consolidada" (as duas em paralelo) | **6 min 0 s**. Conclusão: o ganho dos runners próprios é custo, não velocidade |
| Mac | ISO amd64 via Rosetta (run 38182154412) | **Falhou**: `debootstrap: E: Unable to execute target architecture` |
| Mac | Diagnóstico em container amd64 | 1) fora do chroot OK; 2) chroot sem `/proc`: **FALHOU** (`rosetta error: Unable to open /proc/self/exe: 2`); 3) chroot com `/proc` OK; 4) `arch-test amd64` OK. Causa raiz confirmada |
| Dell | `verificar-instalacao` (sistema `dev-5031d1b`) | **23 OK, 2 AVISO, 1 FALHA**. FALHA: `reiniciar-no-windows` ausente (ISO antiga). AVISOs: SSH ligado à mão; EULA ausente. Secure Boot ligado, UEFI, Windows no firmware e no GRUB, Wi-Fi `wlp0s20f3`, áudio `sof-hda-dsp`, PipeWire, 33 GB livres, runner e Docker ok |
| Dell | `sudo sh .../reiniciar-no-windows` (do repositório) | Reiniciou **direto no Windows**, sem o menu do DuiaOS e **sem pedir a chave do BitLocker** |
| GitHub (patch 3) | Build das duas ISOs (run 38183964897) | Sucesso: `duiaos-dev-333dd41-amd64.iso` (898 MB) e `-arm64.iso` (~1 GB). Baixadas no Mac e copiadas para o Dell |
| Mac | `runners-espera.sh pausar` | O script mostrou "online" (atraso do GitHub); conferido depois: **offline** |

## 7. Estado das máquinas ao fim do chat (11/10 20:52)
- **Mac (MacBook Air M4 16 GB, macOS):**
  - Ferramentas: Homebrew, `gh` 2.102.0 autenticado, Colima 0.10.3 (6 CPU, 8 GB, 80 GB, vz, virtiofs, Rosetta
    ligado) e `docker` 29.9.0.
  - Runner `mac-m4` (rótulo `duiaos-mac`) em `~/Projetos/duiaos-runner`, serviço launchd **desinstalado
    (pausado)**; Colima desligado pelo `runners-espera.sh`.
  - Pastas: `~/Projetos/{duiaos, duiaos-fontes-abertas, duiaos-isos, duiaos-runner}`. Também existem
    `~/Projetos/msn-nostalgic` (outro projeto) e uma pasta antiga `duiaos-dev-5031d1b-amd64`, provavelmente
    download antigo.
  - ISOs em `~/Projetos/duiaos-isos`: `dev-1f82022-arm64` e `dev-333dd41-amd64/arm64`.
  - Chave SSH ed25519 nova, copiada para o Dell (acesso sem senha).
- **Dell (Latitude 3420), DuiaOS `dev-5031d1b` instalado (ISO antiga), usuário `gustavo`, hostname `duiaos`:**
  - Docker (`docker.io`) e `gh` instalados.
  - Runner `dell-latitude` (rótulo `duiaos-dell`) em `~/Projetos/duiaos-runner`, serviço systemd **desinstalado
    (pausado)**.
  - Repositório em `~/Projetos/duiaos`, com deploy key de leitura (host SSH `github-duiaos`; inferido).
  - Clone de `duiaos-fontes-abertas`; ISOs `dev-1f82022-amd64` e `dev-333dd41-amd64/arm64`.
  - SSH ligado à mão; Secure Boot ligado.
- **GitHub:**
  - `duiaos` na `main` = `333dd41`.
  - Visibilidade: o Gustavo foi orientado a torná-lo público (passo 3 do patch 3). A saída não foi mostrada, mas é
    coerente com o resto (não confirmado).
  - `duiaos-fontes-abertas` público. Variáveis opcionais `DUIAOS_AMD64_EM`/`DUIAOS_ARM64_EM` não foram criadas.

## 8. Pendências
1. **Fluxo de trabalho por PR (ADR 022).**
   - **Situação:** **revogado** pelas regras novas (só `main`, sem branch nem PR). Não fazer.
   - **Próximo chat:** confirmar que a ADR 022 está marcada como substituída em `docs/decisoes.md`. Se não estiver,
     o Claude registra a substituição (só na `main`).
2. **P3: tela de login, animação de boot, papel de parede e menu de energia com "Reiniciar no Windows".**
   - **Falta:** o nome da tela de login e a confirmação de que o Wise só aparece depois do login.
   - **Próximo passo:** o Claude implementa na `main` do `duiaos` (greetd + QML provável; Plymouth).
   - **Status:** pode já ter avançado no chat `2026-10-12_19h51_...` (não confirmado). Ler a memória dele antes.
3. **P3b: código próprio em `.deb` + repositório APT assinado** (ADR 023).
   - **Status:** pelo `CLAUDE.md` atual, o apt já vive em `duiaos-fontes-abertas` (`gh-pages`) e existe
     `ferramentas/criar-chave-apt.sh`, então provavelmente foi feito depois (não confirmado).
4. **Reinstalar o Dell com uma ISO nova.**
   - **Por quê:** validar o EULA, o comando `reiniciar-no-windows` no lugar certo e o SSH desligado de fábrica.
   - **Quando:** depois da P3. Ao reinstalar, o runner e o repositório do Dell somem.
   - **Passos:**
     1. Gerar e baixar a ISO:

        🍎 MAC
        ```bash
        bash ferramentas/gerar-iso.sh arm64=nao && bash ferramentas/baixar-isos.sh dell
        ```
     2. Gravar o pendrive e instalar no Dell.
     3. 💻 DELL LOCAL: `sudo systemctl enable --now ssh`.
     4. 🍎 MAC: `ssh-copy-id gustavo@duiaos` e `bash ferramentas/configurar-runners.sh dell` (quando voltar ao
        modo local).
5. **Tag v0.1.0.**
   - **Passo:** 🍎 MAC: `bash ferramentas/lancar-versao.sh 0.1.0`.
   - **Situação:** nunca testado (release em rascunho → upload → publicar no `duiaos-fontes-abertas`); depende do
     segredo `DUIAOS_TOKEN_PUBLICO`.
   - **Status:** pode já ter sido feita (não confirmado).
6. **Fase final (repositório privado + build local).** Quando o projeto estiver terminando:

   🍎 MAC
   ```bash
   gh repo edit gustavoduia/duiaos --visibility private --accept-visibility-change-consequences
   bash ferramentas/configurar-acesso-dell.sh
   bash ferramentas/runners-espera.sh retomar
   ```
   - **Nunca testado:** arm64 no Dell via QEMU.
7. **EULA e oferta de código-fonte:** são minutas. Antes da 1.0 falta revisão por advogado, definir o titular
   (pessoa física ou CNPJ) e definir o e-mail oficial no lugar de **[A DEFINIR]** (`publico/LICENCAS-DE-TERCEIROS.md`).
8. **Limpeza opcional:**
   - 🍎 MAC e 🔗 DELL: `rm -f ~/Projetos/duiaos-isos/duiaos-dev-1f82022-*`.
   - Pasta antiga `duiaos-dev-5031d1b-amd64` no Mac, se não tiver uso.
9. **Mensagem cortada:** às 20:50 o Gustavo escreveu "Uma coisa que lembr…" e o resto se perdeu. Perguntar se
   ainda importa.

## 9. Perguntas em aberto para o Gustavo
- Nome da tela de login.
- Confirmar que o Wise só aparece depois do login (recomendação do Claude).
- Titular dos direitos: Gustavo pessoa física ou empresa (CNPJ)?
- E-mail oficial de contato para o EULA e para a oferta de código-fonte.
- O que ele ia dizer em "Uma coisa que lembr…".

## 10. Erros, correções e lições
- **Comando para a máquina errada:** o Claude não deixou claro que os scripts de `ferramentas/` rodam no Mac, e o
  Gustavo rodou um no Dell. **Mudou:** todo bloco de comando leva 🍎 MAC, 🔗 DELL (sessão SSH, **sem** `ssh` na
  frente, porque ele vive com duas janelas abertas) ou 💻 DELL LOCAL.
- **Usuário do Dell errado:** os scripts assumiam `duia@duiaos`; o usuário real é `gustavo`. Corrigido para
  `gustavo@duiaos`.
- **Container órfão:** cancelar um job (pela regra de concorrência) não parava o `docker run`, e ficaram dois
  builds no Dell ao mesmo tempo. **Corrigido no patch 2:** containers nomeados `duiaos-build-*`, `docker rm -f`
  em `always()` e limpeza de órfãos no início.
- **Afirmação sem medir:** o Claude disse que o GitHub "levava bem mais" que o Mac; a medição mostrou ~6 min nos
  dois. Corrigido na conversa. Lição: medir antes de afirmar ganho.
- **Rosetta:** a amd64 no Mac foi proposta sem teste e falhou. A causa raiz foi provada com um diagnóstico de
  5 passos antes de decidir, sem desligar a checagem do Debian (isso seria paliativo).
- **Armazenamento:** a cota de Artifacts de repositório privado não comporta ISOs. Por isso, no modo local, as ISOs
  ficam na máquina.
- **Segurança:** runner próprio em repositório público permitiria que PRs de terceiros rodassem código nas
  máquinas. Por isso os runners ficam pausados enquanto o repositório for público.
- **Estado aparente de offline:** o GitHub leva de 1 a 2 minutos para marcar um runner como offline. Conferir de
  novo antes de concluir que a pausa falhou.
- **Processo:** o Claude tentou pedir acesso de escrita (`add_repo` push) por conta própria e foi bloqueado pelo
  ambiente; seguiu com patches.

## 11. Forma de trabalho (preferências do Gustavo)
- Ele executa tudo o que é local (aplicar patch, push, tags, comandos); o Claude projeta e entrega.
- Comandos completos para copiar e colar, com passo a passo e marcados por máquina (seção 10).
- Duas janelas sempre abertas: Terminal do Mac e sessão SSH no Dell.
- Conversas curtas: "abrir sempre novas conversas para não ter conversas longas que ficam caras".
- Explicações curtas quando ele pede ("não precisa resposta longa agora").
- Ele decide; o Claude recomenda com alternativas e trade-offs, e ele escolhe.

## 12. Arquivos salvos em cada repositório
| Repositório | Arquivos | Commit |
| --- | --- | --- |
| `duiaos` | `LICENSE`; `README.md`; `CONTRIBUTING.md`; `docs/decisoes.md` (005/006 substituídas; 017–023); `docs/visao.md`; `build/build.sh`; `build/config/hooks/normal/0500-duiaos-identidade.hook.chroot`; `build/config/includes.chroot_after_packages/usr/lib/duiaos/verificar-instalacao` (novo); `.github/workflows/gerar-iso.yml`; `.github/workflows/sincronizar-publico.yml` (novo); `ferramentas/{README.md, runner-instalar.sh, configurar-runners.sh, configurar-acesso-dell.sh, criar-repo-publico.sh, lancar-versao.sh}` (novos); `publico/{EULA.md, LICENCAS-DE-TERCEIROS.md, LICENSE, README.md, TRADEMARKS.md (movido da raiz), logo/duiaos-simbolo.svg, modificacoes/README.md, .github/ISSUE_TEMPLATE/*}` (novos) | `1f82022` |
| `duiaos` | `gerar-iso.yml`; `ferramentas/{runner-instalar.sh, configurar-runners.sh, configurar-acesso-dell.sh, README.md}`; `ferramentas/{gerar-iso.sh, trazer-isos.sh}` (novos); `README.md`; `docs/decisoes.md` (020 revista, 024) | `bce6a39` |
| `duiaos` | `gerar-iso.yml`; `ferramentas/{runners-espera.sh, baixar-isos.sh}` (novos); `ferramentas/{gerar-iso.sh, README.md}`; `README.md`; `CONTRIBUTING.md`; `docs/decisoes.md` (018 ajustada, 025) | `333dd41` |
| `duiaos` | `docs/continuidade/2026-10-11_18h12_licenca-runners-e-build-no-github.md` (esta memória) | "Memória do chat 2026-10-11 18h12: …" |
| `duiaos-fontes-abertas` | Criado neste chat; conteúdo = espelho de `duiaos/publico/` (sincronização automática) | Commits do workflow (mensagem genérica "Atualiza o conteúdo público do DuiaOS") |
| Project do Claude | `claude/contexto.md` e `claude/estado-atual.md` reescritos várias vezes (hoje só histórico) | — |

## 13. Orientação para o próximo chat
- Leia esta memória **depois** da do chat fundador e **antes** de `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`:
  as decisões dela são mais novas e valem sobre estas.
- Continua valendo daqui:
  - Licença proprietária (ADR 017) e repositório `duiaos-fontes-abertas` para o que é aberto, alimentado pela pasta
    `publico/` (ADR 018).
  - Dependências permissivas (ADR 019), pastas `~/Projetos` iguais nas duas máquinas (ADR 024) e build no GitHub
    com runners em espera enquanto o `duiaos` for público (ADR 025).
  - amd64 nunca no Mac.
- **Não vale mais:** branches, PRs e patches (ADR 022). Hoje o Claude trabalha direto na `main`.
- Ferramentas prontas para o Gustavo (todas no Mac): `gerar-iso.sh`, `baixar-isos.sh [dell]`, `lancar-versao.sh`,
  `runners-espera.sh`. O Dell só tem rodado `verificar-instalacao` e `git pull`.
- O Dell ainda roda uma ISO antiga (`dev-5031d1b`), a menos que um chat posterior tenha reinstalado. Confira em
  `ESTADO.md`.
- Por onde começar: ler `ESTADO.md` e a memória mais recente, depois responder às perguntas da seção 9 que
  continuarem abertas (nome da tela de login, Wise depois do login, titular, e-mail).
