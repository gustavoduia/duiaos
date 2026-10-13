# Site e documentação — Inventário de recursos entregues (não pode regredir)

Mora no `duiaos` (ADR 043) e confere os arquivos do repositório `duiaos-websites`, clonado ao lado
(`python3 ferramentas/conferir-recursos.py` no `duiaos`; nos workflows do site também). Mesmas regras do
`RECURSOS.md`: cada linha tem uma conferência `arquivo::texto que só a versão atual tem`; recurso novo ou mudado →
linha nova ou atualizada no mesmo envio.

## Site (`site/`, Worker `duiaos`)

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Página inicial: Órbita em 3D (three.js), cenas na rolagem, dia → noite → dia | `site/src/pages/index.astro`, `site/src/scripts/` | `site/src/scripts/orbita.js::caminhoDoD`, `site/src/scripts/cenas.js::noite-agora` | ADR 038 | main |
| Conversa de exemplo com o cartão "Posso fazer isto?" | `site/src/pages/index.astro` | `site/src/pages/index.astro::Posso fazer isto?` | ADR 038 | main |
| Reserva sem WebGL e "reduzir movimento" respeitado | `site/src/scripts/cenas.js`, `site/src/pages/index.astro` | `site/src/scripts/cenas.js::sem-webgl`, `site/src/pages/index.astro::prefers-reduced-motion` | ADR 038 | main |
| Downloads com a versão mais nova publicada (API + KV) | `site/src/pages/baixar.astro`, `site/worker/index.js` | `site/worker/index.js::/api/versoes` | ADR 038 | main |
| Novidades vindas das notas de cada lançamento | `site/src/pages/novidades.astro`, `site/worker/index.js` | `site/worker/index.js::Notas da versão` | ADR 039 | main |
| Relatórios de "Ajude a melhorar o DuiaOS" sem credencial no computador; lote por hora no `duiaos-diagnosticos`; resumo semanal das falhas (issue) | `site/worker/relatorios.js`, `site/migrations/0002_relatorios.sql` | `site/worker/relatorios.js::export async function enviarLote`, `site/worker/relatorios.js::export async function resumoSemanal`, `site/wrangler.jsonc::0 12 * * 1` | ADR 040 (F3) | main |
| Suporte com protocolo (D1 `duiaos-site`, limite por endereço) | `site/src/pages/suporte.astro`, `site/migrations/` | `site/worker/index.js::INSERT INTO chamados`, `site/worker/index.js::LIMITE_POR_HORA` | ADR 038 | main |

## Documentação (`documentacao/`, Worker `duiaos-docs`)

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Organização pelo Diátaxis, com busca | `documentacao/astro.config.mjs` | `documentacao/astro.config.mjs::grupo("Como fazer", "como-fazer")` | ADR 037 | main |
| Escolha pela janela da 1ª entrada, contagens de uso e envio pelo site | `documentacao/src/content/docs/entenda/ajude-a-melhorar-o-duiaos.md` | `documentacao/src/content/docs/entenda/ajude-a-melhorar-o-duiaos.md::O que entra nas contagens de uso` | ADR 040 (F2/F3) | main |
| Páginas "Ajude a melhorar o DuiaOS" e comando `duiaos-relatorios` | `documentacao/src/content/docs/entenda/`, `documentacao/src/content/docs/referencia/` | `documentacao/src/content/docs/entenda/ajude-a-melhorar-o-duiaos.md::Nada é enviado até você escolher`, `documentacao/src/content/docs/referencia/comando-duiaos-relatorios.md::novo-identificador` | ADR 040 | main |
| Links para o site escritos como `site:/...` | `documentacao/astro.config.mjs` | `documentacao/astro.config.mjs::function linksDoSite` | ADR 039 | main |
| Páginas do Wise usando o computador e da agenda | `documentacao/src/content/docs/wise/` | `documentacao/src/content/docs/wise/usar-aplicativos-pelo-wise.md::nunca faz`, `documentacao/src/content/docs/wise/conectar-a-agenda.md::CalDAV` | W14/W15 | main |
| Aviso "Na próxima versão" no que a 0.2.0 ainda não tem (Wise, IA do sistema) | `documentacao/src/content/docs/` | `documentacao/src/content/docs/wise/conversar-com-o-wise.md::Na próxima versão`, `documentacao/src/content/docs/como-fazer/escolher-o-modelo-de-ia.md::Na próxima versão` | 12/10 | main |
| Aplicativo que não existe para o DuiaOS (web e equivalentes); Wi-Fi e Bluetooth pelo Wise | `documentacao/src/content/docs/como-fazer/instalar-e-remover-aplicativos.md`, `documentacao/src/content/docs/wise/conversar-com-o-wise.md` | `documentacao/src/content/docs/como-fazer/instalar-e-remover-aplicativos.md::Quando o aplicativo não existe para o DuiaOS`, `documentacao/src/content/docs/wise/conversar-com-o-wise.md::Desliga o Wi-Fi` | W20 do Wise | main |
| Página "Quando o Wise erra" (Não ficou bom, diagnóstico) | `documentacao/src/content/docs/wise/quando-o-wise-erra.md` | `documentacao/src/content/docs/wise/quando-o-wise-erra.md::Não ficou bom` | W17/W19 do Wise | main |

## Compartilhado e processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Endereços num lugar só (trocar para duiaos.com.br aqui) | `compartilhado/enderecos.js` | `compartilhado/enderecos.js::duiaos.gustavoduia.workers.dev` | ADR 039 | main |
| Publicação automática por aplicativo | `.github/workflows/` | `.github/workflows/site.yml::wrangler deploy`, `.github/workflows/documentacao.yml::wrangler deploy` | ADR 039 | main |
