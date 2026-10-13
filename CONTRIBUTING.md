# Como trabalhar neste repositório

Este repositório contém o código **proprietário** do DuiaOS. Ele está visível
publicamente durante o desenvolvimento (ADR 025), mas só contribui quem foi
autorizado pelo titular. Pull requests de terceiros não são aceitos.

## Quem pode contribuir

Somente colaboradores com **contrato assinado** contendo:

- **cessão dos direitos patrimoniais** sobre o que for criado para o DuiaOS
  (Lei nº 9.609/1998, art. 4º, e Lei nº 9.610/1998);
- **acordo de confidencialidade (NDA)**.

Não há contribuições externas nem CLA público (ADR 021).

## Fluxo

Todo o trabalho é feito direto na branch `main`, sem branches nem pull
requests (ADR 043). Instruções para quem desenvolve: [CLAUDE.md](CLAUDE.md) e
[docs/continuidade/](docs/continuidade/).

## Regras para o código

- Dependência nova do código próprio: só licença permissiva (MIT, BSD,
  Apache-2.0, ou LGPL usada de forma dinâmica). Programas GPL (ex.: Piper,
  espeak-ng) só como processo separado, nunca importados ou ligados ao código
  próprio. Na dúvida, pergunte antes (ADR 019).
- Verifique também a licença de **modelos e dados** (ex.: os modelos do
  openWakeWord são CC BY-NC-SA, de uso não comercial).
- Alteração em código livre de terceiros vai para o repositório
  [duiaos-fontes-abertas](https://github.com/gustavoduia/duiaos-fontes-abertas)
  (`modificacoes/`), sob a licença do original.

## Problemas relatados por usuários

Usuários relatam problemas no repositório público
https://github.com/gustavoduia/duiaos-fontes-abertas/issues. Ao reproduzir,
anote a versão (`cat /etc/os-release`), o computador, a arquitetura e, para
hardware, a saída de `lspci -nn`.
