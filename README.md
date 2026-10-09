<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="branding/logo/duiaos-simbolo-escuro.svg">
    <img src="branding/logo/duiaos-simbolo.svg" alt="DuiaOS" width="120">
  </picture>
</p>

<h1 align="center">DuiaOS</h1>

<p align="center">
  Um sistema operacional baseado em Linux: claro, leve e simples de usar,<br>
  feito para quem gosta de entender como a tecnologia funciona.
</p>

<p align="center">
  <a href="https://github.com/gustavoduia/duiaos/actions/workflows/gerar-iso.yml"><img src="https://github.com/gustavoduia/duiaos/actions/workflows/gerar-iso.yml/badge.svg" alt="Gerar ISO"></a>
</p>

---

> **Em desenvolvimento.** A versão 1.0 tem o codinome **Zoinho**.
> As ISOs atuais são de teste e iniciam em modo texto.

## O que é

O DuiaOS usa o kernel Linux e a base do Debian 13 (trixie) por baixo, e tem
interface, aplicativos, instalador e identidade próprios por cima.

- **Arquiteturas:** x86_64 (amd64) e ARM64, com uma ISO para cada em todo release.
- **Para quem:** entusiastas de tecnologia, estudantes, desenvolvedores, gamers
  e empresas que usam software livre.

## Baixar

As ISOs ficam na página de [Releases](https://github.com/gustavoduia/duiaos/releases).
Cada ISO vem com um arquivo `.sha256` para conferir o download:

```bash
sha256sum -c duiaos-VERSAO-amd64.iso.sha256     # Linux
shasum -a 256 -c duiaos-VERSAO-amd64.iso.sha256 # macOS
```

Para criar o pendrive de boot, grave a ISO com o [balenaEtcher](https://etcher.balena.io/)
(o gravador próprio do DuiaOS ainda está em desenvolvimento).

No modo live, o usuário é `duia` e a senha é `live`.

## Gerar a ISO

A ISO é gerada automaticamente pelo GitHub Actions:

- cada envio para a branch `main` gera ISOs de teste, disponíveis na aba **Actions**;
- cada tag `v*` (ex.: `v0.0.1`) gera as ISOs e publica um release.

Para gerar localmente, em uma máquina Linux com Docker:

```bash
sudo docker run --rm --privileged -v "$PWD:/work" -w /work \
  -e ARCH=amd64 debian:trixie bash build/build.sh
```

A ISO sai na pasta `out/`.

## Estrutura do repositório

| Pasta | Conteúdo |
| --- | --- |
| `build/` | Script e configuração do live-build que geram a ISO |
| `build/config/` | Configuração comum a todas as arquiteturas |
| `build/arch/` | Configuração específica de cada arquitetura |
| `shell/` | Interface própria do DuiaOS (Qt6/QML + Python) |
| `apps/` | Aplicativos do DuiaOS |
| `installer/` | Instalador |
| `usb-writer/` | Gravador de pendrive |
| `branding/` | Logotipo, cores e fontes |
| `docs/` | Documentação |

## Licença

O código do DuiaOS é distribuído sob a licença [GNU GPL v3](LICENSE).
Os componentes de terceiros incluídos na ISO (kernel Linux, pacotes do Debian
e outros) mantêm as suas licenças originais.

O nome **DuiaOS** e o logotipo são marcas do projeto e não são cobertos pela
licença do código. Veja [TRADEMARKS.md](TRADEMARKS.md).
