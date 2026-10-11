# Registro de decisões de arquitetura (ADRs)

Cada decisão: contexto, decisão, consequência e data. Status: **aceita**
(em uso), **proposta** (a confirmar antes de implementar) ou **substituída**.

| # | Decisão | Status | Data | Contexto e consequência |
| --- | --- | --- | --- | --- |
| 001 | Base Debian 13 (trixie) com live-build | Aceita | 09/10/2026 | Estável, gratuito, suporte ao hardware; ISO reproduzível por script |
| 002 | Shell próprio sobre labwc na 1.0; compositor próprio na 2.0 | Aceita | 09/10/2026 | Interface original sem reescrever o servidor gráfico no início |
| 003 | Interface em Qt6/QML + Python (PySide6) | Aceita | 09/10/2026 | Visual livre, roda igual em x86_64 e ARM64; C++ só onde houver necessidade de desempenho |
| 004 | x86_64 e ARM64 desde o início | Aceita | 09/10/2026 | GitHub Actions gera as duas ISOs; ARM64 testado em VM no Mac |
| 005 | Licença GPLv3 + marca protegida + CLA | Aceita | 09/10/2026 | Mantém aberta a opção de edição corporativa |
| 006 | Repositório público no GitHub; ISOs nos Releases | Aceita | 09/10/2026 | Actions gratuito; ISO abaixo de 2 GiB |
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
