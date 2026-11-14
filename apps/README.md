# Aplicativos do DuiaOS

Aplicativos próprios do DuiaOS. Todos usam a biblioteca QML `import DuiaOS` e os
módulos de `shell/comum/` (ADR 044).

| Pasta | Aplicativo | Pacote |
| --- | --- | --- |
| `central-de-ia/` | **Central de IA**: modelo de IA ativo do sistema, download e remoção de modelos (ADR 030) | `duiaos-ia` |
| `explorador-de-arquivos/` | **Explorador de Arquivos**: pastas, aplicativos, discos e Lixeira; ícones ou lista; copiar, mover, renomear, busca, Abrir com (ADR 044) | `duiaos-shell` |
| `loja/` | **Duia App Store**: Descobrir, categorias, busca, página do aplicativo, Instalados e Atualizações; aplicativos do Flathub (flatpak --user) e do Debian (pelo duiaos-agente) (ADR 049) | `duiaos-shell` |
| `configuracoes/` | **Configurações**: Wi-Fi, Bluetooth, Som, Tela, Energia, Papel de parede, Barra e Ilha, Usuário e senha, Data e hora, Teclado, Aplicativos padrão, Privacidade, IA, Sobre (ADR 044) | `duiaos-shell` |
| `ajude-a-melhorar/` | **Ajude a melhorar o DuiaOS** (ADR 041) | `duiaos-relatorios` |
