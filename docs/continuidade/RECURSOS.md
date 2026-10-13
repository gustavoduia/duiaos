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

| Wise instalado com o sistema (ISO e apt), do repositório privado | `pacotes/trazer-wise.sh`, `build/build.sh`, `.github/workflows/` | `pacotes/trazer-wise.sh::DUIAOS_TOKEN_WISE`, `build/build.sh::pacotes/externos/duiaos-wise_`, `pacotes/duiaos-desktop/DEBIAN/control::Recommends: duiaos-wise` | ADR 042 | PR #12 |
| Lançamento com notas de versão e a mesma tag no Wise | `ferramentas/lancar-versao.sh`, `notas-de-versao/` | `ferramentas/lancar-versao.sh::WISE_TEM_TAG`, `.github/workflows/gerar-iso.yml::notas-de-versao/` | ADR 042 | PR #12 |

## Interface (shell)

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Tela de Entrada e Tela de Bloqueio com o mesmo visual | `shell/comum/TelaDeAcesso.qml` | `shell/comum/TelaDeAcesso.qml::visual único da Tela de Entrada e da Tela de Bloqueio` | ADR 026 | main |
| Tela de Entrada cancela a sessão do greetd depois de um erro | `shell/entrada/main.py` | `shell/entrada/main.py::cancel_session` | PR #8 | main |
| Tela de Bloqueio reaberta se fechar, swaylock de reserva | `shell/bloqueio/bloquear` | `shell/bloqueio/bloquear::swaylock` | ADR 026 | main |
| Barra de Recursos (símbolo, data e hora, Wi-Fi, volume, bateria, botão Wise) | `shell/barra-de-recursos/` | `shell/barra-de-recursos/BarraDeRecursos.qml::component BotaoWise` | P3 | main |
| Ícone do Wise perto da bateria (apagado quando ele descansa) | `shell/barra-de-recursos/BarraDeRecursos.qml` | `shell/barra-de-recursos/BarraDeRecursos.qml::duiaos-wise.svg` | PR #5 | main |
| Ilha de Aplicativos (fixados e abertos; Wise primeiro) | `shell/ilha-de-aplicativos/` | `shell/ilha-de-aplicativos/IlhaDeAplicativos.qml::Ilha de Aplicativos` | P3 | main |
| Central de Aplicativos (busca, Enter abre, clique direito fixa) | `shell/ilha-de-aplicativos/CentralDeAplicativos.qml` | `shell/ilha-de-aplicativos/CentralDeAplicativos.qml::clique direito fixa/desafixa` | P3 | main |
| Programas abertos pela Barra e pela Ilha sem layer-shell | `shell/ilha-de-aplicativos/main.py` | `shell/ilha-de-aplicativos/main.py::QT_WAYLAND_SHELL_INTEGRATION` | PR #4 | main |
| Menu de Energia (inclui Reiniciar no Windows com dual boot) | `shell/comum/MenuDeEnergia.qml`, `shell/menu-de-energia/` | `shell/comum/MenuDeEnergia.qml::Reiniciar no Windows` | P3 | main |
| Atalhos Super+Espaço, Super+W, Super+L, Ctrl+Alt+Delete | `shell/sessao/rc.xml` | `shell/sessao/rc.xml::W-w` | P3 | main |
| Wise iniciado com a sessão e reaberto se fechar | `shell/sessao/autostart` | `shell/sessao/autostart::duiaos-wise --fundo` | PR #5 | main |
| Acessibilidade ligada na sessão (AT-SPI), grim e wtype | `shell/sessao/`, `shell/pacotes.list` | `shell/sessao/environment::QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`, `shell/pacotes.list::wtype` | ADR 035 | main |

## IA do sistema

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Pacote duiaos-ollama (release oficial, sha256, sem CUDA, placa integrada) | `pacotes/duiaos-ollama/` | `pacotes/duiaos-ollama/raiz/usr/lib/systemd/system/ollama.service::OLLAMA_IGPU_ENABLE=1` | ADR 030 | main |
| Serviço duiaos-ia (D-Bus org.duiaos.IA1, polkit com dono) | `ia/servico.py`, `pacotes/duiaos-ia/` | `pacotes/duiaos-ia/raiz/usr/share/polkit-1/actions/org.duiaos.ia.policy::org.freedesktop.policykit.owner` | ADR 031 | main |
| Modelo ativo carregado no boot, antes do login | `pacotes/duiaos-ia/raiz/usr/lib/systemd/system/duiaos-ia.service` | `pacotes/duiaos-ia/raiz/usr/lib/systemd/system/duiaos-ia.service::WantedBy=multi-user.target` | ADR 032 | main |
| Calibração por computador (threads, placa) publicada em "opcoes" | `ia/servico.py`, `ia/hardware.py` | `ia/servico.py::def calibrar`, `ia/hardware.py::def threads_candidatas` | ADR 033 | main |
| Central de IA (modelo ativo, catálogo, download em tempo real) | `apps/central-de-ia/` | `apps/central-de-ia/CentralDeIA.qml::Um só modelo ativo para o sistema inteiro` | ADR 031 | main |
| Termos: motor (Ollama) × modelo | `ia/`, `apps/central-de-ia/` | `ia/catalogo.json::qwen3.5:4b` | PR #8 | main |
| Medição de motores (Ollama × llama-server × MTP × OpenVINO) | `ferramentas/medir-motores.py` | `ferramentas/medir-motores.py::--placa` | 12/10 | main |

## Agente do sistema

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| duiaos-agente: Preparar (simula) e Executar (polkit + mesmo impacto) | `agente/`, `pacotes/duiaos-agente/` | `agente/agente.py::org.duiaos.Agente1`, `agente/plano.py::PROTEGIDOS_FIXOS` | ADR 034 | main |
| Sem senha só para a sessão local ativa de administrador | `pacotes/duiaos-agente/raiz/usr/share/polkit-1/rules.d/50-duiaos-agente.rules` | `pacotes/duiaos-agente/raiz/usr/share/polkit-1/rules.d/50-duiaos-agente.rules::isInGroup("sudo")` | ADR 034 | main |

## Registros do sistema

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Registro único no journal com campos padronizados (`duiaos_registro`) | `relatorios/duiaos_registro/` | `relatorios/duiaos_registro/__init__.py::DUIAOS_ASSINATURA`, `relatorios/duiaos_registro/journal.py::struct.pack("<Q"` | ADR 040 | main |
| Falhas registradas em todos os programas do DuiaOS | `shell/*/main.py`, `apps/central-de-ia/main.py`, `ia/`, `agente/` | `shell/barra-de-recursos/main.py::duiaos_registro.ligar`, `ia/servico.py::duiaos_registro.ligar("duiaos-ia")` | ADR 040 | main |
| Coletor `duiaos-relatorios`: níveis, anonimização, perfil, falhas agrupadas, envio Git | `relatorios/`, `pacotes/duiaos-relatorios/` | `relatorios/coleta.py::def assinatura_nativa`, `relatorios/duiaos_registro/privacidade.py::def anonimizar` | ADR 040 | main |
| Journal persistente, systemd-coredump e catálogo | `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/` | `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/journald.conf.d/50-duiaos.conf::Storage=persistent`, `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/catalog/duiaos.catalog::0b0f983a3fad41bb9a9730053146311a` | ADR 040 | main |
| Uso agregado: lista conhecida, somado no computador (nível erros e uso) | `relatorios/uso.py`, `relatorios/coleta.py`, `shell/` | `relatorios/uso.py::def agregar`, `relatorios/coleta.py::def agregar_uso`, `shell/ilha-de-aplicativos/main.py::uso.aplicativo_aberto` | ADR 041 | PR #12 |
| Janela "Ajude a melhorar o DuiaOS" (1ª entrada sem opção marcada; Central de Aplicativos) | `apps/ajude-a-melhorar/`, `shell/sessao/autostart` | `apps/ajude-a-melhorar/AjudeAMelhorar.qml::Nenhuma opção vem marcada`, `shell/sessao/autostart::--primeira-entrada` | ADR 041 | PR #12 |
| Escolha pelo polkit (administrador sem senha; desenvolvimento só pelo terminal) | `pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/`, `relatorios/principal.py` | `pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/actions/org.duiaos.relatorios.policy::org.duiaos.relatorios.escolher`, `relatorios/principal.py::ESCOLHAS_DA_TELA` | ADR 041 | PR #12 |
| Envio pelo site (HTTPS, sem credencial; padrão) | `relatorios/envio.py`, `relatorios/config.py` | `relatorios/envio.py::def enviar_https`, `relatorios/config.py::ENDERECO_PADRAO` | ADR 041 | PR #12 |
| Leitura dos relatórios pelo Claude | `ferramentas/ler-relatorios.py` | `ferramentas/ler-relatorios.py::def falhas_agrupadas` | ADR 040 | main |

## Site e documentação

Moraram aqui até 12/10 e foram para o repositório `duiaos-websites` (ADR 039), com inventário próprio em
`duiaos-websites/docs/continuidade/RECURSOS.md`.

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| PR irmão exigido quando algo visível muda | `.github/workflows/documentacao-irma.yml` | `.github/workflows/documentacao-irma.yml::Documentação: não precisa` | ADR 039 | main |

## Processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Memória dos chats (um arquivo por chat, lida inteira antes de tudo; só no duiaos) | `docs/memoria-dos-chats/` | `docs/memoria-dos-chats/README.md::Ao começar um chat`, `docs/memoria-dos-chats/MODELO.md::Visão e regras do produto`, `CLAUDE.md::Memória dos chats primeiro` | 12/10 | PR #13 |
| Continuidade à prova de troca de sessão e de conta | `CLAUDE.md`, `docs/continuidade/` | `CLAUDE.md::docs/continuidade/ESTADO.md`, `ferramentas/conferir-recursos.py::RECURSOS.md` | 12/10 | main |
