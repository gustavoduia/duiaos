# Como trabalhar neste repositório

Este repositório é **interno e confidencial**: contém o código proprietário
do DuiaOS. Só acessa quem foi autorizado pelo titular.

## Quem pode contribuir

Somente colaboradores com **contrato assinado** contendo:

- **cessão dos direitos patrimoniais** sobre o que for criado para o DuiaOS
  (Lei nº 9.609/1998, art. 4º, e Lei nº 9.610/1998);
- **acordo de confidencialidade (NDA)**.

Não há contribuições externas nem CLA público (ADR 021).

## Fluxo

Toda mudança chega por pull request de uma branch (`claude/...` para o
Claude). Só o titular faz o merge na `main` (ADR 022). Passo a passo em
[ferramentas/README.md](ferramentas/README.md).

## Regras para o código

- Dependência nova do código próprio: só licença permissiva (MIT, BSD,
  Apache-2.0, ou LGPL usada de forma dinâmica). Programas GPL (ex.: Piper,
  espeak-ng) só como processo separado, nunca importados ou ligados ao código
  próprio. Na dúvida, pergunte antes (ADR 019).
- Verifique também a licença de **modelos e dados** (ex.: os modelos do
  openWakeWord são CC BY-NC-SA, de uso não comercial).
- Alteração em código livre de terceiros vai para `publico/modificacoes/`,
  sob a licença do original.

## Problemas relatados por usuários

Usuários relatam problemas no repositório público
https://github.com/gustavoduia/duiaos-fontes-abertas/issues. Ao reproduzir,
anote a versão (`cat /etc/os-release`), o computador, a arquitetura e, para
hardware, a saída de `lspci -nn`.
