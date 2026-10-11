<!--
  Este arquivo é o README do repositório público
  https://github.com/gustavoduia/duiaos-fontes-abertas.
  A fonte da verdade é a pasta publico/ do repositório interno (privado).
  O workflow sincronizar-publico.yml copia a pasta para cá a cada mudança.
-->

<p align="center">
  <img src="https://raw.githubusercontent.com/gustavoduia/duiaos-fontes-abertas/main/logo/duiaos-simbolo.svg" alt="DuiaOS" width="120">
</p>

<h1 align="center">DuiaOS</h1>

<p align="center">
  <strong>Você diz o que quer. O DuiaOS descobre como fazer.</strong><br>
  Um sistema operacional baseado no Debian 13, com inteligência artificial nativa.
</p>

---

> **Em desenvolvimento.** A versão 1.0 terá o codinome **Zoinho**.

Este repositório reúne o que o DuiaOS publica abertamente:

- as **ISOs** de cada versão, na aba [Releases](https://github.com/gustavoduia/duiaos-fontes-abertas/releases);
- o [Contrato de Licença de Usuário Final](EULA.md);
- as [licenças de terceiros e como obter o código-fonte](LICENCAS-DE-TERCEIROS.md);
- as modificações feitas pelo DuiaOS em software livre de terceiros (`modificacoes/`);
- a política de uso da [marca](TRADEMARKS.md).

O código próprio do DuiaOS (interface, Wise e aplicativos) é proprietário e
não está neste repositório.

## Baixar e instalar

Cada ISO vem com um arquivo `.sha256` para conferência:

```bash
sha256sum -c duiaos-VERSAO-amd64.iso.sha256     # Linux
shasum -a 256 -c duiaos-VERSAO-amd64.iso.sha256 # macOS
```

Há uma ISO para computadores comuns (x86_64, `amd64`) e outra para ARM64.
No modo live, o usuário é `duia` e a senha é `live`.

## Problemas e sugestões

Use a aba [Issues](https://github.com/gustavoduia/duiaos-fontes-abertas/issues)
e informe a versão (`cat /etc/os-release`), o computador e o que aconteceu.
