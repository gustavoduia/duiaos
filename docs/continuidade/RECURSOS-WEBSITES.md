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
| Páginas da interface completa (ADR 044): área de trabalho, Central de Controle, Explorador de Arquivos, Configurações, atalhos | `documentacao/src/content/docs/comecar/`, `documentacao/src/content/docs/como-fazer/` | `documentacao/src/content/docs/como-fazer/usar-a-central-de-controle.md::Modo avião`, `documentacao/src/content/docs/como-fazer/usar-o-explorador-de-arquivos.md::Restaurar`, `documentacao/src/content/docs/como-fazer/usar-as-configuracoes.md::Aplicativos padrão`, `documentacao/src/content/docs/comecar/conhecer-a-area-de-trabalho.md::Menu do DuiaOS` | ADR 044 | main |
| Páginas da 2ª rodada da interface (ADR 045): aparência (modo escuro, papel de parede e vídeo, Tela de Descanso, foto), notificações, atualizações pelas Configurações, botão direito | `documentacao/src/content/docs/como-fazer/` | `documentacao/src/content/docs/como-fazer/personalizar-a-aparencia.md::Modo escuro`, `documentacao/src/content/docs/como-fazer/usar-as-notificacoes.md::Não perturbe`, `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md::Procurar atualizações` | ADR 045 | main |
| Códigos das atualizações (DUIA-AAAA-NNNN) e Central de Atualizações com detalhes | `documentacao/src/content/docs/entenda/atualizacoes.md`, `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md` | `documentacao/src/content/docs/entenda/atualizacoes.md::DUIA-AAAA-NNNN`, `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md::O que mudou` | ADR 046 | main |
| Andamento, travamentos e registros das atualizações | `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md` | `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md::Está demorando?` | ADR 047 | main |
| Página da Duia App Store (encontrar, instalar, atualizar, de onde vêm os aplicativos) e ligações em Instalar aplicativos e Atualizar o sistema (ADR 049) | `documentacao/src/content/docs/como-fazer/usar-a-duia-app-store.md` | `documentacao/src/content/docs/como-fazer/usar-a-duia-app-store.md::Também disponível pelo Debian`, `documentacao/src/content/docs/como-fazer/instalar-e-remover-aplicativos.md::usar-a-duia-app-store`, `documentacao/src/content/docs/como-fazer/atualizar-o-sistema.md::Abrir a loja` | ADR 049 | main |
| Página Personalizar a Ilha de Aplicativos (opções, manter/tirar/reordenar, minimizar com efeito), Super+M nos atalhos (ADR 050) | `documentacao/src/content/docs/como-fazer/personalizar-a-ilha-de-aplicativos.md` | `documentacao/src/content/docs/como-fazer/personalizar-a-ilha-de-aplicativos.md::Tamanho da ampliação`, `documentacao/src/content/docs/referencia/atalhos-de-teclado.md::Minimiza a janela da frente`, `documentacao/src/content/docs/como-fazer/abrir-e-fixar-aplicativos.md::personalizar-a-ilha-de-aplicativos` | ADR 050 | main |
| Página Mudar o papel de parede (telas, ajuste, troca automática, Bloqueio e Entrada); Barra sem o botão Wise (ADR 051) | `documentacao/src/content/docs/como-fazer/mudar-o-papel-de-parede.md` | `documentacao/src/content/docs/como-fazer/mudar-o-papel-de-parede.md::Uma imagem por todas`, `documentacao/src/content/docs/como-fazer/personalizar-a-aparencia.md::mudar-o-papel-de-parede` | ADR 051 | main |
| Estilo padrão ou futurista em Personalizar a aparência (ADR 052) | `documentacao/src/content/docs/como-fazer/personalizar-a-aparencia.md` | `documentacao/src/content/docs/como-fazer/personalizar-a-aparencia.md::Estilo: padrão ou futurista` | ADR 052 | main |

## Compartilhado e processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Endereços num lugar só (trocar para duiaos.com.br aqui) | `compartilhado/enderecos.js` | `compartilhado/enderecos.js::duiaos.gustavoduia.workers.dev` | ADR 039 | main |
| Publicação automática por aplicativo | `.github/workflows/` | `.github/workflows/site.yml::wrangler deploy`, `.github/workflows/documentacao.yml::wrangler deploy` | ADR 039 | main |
