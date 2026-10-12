// DuiaOS — a Órbita em 3D (three.js, MIT), atrás da página inicial.
//
// O símbolo do DuiaOS é um "D" cujo arco é parte de um círculo, e um ponto que
// está nesse mesmo círculo. Aqui o D vira um tubo de vidro azul e o ponto ganha
// vida: no topo da página ele está exatamente no lugar do símbolo; ao rolar,
// solta-se e entra em órbita. À noite (Wise e privacidade) o ponto brilha em
// ciano, como os olhos do Wise, surgem estrelas e, na privacidade, elas se
// recolhem para perto dele ("a inteligência mora no seu computador").
//
// Cuidados: no máximo 2x de densidade de pixels, sem pós-processamento, pausa com
// a aba escondida, para de desenhar quando a cena some e respeita "reduzir
// movimento" (sem animação por tempo, só pela rolagem).
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

const limitar = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const suave = (a, b, v) => { const t = limitar((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const misturar = (a, b, t) => a + (b - a) * t;

// Coordenadas do símbolo (viewBox 12 8 104 104), centro (64, 60), raio do arco 40 → 1
const P = (x, y) => new THREE.Vector3((x - 64) / 40, -(y - 60) / 40, 0);
const CENTRO_ARCO = new THREE.Vector3(-0.15, 0, 0);
const ANGULO_PONTO = Math.atan2(P(80.94, 92.77).y, P(80.94, 92.77).x - CENTRO_ARCO.x);

function caminhoDoD() {
  // Contorno do D com cantos arredondados (como stroke-linejoin: round) e o arco
  const pontos = [];
  const reta = (a, b, n) => { for (let i = 0; i < n; i++) pontos.push(a.clone().lerp(b, i / n)); };
  const canto = (centro, r, de, ate, n) => {
    for (let i = 0; i <= n; i++) {
      const t = misturar(de, ate, i / n);
      pontos.push(new THREE.Vector3(centro.x + r * Math.cos(t), centro.y + r * Math.sin(t), 0));
    }
  };
  const r = 0.16;
  reta(P(58, 100), P(28, 100).add(new THREE.Vector3(r, 0, 0)), 6);
  canto(new THREE.Vector3(P(28, 100).x + r, P(28, 100).y + r, 0), r, -Math.PI / 2, -Math.PI, 6);
  reta(P(28, 100).add(new THREE.Vector3(0, r, 0)), P(28, 20).add(new THREE.Vector3(0, -r, 0)), 12);
  canto(new THREE.Vector3(P(28, 20).x + r, P(28, 20).y - r, 0), r, Math.PI, Math.PI / 2, 6);
  reta(P(28, 20).add(new THREE.Vector3(r, 0, 0)), P(58, 20), 6);
  const fim = Math.atan2(P(95.59, 73.68).y, P(95.59, 73.68).x - CENTRO_ARCO.x);
  for (let i = 0; i <= 40; i++) {
    const t = misturar(Math.PI / 2, fim, i / 40);
    pontos.push(new THREE.Vector3(CENTRO_ARCO.x + Math.cos(t), Math.sin(t), 0));
  }
  return new THREE.CatmullRomCurve3(pontos, false, "centripetal");
}

export function iniciarOrbita(canvas, estado) {
  const reduzir = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const renderizador = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
  renderizador.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderizador.outputColorSpace = THREE.SRGBColorSpace;
  renderizador.toneMapping = THREE.ACESFilmicToneMapping;

  const cena = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderizador);
  cena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  cena.environmentIntensity = 0.55;            // reflexos suaves (sem riscos fortes no vidro)
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
  camera.position.set(0, 0, 8.5);

  const luz = new THREE.DirectionalLight(0xffffff, 1.4);
  luz.position.set(3, 4, 5);
  cena.add(luz);

  // ---------------------------------------------------------------- o D
  const grupo = new THREE.Group();
  cena.add(grupo);
  const curva = caminhoDoD();
  const materialD = new THREE.MeshPhysicalMaterial({
    color: 0x2e6be6, roughness: 0.3, metalness: 0.05, clearcoat: 0.55, clearcoatRoughness: 0.35,
    transparent: true, opacity: 1,
  });
  const tubo = new THREE.Mesh(new THREE.TubeGeometry(curva, 320, 0.175, 32, false), materialD);
  grupo.add(tubo);
  for (const ponta of [curva.getPoint(0), curva.getPoint(1)]) {             // pontas arredondadas
    const tampa = new THREE.Mesh(new THREE.SphereGeometry(0.175, 32, 16), materialD);
    tampa.position.copy(ponta);
    grupo.add(tampa);
  }

  // ------------------------------------------------------------ o ponto
  const materialPonto = new THREE.MeshStandardMaterial({ color: 0x2e6be6, emissive: 0x2e6be6, emissiveIntensity: 0.25,
                                                         roughness: 0.3, transparent: true });
  const ponto = new THREE.Mesh(new THREE.SphereGeometry(0.2, 48, 24), materialPonto);
  grupo.add(ponto);
  const brilho = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texturaDeBrilho(), color: 0x86f2ff, transparent: true, opacity: 0, depthWrite: false,
    blending: THREE.AdditiveBlending,
  }));
  brilho.scale.setScalar(1.6);
  ponto.add(brilho);

  // Trilha da órbita (um anel fino, inclinado)
  const inclinacao = new THREE.Euler(1.15, 0.0, -0.35);
  const anel = new THREE.Mesh(new THREE.TorusGeometry(1.55, 0.006, 8, 220),
                              new THREE.MeshBasicMaterial({ color: 0x6e9bf5, transparent: true, opacity: 0, depthWrite: false }));
  anel.rotation.copy(inclinacao);
  anel.position.copy(CENTRO_ARCO);
  grupo.add(anel);

  // ------------------------------------------------------------ estrelas
  const quantas = innerWidth < 760 ? 700 : 1600;
  const posicoes = new Float32Array(quantas * 3);
  const origem = new Float32Array(quantas * 3);
  const perto = new Float32Array(quantas * 3);
  for (let i = 0; i < quantas; i++) {
    const r = 3 + Math.random() * 9, t = Math.random() * Math.PI * 2, f = Math.acos(2 * Math.random() - 1);
    origem.set([r * Math.sin(f) * Math.cos(t), r * Math.sin(f) * Math.sin(t) * 0.6, r * Math.cos(f) - 3], i * 3);
    const rp = 0.35 + Math.random() * 0.5, tp = Math.random() * Math.PI * 2, fp = Math.acos(2 * Math.random() - 1);
    perto.set([rp * Math.sin(fp) * Math.cos(tp), rp * Math.sin(fp) * Math.sin(tp), rp * Math.cos(fp)], i * 3);
  }
  posicoes.set(origem);
  const geometriaEstrelas = new THREE.BufferGeometry();
  geometriaEstrelas.setAttribute("position", new THREE.BufferAttribute(posicoes, 3));
  const materialEstrelas = new THREE.PointsMaterial({ color: 0xcfe0ff, size: 0.035, transparent: true, opacity: 0,
                                                      depthWrite: false, blending: THREE.AdditiveBlending });
  const estrelas = new THREE.Points(geometriaEstrelas, materialEstrelas);
  cena.add(estrelas);

  // ------------------------------------------------------------ animação
  const mouse = { x: 0, y: 0, ax: 0, ay: 0 };
  addEventListener("pointermove", (e) => { mouse.x = e.clientX / innerWidth - 0.5; mouse.y = e.clientY / innerHeight - 0.5; },
                   { passive: true });
  const atual = { x: 1.9, y: 0.1, escala: 1, opacidade: 1, noite: 0, juntar: 0, voo: 0, giro: 0 };
  let largura = 0, altura = 0, tempo = 0, ultimo = performance.now(), anguloOrbita = 0;
  const posPonto = new THREE.Vector3(), posLogo = new THREE.Vector3(), centroGrupo = new THREE.Vector3();

  function redimensionar() {
    largura = canvas.clientWidth; altura = canvas.clientHeight;
    renderizador.setSize(largura, altura, false);
    camera.aspect = largura / Math.max(1, altura);
    camera.updateProjectionMatrix();
  }
  addEventListener("resize", redimensionar);
  redimensionar();

  function alvos() {
    const c = estado.cenas;
    const estreito = largura < 860;
    const a = c.abertura ?? 0, w = c.wise ?? 0, pr = c.privacidade ?? 0, it = c.interface ?? 0;
    const naWise = estado.cena === "wise", naPriv = estado.cena === "privacidade", naInt = estado.cena === "interface";
    // Celular: o símbolo inteiro e opaco, embaixo do texto (meio transparente ele mostraria as próprias dobras)
    let x = estreito ? 0 : 1.85, y = estreito ? -1.55 : 0.05, escala = estreito ? 0.5 : 1, opacidade = 1;
    if (estado.cena === "abertura") {
      x = misturar(x, estreito ? 0 : 0.2, suave(0.35, 1, a));
      escala = misturar(escala, 0.85, suave(0.35, 1, a));
    }
    // No Wise o símbolo some (o texto e a conversa ficam limpos); só as estrelas ficam
    if (naWise) { x = 0; y = 0; escala = 0.8; opacidade = 1 - suave(0, 0.12, w); }
    // Na privacidade o ponto volta, embaixo do texto, e as estrelas se recolhem nele
    if (naPriv) { x = 0; y = estreito ? -1.25 : -1.15; escala = misturar(0.7, 0.5, pr); opacidade = suave(0, 0.15, pr); }
    if (naInt || ["outras"].includes(estado.cena)) { x = 0; y = 0; escala = 0.4; opacidade = 1 - suave(0, 0.25, it); }
    if (!["abertura", "wise", "privacidade", "interface"].includes(estado.cena)) opacidade = 0;
    return {
      x, y, escala, opacidade,
      noite: estado.noite,
      juntar: naPriv ? suave(0.1, 0.7, pr) : 0,
      voo: estado.cena === "abertura" ? suave(0.04, 0.4, a) : 1,
      giro: naWise ? w : naPriv ? 1 + pr : 0,
      sumirD: naPriv || naWise ? 1 : 0,
    };
  }

  function quadro(agora) {
    const dt = Math.min(0.05, (agora - ultimo) / 1000);
    ultimo = agora;
    if (!reduzir) tempo += dt;
    const alvo = alvos();
    const k = 1 - Math.pow(0.0015, dt);                      // amortecimento independente da taxa de quadros
    for (const chave of ["x", "y", "escala", "opacidade", "noite", "juntar", "voo", "giro"]) {
      atual[chave] = reduzir ? alvo[chave] : misturar(atual[chave], alvo[chave], k);
    }
    atual.sumirD = misturar(atual.sumirD ?? 0, alvo.sumirD, reduzir ? 1 : k);
    mouse.ax = misturar(mouse.ax, mouse.x, k * 0.6); mouse.ay = misturar(mouse.ay, mouse.y, k * 0.6);

    // Grupo: lugar, tamanho e um leve balanço que segue o mouse
    grupo.position.set(atual.x, atual.y, 0);
    grupo.scale.setScalar(atual.escala);
    grupo.rotation.set(mouse.ay * 0.25 + Math.sin(tempo * 0.4) * 0.04,
                       -0.32 + mouse.ax * 0.45 + atual.giro * 0.6, 0);

    // O ponto: no lugar do símbolo, depois em órbita (mais rápido quanto mais longe na página)
    anguloOrbita += dt * (0.55 + atual.voo * 0.6);
    posLogo.set(CENTRO_ARCO.x + Math.cos(ANGULO_PONTO), Math.sin(ANGULO_PONTO), 0);
    posPonto.set(Math.cos(ANGULO_PONTO + anguloOrbita * atual.voo) * 1.55, Math.sin(ANGULO_PONTO + anguloOrbita * atual.voo) * 1.55, 0)
      .applyEuler(inclinacao).add(CENTRO_ARCO);
    ponto.position.copy(posLogo).lerp(posPonto, atual.voo);
    if (atual.juntar > 0) ponto.position.lerp(CENTRO_ARCO, atual.juntar);
    ponto.scale.setScalar(1 + atual.noite * 0.3 + atual.juntar * 0.45);
    anel.material.opacity = 0.35 * atual.voo * atual.opacidade * (1 - atual.juntar);

    // Dia → noite: o ponto vira a luz ciano do Wise
    const azul = new THREE.Color(0x2e6be6), ciano = new THREE.Color(0x86f2ff);
    materialPonto.color.copy(azul).lerp(ciano, atual.noite);
    materialPonto.emissive.copy(azul).lerp(ciano, atual.noite);
    materialPonto.emissiveIntensity = 0.25 + atual.noite * 1.6;
    materialPonto.opacity = atual.opacidade;
    brilho.material.opacity = atual.noite * 0.75 * atual.opacidade;
    materialD.opacity = atual.opacidade * (1 - atual.sumirD);
    // Meio transparente não escreve profundidade: senão o D invisível "apagaria" as estrelas atrás dele
    materialD.depthWrite = materialD.opacity > 0.98;
    tubo.visible = materialD.opacity > 0.01;
    grupo.children.forEach((filho) => { if (filho.material === materialD) filho.visible = tubo.visible; });
    materialD.color.set(0x2e6be6).lerp(new THREE.Color(0x1a3a73), atual.noite * 0.6);

    // Estrelas: aparecem à noite; na privacidade, recolhem-se para perto do ponto
    materialEstrelas.opacity = atual.noite * 0.85;
    if (atual.noite > 0.01) {
      grupo.updateMatrixWorld();
      ponto.getWorldPosition(centroGrupo);
      const j = atual.juntar;
      for (let i = 0; i < quantas * 3; i += 3) {
        posicoes[i] = misturar(origem[i], centroGrupo.x + perto[i], j);
        posicoes[i + 1] = misturar(origem[i + 1], centroGrupo.y + perto[i + 1], j);
        posicoes[i + 2] = misturar(origem[i + 2], centroGrupo.z + perto[i + 2], j);
      }
      geometriaEstrelas.attributes.position.needsUpdate = true;
      estrelas.rotation.y = tempo * 0.015 * (1 - j);
    }

    if (atual.opacidade > 0.005 || atual.noite > 0.01) renderizador.render(cena, camera);
    else renderizador.clear();
  }

  let rodando = true;
  function laco(agora) {
    if (!rodando) return;
    quadro(agora);
    requestAnimationFrame(laco);
  }
  document.addEventListener("visibilitychange", () => {
    rodando = !document.hidden;
    if (rodando) { ultimo = performance.now(); requestAnimationFrame(laco); }
  });
  requestAnimationFrame(laco);
}

function texturaDeBrilho() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.25, "rgba(255,255,255,.55)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
