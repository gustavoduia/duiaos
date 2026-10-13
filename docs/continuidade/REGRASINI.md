# REGRASINI — como iniciar um chat novo do DuiaOS

Comando do Gustavo: **"Continuar o DuiaOS. Para isso, leia o arquivo
github.com/gustavoduia/duiaos/docs/continuidade/REGRASINI.md"**.

## 1. Ler toda a memória do projeto, na íntegra
1. Anexe o repositório oficial `gustavoduia/duiaos` (add_repo com push) e clone a `main`. Anexe também os outros
   repositórios que a tarefa usar (seção 6) e clone-os **ao lado** do `duiaos` (`../duiaos-wise` etc.).
2. Abra **todos** os arquivos `.md` de `docs/continuidade/` e leia **na íntegra**, sem pular nenhum:
   - primeiro as **memórias dos chats** (`AAAA-MM-DD_HHhMM_assunto.md`), em sequência, **do mais antigo para o
     mais recente**: elas contam como o projeto foi criado, o que o Gustavo decidiu e por quê;
   - depois os arquivos de referência: `CONTEXTO.md` (visão, regras, arquitetura), `ESTADO.md` (onde estamos),
     `RECURSOS.md`, `RECURSOS-WISE.md`, `RECURSOS-WEBSITES.md` (o que não pode regredir), `DIARIO*.md`
     (histórico técnico), `GUIA-SITE-E-DOCUMENTACAO.md` e o `REGRASFIM.md`.
3. Leia também `CLAUDE.md` e `docs/decisoes.md` (ADRs) do `duiaos`.
4. Decisão registrada numa memória vale até uma memória posterior dizer o contrário. **Nunca decida contra a
   visão do produto ou contra uma decisão do Gustavo; em dúvida, pergunte a ele.**

## 2. Planejar as pendências do último chat
Se a **memória mais recente** tem pendências em aberto, monte um planejamento para continuá-las e concluí-las
**neste chat**: o que falta, em que ordem, em qual repositório, o que depende do Gustavo (testes no Dell,
segredos, decisões).

## 3. Dizer ao Gustavo como vai continuar
Antes de mudar qualquer arquivo, faça um **pequeno resumo**, com base na última memória, de como vai continuar o
projeto nesta conversa (pendências e próximos passos), e rode `python3 ferramentas/conferir-recursos.py`.

## 4. Só a branch `main`
O projeto é feito **exclusivamente na `main`** de cada repositório. **Não há autorização para criar branches**
(nem para PRs). Antes de enviar: `git pull --rebase origin main`; depois `git push origin main`. Se o ambiente
bloquear ou pedir aprovação para enviar à `main`, pare e peça ao Gustavo para aprovar — nunca crie uma branch para
contornar.

## 5. O que é o DuiaOS
O DuiaOS é um sistema operacional baseado no **Debian 13 (trixie)**, com recursos de **propriedade fechada**.
O **Wise é o cérebro do DuiaOS**: vai embarcado e instalado com o sistema (ISO e apt; ADR 042).

## 6. Cada coisa no seu repositório
| Repositório | O que guarda |
| --- | --- |
| `gustavoduia/duiaos` | **Repositório oficial do projeto.** Código próprio do sistema e **todas** as instruções, memórias, decisões e a continuidade do projeto (inclusive do Wise e do site). |
| `gustavoduia/duiaos-fontes-abertas` | Código herdado com licença **GPL-3** (e outras que exigem publicação) que não podemos fechar, modificações em software livre de terceiros, EULA e licenças; ISOs nos Releases e o repositório apt (branch `gh-pages`, gerada pelo workflow). |
| `gustavoduia/duiaos-wise` | Todos os fontes do **Wise** (produto próprio). |
| `gustavoduia/duiaos-diagnosticos` | Logs do DuiaOS enviados para análise do suporte ("Ajude a melhorar o DuiaOS"). |
| `gustavoduia/duiaos-websites` | Fontes do site institucional e do site da documentação. |

**Nenhuma instrução para o Claude (CLAUDE.md, memórias, estado, regras) fica fora do `duiaos`.** Siga o que as
memórias anteriores ensinaram sobre manter cada arquivo no seu repositório.
