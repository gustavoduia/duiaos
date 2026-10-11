# Licenças de terceiros e código-fonte

O DuiaOS é construído sobre software livre. Este documento diz quais são os
principais componentes de terceiros, sob quais licenças estão e como obter o
código-fonte de cada um.

## Componentes principais

| Componente | Licença | Observação |
| --- | --- | --- |
| Kernel Linux | GPL-2.0 | Pacote do Debian, sem modificações |
| Pacotes do Debian 13 (trixie) | Diversas (GPL, LGPL, MIT, BSD, Apache…) | Sem modificações |
| GRUB | GPL-3.0 | Pacote do Debian; o tema visual é do DuiaOS |
| debian-installer | GPL-2.0 e outras | Configurado por arquivo de respostas (preseed) |
| labwc (compositor Wayland) | GPL-2.0 | Sem modificações; executado como processo separado |
| Qt 6 e LayerShellQt | LGPL-3.0 | Bibliotecas usadas de forma dinâmica |
| PySide6 | LGPL-3.0 | Biblioteca usada de forma dinâmica |
| Inter, Manrope, JetBrains Mono | SIL Open Font License 1.1 | Fontes tipográficas |

A lista completa de pacotes de cada versão, com as versões exatas, é publicada
junto com a ISO no arquivo `duiaos-VERSÃO-ARQUITETURA.packages`. No sistema
instalado, a licença de cada pacote está em `/usr/share/doc/PACOTE/copyright`.

## Como obter o código-fonte

- **Pacotes do Debian:** em um DuiaOS ou Debian, `apt source NOME-DO-PACOTE`;
  ou em https://sources.debian.org. As versões exatas de uma ISO podem ser
  baixadas em https://snapshot.debian.org.
- **Modificações feitas pelo DuiaOS em software livre de terceiros:** pasta
  `modificacoes/` do repositório https://github.com/gustavoduia/duiaos-fontes-abertas.
  Até esta versão não há nenhuma modificação.

## Oferta por escrito de código-fonte

Por no mínimo três anos após a distribuição de cada versão do DuiaOS, o
titular do DuiaOS fornece, a quem pedir, uma cópia completa do código-fonte
correspondente de todos os componentes licenciados sob a GPL ou a LGPL
incluídos naquela versão, em meio digital, cobrando no máximo o custo de
fazer a cópia. Pedidos: abra uma issue em
https://github.com/gustavoduia/duiaos-fontes-abertas/issues informando a
versão e a arquitetura da ISO. **[A DEFINIR: e-mail de contato oficial.]**

## O que não é software livre

A interface, o assistente Wise, os aplicativos, scripts, configurações e a
identidade visual criados para o DuiaOS são software proprietário, regidos
pelo [Contrato de Licença de Usuário Final](EULA.md).
