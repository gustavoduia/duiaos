// DuiaOS — Worker do site (Cloudflare Workers).
// Só as rotas /api/* passam por aqui (wrangler.jsonc: assets.run_worker_first);
// o resto é o site estático em dist/ (env.ASSETS).
//
//   GET  /api/versoes   versões publicadas (Releases do repositório público), guardadas no KV por 30 min
//   POST /api/suporte   pedido de suporte → D1 (tabela chamados), devolve o protocolo
//   GET  /api/saude     confere D1 e KV (para o deploy)
//
// Bindings: DB (D1 duiaos-site), CACHE (KV duiaos-site-cache), ASSETS.

const REPOSITORIO = "gustavoduia/duiaos-fontes-abertas";
const VALIDADE_VERSOES = 1800;           // segundos
const LIMITE_POR_HORA = 5;               // pedidos de suporte por endereço

const json = (dados, status = 200, extra = {}) =>
  new Response(JSON.stringify(dados), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });

export default {
  async fetch(pedido, env) {
    const url = new URL(pedido.url);
    try {
      if (url.pathname === "/api/versoes" && pedido.method === "GET") return await versoes(env);
      if (url.pathname === "/api/suporte" && pedido.method === "POST") return await suporte(pedido, env);
      if (url.pathname === "/api/saude") return await saude(env);
      if (url.pathname.startsWith("/api/")) return json({ erro: "Endereço não encontrado." }, 404);
    } catch (erro) {
      console.error("api", url.pathname, erro?.stack || erro);
      return json({ erro: "Falha no servidor." }, 500);
    }
    return env.ASSETS.fetch(pedido);
  },
};

// ------------------------------------------------------------------ versões
async function versoes(env) {
  const guardado = await env.CACHE.get("versoes", "json");
  if (guardado) return json(guardado, 200, { "cache-control": "public, max-age=300" });
  const resposta = await fetch(`https://api.github.com/repos/${REPOSITORIO}/releases?per_page=10`, {
    headers: { "user-agent": "duiaos-site", accept: "application/vnd.github+json" },
  });
  if (!resposta.ok) return json({ erro: "Não consegui consultar as versões agora." }, 502);
  const lista = await resposta.json();
  const dados = { versoes: lista.filter((r) => !r.draft).map(converterVersao).filter((v) => v.isos.length) };
  await env.CACHE.put("versoes", JSON.stringify(dados), { expirationTtl: VALIDADE_VERSOES });
  return json(dados, 200, { "cache-control": "public, max-age=300" });
}

function converterVersao(r) {
  const rotulos = { amd64: "Intel e AMD (64 bits)", arm64: "ARM (64 bits)" };
  const isos = (r.assets || [])
    .filter((a) => /\.iso$/i.test(a.name))
    .map((a) => {
      const arquitetura = /arm64|aarch64/i.test(a.name) ? "arm64" : "amd64";
      return { arquitetura, rotulo: rotulos[arquitetura], nome: a.name, tamanho: a.size, url: a.browser_download_url };
    })
    .sort((a, b) => (a.arquitetura === "amd64" ? -1 : 1) - (b.arquitetura === "amd64" ? -1 : 1));
  return {
    versao: String(r.tag_name || "").replace(/^v/, ""),
    data: r.published_at,
    canal: r.prerelease ? "pré-lançamento" : "estável",
    pagina: r.html_url,
    isos,
  };
}

// ------------------------------------------------------------------ suporte
const ASSUNTOS = new Set(["Instalação", "Wise e IA", "Aplicativos e atualizações", "Hardware (Wi-Fi, som, vídeo)", "Outro"]);

async function suporte(pedido, env) {
  let dados;
  try {
    dados = await pedido.json();
  } catch {
    return json({ erro: "Pedido em formato inválido." }, 400);
  }
  if (dados.site) return json({ protocolo: "0" });           // armadilha para robôs: finge que deu certo
  const nome = texto(dados.nome, 120), email = texto(dados.email, 200), mensagem = texto(dados.mensagem, 8000, false);
  const assunto = ASSUNTOS.has(dados.assunto) ? dados.assunto : "Outro";
  if (!nome || !mensagem || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ erro: "Preencha nome, e-mail válido e o que aconteceu." }, 400);
  }
  // Limite por endereço (guardado só como resumo, nunca o IP)
  const ip = pedido.headers.get("cf-connecting-ip") || "desconhecido";
  const chave = "limite:" + (await resumo(ip + new Date().toISOString().slice(0, 13)));
  const contagem = Number((await env.CACHE.get(chave)) || 0);
  if (contagem >= LIMITE_POR_HORA) return json({ erro: "Muitos pedidos em pouco tempo." }, 429);
  await env.CACHE.put(chave, String(contagem + 1), { expirationTtl: 3600 });

  const protocolo = new Date().toISOString().slice(0, 10).replaceAll("-", "") + "-" +
    crypto.getRandomValues(new Uint32Array(1))[0].toString(36).slice(0, 6).toUpperCase();
  await env.DB.prepare(
    "INSERT INTO chamados (protocolo, criado_em, nome, email, assunto, mensagem, situacao) VALUES (?, ?, ?, ?, ?, ?, 'novo')",
  ).bind(protocolo, new Date().toISOString(), nome, email, assunto, mensagem).run();
  return json({ protocolo }, 201);
}

function texto(valor, limite, umaLinha = true) {
  const t = String(valor ?? "").trim().slice(0, limite);
  return umaLinha ? t.replace(/\s+/g, " ") : t;
}

async function resumo(valor) {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(valor));
  return [...new Uint8Array(bytes)].slice(0, 12).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function saude(env) {
  const d1 = await env.DB.prepare("SELECT COUNT(*) AS n FROM chamados").first().then(() => true).catch(() => false);
  const kv = await env.CACHE.get("versoes").then(() => true).catch(() => false);
  return json({ d1, kv }, d1 && kv ? 200 : 503);
}
