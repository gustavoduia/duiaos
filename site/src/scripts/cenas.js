// DuiaOS — rolagem da página inicial: progresso de cada cena (--p), dia/noite
// (--noite-agora) e os passos das demonstrações. A cena 3D (orbita.js) lê o
// mesmo estado. Tudo calculado num só quadro de animação por rolagem.

const limitar = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const suave = (a, b, v) => { const t = limitar((v - a) / (b - a)); return t * t * (3 - 2 * t); };

export const estado = { cena: "abertura", p: 0, noite: 0, global: 0, cenas: {} };

export function iniciarCenas() {
  const raiz = document.documentElement;
  const cenas = [...document.querySelectorAll(".cena")];
  const falas = [...document.querySelectorAll(".fala[data-passo]")];
  const cartao = document.querySelector(".fala-cartao");
  const andamento = document.querySelector(".fala-andamento");
  const tela = document.querySelector(".tela");
  const partes = [...document.querySelectorAll(".partes li")];
  const noturnas = cenas.filter((c) => c.hasAttribute("data-noite"));
  let pedido = 0;

  function medir() {
    pedido = 0;
    const alto = innerHeight;
    let ativa = cenas[0];
    for (const cena of cenas) {
      const r = cena.getBoundingClientRect();
      const percurso = Math.max(1, cena.offsetHeight - alto);
      const p = limitar(-r.top / percurso);
      cena.style.setProperty("--p", p.toFixed(4));
      estado.cenas[cena.dataset.cena] = p;
      if (r.top <= alto * 0.5) ativa = cena;
    }
    estado.cena = ativa.dataset.cena;
    estado.p = estado.cenas[estado.cena];
    estado.global = limitar(scrollY / Math.max(1, document.body.scrollHeight - alto));

    // Noite: entra quando a cena do Wise sobe e sai no fim da privacidade
    if (noturnas.length) {
      const primeira = noturnas[0].getBoundingClientRect();
      const ultima = noturnas[noturnas.length - 1].getBoundingClientRect();
      const entrar = suave(alto * 0.9, alto * 0.1, primeira.top);
      const sair = 1 - suave(alto * 0.85, alto * 0.05, ultima.bottom);
      estado.noite = limitar(Math.min(entrar, sair));
      raiz.style.setProperty("--noite-agora", estado.noite.toFixed(3));
      raiz.toggleAttribute("data-noite", estado.noite > 0.5);
    }

    // Conversa com o Wise: cada fala aparece no seu ponto da rolagem
    const pw = estado.cenas.wise ?? 0;
    for (const fala of falas) fala.classList.toggle("visivel", pw >= Number(fala.dataset.passo));
    cartao?.classList.toggle("aprovado", pw >= 0.48);
    andamento?.style.setProperty("--andamento", limitar((pw - 0.54) / 0.14).toFixed(3));

    // Interface: uma parte por vez, na ordem da lista
    const pi = estado.cenas.interface ?? 0;
    const parte = Math.min(3, Math.floor(pi * 4.2));
    tela?.setAttribute("data-parte", String(parte));
    partes.forEach((li, i) => li.classList.toggle("ativa", i === parte));
  }

  const agendar = () => { if (!pedido) pedido = requestAnimationFrame(medir); };
  addEventListener("scroll", agendar, { passive: true });
  addEventListener("resize", agendar);
  medir();

  // A cena 3D só carrega se o navegador tiver WebGL (senão fica o símbolo estático)
  const canvas = document.getElementById("orbita");
  if (canvas && temWebGL()) {
    import("./orbita.js").then(({ iniciarOrbita }) => iniciarOrbita(canvas, estado)).catch(() => {
      raiz.classList.add("sem-webgl");
    });
  } else {
    raiz.classList.add("sem-webgl");
  }
}

function temWebGL() {
  try {
    const c = document.createElement("canvas");
    return Boolean(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}
