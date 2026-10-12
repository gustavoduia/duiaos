# Pacotes do DuiaOS (P3b, ADRs 023 e 028)

O código próprio do DuiaOS é distribuído em pacotes `.deb` (todos
`Architecture: all`: servem para x86_64 e ARM64).

| Pacote | Conteúdo |
| --- | --- |
| `duiaos-identidade` | os-release, `/etc/issue` e `/etc/motd`, animação de boot (Plymouth), tema do menu de boot (GRUB), papel de parede, teclado ABNT2, scripts de `/usr/lib/duiaos`, licença (EULA) e o repositório apt (chave e canal) |
| `duiaos-shell` | Interface (`shell/` → `/usr/share/duiaos/shell`), configuração do labwc (`/etc/xdg/labwc`), Tela de Entrada (greetd), Menu de Energia (serviço e regra do polkit), PAM da Tela de Bloqueio. Dependências: `shell/pacotes.list` |
| `duiaos-desktop` | Metapacote: instala e mantém os dois acima |

## Arquivos desta pasta

| Arquivo | O que faz |
| --- | --- |
| `NOME/raiz/` | Arquivos do pacote, no lugar onde ficam no sistema |
| `NOME/DEBIAN/` | `control` e scripts de instalação (`postinst`, `postrm`); `@VERSAO_DEB@`, `@VERSAO_SISTEMA@` e `@DEPENDENCIAS_SHELL@` são trocados na geração |
| `construir.sh` | Gera os três `.deb` (usado pela ISO e pelo workflow `pacotes.yml`) |
| `versao.sh` | Versão e canal: tag `vX.Y.Z` → `X.Y.Z` no canal `estavel`; commit → `X.Y.Z+gitDATA.SHA` no canal `teste` |
| `publicar.sh` | Monta o repositório apt assinado (mantém as 5 versões mais novas de cada pacote) |
| `instalar-local.sh` | Gera e instala os pacotes desta pasta no próprio computador (testar uma branch no Dell) |
| `site/index.html` | Página inicial do site do repositório |

## Repositório apt

- Endereço: `https://gustavoduia.github.io/duiaos-fontes-abertas/apt`
  (branch `gh-pages` do repositório público, servida pelo GitHub Pages).
- Canais: `estavel` (versões lançadas) e `teste` (cada envio para a `main`).
- Assinado com a chave do segredo `DUIAOS_APT_CHAVE`
  (`ferramentas/criar-chave-apt.sh`). A chave pública vai dentro do
  `duiaos-identidade` (`/usr/share/keyrings/duiaos.gpg`) e no site
  (`apt/duiaos.asc`).
- O sistema instalado pela ISO já sai com o repositório ligado
  (`/usr/lib/duiaos/configurar-repositorio`, chamado pelo `pos-instalacao`).
  Atualizar: `sudo apt update && sudo apt full-upgrade`.

## Regras

- Arquivo novo do sistema entra em `NOME/raiz/`, nunca mais em
  `build/config/includes.chroot_after_packages` (pasta removida).
- Unidades do systemd em `/usr/lib/systemd/system`; regras do polkit em
  `/usr/share/polkit-1/rules.d`. Tudo o que fica em `/etc` vira arquivo de
  configuração (o dpkg preserva as mudanças da pessoa).
- Nada de labwc ou outro pacote do Debian modificado (ADR 027).
