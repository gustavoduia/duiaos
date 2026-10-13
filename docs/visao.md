# DuiaOS — Visão, arquitetura e roadmap consolidados

Versão 2.0 · 11/10/2026 · consolida o plano de construção (Fases 0–11) com o
documento "DuiaOS — Visão de Produto, Arquitetura e Roadmap" v1.1.

Este documento separa o que **já existe** do que é **arquitetura-alvo**.
Nada marcado como planejado deve ser tratado como implementado.

---

## 1. Propósito

O DuiaOS é um sistema operacional baseado no Debian 13 (trixie) que muda a
forma de usar o computador: a pessoa descreve o resultado que deseja e o
sistema interpreta, planeja, escolhe as ferramentas, executa ações
autorizadas e explica o que fez.

- **Visão:** que qualquer pessoa consiga aproveitar o potencial das
  tecnologias digitais avançadas sem precisar dominar sua complexidade.
- **Missão:** traduzir objetivos expressos em linguagem natural, voz, texto e
  contexto visual em ações úteis, seguras e verificáveis no computador e nos
  serviços conectados.
- **Proposta de valor:** o usuário diz o que quer; o sistema descobre como
  fazer — com as IAs, contas e serviços que o próprio usuário escolher.

### 1.1 Os quatro pilares

1. **Sistema operacional confiável** — base Debian, instalação simples,
   atualizações seguras, interface própria (Barra de Recursos, Ilha e Central
   de Aplicativos).
2. **Wise** — assistente multimodal (texto, voz, visão) que orquestra
   tarefas.
3. **Camada segura de agentes** — ferramentas tipadas, permissões, confirmação
   proporcional ao risco e auditoria.
4. **Painel de Tecnologias** — onde o usuário conecta provedores de IA, contas
   (GitHub, nuvens, e-mail, agenda), permissões e limites de custo.

### 1.2 O que o DuiaOS é — e o que não é

| É | Não é |
| --- | --- |
| Uma experiência centrada em objetivos e assistência | Uma distribuição Linux com um chatbot instalado |
| Uma camada de integração de modelos, serviços e recursos locais | Um produto preso a um único provedor de IA |
| Um sistema de agentes com permissões, auditoria e confirmação | Uma IA com acesso irrestrito e invisível |
| Acessível a iniciantes sem tirar recursos dos avançados | Uma promessa de automatizar tudo no primeiro release |

### 1.3 Valores (princípios orientadores)

Objetivo antes da ferramenta · IA agnóstica · Automação com limites ·
Transparência · Confirmação proporcional ao risco · Privacidade por padrão ·
Falha segura · Composição e interoperabilidade · Acessibilidade · Evolução
incremental · Identidade própria e coerente (visual claro, azul, minimalista).

### 1.4 Público

**Usuários finais**: pessoa sem conhecimento técnico, profissional de
escritório, estudante, família, quem quer controlar custos — e, no futuro,
empresas. O DuiaOS é um produto, não um projeto de comunidade de
desenvolvedores.

---

## 2. Estado atual (as-built, 11/10/2026)

| Área | Situação |
| --- | --- |
| ISO x86_64 e ARM64 geradas pelo GitHub Actions; release a cada tag | Pronto (v0.0.1 publicada) |
| Identidade: nome, os-release, menu de boot com tema, mensagens em pt-BR | Pronto |
| Instalação no SSD (instalador provisório Debian), dual boot com Windows | Pronto; BitLocker em correção |
| Wi-Fi, áudio (PipeWire/SOF), Bluetooth, zram, relógio por NTP | Pronto |
| Teclado ABNT2 e português no sistema instalado e na sessão gráfica | Pronto |
| Sessão gráfica: labwc + Qt6/QML + Python (PySide6) | Pronto (abre pela Tela de Entrada) |
| **Barra de Recursos** (posição configurável) | Pronto |
| **Ilha de Aplicativos** (fixados, abertos, foco) | Pronto |
| **Central de Aplicativos** (busca, fixar, Super+Espaço) | Pronto |
| **Tela de Entrada** e **Tela de Bloqueio** (mesmo visual), animação de boot, papel de parede, Menu de Energia com "Reiniciar no Windows" | Pronto |
| Código próprio em pacotes `.deb` e atualizações pelo apt | Em teste (P3b) |
| Wise, Painel de Tecnologias, agentes | Projeto (este documento) |

---

## 3. Arquitetura-alvo

### 3.1 Princípio central

O Wise **não** transforma pedidos em comandos de terminal. Ele é um
**orquestrador de tarefas**: o modelo de IA interpreta e planeja; a execução
acontece por **ferramentas declaradas**, validadas por código determinístico,
sob permissões e com registro. A IA é um componente probabilístico, nunca a
autoridade de segurança.

### 3.2 Camadas e tecnologias propostas

As escolhas abaixo seguem a stack já adotada (Debian, systemd, Wayland,
Qt6/QML, Python) e serão confirmadas por ADR antes de implementar.

| Camada | Responsabilidade | Proposta para o DuiaOS |
| --- | --- | --- |
| 1. Experiência | Janela do Wise, notificações, integração com a interface | QML (PySide6), acionado pela Barra de Recursos, pela Ilha e por atalho |
| 2. Percepção | Palavra de ativação, fala↔texto, captura sob demanda | Candidatos locais: openWakeWord, whisper.cpp ou Vosk, Piper (TTS) |
| 3. Orquestração | Intenção, plano, estado e fila de tarefas | Serviço de usuário `duiaos-wise` (Python, `systemd --user`) |
| 4. IA do sistema (gateway de modelos) | Recurso do sistema operacional, não do Wise: motores, chaves, consentimento, roteamento, fallback, custo — para qualquer programa | Serviço do sistema `duiaos-ia` com API D-Bus; adaptadores Gemini, OpenAI, Anthropic e locais (Ollama) — ADR 029 |
| 5. Registro de ferramentas | Ferramentas tipadas com escopo e risco | Esquemas JSON com nível de risco, efeitos e verificação |
| 6. Conectores | Serviços externos | GitHub, CalDAV/Google Agenda, IMAP/Microsoft Graph, Cloudflare, AWS, Azure, GCP, Oracle |
| 7. Agentes locais | Operações no computador | Serviço privilegiado mínimo `duiaos-agente` via D-Bus + polkit; pacotes via PackageKit |
| 8. Segurança e políticas | Autorizar, limitar, auditar | polkit, níveis N0–N4, cofre de segredos (Secret Service), trilha de auditoria |
| 9. Contexto e memória | Preferências, histórico, conhecimento | SQLite local; busca semântica com índice separado (ex.: sqlite-vec) |
| 10. Observabilidade | Logs, métricas, diagnóstico | journald + logs estruturados; exportação de diagnóstico sem segredos |

Comunicação interna (IPC): **D-Bus**, o padrão do Linux, com controle de
acesso por polkit.

### 3.3 Fluxo de execução de uma tarefa

1. Receber o pedido e identificar objetivo, contexto e restrições.
2. Perguntar só o que faltar.
3. Classificar risco e permissões.
4. Montar o plano e escolher ferramentas e provedor.
5. Mostrar o plano quando a tarefa for complexa ou sensível.
6. Executar por ferramentas autorizadas, sem inventar resultados.
7. Verificar o resultado com evidência real.
8. Relatar o feito, o que falhou e como desfazer.
9. Registrar auditoria.

Estados da tarefa: recebida · esclarecendo · planejada · aguardando
aprovação · executando · verificando · concluída · falhou · cancelada ·
revertida.

### 3.4 Níveis de autonomia

| Nível | Comportamento | Exemplo |
| --- | --- | --- |
| N0 Consultar | Lê e explica | Ler agenda, ver processos |
| N1 Preparar | Monta rascunho, não efetiva | Rascunho de e-mail, plano de atualização |
| N2 Executar com aprovação | Mostra impacto e executa após confirmar | Instalar pacote, enviar mensagem |
| N3 Automação delimitada | Executa dentro de regra já aprovada | Atualizar apps confiáveis à noite |
| N4 Autonomia ampla | Só em ambiente isolado e com limites | Agente de desenvolvimento em contêiner |

Padrão do DuiaOS: N0 e N1 livres; N2 para alterações; N3 só com regra criada
pelo usuário; N4 desativado.

### 3.5 Segurança, privacidade e voz

- Segredos em cofre do sistema, nunca em texto puro, prompts ou logs.
- Conteúdo de páginas, e-mails e documentos é **dado**, nunca instrução
  (defesa contra prompt injection).
- Ler, rascunhar e enviar são permissões separadas.
- Palavra de ativação detectada **localmente**; nada de áudio ou vídeo vai à
  nuvem antes da ativação; indicador visível de microfone e câmera; botão de
  silêncio.
- Botão global para interromper tarefas; cancelamento e reversão quando
  possível.
- Acesso remoto (SSH) desligado por padrão.

### 3.6 A IA é do sistema operacional (ADR 029)

A IA é um **recurso universal do DuiaOS**, como a rede ou o som: pertence ao
sistema, não a um aplicativo. Qualquer programa, recurso ou componente do
sistema pode usá-la pela mesma porta, sem trazer motor, chave ou
configuração próprios. Exceção: aplicativos que são uma IA ou que trazem a
sua IA embarcada.

- **Serviço de IA do sistema** (`duiaos-ia`): reúne os motores (locais e na
  nuvem), as chaves no cofre do sistema, o consentimento para a nuvem, a
  escolha do motor por tarefa, a reserva quando um falha e o controle de
  custo. Os programas falam com ele por D-Bus.
- **Central de IA** (dentro da Central de Configurações, junto do Painel de
  Tecnologias): o único lugar onde a pessoa escolhe motores, cola chaves,
  autoriza a nuvem e vê o uso. Garante independência dos motores.
- **O Wise é um cliente** desse serviço, como qualquer outro programa. As
  configurações dele ficam só no que é dele (comportamento, integração com o
  sistema).
- **Transição:** na W1 o gateway e as configurações de IA ficam dentro do
  Wise, para testar rápido. O gateway do Wise já é escrito como o futuro
  serviço e migra para o `duiaos-ia` antes da W4.

---

## 4. Roadmap consolidado

O plano original (Fases 0–11) vira a **Trilha Plataforma**; o roadmap do
documento de visão vira a **Trilha Wise**. As duas avançam intercaladas.

### 4.1 Trilha Plataforma (P)

| Etapa | Conteúdo | Situação |
| --- | --- | --- |
| P0 Concepção e identidade | Nome, logotipo, paleta, decisões D1–D11 | Concluída |
| P1 Ambiente e automação | Repositório, GitHub Actions, ISOs x86_64/ARM64 | Concluída (v0.0.1) |
| P2 Base instalável | Instalador provisório, Wi-Fi, áudio, dual boot, pt-BR | Concluída (v0.1.0 a publicar) |
| P3 Sessão gráfica | Barra de Recursos, Ilha, Central, Tela de Entrada e de Bloqueio, animação de boot, papel de parede, Menu de Energia | Concluída |
| P3b Pacotes e repositório APT | Código próprio em `.deb` (`duiaos-shell`, `duiaos-identidade`, metapacote `duiaos-desktop`), repositório APT assinado, ISO montada a partir dele (ADRs 023 e 028) | Em teste |
| P4 Instalador próprio | Calamares com identidade DuiaOS, detecção de BitLocker | Planejada |
| P5 Central de Configurações | Rede, tela, som, aparência, usuários — e abriga o Painel de Tecnologias | Planejada |
| P6 Atualizações e loja | Atualizações automáticas sobre o repositório APT da P3b, rollback, loja | Planejada |
| P7 Gravador de pendrive | App próprio para Linux, macOS e Windows | Planejada |

### 4.2 Trilha Wise (W)

| Etapa | Conteúdo | Critério de saída |
| --- | --- | --- |
| W1 Wise textual (MVP) | Janela do Wise, gateway com 1 provedor (desenho multi-provedor), ferramentas de leitura, plano → aprovação → execução → verificação, auditoria, cancelamento | Responde e executa ferramentas simples com logs e resultados verificáveis |
| W2 Operações locais seguras | Diagnóstico de recursos, consulta e aplicação de atualizações, instalar/remover com aprovação | Ações comuns testadas, auditadas e com tratamento de falha |
| W3 Voz e notificações | Palavra de ativação local, fala↔texto, indicador de microfone, modo silencioso | Ativar, interromper, falar e ouvir de forma confiável |
| W4 Central de IA e Painel de Tecnologias | Serviço `duiaos-ia` (IA do sistema, API D-Bus para qualquer programa); Central de IA com motores, chaves, consentimento e custos; contas e permissões; Wise passa a ser cliente | Qualquer programa usa a IA do sistema; trocar de motor sem mexer nos programas |
| W5 Produtividade | Agenda, e-mail, tarefas, notas, rascunhos | Fluxos ponta a ponta sem envio/alteração fora da política |
| W6 Desenvolvimento e nuvem | GitHub, ambientes isolados, nuvens em modo leitura | Leitura e preparação confiáveis; produção exige aprovação |
| W7 Visão | Webcam e tela sob demanda, OCR | Usuário sabe quando a câmera/tela é usada |
| W8 Memória e rotinas | Preferências editáveis, tarefas agendadas, busca em documentos | Rotinas com limites, histórico e desativação |
| W9 Perfis especializados | Professor, tutor, assistente de pesquisa | Progresso real acompanhado, dados sob controle do usuário |

### 4.3 Sequência e versões

| Versão | Entrega |
| --- | --- |
| 0.1 | P2 — instalação no SSD e dual boot |
| 0.2 | P3 completa — o Dell liga direto na interface do DuiaOS |
| 0.3 | W1 — primeiro Wise textual com ferramentas de leitura |
| 0.4 | P4 + W2 — instalador próprio; Wise diagnostica e atualiza com aprovação |
| 0.5 | P5 + W4 — Central de Configurações com Painel de Tecnologias |
| 0.6 | P6 + W3 — atualizações assinadas, loja e voz |
| 0.7–0.9 | P7, W5, W6, testes, segurança, acessibilidade, documentação |
| **1.0 Zoinho** | Plataforma completa + Wise com texto, voz, operações locais, painel e produtividade básica |
| 1.x / 2.0 | W7–W9, compositor próprio, ARM64 em hardware físico |

**Primeiro fluxo ponta a ponta do Wise (W1):** "Como está o meu
computador?" — diagnóstico do sistema e consulta de atualizações, sem
alterações automáticas.

---

## 5. Respostas às questões em aberto do documento de visão

| Questão | Resposta atual |
| --- | --- |
| Stack do release atual | Debian 13, live-build, GitHub Actions; sessão labwc (Wayland); interface Qt6/QML + Python (PySide6) |
| Ambiente gráfico | Shell próprio sobre o labwc na 1.0; compositor próprio na 2.0 |
| Uso pessoal ou público | Produto para usuários finais: código próprio fechado (repositório privado), ISOs públicas no repositório `duiaos-fontes-abertas` |
| Arquiteturas | x86_64 e ARM64 desde o início; referência: Dell Latitude 3420 |
| Hardware mínimo | A definir na estabilização (proposta: 4 GB de RAM, 30 GB de disco, UEFI) |
| Dados locais × nuvem | Local por padrão; envio a provedores só com consentimento e indicação visível |
| Política de atualizações e ações destrutivas | Níveis N0–N4; atualização e remoção exigem aprovação (N2) |
| Integrações prioritárias | 1 provedor de IA + modelo local; depois GitHub e agenda |
| Distribuição de pacotes | Repositório APT próprio assinado (P3b), ISOs nos Releases do repositório público |
| Modelos locais | Via Ollama, conforme o hardware; obrigatórios como opção de privacidade |
| Idiomas e acessibilidade | Português do Brasil na 1.0; inglês depois; teclado, contraste e leitor de tela desde a interface |

---

## 6. Modelo de produto e negócio

- Código próprio (interface, Wise, aplicativos) **proprietário**, em
  repositório privado; usuários finais usam o sistema pelo **EULA**
  (`EULA.md` no `duiaos-fontes-abertas`). Wise e aplicativos distribuídos compilados (Nuitka);
  a parte mais valiosa do Wise roda no servidor.
- Componentes livres de terceiros mantêm as licenças deles; o que a lei exige
  publicar fica no repositório público `duiaos-fontes-abertas` (ADRs 017–019).
- Marcas **DuiaOS**, **Zoinho**, **Wise** e logotipo protegidas
  (`TRADEMARKS.md` no `duiaos-fontes-abertas`; registro no INPI — avaliar o risco do nome Wise
  diante da fintech Wise).
- Colaboradores somente com contrato de cessão de direitos + NDA (ADR 021).
- Edição corporativa futura: serviços, suporte, gestão de frotas e conectores
  corporativos em componentes separados.
- Custos de IA transparentes: o usuário usa os provedores que já paga, os
  gratuitos ou modelos locais; o DuiaOS mostra consumo e limites.

---

## 7. Riscos principais

Escopo excessivo · agente executar ação incorreta · prompt injection ·
dependência de um fornecedor · custos imprevisíveis · integrações que quebram
· desconfiança com microfone/câmera · atualização que falha · promessa maior
que a capacidade. As mitigações seguem o documento de visão (seções 9 e 17) e
são verificadas a cada release.

---

## 8. Documentação e decisões

As decisões de arquitetura ficam em [decisoes.md](decisoes.md). Cada nova
capacidade declara permissões, riscos, limitações, dependências e como
testá-la, e o projeto mantém uma lista explícita do que o DuiaOS ainda não faz
de forma confiável.
