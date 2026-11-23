# Segredo DUIAOS_TOKEN_APPS — acesso do build ao Ora e ao Mail Box (ADR 073 e 074)

O `duiaos` gera as ISOs e as atualizações nos servidores do GitHub. O Ora e o Mail Box ficam em repositórios
**privados** (`gustavoduia/duiaos-ora` e `gustavoduia/duiaos-mailbox`), então o build precisa de um token que só
**lê** esses dois repositórios. Sem ele, o passo "Gerar os pacotes" falha com `403` e **nenhuma atualização é
publicada** (o `duiaos-desktop` depende do Ora e do Mail Box: publicar sem eles travaria a atualização dos
computadores).

O token nunca vai para a ISO, para os pacotes nem para os registros: só o passo que baixa os dois repositórios o
recebe (`pacotes/trazer-apps.sh`).

## 1. Criar o token (no navegador, logado como gustavoduia)
1. Abra https://github.com/settings/personal-access-tokens/new
   (ou: foto › Settings › Developer settings › Personal access tokens › **Fine-grained tokens** › Generate new token).
2. **Token name**: `DuiaOS build — Ora e Mail Box`.
3. **Resource owner**: `gustavoduia`.
4. **Expiration**: 1 ano (anote na agenda para renovar; ao vencer, os builds voltam a falhar com 403).
5. **Repository access**: *Only select repositories* › escolha `gustavoduia/duiaos-ora` e `gustavoduia/duiaos-mailbox`.
6. **Permissions** › Repository permissions › **Contents: Read-only** (o *Metadata: Read-only* entra sozinho).
   Nada mais.
7. **Generate token** e copie o valor (`github_pat_...`). Ele só aparece uma vez.

## 2. Guardar como segredo do repositório duiaos
Pelo site: https://github.com/gustavoduia/duiaos/settings/secrets/actions › **New repository secret** ›
Name `DUIAOS_TOKEN_APPS` › Secret: cole o token › **Add secret**.

Ou pelo terminal (cola o token quando ele pedir, sem aparecer na tela):

🍎 MAC
```
gh secret set DUIAOS_TOKEN_APPS -R gustavoduia/duiaos
```

## 3. Publicar de novo
🍎 MAC
```
gh workflow run pacotes.yml -R gustavoduia/duiaos --ref main
gh run watch -R gustavoduia/duiaos
```
Pelo site: Actions › **Pacotes e repositório apt** › Run workflow › main. Quando terminar verde, todo computador
DuiaOS (inclusive a VM com a 0.3.1) recebe a atualização acumulada na próxima busca.

## Alternativa
Em vez de um token novo, dá para editar o token do Wise (o do segredo `DUIAOS_TOKEN_WISE`) e acrescentar os dois
repositórios em *Repository access*: sem o `DUIAOS_TOKEN_APPS`, o build usa o do Wise. O token separado é melhor:
cada um lê só o que precisa e vence sem derrubar o outro.
