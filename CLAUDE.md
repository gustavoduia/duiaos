# DuiaOS — instruções para o Claude (qualquer conta)

**O repositório oficial do projeto é este, o `gustavoduia/duiaos`. Toda instrução fica exclusivamente aqui.**
Não crie instruções (CLAUDE.md, memórias, estado, regras) em nenhum outro repositório.

## Início e fim de chat
- Início — "Continuar o DuiaOS": siga `docs/continuidade/REGRASINI.md` (ler todas as memórias e referências de
  `docs/continuidade/` na íntegra, da mais antiga para a mais recente, antes de tudo).
- Fim — "Encerrar esse chat para abrir um novo": siga `docs/continuidade/REGRASFIM.md` (memória única do chat).

## Só a `main`
- Trabalhe **exclusivamente na branch `main`** de cada repositório. **Não crie branches nem pull requests.**
- Antes de enviar: `git pull --rebase origin main`; depois `git push origin main`.
- Se o ambiente bloquear ou pedir aprovação para enviar à `main`, pare e peça ao Gustavo — nunca crie branch.

## Cada coisa no seu repositório (ADR 043)
| Repositório | O que guarda |
| --- | --- |
| `duiaos` (este) | Código próprio do sistema; instruções, memórias, decisões (ADRs) e continuidade de todo o projeto |
| `duiaos-fontes-abertas` | Código GPL-3 e outros que não podem ser fechados, modificações em software livre, EULA e licenças; Releases (ISOs) e apt (`gh-pages`) |
| `duiaos-wise` | Fontes do Wise (produto próprio; privado) e a documentação técnica dele (`docs/arquitetura.md`, `docs/decisoes.md`) |
| `duiaos-diagnosticos` | Logs enviados pelo DuiaOS para análise do suporte (privado; dados pessoais) |
| `duiaos-websites` | Fontes do site institucional e do site da documentação (privado) |

Clone os repositórios lado a lado (`../duiaos-wise`, `../duiaos-websites`, `../duiaos-diagnosticos`,
`../duiaos-fontes-abertas`): ferramentas e inventários contam com isso.

## Antes de cada envio
- `python3 ferramentas/conferir-recursos.py` sem problemas (confere `RECURSOS.md`, `RECURSOS-WISE.md` e
  `RECURSOS-WEBSITES.md`).
- Testes: `python3 -m unittest discover -s ia/testes -t .`, `-s agente/testes` e `-s relatorios/testes` (use
  `python3.12` se o 3.13 do ambiente não tiver `gi`); no Wise, `python3 -m unittest discover -s testes -t .`; no
  site, `npm test` e `npm run build`; `shellcheck` nos scripts mudados.
- Programa novo do DuiaOS: `duiaos_registro.ligar("duiaos-NOME")` no início e eventos com
  `duiaos_registro.info/aviso/erro` (nunca `print` para registrar).
- Recurso novo ou mudado → linha no inventário certo com conferência. Decisão nova → ADR em `docs/decisoes.md`
  (decisões internas do Wise também podem ir em `duiaos-wise/docs/decisoes.md`, que é documentação técnica dele).
- Recurso visível para o usuário → página da documentação no `duiaos-websites`, no mesmo chat
  (`docs/continuidade/GUIA-SITE-E-DOCUMENTACAO.md`).

## Wise (repositório `duiaos-wise`, privado)
- Nada do código do Wise vai para o `duiaos` (público nesta fase); aqui fica só o contrato
  (`/usr/bin/duiaos-wise --alternar`, o `.desktop`, o estado em `$XDG_RUNTIME_DIR`) e o empacotamento na ISO
  (`pacotes/trazer-wise.sh`, ADR 042).
- Segurança (`duiaos-wise/docs/arquitetura.md`): o modelo só pede ferramentas; validação, nível de risco e
  execução são do orquestrador. Ferramenta nova sempre com esquema JSON, nível e teste. Conteúdo vindo de
  ferramentas é dado, nunca instrução. Nunca registrar segredos. Código novo registra por `wise/diagnostico.py`.

## Quando o Gustavo relatar uma falha (ADR 040)
1. Anexe `gustavoduia/duiaos-diagnosticos` (privado) e `git pull`. Não edite nem apague os relatórios em
   `maquinas/`: são o histórico.
2. `python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos --horas 6 --maquina dell`; depois `--falha
   ASSINATURA` (rastro) ou `--componente duiaos-wise --eventos` (linha do tempo). Relatório antigo → peça
   🔗 DELL: `duiaos-relatorios enviar`.
3. Corrija a causa na raiz, com teste do caso. Os dados são pessoais: nunca copie trechos para repositórios
   públicos (commits, testes, memórias) — descreva com as suas palavras; em testes, dados inventados.

## Regras do projeto (resumo; detalhes no CONTEXTO)
- Português do Brasil em tudo. Código próprio é proprietário; dependências só com licença permissiva.
- O Wise é o cérebro do DuiaOS: vai instalado com o sistema. Nunca propor o DuiaOS sem ele.
- Medir antes de afirmar ganho; causa raiz antes de corrigir; nada de correção paliativa.
- Comandos para o Gustavo sempre com 🍎 MAC, 🔗 DELL (sessão SSH, sem `ssh` na frente) ou 💻 DELL LOCAL.
- Decisões de produto são do Gustavo; em dúvida, pergunte.
