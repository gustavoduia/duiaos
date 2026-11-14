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

| Wise instalado com o sistema (ISO e apt), do repositório privado | `pacotes/trazer-wise.sh`, `build/build.sh`, `.github/workflows/` | `pacotes/trazer-wise.sh::DUIAOS_TOKEN_WISE`, `build/build.sh::pacotes/externos/duiaos-wise_`, `pacotes/duiaos-desktop/DEBIAN/control::Recommends: duiaos-wise` | ADR 042 | main |
| Lançamento com notas de versão e a mesma tag no Wise | `ferramentas/lancar-versao.sh`, `notas-de-versao/` | `ferramentas/lancar-versao.sh::WISE_TEM_TAG`, `.github/workflows/gerar-iso.yml::notas-de-versao/` | ADR 042 | main |

## Interface (shell)

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Tela de Entrada e Tela de Bloqueio com o mesmo visual | `shell/comum/TelaDeAcesso.qml` | `shell/comum/TelaDeAcesso.qml::visual único da Tela de Entrada e da Tela de Bloqueio` | ADR 026 | main |
| Tela de Entrada cancela a sessão do greetd depois de um erro | `shell/entrada/main.py` | `shell/entrada/main.py::cancel_session` | PR #8 | main |
| Tela de Bloqueio reaberta se fechar, swaylock de reserva | `shell/bloqueio/bloquear` | `shell/bloqueio/bloquear::swaylock` | ADR 026 | main |
| Barra de Recursos: Menu do DuiaOS, botão Wise, aplicativo em uso, até 4 ícones + balão da seta, Central de Controle, relógio com calendário | `shell/barra-de-recursos/` | `shell/barra-de-recursos/Barra.qml::readonly property var ocultos`, `shell/barra-de-recursos/Barra.qml::id: botaoWise`, `shell/barra-de-recursos/ConteudoPainel.qml::Sobre este computador` | ADR 044 | main |
| Central de Controle (Wi-Fi, Bluetooth, modo avião, luz noturna, bloquear, capturar tela, brilho, som, bateria e modo de energia) e balões de cada ícone | `shell/barra-de-recursos/ConteudoPainel.qml`, `shell/comum/controles.py` | `shell/barra-de-recursos/ConteudoPainel.qml::nome: "central"`, `shell/comum/controles.py::def interpretar_redes` | ADR 044 | main |
| Confirmação antes de Reiniciar, Desligar e Encerrar sessão (Menu do DuiaOS) | `shell/barra-de-recursos/` | `shell/barra-de-recursos/main.py::def confirmarEnergia` | ADR 044 | main |
| Ícone do Wise perto da bateria (apagado quando ele descansa) | `shell/barra-de-recursos/Barra.qml` | `shell/barra-de-recursos/Barra.qml::duiaos-wise.svg` | PR #5 | main |
| Ilha de Aplicativos (fixados e abertos; Wise primeiro) | `shell/ilha-de-aplicativos/` | `shell/ilha-de-aplicativos/IlhaDeAplicativos.qml::Ilha de Aplicativos` | P3 | main |
| Ilha: Explorador fixo, Configurações por padrão, pasta Aplicativos, pilha de Downloads e Lixeira | `shell/ilha-de-aplicativos/` | `shell/ilha-de-aplicativos/Ilha.qml::pasta-downloads`, `shell/ilha-de-aplicativos/main.py::def downloads_recentes` | ADR 044 | main |
| Central de Aplicativos em tela cheia (busca, Enter abre, clique direito fixa) | `shell/ilha-de-aplicativos/ConteudoCentral.qml` | `shell/ilha-de-aplicativos/ConteudoCentral.qml::clique direito fixa/desafixa` | ADR 044 | main |
| Programas abertos pela Barra e pela Ilha sem layer-shell | `shell/ilha-de-aplicativos/main.py` | `shell/ilha-de-aplicativos/main.py::QT_WAYLAND_SHELL_INTEGRATION` | PR #4 | main |
| Menu de Energia (inclui Reiniciar no Windows com dual boot) | `shell/comum/MenuDeEnergia.qml`, `shell/menu-de-energia/` | `shell/comum/MenuDeEnergia.qml::Reiniciar no Windows` | P3 | main |
| Atalhos Super+Espaço, Super+W, Super+L, Ctrl+Alt+Delete | `shell/sessao/rc.xml` | `shell/sessao/rc.xml::W-w` | P3 | main |
| Explorador de Arquivos (Favoritos, Aplicativos, discos, Lixeira freedesktop, ícones/lista, copiar/recortar/colar, renomear, busca, Abrir com, Informações; Super+E) | `apps/explorador-de-arquivos/`, `pacotes/duiaos-shell/raiz/` | `apps/explorador-de-arquivos/operacoes.py::def mover_para_lixeira`, `apps/explorador-de-arquivos/ExploradorDeArquivos.qml::Abrir com…`, `shell/sessao/rc.xml::W-e` | ADR 044 | main |
| Configurações (Wi-Fi, Bluetooth, Som, Tela, Energia, Papel de parede, Barra e Ilha, Usuário e senha, Data e hora, Teclado, Aplicativos padrão, Privacidade, IA, Sobre) | `apps/configuracoes/`, `pacotes/duiaos-shell/raiz/usr/lib/duiaos/conta` | `apps/configuracoes/Configuracoes.qml::Sobre este computador`, `pacotes/duiaos-shell/raiz/usr/lib/duiaos/conta::PKEXEC_UID` | ADR 044 | main |
| Preferências aplicadas ao entrar (papel de parede, telas, luz noturna, bloqueio e repouso) | `shell/comum/sessao.py`, `shell/sessao/autostart` | `shell/sessao/autostart::sessao.py" aplicar`, `shell/comum/sessao.py::def comando_swayidle` | ADR 044 | main |
| Biblioteca QML comum (import DuiaOS) e ícones próprios | `shell/comum/qml/DuiaOS/`, `shell/comum/icones.py` | `shell/comum/qml/DuiaOS/qmldir::module DuiaOS`, `shell/comum/icones.py::def registrar` | ADR 044 | main |
| Área de Trabalho: papel de parede (imagem, GIF, vídeo, cor), ícones da pasta Área de Trabalho, menus do botão direito; sem o menu Reconfigurar/Sair do labwc | `shell/area-de-trabalho/`, `shell/sessao/rc.xml` | `shell/area-de-trabalho/ConteudoArea.qml::Mudar o papel de parede…`, `shell/comum/qml/DuiaOS/FundoVideo.qml::MediaPlayer.Infinite`, `shell/sessao/rc.xml::context name="Root"` | ADR 045 | main |
| Barra das janelas no estilo do macOS (bolinhas à esquerda, título no centro) e menu das janelas em português | `pacotes/duiaos-identidade/raiz/usr/share/themes/DuiaOS/`, `shell/sessao/rc.xml`, `shell/sessao/menu.xml` | `pacotes/duiaos-identidade/raiz/usr/share/themes/DuiaOS/openbox-3/close-active.svg::#FF5F57`, `shell/sessao/rc.xml::close,iconify,max:`, `shell/sessao/menu.xml::Sempre na frente` | ADR 045 | main |
| Modo escuro em toda a interface do DuiaOS, nas janelas (labwc) e nos aplicativos GTK | `shell/comum/qml/DuiaOS/Tema.qml`, `shell/comum/interface.py`, `shell/comum/sessao.py` | `shell/comum/qml/DuiaOS/Tema.qml::aparencia.escuro`, `shell/comum/sessao.py::def aplicar_aparencia` | ADR 045 | main |
| Notificações: serviço org.freedesktop.Notifications, balões, histórico no relógio, Não perturbe | `shell/notificacoes/`, `shell/barra-de-recursos/` | `shell/notificacoes/servico.py::org.freedesktop.Notifications`, `shell/barra-de-recursos/ConteudoPainel.qml::Não perturbe` | ADR 045 | main |
| Tela de Descanso (imagem, vídeo ou papel de parede, com relógio) pelo swayidle | `shell/descanso/`, `shell/comum/sessao.py` | `shell/descanso/ConteudoDescanso.qml::raiz.sair()`, `shell/comum/sessao.py::pkill -f descanso/main.py` | ADR 045 | main |
| Configurações: Notificações, Aparência, Tela de Descanso, importar imagem/vídeo, Atualizações (duiaos-agente), foto da conta | `apps/configuracoes/`, `pacotes/duiaos-shell/raiz/usr/lib/duiaos/conta` | `apps/configuracoes/main.py::def procurarAtualizacoes`, `apps/configuracoes/main.py::def importarFundo`, `pacotes/duiaos-shell/raiz/usr/lib/duiaos/conta::/var/lib/duiaos/fotos` | ADR 045 | main |
| Foto da conta na Tela de Entrada e na Tela de Bloqueio | `shell/comum/TelaDeAcesso.qml`, `shell/comum/sistema.py` | `shell/comum/TelaDeAcesso.qml::id: fotoConta`, `shell/comum/sistema.py::def foto` | ADR 045 | main |
| Menu do botão direito na Ilha de Aplicativos | `shell/ilha-de-aplicativos/MenuDaIlha.qml` | `shell/ilha-de-aplicativos/MenuDaIlha.qml::Manter na Ilha`, `shell/ilha-de-aplicativos/main.py::def acaoMenu` | ADR 045 | main |
| Fichas de atualização DUIA-AAAA-NNNN, catálogo publicado e instalado, Central de Atualizações com detalhes, Debian com segurança e registro de mudanças | `atualizacoes/`, `ferramentas/atualizacoes.py`, `apps/configuracoes/atualizacoes_sistema.py`, `.github/workflows/pacotes.yml` | `ferramentas/atualizacoes.py::def conferir`, `apps/configuracoes/atualizacoes_sistema.py::def fichas_pendentes`, `.github/workflows/pacotes.yml::atualizacoes.py catalogo`, `pacotes/construir.sh::atualizacoes.json` | ADR 046 | main |
| Atualizações: tempo previsto e decorrido, etapa atual, alerta e interrupção da etapa parada com reparo, motivo do erro, registros completos, idempotência | `agente/agente.py`, `agente/plano.py`, `apps/configuracoes/` | `agente/agente.py::def _vigiar`, `agente/agente.py::LerRegistro`, `agente/plano.py::def explicar_erro`, `apps/configuracoes/Configuracoes.qml::Ver o que está acontecendo` | ADR 047 | main |
| Agente não se reinicia nem se isola durante uma atualização (adia o SIGTERM; sai sozinho quando trocado) | `pacotes/duiaos-agente/`, `agente/agente.py` | `agente/agente.py::GLib.unix_signal_add`, `pacotes/duiaos-agente/raiz/usr/lib/systemd/system/duiaos-agente.service::Sem isolamento`, `agente/testes/test_andamento.py::class TesteAutoAtualizacao` | ADR 048 | main |
| Duia App Store: Descobrir (destaques e coleções), categorias, busca, página do aplicativo, Instalados e Atualizações; Debian (AppStream/DEP-11, pelo duiaos-agente) e Flathub (flatpak --user); fixa na Ilha | `apps/loja/`, `pacotes/duiaos-shell/raiz/usr/bin/duiaos-loja`, `shell/sessao/iniciar-sessao` | `apps/loja/catalogo.py::def ler_dep11`, `apps/loja/catalogo.py::def ler_appstream_xml`, `apps/loja/main.py::def _rodar_flatpak`, `shell/ilha-de-aplicativos/main.py::duiaos-loja.desktop`, `shell/sessao/iniciar-sessao::flatpak/exports/share` | ADR 049 | main |
| Ilha como o Dock: tamanho, ampliação, posição (base/esquerda/direita), ocultar, indicadores, pular ao abrir, recentes, clique minimiza; menus do aplicativo e do fundo; arrastar para reordenar/tirar; minimizar e restaurar com gênio ou escala | `shell/ilha-de-aplicativos/`, `shell/sessao/rc.xml`, `apps/configuracoes/` | `shell/ilha-de-aplicativos/efeitos.py::def regiao_alterada`, `shell/ilha-de-aplicativos/EfeitoDeJanela.qml::faixas: 64`, `shell/ilha-de-aplicativos/Ilha.qml::raioAmpliacao`, `shell/ilha-de-aplicativos/main.py::def definirMascara`, `shell/sessao/rc.xml::context name="Iconify"`, `apps/configuracoes/main.py::def definirOpcaoIlha` | ADR 050 | main |
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
| Falhas registradas em todos os programas do DuiaOS | `shell/*/main.py`, `apps/central-de-ia/main.py`, `ia/`, `agente/` | `shell/comum/interface.py::duiaos_registro.ligar`, `ia/servico.py::duiaos_registro.ligar("duiaos-ia")` | ADR 040 | main |
| Coletor `duiaos-relatorios`: níveis, anonimização, perfil, falhas agrupadas, envio Git | `relatorios/`, `pacotes/duiaos-relatorios/` | `relatorios/coleta.py::def assinatura_nativa`, `relatorios/duiaos_registro/privacidade.py::def anonimizar` | ADR 040 | main |
| Journal persistente, systemd-coredump e catálogo | `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/` | `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/journald.conf.d/50-duiaos.conf::Storage=persistent`, `pacotes/duiaos-relatorios/raiz/usr/lib/systemd/catalog/duiaos.catalog::0b0f983a3fad41bb9a9730053146311a` | ADR 040 | main |
| Uso agregado: lista conhecida, somado no computador (nível erros e uso) | `relatorios/uso.py`, `relatorios/coleta.py`, `shell/` | `relatorios/uso.py::def agregar`, `relatorios/coleta.py::def agregar_uso`, `shell/ilha-de-aplicativos/main.py::uso.aplicativo_aberto` | ADR 041 | main |
| Janela "Ajude a melhorar o DuiaOS" (1ª entrada sem opção marcada; Central de Aplicativos) | `apps/ajude-a-melhorar/`, `shell/sessao/autostart` | `apps/ajude-a-melhorar/AjudeAMelhorar.qml::Nenhuma opção vem marcada`, `shell/sessao/autostart::--primeira-entrada` | ADR 041 | main |
| Escolha pelo polkit (administrador sem senha; desenvolvimento só pelo terminal) | `pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/`, `relatorios/principal.py` | `pacotes/duiaos-relatorios/raiz/usr/share/polkit-1/actions/org.duiaos.relatorios.policy::org.duiaos.relatorios.escolher`, `relatorios/principal.py::ESCOLHAS_DA_TELA` | ADR 041 | main |
| Envio pelo site (HTTPS, sem credencial; padrão) | `relatorios/envio.py`, `relatorios/config.py` | `relatorios/envio.py::def enviar_https`, `relatorios/config.py::ENDERECO_PADRAO` | ADR 041 | main |
| Leitura dos relatórios pelo Claude | `ferramentas/ler-relatorios.py` | `ferramentas/ler-relatorios.py::def falhas_agrupadas` | ADR 040 | main |

## Site e documentação

Moraram aqui até 12/10 e foram para o repositório `duiaos-websites` (ADR 039), com inventário próprio em
`duiaos-websites/docs/continuidade/RECURSOS.md`.

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |

## Processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Início e fim de chat (REGRASINI/REGRASFIM), memória única por chat em `docs/continuidade/`, toda instrução só no duiaos, só a main | `docs/continuidade/`, `CLAUDE.md` | `docs/continuidade/REGRASINI.md::Não há autorização para criar branches`, `docs/continuidade/REGRASFIM.md::Orientação para o próximo chat`, `CLAUDE.md::Toda instrução fica exclusivamente aqui` | ADR 043 | main |
| Inventários do Wise e do site conferidos daqui | `ferramentas/conferir-recursos.py`, `docs/continuidade/RECURSOS-*.md` | `ferramentas/conferir-recursos.py::RECURSOS-WISE.md` | ADR 043 | main |
| Código aberto, EULA e licenças lidos do duiaos-fontes-abertas | `pacotes/construir.sh`, `.github/workflows/` | `pacotes/construir.sh::FONTES_ABERTAS`, `.github/workflows/pacotes.yml::repository: gustavoduia/duiaos-fontes-abertas` | ADR 043 | main |
| Continuidade à prova de troca de sessão e de conta | `CLAUDE.md`, `docs/continuidade/` | `CLAUDE.md::docs/continuidade/REGRASINI.md`, `ferramentas/conferir-recursos.py::RECURSOS.md` | 12/10 | main |
