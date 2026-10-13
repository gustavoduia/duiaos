# Prompt para gerar a memória de um chat anterior

Cole o texto abaixo (entre as linhas) em cada chat antigo do DuiaOS, um de cada vez.

---

Preciso que você registre a memória deste chat para os próximos chats do DuiaOS continuarem sem perder nada.
Num chat novo, decisões minhas se perderam (ex.: o Wise ser parte nativa do sistema) porque os arquivos de
continuidade não guardavam o histórico das conversas. Agora cada chat tem um arquivo de memória.

Faça assim:

1. Anexe o repositório `gustavoduia/duiaos` com permissão de escrita (add_repo com push) e clone-o.
2. Vá para a branch `claude/memoria-dos-chats` (`git fetch origin claude/memoria-dos-chats && git checkout
   claude/memoria-dos-chats`). Leia `docs/memoria-dos-chats/README.md` e `docs/memoria-dos-chats/MODELO.md`.
3. Releia **esta conversa inteira, do começo ao fim**, e preencha o MODELO com tudo o que foi tratado aqui.
   Capriche principalmente em:
   - o que eu pedi e o que eu disse sobre a visão do produto (o que o DuiaOS e o Wise são e devem ser), com
     citações curtas minhas quando a frase define uma decisão;
   - todas as decisões, quem decidiu, por quê, e as alternativas descartadas;
   - o que foi entregue (repositórios, PRs, commits) e o que ficou instalado no Dell e no Mac;
   - pendências, perguntas em aberto, erros e correções;
   - nomes de componentes definidos por mim.
   Escreva para quem não viu a conversa. Não invente: se não tiver certeza de algo, escreva "não confirmado".
   Nunca inclua senhas, tokens, chaves, dados pessoais nem código do Wise (o repositório é público por enquanto).
4. Nome do arquivo: `docs/memoria-dos-chats/AAAA-MM-DD_HHhMM_assunto-curto.md`, com a data e a hora (Brasília)
   da **primeira mensagem** desta conversa e 3 a 6 palavras sem acento, separadas por hífen. Hora desconhecida:
   `xxhxx`. Não mexa em nenhum outro arquivo.
5. Envie: `git add` do arquivo, commit com a mensagem `Memória do chat AAAA-MM-DD HHhMM: assunto`, depois
   `git pull --rebase origin claude/memoria-dos-chats` e `git push origin claude/memoria-dos-chats` (outros
   chats podem ter enviado antes; o rebase resolve, porque cada um cria um arquivo diferente).
6. Responda só com o nome do arquivo criado e um resumo de 3 linhas.

Se você não conseguir anexar o repositório ou enviar para o GitHub: não desista. Gere o arquivo completo
seguindo o modelo abaixo e me responda com ele inteiro dentro de um bloco de código, com o nome do arquivo
na primeira linha, para eu levar ao chat atual.

Modelo (seções obrigatórias): 1. Identificação (início/fim, conta/sessão, repositórios) · 2. O que o Gustavo
pediu · 3. Visão e regras do produto ditas neste chat · 4. Decisões (tabela: decisão, quem decidiu, por quê,
onde ficou registrada; e alternativas descartadas) · 5. O que foi entregue (tabela: repositório, PR/branch,
commit, o que faz, situação) · 6. Testes e medições · 7. Estado das máquinas ao fim do chat · 8. Pendências e
próximos passos combinados · 9. Perguntas em aberto · 10. Erros, correções e lições · 11. Forma de trabalho.

---
