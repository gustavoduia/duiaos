# Ferramentas do DuiaOS

Scripts para o dia a dia. **Todos rodam na janela do Terminal do Mac**, na
pasta `~/Projetos/duiaos`. Os que mexem no Dell entram nele sozinhos por SSH.
Todos podem ser rodados de novo sem estragar nada.

| Script | O que faz |
| --- | --- |
| `gerar-iso.sh` | Gera ISOs de teste escolhendo a máquina de cada arquitetura |
| `trazer-isos.sh` | Copia as ISOs geradas no Dell para o Mac |
| `lancar-versao.sh X.Y.Z` | Cria a tag e publica o Release no repositório público |
| `configurar-runners.sh mac\|dell` | Prepara a máquina para gerar ISOs e organiza `~/Projetos` |
| `configurar-acesso-dell.sh` | Chave somente leitura para o Dell fazer `git pull` do repositório privado |
| `criar-repo-publico.sh` | Cria o `duiaos-fontes-abertas`, cadastra o token e sincroniza |

No Dell, o teste da instalação é `sudo /usr/lib/duiaos/verificar-instalacao`
(ou, antes de reinstalar com uma ISO nova,
`sudo bash ~/Projetos/duiaos/build/config/includes.chroot_after_packages/usr/lib/duiaos/verificar-instalacao`).

## Pastas (iguais no Mac e no Dell)

```
~/Projetos/
  duiaos/                  repositório privado (o código)
  duiaos-fontes-abertas/   cópia do repositório público — só leitura (edite em duiaos/publico/)
  duiaos-isos/             ISOs de teste geradas nesta máquina (últimas 3 por arquitetura)
  duiaos-runner/           runner do GitHub Actions (não mexa)
```

Mac: `/Users/gustavoduia/Projetos`. Dell: `/home/gustavo/Projetos`.
Fora de `~/Projetos` ficam só os dados internos do Colima (`~/.colima`, no Mac).

## Gerar ISOs de teste

```bash
bash ferramentas/gerar-iso.sh                         # padrão: amd64 no Dell, arm64 no Mac
bash ferramentas/gerar-iso.sh amd64=mac arm64=mac     # as duas no Mac
bash ferramentas/gerar-iso.sh amd64=dell arm64=dell   # as duas no Dell
bash ferramentas/gerar-iso.sh amd64=mac arm64=nao     # só a amd64, no Mac
```

Opções por arquitetura: `mac`, `dell`, `github` (servidores do GitHub; gasta
minutos e não guarda a ISO de teste) ou `nao`.

| Máquina | amd64 | arm64 |
| --- | --- | --- |
| Mac M4 | Emulada pelo Rosetta (razoável) | Nativa (~6 min) |
| Dell i5 | Nativa (~20–40 min) | Emulada pelo QEMU (lenta, 1–2 h) |

Na mesma máquina, as duas ISOs saem uma depois da outra.

Acompanhar: `gh run watch` (Ctrl+C sai sem cancelar) · situação:
`gh run list --workflow gerar-iso.yml -L 3` · cancelar: `gh run cancel NUMERO`.

A máquina escolhida precisa estar ligada e acordada (o Dell no DuiaOS). Se
estiver desligada, o job espera na fila e começa quando ela ligar. No Mac:
Ajustes do Sistema → Bateria → Opções → ative "Impedir repouso automático no
adaptador de energia quando a tela estiver desligada".

Máquinas padrão (usadas no push na `main` e nas tags):
```bash
gh variable set DUIAOS_AMD64_EM --body mac     # muda o padrão da amd64 (dell, mac ou github)
gh variable set DUIAOS_ARM64_EM --body dell    # muda o padrão da arm64
gh variable delete DUIAOS_AMD64_EM             # volta ao padrão (amd64 no Dell)
```

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

## Lançar uma versão

```bash
bash ferramentas/lancar-versao.sh 0.1.0
```
Gera as duas ISOs nas máquinas padrão e publica no Release do repositório público.

## Segredos e variáveis do repositório

| Nome | Tipo | Valor |
| --- | --- | --- |
| `DUIAOS_TOKEN_PUBLICO` | Segredo | Token fine-grained com Contents: Read and write só no `duiaos-fontes-abertas` (renovar anualmente) |
| `DUIAOS_AMD64_EM` | Variável (opcional) | Máquina padrão da amd64: `dell` (padrão), `mac` ou `github` |
| `DUIAOS_ARM64_EM` | Variável (opcional) | Máquina padrão da arm64: `mac` (padrão), `dell` ou `github` |
| `DUIAOS_REPO_PUBLICO` | Variável (opcional) | Outro repositório público; ausente = `gustavoduia/duiaos-fontes-abertas` |

## Remover um runner

Settings → Actions → Runners → o runner → Remove. Depois, na máquina:
Dell `cd ~/Projetos/duiaos-runner && sudo ./svc.sh uninstall`;
Mac `cd ~/Projetos/duiaos-runner && ./svc.sh uninstall`; e apague a pasta.
