// DuiaOS — site: apresentação, documentação (Starlight), downloads, novidades e suporte.
// Gerado como site estático (dist/) e servido pelo Cloudflare Workers (wrangler.jsonc):
// as rotas /api/* passam pelo worker/index.js (D1 e KV); o resto são arquivos.
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://duiaos.com.br",
  trailingSlash: "ignore",
  integrations: [
    starlight({
      title: "Documentação do DuiaOS",
      description: "Aprenda a usar e configurar o DuiaOS e o Wise.",
      defaultLocale: "root",
      locales: { root: { label: "Português (Brasil)", lang: "pt-BR" } },
      logo: { src: "./public/simbolo.svg", alt: "DuiaOS" },
      favicon: "/favicon.svg",
      customCss: [
        "@fontsource-variable/manrope",
        "@fontsource-variable/inter",
        "./src/styles/documentacao.css",
      ],
      lastUpdated: true,
      disable404Route: true,
      sidebar: [
        { label: "Começar", items: [{ autogenerate: { directory: "documentacao/comecar" } }] },
        { label: "Como fazer", items: [{ autogenerate: { directory: "documentacao/como-fazer" } }] },
        { label: "Wise", items: [{ autogenerate: { directory: "documentacao/wise" } }] },
        { label: "Solução de problemas", items: [{ autogenerate: { directory: "documentacao/problemas" } }] },
        { label: "Referência", items: [{ autogenerate: { directory: "documentacao/referencia" } }] },
        { label: "Entenda", items: [{ autogenerate: { directory: "documentacao/entenda" } }] },
      ],
    }),
  ],
});
