# Ferramentas do DuiaOS

Scripts para o dia a dia. **Rodam na janela do Terminal do Mac**, na pasta
`~/Projetos/duiaos`; os que mexem no Dell entram nele sozinhos por SSH.
Exceção: `pacotes/instalar-local.sh` roda na sessão SSH já conectada ao Dell.
Todos podem ser rodados de novo sem estragar nada.

| Script | O que faz |
| --- | --- |
| `gerar-iso.sh` | Gera ISOs de teste (fase atual: nos servidores do GitHub) |
| `baixar-isos.sh [dell]` | Baixa as ISOs do GitHub para o Mac e, com `dell`, envia ao Dell |
| `lancar-versao.sh X.Y.Z` | Cria a tag e publica o Release no repositório público |
| `runners-espera.sh pausar\|retomar\|estado` | Liga/desliga os runners próprios (Mac e Dell) |
| `trazer-isos.sh` | Copia para o Mac as ISOs geradas no runner do Dell (fase local) |
| `configurar-runners.sh mac\|dell` | Instala/refaz o runner da máquina e organiza `~/Projetos` |
| `configurar-acesso-dell.sh` | Chave somente leitura para o Dell fazer `git pull` (repositório privado) |
| `criar-repo-publico.sh` | Cria o `duiaos-fontes-abertas`, cadastra o token e sincroniza |
| `criar-chave-apt.sh` | Cria a chave que assina o repositório apt (uma vez só) |

No Dell, o teste da instalação é `sudo /usr/lib/duiaos/verificar-instalacao`.

## Fases do build (ADR 025)

| | Fase atual (desenvolvimento) | Fase final |
| --- | --- | --- |
| Repositório `duiaos` | Público | Privado |
| Onde as ISOs são geradas | Servidores do GitHub (~6 min, sem limite) | amd64 no Dell, arm64 no Mac |
| Runners próprios | **Pausados** (segurança) | Ligados |
| ISO de teste | 7 dias no GitHub → `baixar-isos.sh` | Na máquina, em `~/Projetos/duiaos-isos` |

O workflow escolhe sozinho conforme a visibilidade do repositório. Com o
repositório público, ele recusa `mac`/`dell`.

**Passar para a fase final** (quando o projeto estiver terminando):
```bash
gh repo edit gustavoduia/duiaos --visibility private --accept-visibility-change-consequences
bash ferramentas/configurar-acesso-dell.sh
bash ferramentas/runners-espera.sh retomar
```

## Pastas (iguais no Mac e no Dell)

```
~/Projetos/
  duiaos/                  repositório principal (o código)
  duiaos-fontes-abertas/   cópia do repositório público — só leitura (edite em duiaos/publico/)
  duiaos-isos/             ISOs de teste
  duiaos-runner/           runner do GitHub Actions (não mexa)
```

Mac: `/Users/gustavoduia/Projetos`. Dell: `/home/gustavo/Projetos`.

## Gerar e baixar ISOs de teste

```bash
bash ferramentas/gerar-iso.sh                 # as duas
bash ferramentas/gerar-iso.sh arm64=nao       # só a amd64
bash ferramentas/gerar-iso.sh amd64=nao       # só a arm64
bash ferramentas/baixar-isos.sh dell          # ao terminar: baixa no Mac e envia ao Dell
```

Opções: `amd64` = `github`, `dell` ou `nao`; `arm64` = `github`, `mac`, `dell`
ou `nao`. A amd64 não é gerada no Mac: o Rosetta da Apple não executa
programas no chroot do Debian sem `/proc`. A arm64 no Dell funciona (QEMU),
mas leva 1–2 h.

Acompanhar: `gh run watch NUMERO` (Ctrl+C sai sem cancelar) · situação:
`gh run list --workflow gerar-iso.yml -L 3` · cancelar: `gh run cancel NUMERO`.

## Fluxo de trabalho com o Claude (ADR 022)

1. O Claude envia o trabalho numa branch `claude/...` e abre um pull request.
2. Você revisa e aprova:
   ```bash
   gh pr list                         # ver os pull requests abertos
   gh pr diff NUMERO                  # ver as mudanças
   gh pr merge NUMERO --squash --delete-branch
   ```
3. Atualize: `git pull` no Mac e, na sessão SSH do Dell, `cd ~/Projetos/duiaos && git pull`.

O Claude nunca envia nada direto para a `main`.

## Atualizar o Dell (repositório apt, ADR 028)

O código próprio do DuiaOS chega em pacotes `.deb` (pasta `pacotes/`). Cada
envio para a `main` publica uma versão nova no canal `teste`; cada tag, no
`estavel`.

🔗 **DELL (sessão SSH)** — atualizar para a última versão da `main`:
```bash
sudo apt update && sudo apt full-upgrade
```

🔗 **DELL (sessão SSH)** — testar a branch de um pull request antes do merge:
```bash
cd ~/Projetos/duiaos && git fetch --tags && git checkout BRANCH && git pull
bash pacotes/instalar-local.sh
```

Depois do merge, volte para a `main` (`git checkout main && git pull`) e o
próximo `apt full-upgrade` traz a versão publicada. A reinstalação pela ISO
continua sendo o teste completo antes de lançar uma versão.

## Lançar uma versão

```bash
bash ferramentas/lancar-versao.sh 0.1.0
```

## Segredos e variáveis do repositório

| Nome | Tipo | Valor |
| --- | --- | --- |
| `DUIAOS_TOKEN_PUBLICO` | Segredo | Token fine-grained com Contents: Read and write só no `duiaos-fontes-abertas` (renovar anualmente) |
| `DUIAOS_APT_CHAVE` | Segredo | Chave privada que assina o repositório apt (`criar-chave-apt.sh`; cópia em `~/Projetos/duiaos-chaves`) |
| `DUIAOS_AMD64_EM` | Variável (opcional) | Força a máquina padrão da amd64 (`github` ou `dell`) |
| `DUIAOS_ARM64_EM` | Variável (opcional) | Força a máquina padrão da arm64 (`github`, `mac` ou `dell`) |
| `DUIAOS_REPO_PUBLICO` | Variável (opcional) | Outro repositório público; ausente = `gustavoduia/duiaos-fontes-abertas` |
