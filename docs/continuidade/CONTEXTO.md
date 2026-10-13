# DuiaOS — Contexto permanente do projeto

Muda pouco. Vale para qualquer pessoa ou conta do Claude que trabalhe no
projeto. Ordem de leitura no início de toda sessão: a **memória dos chats**
(`duiaos-wise/docs/memoria-dos-chats/`, privada, todos os arquivos) → `CLAUDE.md` → este arquivo
→ `ESTADO.md` → `RECURSOS.md` (e, no Wise e no site, os equivalentes em
`duiaos-wise/docs/continuidade/` e `duiaos-websites/docs/continuidade/`).

## Pessoas e forma de trabalho
- Dono: **Gustavo** (GitHub `gustavoduia`), fuso America/Sao_Paulo. Decide tudo e dá nome a todo componente
  visível. Pode haver um segundo programador com outra conta do Claude (ver "Várias contas").
- O Claude atua como arquiteto + engenheiro: guia, propõe e entrega; quem executa e testa no hardware é a pessoa.
- Regras: objetividade e economia de tokens; NÃO testar em VM no ambiente do Claude (testes no Dell ou no UTM);
  investigar a causa raiz antes de propor correção; nada de correção paliativa (corrigir na ISO/pacote);
  no teclado do Dell não dá para colar texto; **medir antes de afirmar ganho de desempenho**.
- Entregas sempre com passo a passo e comandos completos para copiar e colar.
- Duas janelas abertas o tempo todo: Terminal do Mac + uma sessão SSH já conectada ao Dell.
  **Todo bloco de comando leva, logo acima, uma destas marcas:**
  - 🍎 **MAC** — Terminal do Mac.
  - 🔗 **DELL (sessão SSH)** — comando puro, SEM `ssh ...` na frente (nunca escrever `ssh gustavo@duiaos '...'`).
  - 💻 **DELL LOCAL** — teclado do próprio Dell (só boot, reiniciar, tela; comandos curtos).
  Scripts de `ferramentas/` rodam no Mac, exceto os que dizem "Onde rodar: 🔗 DELL"
  (`pacotes/instalar-local.sh`, `ferramentas/medir-motores.py` e, no Wise, `pacote/instalar-local.sh`).
  Não misturar máquinas num bloco. Depois de `sudo reboot` a sessão SSH cai: avisar para reconectar.
- Fluxo (ADR 022): branch `claude/...` + pull request (`add_repo` com push). Merge só pelo Gustavo, por **squash**
  (`gh pr merge N --squash --delete-branch`). Ninguém além dele envia para a `main`.
- Atualizar o Dell: `sudo apt update && sudo apt full-upgrade` (canal teste). Testar branch antes do merge:
  `bash pacotes/instalar-local.sh` (duiaos) e `bash pacote/instalar-local.sh` (Wise, que não está no apt).
- SSH Mac→Dell por chave. `gh` no ambiente do Claude só via REST (GraphQL bloqueado).
- Termos da IA (sempre assim): **motor** = Ollama; **modelo** = Qwen3.5 4B etc.; **modelo ativo** = o único em uso
  no sistema; **IA do sistema** = serviço `duiaos-ia`. Llama ≠ Ollama.

## Várias contas do Claude (decisão de 12/10/2026)
- **A fonte da verdade é o Git**, não a memória de uma conta: tudo o que precisa sobreviver entre sessões e entre
  contas fica em `docs/continuidade/` (duiaos, público) e `duiaos-wise/docs/continuidade/` (Wise, privado).
- O Project "DuiaOS" do claude.ai é só um atalho da conta do Gustavo: os arquivos dele apontam para cá.
- Para um segundo programador: convite de colaborador nos dois repositórios (o Wise é privado; antes, contrato de
  cessão de direitos + NDA — ADR 021), GitHub conectado na conta Claude dele; ele começa a sessão pedindo
  "Continuar o DuiaOS" e o Claude lê os arquivos na ordem acima.
- Trabalho em paralelo: cada frente numa branch própria e com **PR em rascunho aberto logo no início** (é o aviso
  de "isto está em andamento"); `ESTADO.md` diz quem está em qual frente. Nunca duas pessoas na mesma branch.
- Commits identificam a conta/pessoa (autor do git + linha `Claude-Session`).

## Repositórios e fases (ADRs 018, 025 e 028)
- `gustavoduia/duiaos`: código proprietário (LICENSE "todos os direitos reservados"). **Fase atual: PÚBLICO**.
  Fase final: volta a PRIVADO e o build passa a ser local. Não colocar aqui nada do código do Wise.
- `gustavoduia/duiaos-fontes-abertas` (público): espelho de `publico/`, ISOs nos Releases e, na branch gh-pages,
  o repositório apt (https://gustavoduia.github.io/duiaos-fontes-abertas/apt).
- `gustavoduia/duiaos-websites` (PRIVADO): site (`site/`, duiaos.gustavoduia.workers.dev) e documentação
  (`documentacao/`, duiaos-docs.gustavoduia.workers.dev); com domínio: duiaos.com.br e docs.duiaos.com.br.
  Mudança visível no sistema ou no Wise = PR irmão lá (ADR 039).
- `gustavoduia/duiaos-diagnosticos` (PRIVADO): relatórios de "Ajude a melhorar o DuiaOS" de todos os
  computadores (ADR 040). Dados pessoais: nada dele vai para repositórios públicos.
- `gustavoduia/duiaos-wise` (PRIVADO): o Wise. O público só conhece `/usr/bin/duiaos-wise --alternar` e
  `duiaos-wise.desktop`; o Wise só lê `/var/lib/duiaos-ia/estado.json`. Dell acessa por deploy key
  (Host github-duiaos-wise).
- Enquanto `duiaos` for público: runners próprios PAUSADOS; o workflow recusa mac/dell.

## Pastas padrão (ADR 024) — iguais no Mac e no Dell
`~/Projetos/duiaos` · `~/Projetos/duiaos-wise` · `~/Projetos/duiaos-fontes-abertas` (só leitura) ·
`~/Projetos/duiaos-isos` · `~/Projetos/duiaos-runner` · Mac: `~/Projetos/duiaos-chaves` (chave privada do apt).
`~/Projetos/duiaos-websites`. Mac = /Users/gustavoduia/Projetos; Dell = /home/gustavo/Projetos.

## Máquinas
- Mac: MacBook Air M4 16 GB. Runner `mac-m4` (Colima), só arm64.
- Dell Latitude 3420 (teste + runner `dell-latitude`): i5-1135G7 (4 núcleos, AVX-512 VNNI), 16 GB (3200 + 2667 →
  roda a 2667; upgrade do pente fica para depois, decisão do Gustavo), NVMe 240 GB, Wi-Fi AX201, Ethernet RTL8168,
  Iris Xe (Vulkan), áudio SOF. Dual boot com Windows (BitLocker). Hostname `duiaos`, usuário `gustavo`.
  IA: Ollama + Qwen3.5 4B na Iris Xe (escrever ~8 pedaços/s com 100 pedaços).

## Produto
- DuiaOS: SO baseado em Debian 13 trixie, x86_64 + ARM64. Codinome da 1.0: **Zoinho** (homenagem ao pai).
- Público: **usuários finais**. Bonito, leve, simples, seguro.
- IA nativa: assistente **Wise** — "o cérebro do DuiaOS": vai embarcado e instalado com o sistema, na ISO e no
  apt (decisão do Gustavo, ADR 042); nunca propor o DuiaOS sem ele. Aparece só após o login; a IA é do sistema operacional (ADR 029): serviço `duiaos-ia`
  + Central de IA; um só modelo ativo (ADR 030); o Wise é cliente. Motor: **Ollama** (mantido em 12/10 após
  medição; ADR 036).
- Site e documentação para usuários: repositório privado `duiaos-websites` (ADRs 037–039).
- O Wise usa o computador como a pessoa (12/10): "o Wise é soberano no sistema" — com aprovação para enviar,
  apagar, pagar, instalar ou confirmar.
- Nomes já definidos: Barra de Recursos (painel), Ilha de Aplicativos (dock), Central de Aplicativos (lançador),
  Tela de Entrada e Tela de Bloqueio (mesmo visual), Menu de Energia, Central de IA.
- Identidade: paleta clara azul (#1A3A73, #2E6BE6, fundo #E8F0FE), logo "Órbita", fontes Inter/Manrope/
  JetBrains Mono, papel de parede "Órbita". Wise: carinha de robô alegre (aberto/feliz/pensando/descansando).

## Licença (decisão de 11/10/2026)
- Tudo o que o DuiaOS desenvolve é **proprietário**, mesmo com o repositório visível. Aberto só o obrigatório
  (componentes de terceiros e modificações em código GPL de terceiros → `publico/modificacoes/`).
- Versões publicadas sob GPLv3 (até o commit d6526e4 / v0.0.1) continuam GPL para quem as obteve.
- Dependências do código próprio: só licença permissiva (MIT/BSD/Apache/LGPL dinâmico); vale para modelos de IA
  e serviços de dados (ex.: previsão do tempo com uso comercial permitido).
- Colaboradores: contrato com cessão de direitos + NDA (não CLA público).

## Arquitetura técnica
- ISO: live-build no GitHub Actions; instala os .deb do mesmo commit. `bash ferramentas/gerar-iso.sh`.
- Pacotes (`pacotes/`): duiaos-identidade, duiaos-shell, duiaos-ia, duiaos-agente, duiaos-relatorios,
  duiaos-desktop (all) e
  duiaos-ollama (por arquitetura). Arquivo novo do sistema vai em `pacotes/NOME/raiz/`.
- Interface: labwc (Debian sem modificações — ADR 027) + Qt6/QML + Python (PySide6), LayerShellQt, wlrctl.
  Login: greetd + cage (ADR 026). Painéis layer-shell NÃO podem vazar QT_WAYLAND_SHELL_INTEGRATION para filhos.
- IA: `ia/` (serviço Python + Gio, polkit com anotação owner), `apps/central-de-ia/`.
- Agente: `agente/` (duiaos-agente, ADR 034).
- Registros: `relatorios/` (biblioteca `duiaos_registro` usada por todos os programas + coletor
  `duiaos-relatorios`; journal persistente; ADR 040).
- Documentação técnica: `docs/visao.md`, `docs/decisoes.md` (ADRs), `pacotes/README.md`, `shell/README.md`,
  `ia/README.md`. Documentação para usuários e site: `duiaos-websites` (guia em `duiaos-websites/CLAUDE.md`).
- Cloudflare (conta do Gustavo): Workers `duiaos` e `duiaos-docs`, D1 `duiaos-site`, KV `duiaos-site-cache`.
