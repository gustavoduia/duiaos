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
| greetd (gerenciador de login) | GPL-3.0 | Sem modificações; executado como processo separado |
| cage (compositor da Tela de Entrada) | MIT | Sem modificações; executado como processo separado |
| Plymouth (animação de boot) | GPL-2.0 | Pacote do Debian; o tema visual é do DuiaOS |
| swayidle e swaylock | MIT | Sem modificações; executados como processos separados |
| python-pamela | MIT | Biblioteca usada pela Tela de Bloqueio para conferir a senha |
| Qt 6 e LayerShellQt | LGPL-3.0 | Bibliotecas usadas de forma dinâmica |
| PySide6 | LGPL-3.0 | Biblioteca usada de forma dinâmica |
| Inter, Manrope, JetBrains Mono | SIL Open Font License 1.1 | Fontes tipográficas |
| Ollama (pacote `duiaos-ollama`) | MIT | Binários oficiais, sem modificações e sem as bibliotecas CUDA; executado como serviço separado |
| llama.cpp / ggml, cpp-httplib, fmt, MLX | MIT | Trazidos pelo release do Ollama (`/usr/lib/ollama/*LICENSE`) |
| XGrammar, DLPack | Apache-2.0 | Trazidos pelo release do Ollama |
| Go (biblioteca padrão), PicoJSON | BSD | Trazidos pelo release do Ollama |
| libgomp / libomp | GPL-3.0 com exceção de runtime do GCC / Apache-2.0 com exceção LLVM | Bibliotecas de execução paralela usadas de forma dinâmica pelo Ollama |

### Modelos de IA

Nenhum modelo de IA vem dentro da ISO. Os modelos são baixados da biblioteca
do Ollama quando a pessoa usa o DuiaOS (o padrão, Qwen3.5 4B, no primeiro
login), e cada um tem a sua própria licença, mostrada antes do download.
Qwen e Gemma usam Apache-2.0 e Phi usa MIT. Os modelos Llama usam a Llama
Community License da Meta, que não é uma licença livre e tem regras de uso
próprias: são opcionais e só baixados quando a pessoa escolhe.

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
