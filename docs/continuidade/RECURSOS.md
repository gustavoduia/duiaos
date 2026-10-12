# DuiaOS — Inventário de recursos entregues (não pode regredir)

Tudo o que já foi entregue e aprovado, com onde mora e uma **conferência**
automática (`arquivo::texto que só a versão atual tem`). Antes de todo pull
request: `python3 ferramentas/conferir-recursos.py`. Se uma conferência falhar,
alguém trouxe uma versão antiga de volta (ex.: partiu de uma branch velha) —
pare e descubra antes de seguir.

Regras:
- Recurso novo ou mudado = linha nova ou atualizada **no mesmo PR**.
- Situação: **main** (já na main), **PR #N** (pronto, aguardando merge) ou
  **branch** (em desenvolvimento).
- Para mudar de propósito um recurso daqui (ex.: trocar o visual), atualize a
  conferência e diga no PR o que mudou e por quê.
- O Wise (repositório privado `duiaos-wise`) tem o próprio inventário em
  `duiaos-wise/docs/continuidade/RECURSOS.md`.

## Sistema e instalação

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| ISO com live-build (x86_64 e ARM64) instalando os .deb do mesmo commit | `build/`, `.github/workflows/gerar-iso.yml` | `build/build.sh::live` | P1 | main |
| Pós-instalação (repositórios, idioma, teclado, SSH, repositório apt) | `pacotes/duiaos-identidade/raiz/usr/lib/duiaos/pos-instalacao` | `pacotes/duiaos-identidade/raiz/usr/lib/duiaos/pos-instalacao::configurar-repositorio` | P2/P3b | main |
| Repositório apt assinado (canais estavel e teste) | `pacotes/publicar.sh`, `.github/workflows/pacotes.yml` | `pacotes/publicar.sh::Release` | ADR 028 | main |
| Dual boot: "Reiniciar no Windows" pelo firmware | `pacotes/duiaos-identidade/raiz/usr/lib/duiaos/reiniciar-no-windows` | `shell/comum/sistema.py::Reiniciar no Windows` | ADR 009 | main |
| Identidade: GRUB, Plymouth (Órbita), papel de parede Órbita | `branding/`, `pacotes/duiaos-identidade/raiz/usr/share/` | `pacotes/duiaos-identidade/raiz/usr/share/plymouth/themes/duiaos/duiaos.plymouth::duiaos` | P3 | main |

## Interface (shell)

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Tela de Entrada e Tela de Bloqueio com o mesmo visual | `shell/comum/TelaDeAcesso.qml` | `shell/comum/TelaDeAcesso.qml::visual único da Tela de Entrada e da Tela de Bloqueio` | ADR 026 | main |
| Tela de Entrada cancela a sessão do greetd depois de um erro | `shell/entrada/main.py` | `shell/entrada/main.py::cancel_session` | PR #8 | PR #9 |
| Tela de Bloqueio reaberta se fechar, swaylock de reserva | `shell/bloqueio/bloquear` | `shell/bloqueio/bloquear::swaylock` | ADR 026 | main |
| Barra de Recursos (símbolo, data e hora, Wi-Fi, volume, bateria, botão Wise) | `shell/barra-de-recursos/` | `shell/barra-de-recursos/BarraDeRecursos.qml::component BotaoWise` | P3 | main |
| Ícone do Wise perto da bateria (apagado quando ele descansa) | `shell/barra-de-recursos/BarraDeRecursos.qml` | `shell/barra-de-recursos/BarraDeRecursos.qml::duiaos-wise.svg` | PR #5 | main |
| Ilha de Aplicativos (fixados e abertos; Wise primeiro) | `shell/ilha-de-aplicativos/` | `shell/ilha-de-aplicativos/IlhaDeAplicativos.qml::Ilha de Aplicativos` | P3 | main |
| Central de Aplicativos (busca, Enter abre, clique direito fixa) | `shell/ilha-de-aplicativos/CentralDeAplicativos.qml` | `shell/ilha-de-aplicativos/CentralDeAplicativos.qml::clique direito fixa/desafixa` | P3 | main |
| Programas abertos pela Barra e pela Ilha sem layer-shell | `shell/ilha-de-aplicativos/main.py` | `shell/ilha-de-aplicativos/main.py::QT_WAYLAND_SHELL_INTEGRATION` | PR #4 | main |
| Menu de Energia (inclui Reiniciar no Windows com dual boot) | `shell/comum/MenuDeEnergia.qml`, `shell/menu-de-energia/` | `shell/comum/MenuDeEnergia.qml::Reiniciar no Windows` | P3 | main |
| Atalhos Super+Espaço, Super+W, Super+L, Ctrl+Alt+Delete | `shell/sessao/rc.xml` | `shell/sessao/rc.xml::W-w` | P3 | main |
| Wise iniciado com a sessão e reaberto se fechar | `shell/sessao/autostart` | `shell/sessao/autostart::duiaos-wise --fundo` | PR #5 | main |
| Acessibilidade ligada na sessão (AT-SPI), grim e wtype | `shell/sessao/`, `shell/pacotes.list` | `shell/sessao/environment::QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`, `shell/pacotes.list::wtype` | ADR 035 | PR #9 |

## IA do sistema

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Pacote duiaos-ollama (release oficial, sha256, sem CUDA, placa integrada) | `pacotes/duiaos-ollama/` | `pacotes/duiaos-ollama/raiz/usr/lib/systemd/system/ollama.service::OLLAMA_IGPU_ENABLE=1` | ADR 030 | PR #9 |
| Serviço duiaos-ia (D-Bus org.duiaos.IA1, polkit com dono) | `ia/servico.py`, `pacotes/duiaos-ia/` | `pacotes/duiaos-ia/raiz/usr/share/polkit-1/actions/org.duiaos.ia.policy::org.freedesktop.policykit.owner` | ADR 031 | PR #9 |
| Modelo ativo carregado no boot, antes do login | `pacotes/duiaos-ia/raiz/usr/lib/systemd/system/duiaos-ia.service` | `pacotes/duiaos-ia/raiz/usr/lib/systemd/system/duiaos-ia.service::WantedBy=multi-user.target` | ADR 032 | PR #9 |
| Calibração por computador (threads, placa) publicada em "opcoes" | `ia/servico.py`, `ia/hardware.py` | `ia/servico.py::def calibrar`, `ia/hardware.py::def threads_candidatas` | ADR 033 | PR #9 |
| Central de IA (modelo ativo, catálogo, download em tempo real) | `apps/central-de-ia/` | `apps/central-de-ia/CentralDeIA.qml::Um só modelo ativo para o sistema inteiro` | ADR 031 | PR #9 |
| Termos: motor (Ollama) × modelo | `ia/`, `apps/central-de-ia/` | `ia/catalogo.json::qwen3.5:4b` | PR #8 | PR #9 |
| Medição de motores (Ollama × llama-server × MTP × OpenVINO) | `ferramentas/medir-motores.py` | `ferramentas/medir-motores.py::--placa` | 12/10 | PR #9 |

## Agente do sistema

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| duiaos-agente: Preparar (simula) e Executar (polkit + mesmo impacto) | `agente/`, `pacotes/duiaos-agente/` | `agente/agente.py::org.duiaos.Agente1`, `agente/plano.py::PROTEGIDOS_FIXOS` | ADR 034 | PR #9 |
| Sem senha só para a sessão local ativa de administrador | `pacotes/duiaos-agente/raiz/usr/share/polkit-1/rules.d/50-duiaos-agente.rules` | `pacotes/duiaos-agente/raiz/usr/share/polkit-1/rules.d/50-duiaos-agente.rules::isInGroup("sudo")` | ADR 034 | PR #9 |

## Site e documentação

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Página inicial com a Órbita em 3D e cenas na rolagem (dia → noite → dia) | `site/src/pages/index.astro`, `site/src/scripts/` | `site/src/scripts/orbita.js::caminhoDoD`, `site/src/scripts/cenas.js::noite-agora` | ADR 038 | PR #9 |
| Downloads com a versão mais nova (API + KV) | `site/src/pages/baixar.astro`, `site/worker/index.js` | `site/worker/index.js::/api/versoes` | ADR 038 | PR #9 |
| Suporte com protocolo (D1) | `site/src/pages/suporte.astro`, `site/migrations/` | `site/worker/index.js::INSERT INTO chamados` | ADR 038 | PR #9 |
| Documentação para usuários (Diátaxis, busca) | `site/src/content/docs/documentacao/` | `site/astro.config.mjs::documentacao/como-fazer`, `site/src/content/docs/documentacao/wise/usar-aplicativos-pelo-wise.md::nunca faz` | ADR 037 | PR #9 |
| Publicação automática no Cloudflare | `.github/workflows/site.yml` | `.github/workflows/site.yml::wrangler deploy` | ADR 038 | PR #9 |

## Processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Continuidade à prova de troca de sessão e de conta | `CLAUDE.md`, `docs/continuidade/` | `CLAUDE.md::docs/continuidade/ESTADO.md`, `ferramentas/conferir-recursos.py::RECURSOS.md` | 12/10 | PR #9 |
