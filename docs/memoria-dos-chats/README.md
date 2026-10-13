# Memória dos chats do DuiaOS

Pedido do Gustavo em 12/10/2026, depois de um erro grave: um chat novo recomendou lançar a 0.3.0 **sem o Wise**,
contrariando a visão do produto ("o Wise é o cérebro do DuiaOS; vai embarcado e instalado com o sistema"). A
causa: os arquivos de continuidade guardavam *o que* foi feito, mas não *por que* nem *o que o Gustavo disse*.

Esta pasta é a **memória contínua do projeto**: um arquivo por chat, com tudo o que foi tratado nele. Ela vem
ANTES de qualquer outro arquivo de continuidade. Fica **só aqui, no `duiaos`** (decisão do Gustavo, 12/10): o
projeto é o DuiaOS; os outros repositórios têm finalidades específicas.

## Ao começar um chat ("Continuar o DuiaOS")
1. Anexe os repositórios e leia **todos** os arquivos desta pasta, do mais
   antigo ao mais novo (a ordem do nome é a ordem cronológica). Não pule nenhum: as decisões antigas valem até
   um chat posterior dizer o contrário.
2. Só depois leia `duiaos/CLAUDE.md` e `docs/continuidade/` de cada repositório.
3. Antes de propor algo, confira se já não foi decidido. **Em dúvida, pergunte ao Gustavo; não decida sozinho
   contra a visão do produto.** Uma "pergunta em aberto" do ESTADO pode já ter resposta num chat.

## Ao terminar um chat (ou quando o Gustavo pedir)
Crie (ou atualize, se o chat continuar) o arquivo do chat seguindo `MODELO.md`, na branch
`claude/memoria-dos-chats` (PR único; merge pelo Gustavo). Escreva para alguém que não viu a conversa.

## Nome do arquivo
`AAAA-MM-DD_HHhMM_assunto-curto.md` — data e hora (Brasília) da **primeira mensagem** do chat, e 3 a 6
palavras sem acento separadas por hífen. Ex.: `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`. Hora
desconhecida: `xxhxx`; dois chats na mesma hora: acrescente `-2`.

## O que nunca entra
Senhas, tokens, chaves, e-mails pessoais de terceiros, conteúdo dos relatórios do `duiaos-diagnosticos` e código
do Wise. Enquanto o `duiaos` for público (ADR 025), estes arquivos ficam visíveis a qualquer pessoa: descreva
decisões e o que foi feito, sem colar código nem dados pessoais.
