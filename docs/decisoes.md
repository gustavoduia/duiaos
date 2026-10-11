# Registro de decisões de arquitetura (ADRs)

Cada decisão: contexto, decisão, consequência e data. Status: **aceita**
(em uso), **proposta** (a confirmar antes de implementar) ou **substituída**.

| # | Decisão | Status | Data | Contexto e consequência |
| --- | --- | --- | --- | --- |
| 001 | Base Debian 13 (trixie) com live-build | Aceita | 09/10/2026 | Estável, gratuito, suporte ao hardware; ISO reproduzível por script |
| 002 | Shell próprio sobre labwc na 1.0; compositor próprio na 2.0 | Aceita | 09/10/2026 | Interface original sem reescrever o servidor gráfico no início |
| 003 | Interface em Qt6/QML + Python (PySide6) | Aceita | 09/10/2026 | Visual livre, roda igual em x86_64 e ARM64; C++ só onde houver necessidade de desempenho |
| 004 | x86_64 e ARM64 desde o início | Aceita | 09/10/2026 | GitHub Actions gera as duas ISOs; ARM64 testado em VM no Mac |
| 005 | Licença GPLv3 + marca protegida + CLA | Substituída (017, 021) | 09/10/2026 | Mantém aberta a opção de edição corporativa |
| 006 | Repositório público no GitHub; ISOs nos Releases | Substituída (018) | 09/10/2026 | Actions gratuito; ISO abaixo de 2 GiB |
| 007 | Instalador provisório (debian-installer live) até o Calamares | Aceita | 09/10/2026 | Pós-instalação grava repositórios, idioma, teclado e SSH |
| 008 | Secure Boot ligado (shim e GRUB assinados) | Aceita | 11/10/2026 | Evita desligar o Secure Boot, o que dispara BitLocker e invalida o PIN do Windows |
| 009 | Dual boot: Windows no menu (os-prober) e "Reiniciar no Windows" via firmware | Aceita | 11/10/2026 | Ir ao Windows pelo firmware evita pedidos da chave do BitLocker |
| 010 | SSH desligado por padrão; chaves próprias por instalação | Aceita | 11/10/2026 | Padrão de mercado (Windows, macOS); privacidade por padrão |
| 011 | Wise como orquestrador de tarefas com ferramentas tipadas, nunca shell livre | Aceita | 11/10/2026 | Segurança: a IA planeja, código determinístico autoriza e executa |
| 012 | IPC por D-Bus, autorização por polkit, pacotes via PackageKit | Proposta | 11/10/2026 | Padrões do Linux; a confirmar no início da W1/W2 |
| 013 | Serviço de usuário `duiaos-wise` + serviço privilegiado mínimo `duiaos-agente` | Proposta | 11/10/2026 | Menor privilégio: o processo que fala com a IA não roda como root |
| 014 | Gateway multi-modelo (OpenAI, Anthropic, Gemini, Ollama local) | Proposta | 11/10/2026 | Evita dependência de um fornecedor; modelo local como opção de privacidade |
| 015 | Armazenamento local em SQLite; segredos no cofre do sistema (Secret Service) | Proposta | 11/10/2026 | Transacional, simples de migrar; nenhuma chave em texto puro |
| 016 | Voz local: palavra de ativação, fala↔texto e TTS no próprio computador | Proposta | 11/10/2026 | Nada de áudio vai à nuvem antes da ativação |
| 017 | Código próprio proprietário (todos os direitos reservados); usuários finais pelo EULA | Aceita | 11/10/2026 | Protege o Wise e a interface; até o commit d6526e4 (v0.0.1) o código continua GPLv3 para quem o obteve |
| 018 | Repositório principal privado; repositório público `duiaos-fontes-abertas` com ISOs, EULA, licenças de terceiros e modificações em código livre | Aceita | 11/10/2026 | Cumpre as licenças livres sem expor o código próprio; a pasta `publico/` é a fonte da verdade do repositório público |
| 019 | Dependências do código próprio só com licença permissiva (MIT, BSD, Apache-2.0, LGPL dinâmica); GPL só como processo separado | Aceita | 11/10/2026 | Evita obrigação de abrir o código próprio; vale também para modelos e dados de IA |
| 020 | CI com runners próprios: Mac M4 (`duiaos-mac`) e Dell (`duiaos-dell`); a máquina de cada arquitetura é escolhida a cada build (mac, dell, github ou não gerar); padrão amd64 no Dell e arm64 no Mac; arquitetura estrangeira roda emulada (Rosetta no Mac, QEMU no Dell); push na `main` gera só amd64; tag gera as duas e publica no repositório público | Aceita | 11/10/2026 | Sem custo de minutos (a taxa de runner próprio anunciada pelo GitHub foi adiada); ISOs de teste ficam em `~/Projetos/duiaos-isos` da máquina, porque a cota de armazenamento de repositório privado não comporta ISOs |
| 021 | Colaboradores só com contrato de cessão de direitos + NDA (substitui o CLA) | Aceita | 11/10/2026 | Sem contribuições externas; titularidade do código fica com o DuiaOS |
| 022 | Fluxo de trabalho: Claude envia branch `claude/...` + pull request; Gustavo revisa e faz o merge; ninguém além do Gustavo envia para a `main` | Aceita | 11/10/2026 | Elimina baixar e aplicar patches; toda mudança fica revisável |
| 023 | Código próprio empacotado em `.deb` num repositório APT próprio e assinado, logo após a P3 (antes previsto na P6) | Aceita | 11/10/2026 | Atualizações pelo apt sem reinstalar; licença declarada por pacote; build de pacote em segundos em vez de ISO |
| 024 | Pastas padrão iguais no Mac e no Dell: `~/Projetos/{duiaos, duiaos-fontes-abertas, duiaos-isos, duiaos-runner}` | Aceita | 11/10/2026 | Tudo do projeto num só lugar; scripts e workflow usam os mesmos caminhos nas duas máquinas |
