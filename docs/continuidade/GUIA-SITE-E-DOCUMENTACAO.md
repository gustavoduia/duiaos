# Guia do site e da documentação (repositório `duiaos-websites`)

Veio do `CLAUDE.md` do `duiaos-websites` (13/10: toda instrução fica no `duiaos`, ADR 043).

## Os dois aplicativos (ADR 039)
| Pasta | Aplicativo | Worker | Endereço (até haver domínio) | Com domínio |
| --- | --- | --- | --- | --- |
| `site/` | Site: apresentação, downloads, novidades, suporte, relatórios (API em `site/worker/`) | `duiaos` | https://duiaos.gustavoduia.workers.dev | duiaos.com.br |
| `documentacao/` | Documentação para usuários (Starlight) | `duiaos-docs` | https://duiaos-docs.gustavoduia.workers.dev | docs.duiaos.com.br |
| `compartilhado/` | Endereços, cores e fontes usados pelos dois | — | — | — |

Publicação automática a cada envio para a `main` (workflows `site.yml` e `documentacao.yml`).

## O site acompanha o sistema
- Mudança no `duiaos` ou no `duiaos-wise` que a pessoa percebe (tela, botão, comando, atalho, recurso do Wise)
  → atualize a página da documentação **no mesmo chat**, na `main` do `duiaos-websites`.
- Recurso que só chega na próxima versão: a página leva o aviso `:::note[Na próxima versão]`, retirado quando a
  versão sai.
- Versões, downloads e novidades vêm sozinhos dos lançamentos do `duiaos-fontes-abertas` (`/api/versoes`; as
  linhas "- ..." das notas do lançamento — `duiaos/notas-de-versao/X.Y.Z.md` — viram a lista de novidades).

## Como escrever a documentação (Diátaxis, o mesmo modelo do Ubuntu)
| Pasta em `documentacao/src/content/docs/` | Tipo | Pergunta que responde |
| --- | --- | --- |
| `comecar/` | Tutorial | "Sou novo: me leve do começo ao fim." |
| `como-fazer/` | Guia de tarefa | "Quero fazer X agora." |
| `wise/` | Guias do Wise | Tarefas e conversas com o assistente. |
| `problemas/` | Solução de problemas | "Aconteceu Y." Sintoma → causa → solução. |
| `referencia/` | Referência | "Qual é o atalho / comando / requisito?" |
| `entenda/` | Explicação | "Por que é assim?" |

- Português do Brasil, frases curtas, voz ativa, "você". Nomes oficiais (Barra de Recursos, Ilha de Aplicativos,
  Central de Aplicativos, Tela de Entrada, Tela de Bloqueio, Menu de Energia, Central de IA, Wise).
- Botões em **negrito** com o texto exato da tela; teclas com `<kbd>`; menus com ›.
- Links entre páginas: `/como-fazer/...`. Links para o site: `site:/baixar/`. Nunca o endereço completo no texto.
- Cada página com `title` e `description`.

## Antes de enviar
- `npm ci && npm run build` (os dois aplicativos) e `npm test` (Worker).
- `python3 ferramentas/conferir-recursos.py` no `duiaos` (confere `RECURSOS-WEBSITES.md`); recurso novo → linha lá.
- Ver no navegador: `npm run dev:site` ou `npm run dev:documentacao`.

## Regras
- Dependências só com licença permissiva (MIT, BSD, Apache-2.0); three.js sim, GSAP não.
- Segredos só nos segredos do GitHub do `duiaos-websites`: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`,
  `GITHUB_DIAGNOSTICOS` (token só do `duiaos-diagnosticos`, passado ao Worker na publicação).
- Recursos do Cloudflare (conta do Gustavo): D1 `duiaos-site`, KV `duiaos-site-cache` (IDs em `site/wrangler.jsonc`).
