# Ora — Inventário de recursos entregues (não pode regredir)

Mora no `duiaos` (ADR 043, 073) e confere os arquivos do repositório `duiaos-ora`, clonado ao lado
(`python3 ferramentas/conferir-recursos.py` no `duiaos`). Mesmas regras do `RECURSOS.md`: cada linha tem uma
conferência `arquivo::texto que só a versão atual tem`; recurso novo ou mudado → linha nova ou atualizada no mesmo envio.

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Ora, o navegador: abas, barra de endereço com sugestões e buscador escolhido (Google por padrão), nova aba, favoritos (barra, pastas, importar do Chrome/Firefox/HTML, exportar), histórico com busca, downloads, configurações, janela privada, popups de login, permissões por site, tela cheia, PDF, ferramentas do desenvolvedor, menus na Barra, um processo por pessoa | `ora/`, `pacote/` | `ora/main.py::NOME_SOQUETE`, `ora/JanelaOra.qml::function pedidoDeJanela`, `ora/dados.py::def ler_firefox`, `ora/endereco.py::_EXTENSOES`, `ora/endereco.py::BUSCADOR_PADRAO = "google"`, `ora/BarraDeEndereco.qml::Buscar ou digitar um endereço`, `testes/test_ora.py::TestTelasDoOra` | ADR 072 | main |
| Motor web do DuiaOS à frente do PySide6 do sistema, só no processo do Ora | `ora/main.py` | `ora/main.py::DUIAOS_MOTOR_WEB` | ADR 072 | main |
| Modo aplicativo: um site numa janela própria, sem abas nem barra (WhatsApp Web do instalador) | `ora/main.py`, `ora/JanelaOra.qml` | `ora/main.py::--aplicativo https://SITE`, `ora/JanelaOra.qml::property bool modoAplicativo` | ADR 073 | main |
| Pacote duiaos-ora, navegador do sistema (x-www-browser) | `pacote/` | `pacote/construir.sh::NOME=duiaos-ora`, `pacote/DEBIAN/postinst::x-www-browser`, `pacote/raiz/usr/share/applications/duiaos-ora.desktop::x-scheme-handler/https` | ADR 073 | main |
