# Ferramentas do DuiaOS

Scripts para o Gustavo rodar no Mac (e, por SSH, no Dell). Todos podem ser
rodados de novo sem estragar nada: o que já está pronto é mantido.

| Script | Onde roda | Para quê |
| --- | --- | --- |
| `criar-repo-publico.sh` | Mac | Cria o `duiaos-fontes-abertas`, cadastra o token e faz a 1ª sincronização |
| `configurar-acesso-dell.sh` | Mac → Dell | Chave somente leitura para o Dell fazer `git pull` do repositório privado |
| `configurar-runners.sh mac` | Mac | Runner arm64 (Colima + runner como serviço) |
| `configurar-runners.sh dell` | Mac → Dell | Runner amd64 (Docker + runner como serviço) |
| `lancar-versao.sh X.Y.Z` | Mac | Cria a tag e dispara o release |
| `/usr/lib/duiaos/verificar-instalacao` | Dell | Testa a instalação e imprime OK / AVISO / FALHA |

## Pré-requisitos no Mac (uma vez)

```bash
brew install gh
gh auth login          # GitHub.com → HTTPS → Login with a web browser
```

## Fluxo de trabalho com o Claude (ADR 022)

1. O Claude envia o trabalho numa branch `claude/...` e abre um pull request.
2. Você revisa e aprova:
   ```bash
   gh pr list                         # ver os pull requests abertos
   gh pr diff NUMERO                  # ver as mudanças
   gh pr merge NUMERO --squash --delete-branch
   ```
   (Ou pelo site/app do GitHub: Pull requests → o PR → Files changed →
   Squash and merge.)
3. Atualize as máquinas: `git pull` no Mac e
   `ssh duia@duiaos 'cd ~/Projetos/duiaos && git pull'`.

O Claude nunca envia nada direto para a `main`.

## Runners próprios

- Dell: rótulo `duiaos-amd64`; Mac: rótulo `duiaos-arm64`. Status em
  Settings → Actions → Runners do repositório.
- A máquina precisa estar ligada (o Dell no DuiaOS) e acordada. Se estiver
  desligada, o job espera até 24 h.
- ISOs de teste ficam na própria máquina, em `~/duiaos-isos`.
- No Mac, para não dormir durante o build: Ajustes do Sistema → Bateria →
  Opções → ative "Impedir repouso automático no adaptador de energia quando a
  tela estiver desligada".
- Se uma máquina ficar indisponível por muito tempo, use os runners do
  GitHub (consomem minutos do plano):
  ```bash
  gh variable set DUIAOS_EXECUTOR --body github     # usar o GitHub
  gh variable delete DUIAOS_EXECUTOR                # voltar aos runners próprios
  ```
- Remover um runner: Settings → Actions → Runners → o runner → Remove, e
  apagar a pasta `~/actions-runner-duiaos` da máquina (no Dell, antes:
  `cd ~/actions-runner-duiaos && sudo ./svc.sh uninstall`; no Mac:
  `cd ~/actions-runner-duiaos && ./svc.sh uninstall`).

## Segredos e variáveis do repositório

| Nome | Tipo | Valor |
| --- | --- | --- |
| `DUIAOS_TOKEN_PUBLICO` | Segredo | Token fine-grained com Contents: Read and write só no `duiaos-fontes-abertas` (renovar anualmente) |
| `DUIAOS_EXECUTOR` | Variável (opcional) | `github` para usar os runners do GitHub; ausente = runners próprios |
| `DUIAOS_REPO_PUBLICO` | Variável (opcional) | Outro repositório público; ausente = `gustavoduia/duiaos-fontes-abertas` |
