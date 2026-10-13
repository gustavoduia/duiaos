# REGRASFIM — como encerrar um chat do DuiaOS

Comando do Gustavo: **"Encerrar esse chat para abrir um novo. Leia as instruções em
github.com/gustavoduia/duiaos/docs/continuidade/REGRASFIM.md"**.

## 1. Criar o arquivo único de memória deste chat
- Caminho: `docs/continuidade/AAAA-MM-DD_HHhMM_assunto-curto.md` no repositório `gustavoduia/duiaos`, na `main`.
- Nome: data e hora (Brasília) da **primeira mensagem desta conversa** e 3 a 6 palavras sem acento, separadas
  por hífen. Ex.: `2026-10-12_19h51_cinco-etapas-e-wise-na-iso.md`. Hora desconhecida: `xxhxx`.
- Um arquivo só por chat. Se ele já existe (o chat continuou), atualize o mesmo arquivo.

## 2. Conteúdo: tudo o que aconteceu no chat
Releia a conversa inteira e descreva, para quem não viu nada:
- o que o Gustavo **pediu**, e o que ele disse sobre a **visão do produto** (citações curtas quando a frase
  define uma decisão; inclua o que ele corrigiu);
- o que foi **decidido** (quem decidiu, por quê, alternativas descartadas), **feito**, **removido**,
  **concluído**;
- testes e medições (onde, com números) e o que ficou instalado no Dell e no Mac;
- erros cometidos e o que mudou para não repetir.

No **final**, uma seção **"Orientação para o próximo chat"**: o que o Claude precisa ler e entender para
continuar, o que não pode esquecer e por onde começar.

## 3. Pendências bem descritas
Para cada pendência: o que está pendente, por que, o que precisa ser feito (passo a passo), em qual repositório
e arquivo, quem faz (Claude ou Gustavo, com os comandos 🍎 MAC / 🔗 DELL / 💻 DELL LOCAL) e **como será feito
no próximo chat**. Nada de "continuar X": diga exatamente qual é o próximo passo.

## 4. Resumo dos arquivos salvos em cada repositório
Liste, por repositório, os arquivos criados, mudados ou removidos neste chat (com o commit), para o próximo
chat saber como manter cada coisa no seu repositório (regras em `REGRASINI.md`, seção 6).

## 5. Atualizar e enviar
- Atualize também `ESTADO.md` (o que está na `main` de cada repositório, o que está instalado em cada máquina,
  próximos passos, perguntas em aberto) e acrescente a entrada do `DIARIO.md`.
- Só na `main`: `git pull --rebase origin main`, commit `Memória do chat AAAA-MM-DD HHhMM: assunto` e
  `git push origin main`. Nunca crie branch.
- Nunca inclua senhas, tokens, chaves, dados pessoais nem código do Wise (o `duiaos` é público por enquanto).
- Responda ao Gustavo com o nome do arquivo e um resumo de 3 linhas.

## 6. Abrir um novo chat
Escrever no final desse chat que está sendo fechado: "Para o próximo chat: “Continuar o DuiaOS. Para isso, leia o arquivo github.com/gustavoduia/duiaos/docs/continuidade/REGRASINI.md”.".
