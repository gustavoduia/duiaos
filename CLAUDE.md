# DuiaOS — instruções para o Claude (qualquer conta)

A memória do projeto é este repositório, não o histórico de uma conversa. Siga a ordem abaixo em TODA sessão.

## Ao começar (antes de mudar qualquer arquivo)
0. **Memória dos chats primeiro** (`docs/memoria-dos-chats/` deste repositório): leia o README e TODOS os arquivos, do mais antigo ao mais novo (na `main` e na
   branch `claude/memoria-dos-chats`, se ainda não tiver merge). Eles guardam o que o Gustavo decidiu e por quê.
   Nada de decidir contra a visão do produto ou contra uma decisão registrada lá; em dúvida, pergunte.
1. Leia, nesta ordem: `docs/continuidade/CONTEXTO.md` → `docs/continuidade/ESTADO.md` →
   `docs/continuidade/RECURSOS.md` → as duas últimas entradas de `docs/continuidade/DIARIO.md`.
   Se a tarefa envolve o Wise, leia também `duiaos-wise/CLAUDE.md` e `duiaos-wise/docs/continuidade/`.
   Falha relatada (sistema ou Wise) → seção "Quando o Gustavo relatar uma falha" abaixo.
2. Confira os PRs abertos (`gh api repos/gustavoduia/duiaos/pulls?state=open`) e compare com a seção 1 do
   ESTADO. Se houver PR aberto que o ESTADO não conhece, PARE e pergunte ao Gustavo.
3. Escolha a base: a `main` atualizada; se houver PR aberto que reúne trabalho ainda sem merge, parta da branch
   desse PR (a mais recente, que reúne as outras) e diga isso ao Gustavo. **Nunca** parta de uma branch antiga.
4. Rode `python3 ferramentas/conferir-recursos.py`. Se falhar na base escolhida, a base está errada.
5. Abra o PR em rascunho logo no início (é o aviso de "em andamento" para as outras contas) e anote a frente
   na seção 3 do ESTADO.

## Quando o Gustavo relatar uma falha (ADR 040)
1. `add_repo` de `gustavoduia/duiaos-diagnosticos` (privado; leia o CLAUDE.md dele) e `git pull`.
2. `python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos --horas 6 --maquina dell`; depois `--falha
   ASSINATURA` (rastro) ou `--componente duiaos-wise --eventos` (linha do tempo). Relatório antigo → peça
   🔗 DELL: `duiaos-relatorios enviar`.
3. Corrija a causa na raiz, com teste do caso. Os dados são pessoais: nunca copie trechos para este repositório
   público (commits, issues, testes) — descreva com as suas palavras.

## Antes de cada pull request
- `python3 ferramentas/conferir-recursos.py` sem problemas.
- Testes: `python3 -m unittest discover -s ia/testes -t .`, `-s agente/testes` e `-s relatorios/testes` (use
  `python3.12` se o 3.13 do ambiente não tiver `gi`); `shellcheck` nos scripts mudados.
- Programa novo do DuiaOS: `duiaos_registro.ligar("duiaos-NOME")` no início (falhas no registro do sistema) e
  eventos com `duiaos_registro.info/aviso/erro` (nunca `print` para registrar).
- Recurso novo ou mudado → linha em `docs/continuidade/RECURSOS.md` com conferência.
- Decisão nova → ADR em `docs/decisoes.md`.
- Recurso visível para o usuário → **PR irmão** no `gustavoduia/duiaos-websites` (mesmo nome de branch) com a
  página da documentação (e o site, se for de divulgar), seguindo `duiaos-websites/CLAUDE.md`. Cite o irmão na
  descrição (`gustavoduia/duiaos-websites#N`) — o workflow `documentacao-irma.yml` confere.

## Ao terminar o bloco de trabalho
- Escreva (ou atualize) o arquivo deste chat em `docs/memoria-dos-chats/` (pelo `MODELO.md`). Sem segredos,
  dados pessoais nem código do Wise (este repositório é público por enquanto).
- Atualize `docs/continuidade/ESTADO.md` (o que está na main, PRs, o que está instalado em cada máquina,
  próximos passos, perguntas) e acrescente a entrada no `docs/continuidade/DIARIO.md`.
- Envie (push) tudo para a branch do PR. Nada pode ficar só no ambiente do Claude ou só no Project do claude.ai.

## Regras do projeto (resumo; detalhes no CONTEXTO)
- Português do Brasil em tudo. Código próprio é proprietário; dependências só com licença permissiva.
- Este repositório é PÚBLICO nesta fase: nada do código do Wise aqui.
- Fluxo: branch `claude/...` + PR; merge só pelo Gustavo (squash). Medir antes de afirmar ganho.
- Comandos para o Gustavo sempre com 🍎 MAC, 🔗 DELL (sessão SSH, sem `ssh` na frente) ou 💻 DELL LOCAL.
