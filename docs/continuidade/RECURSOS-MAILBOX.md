# Mail Box — Inventário de recursos entregues (não pode regredir)

Mora no `duiaos` (ADR 043, 073) e confere os arquivos do repositório `duiaos-mailbox`, clonado ao lado
(`python3 ferramentas/conferir-recursos.py` no `duiaos`). Mesmas regras do `RECURSOS.md`: cada linha tem uma
conferência `arquivo::texto que só a versão atual tem`; recurso novo ou mudado → linha nova ou atualizada no mesmo envio.

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Mail Box, o e-mail: wizard com catálogo de provedores e descoberta (MX, ISPDB, autoconfig, SRV), IMAP, POP3 e SMTP, caixa unificada, busca, leitura segura (imagens externas bloqueadas), escrever/responder/encaminhar com anexos, mover, Lixeira, notificações, mailto:, senhas no cofre | `mailbox/`, `pacote/` | `mailbox/autoconfig.py::RFC 6186`, `mailbox/provedores.py::myaccount.google.com/apppasswords`, `mailbox/mensagem.py::Content-Security-Policy`, `mailbox/sincronizador.py::uidvalidity`, `mailbox/cofre.py::Secret Service`, `mailbox/Wizard.qml::Configurar manualmente` | ADR 072 | main |
| Laboratório de e-mail para testes (Dovecot com IMAP, IMAPS e POP3 e SMTP com login, em 127.0.0.1) | `testes/laboratorio_email.py`, `testes/test_mailbox.py` | `testes/laboratorio_email.py::class Laboratorio`, `testes/test_mailbox.py::TestMotorContraServidoresReais` | ADR 072 | main |
| Pacote duiaos-mailbox, programa de e-mail do sistema (mailto) | `pacote/` | `pacote/construir.sh::NOME=duiaos-mailbox`, `pacote/raiz/usr/share/applications/duiaos-mailbox.desktop::x-scheme-handler/mailto` | ADR 073 | main |
