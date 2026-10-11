<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="branding/logo/duiaos-simbolo-escuro.svg">
    <img src="branding/logo/duiaos-simbolo.svg" alt="DuiaOS" width="120">
  </picture>
</p>

<h1 align="center">DuiaOS</h1>

<p align="center">
  <strong>Você diz o que quer. O DuiaOS descobre como fazer.</strong><br>
  Um sistema operacional baseado no Debian 13, com inteligência artificial nativa,<br>
  para que qualquer pessoa aproveite toda a tecnologia disponível sem precisar dominá-la.
</p>

<p align="center">
  <a href="https://github.com/gustavoduia/duiaos/actions/workflows/gerar-iso.yml"><img src="https://github.com/gustavoduia/duiaos/actions/workflows/gerar-iso.yml/badge.svg" alt="Gerar ISO"></a>
</p>

---

> **Em desenvolvimento.** A versão 1.0 tem o codinome **Zoinho**.
> Já funcionam: instalação (inclusive ao lado do Windows), interface gráfica
> própria com Barra de Recursos, Ilha de Aplicativos e Central de Aplicativos.
> O Wise ainda está em projeto.

## Propósito

Hoje, usar um computador significa saber **qual** programa abrir, **onde**
clicar e **que** comando digitar. O DuiaOS inverte essa lógica: a pessoa
descreve o resultado que deseja — por texto ou por voz — e o sistema
interpreta, planeja, escolhe as ferramentas, executa as ações autorizadas e
explica o que fez.

**Visão:** que qualquer pessoa consiga aproveitar o potencial das tecnologias
digitais avançadas sem precisar dominar sua complexidade técnica.

**Missão:** traduzir objetivos expressos em linguagem natural, voz, texto e
contexto visual em ações úteis, seguras e verificáveis no computador e nos
serviços conectados.

## O Wise

O coração do DuiaOS é o **Wise**: um assistente de texto e voz, disponível
desde o login, ativado pela palavra "Wise". Ele não é um chat solto: é a
camada que transforma pedidos em tarefas, executadas por ferramentas
autorizadas, com permissões, confirmação proporcional ao risco e registro de
tudo o que foi feito.

- *"Wise, atualize meus aplicativos."* — consulta, mostra o que muda, pede
  aprovação, atualiza e confirma o resultado.
- *"Por que o computador está lento?"* — mede CPU, memória e processos e
  explica em linguagem simples.
- *"Coloque na agenda os compromissos que eu disser."* — ouve, organiza,
  mostra para revisão e só então grava.

## Princípios

- **Objetivo antes da ferramenta** — o usuário diz o resultado; o sistema escolhe o caminho.
- **IA agnóstica** — funciona com OpenAI, Gemini, Anthropic, modelos gratuitos e locais.
- **Automação com limites** — permissões claras; ações sensíveis pedem confirmação.
- **Transparência** — o sistema mostra o plano, o que fez e o que falhou.
- **Privacidade por padrão** — microfone, câmera e dados sob controle do usuário; nada sai do computador sem consentimento.
- **Falha segura** — na dúvida, para e pergunta.
- **Acessibilidade** — voz, teclado, leitor de tela e linguagem simples.
- **Evolução incremental** — entregas pequenas, testadas e reversíveis.

## Para quem

Usuários sem conhecimento técnico, profissionais, estudantes, desenvolvedores
e quem administra o próprio computador — e empresas que usam software livre e
querem um sistema bonito, leve, seguro e simples de operar.

## Arquiteturas

x86_64 (amd64) e ARM64, com uma ISO para cada em todo release.

## Baixar e instalar

As ISOs ficam em [Releases](https://github.com/gustavoduia/duiaos/releases),
cada uma com um arquivo `.sha256` para conferência:

```bash
sha256sum -c duiaos-VERSAO-amd64.iso.sha256     # Linux
shasum -a 256 -c duiaos-VERSAO-amd64.iso.sha256 # macOS
```

- Instalar ao lado do Windows: [docs/instalacao-dual-boot.md](docs/instalacao-dual-boot.md)
- No modo live, o usuário é `duia` e a senha é `live`.

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [docs/visao.md](docs/visao.md) | Visão, arquitetura-alvo do Wise e roadmap consolidado |
| [docs/decisoes.md](docs/decisoes.md) | Registro das decisões de arquitetura (ADRs) |
| [docs/instalacao-dual-boot.md](docs/instalacao-dual-boot.md) | Instalação ao lado do Windows, BitLocker e SSH |
| [branding/README.md](branding/README.md) | Logotipo, cores e fontes |

## Gerar a ISO

O GitHub Actions gera as ISOs a cada envio para a `main` (aba **Actions**) e
publica um release a cada tag `v*`. Localmente, numa máquina Linux com Docker:

```bash
sudo docker run --rm --privileged -v "$PWD:/work" -w /work \
  -e ARCH=amd64 debian:trixie bash build/build.sh
```

## Estrutura do repositório

| Pasta | Conteúdo |
| --- | --- |
| `build/` | Geração da ISO (live-build), instalador e ajustes do sistema |
| `shell/` | Interface: Barra de Recursos, Ilha e Central de Aplicativos, sessão |
| `wise/` | O Wise (a criar) |
| `apps/` | Aplicativos do DuiaOS, como a Central de Configurações |
| `installer/` | Instalador próprio (Calamares com a identidade do DuiaOS) |
| `usb-writer/` | Gravador de pendrive |
| `branding/` | Identidade visual |
| `docs/` | Documentação |

## Licença

O código do DuiaOS é distribuído sob a [GNU GPL v3](LICENSE). Componentes de
terceiros incluídos na ISO mantêm suas licenças originais.

O nome **DuiaOS** e o logotipo são marcas do projeto e não são cobertos pela
licença do código. Veja [TRADEMARKS.md](TRADEMARKS.md).
