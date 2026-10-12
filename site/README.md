# Site e documentação do DuiaOS

Um só projeto (Astro + Starlight, MIT) gera o site inteiro como arquivos estáticos; o Cloudflare Workers serve
os arquivos e responde às rotas `/api/*` (ADRs 037 e 038).

| Endereço | O que é | Onde mora |
| --- | --- | --- |
| `/` | Apresentação (cena 3D da Órbita em three.js, rolagem com cenas) | `src/pages/index.astro`, `src/scripts/cenas.js`, `src/scripts/orbita.js` |
| `/baixar/` | Downloads (versão mais nova pelo `/api/versoes`) | `src/pages/baixar.astro`, `src/dados/versoes.json` |
| `/novidades/` | Notas de cada versão e o que vem por aí | `src/pages/novidades.astro`, `src/dados/versoes.json` |
| `/suporte/` | Caminhos de ajuda e formulário (D1) | `src/pages/suporte.astro` |
| `/documentacao/` | Documentação para usuários, com busca | `src/content/docs/documentacao/` |
| `/api/versoes`, `/api/suporte`, `/api/saude` | API | `worker/index.js` |

Recursos do Cloudflare (conta do Gustavo): Worker `duiaos-site`, D1 `duiaos-site` (tabela `chamados`,
`migrations/`), KV `duiaos-site-cache` (versões e limite do formulário). IDs em `wrangler.jsonc`.

## Rodar e publicar

🍎 **MAC** — ver no navegador (http://localhost:4321):
```
cd ~/Projetos/duiaos/site && npm install && npm run dev
```

🍎 **MAC** — primeira publicação (abre o navegador para entrar na conta Cloudflare uma vez):
```
cd ~/Projetos/duiaos/site && npx wrangler login && npm run deploy
```

Depois disso, cada merge na `main` que mexe em `site/` publica sozinho pelo workflow `site.yml`, se os
segredos `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` estiverem no repositório.

## Como escrever a documentação (vale para qualquer pessoa ou conta do Claude)

**Toda mudança visível para o usuário leva a página da documentação no mesmo PR.**

A organização segue o **Diátaxis** (o mesmo modelo da documentação do Ubuntu): cada página tem um só tipo.

| Pasta | Tipo | Para quem / pergunta que responde |
| --- | --- | --- |
| `comecar/` | Tutorial | "Sou novo: me leve do começo ao fim." Passos em ordem, com um resultado no final. |
| `como-fazer/` | Guia de tarefa | "Quero fazer X agora." Curto, só os passos. |
| `wise/` | Guias do Wise | Tarefas e conversas com o assistente. |
| `problemas/` | Solução de problemas | "Aconteceu Y." Sintoma → causa → solução. |
| `referencia/` | Referência | "Qual é o atalho / comando / requisito?" Tabelas, sem narrativa. |
| `entenda/` | Explicação | "Por que é assim?" Conceitos, privacidade, decisões. |

Estilo:
- Português do Brasil, frases curtas, voz ativa, "você". Fale do que a pessoa vê, não de como o sistema é feito
  por dentro ("Ilha de Aplicativos", nunca "dock" ou "layer-shell").
- Use os nomes oficiais: Barra de Recursos, Ilha de Aplicativos, Central de Aplicativos, Tela de Entrada, Tela de
  Bloqueio, Menu de Energia, Central de IA, Wise. Botões entre **negrito** com o texto exato da tela.
- Teclas com `<kbd>`: <kbd>Super</kbd> + <kbd>W</kbd>. Caminhos de menu com ›.
- Comandos de terminal só quando não houver caminho pela interface, sempre num bloco próprio.
- Cada página começa com `title` e `description` (aparecem na busca e no Wise).
- Avisos: `:::tip`, `:::note`, `:::caution`, `:::danger`.

Conferência antes do PR: `npm run build` (falha com link quebrado de navegação ou erro de conteúdo).

## Próximos passos previstos (ADR 037)
- Ajuda dentro do sistema: as mesmas páginas empacotadas (`duiaos-ajuda`) para abrir sem internet, e o Wise
  consultando a documentação para responder "como faço…".
- Páginas `man` para os comandos (`duiaos-ia`), geradas a partir da referência.
- Outros idiomas (Starlight já suporta; tradução por arquivos `.po` quando houver tradutores).
- "Esta página ajudou?" ligado ao D1.
