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

> **Repositório interno e confidencial.** Código proprietário do DuiaOS
> ([LICENSE](LICENSE)); não copie nem compartilhe sem autorização. O que é
> público (ISOs, EULA, licenças de terceiros, marca) fica na pasta
> [`publico/`](publico/), espelhada no repositório
> [duiaos-fontes-abertas](https://github.com/gustavoduia/duiaos-fontes-abertas).

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

**Usuários finais**: pessoas sem conhecimento técnico, profissionais,
estudantes e famílias que querem um computador bonito, leve, seguro e simples
de usar — e, no futuro, empresas que precisem do mesmo em escala. O DuiaOS não
é um projeto de comunidade de desenvolvedores.

## Arquiteturas

x86_64 (amd64) e ARM64, com uma ISO para cada em todo release.

## Baixar e instalar

As ISOs públicas ficam nos [Releases do repositório público](https://github.com/gustavoduia/duiaos-fontes-abertas/releases),
cada uma com um arquivo `.sha256` para conferência e a lista de pacotes
(`.packages`):

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

O GitHub Actions coordena e as ISOs são geradas nas nossas máquinas (Mac M4 e
Dell), escolhendo a máquina de cada arquitetura a cada build:

```bash
bash ferramentas/gerar-iso.sh amd64=dell arm64=mac
```

Um envio para a `main` gera a amd64; cada tag `v*` gera as duas e publica o
release no repositório público. ISOs de teste ficam em `~/Projetos/duiaos-isos`
da máquina que gerou. Guia completo: [ferramentas/README.md](ferramentas/README.md)
(ADRs 020 e 024). Localmente, numa máquina Linux com Docker:

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
| `ferramentas/` | Scripts do dia a dia: runners, repositório público, lançar versão |
| `publico/` | Conteúdo do repositório público: EULA, licenças de terceiros, marca, modificações em código livre |

## Licença

O código próprio do DuiaOS é **proprietário, com todos os direitos
reservados** ([LICENSE](LICENSE)). Usuários finais usam o sistema nos termos
do [EULA](publico/EULA.md). Componentes de terceiros mantêm as suas licenças
([publico/LICENCAS-DE-TERCEIROS.md](publico/LICENCAS-DE-TERCEIROS.md)).

As versões publicadas até o commit `d6526e4` (release v0.0.1) foram
distribuídas sob a GPLv3 e continuam assim para quem as obteve.

Regra para dependências novas do código próprio: só licenças permissivas
(MIT, BSD, Apache-2.0, ou LGPL usada de forma dinâmica). Código GPL só como
programa separado. Veja o ADR 019.

Marcas: [publico/TRADEMARKS.md](publico/TRADEMARKS.md).
