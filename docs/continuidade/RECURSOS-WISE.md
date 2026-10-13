# Wise — Inventário de recursos entregues (não pode regredir)

Mora no `duiaos` (ADR 043) e confere os arquivos do repositório `duiaos-wise`, clonado ao lado
(`python3 ferramentas/conferir-recursos.py` no `duiaos`; nos testes do Wise também). Mesmas regras do
`RECURSOS.md`: cada linha tem uma conferência `arquivo::texto que só a versão atual tem`; recurso novo ou mudado →
linha nova ou atualizada no mesmo envio.

## Presença e visual

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Carinha de robô alegre (aberto, feliz, pensando, descansando; pisca, olha em volta, pulinho) | `wise/interface/Carinha.qml` | `wise/interface/Carinha.qml::a carinha de robô do botão flutuante`, `wise/interface/Carinha.qml::function pular()` | W10 | main |
| Reticências de "pensando" sem redesenhar a tela (não disputa o processador) | `wise/interface/Carinha.qml` | `wise/interface/Carinha.qml::Reticências de "pensando"` | W12 | main |
| Balão animado: saudação digitada, resposta com a janela fechada, progresso da IA | `wise/interface/ConteudoBolha.qml` | `wise/interface/ConteudoBolha.qml::a carinha de robô e o balão de fala`, `wise/interface/ConteudoBolha.qml::responder(resumo)` | W10 | main |
| Botão flutuante (layer-shell) acima da Ilha | `wise/interface/Bolha.qml`, `wise/interface/bolha.py` | `wise/interface/Bolha.qml::botão flutuante no canto inferior direito` | W09 | main |
| Estado para a Barra de Recursos ($XDG_RUNTIME_DIR/duiaos-wise.estado) | `wise/interface/presenca.py` | `wise/interface/presenca.py::duiaos-wise.estado` | W09 | main |
| Sempre rodando; fechar a janela só põe para descansar; saudação ao entrar | `wise/interface/main.py` | `wise/interface/main.py::setQuitOnLastWindowClosed(False)`, `wise/interface/main.py::def saudar` | W09 | main |
| Campo de texto que acompanha o cursor; resposta no balão com a janela fechada | `wise/interface/Wise.qml`, `wise/interface/main.py` | `wise/interface/Wise.qml::function mostrarCursor`, `wise/interface/main.py::def _avisar_resposta` | W10 | main |

## IA e velocidade

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Modelo local = modelo ativo da IA do sistema (estado.json conferido) | `wise/ia_do_sistema.py` | `wise/ia_do_sistema.py::/var/lib/duiaos-ia/estado.json`, `wise/ia_do_sistema.py::class Acompanhamento` | W10 | main |
| Abertura fixa + aquecimento (pergunta lê só as palavras novas) | `wise/modelos/local.py`, `wise/orquestrador.py` | `wise/modelos/local.py::ABERTURA = [`, `wise/modelos/local.py::def aquecer` | W11 | main |
| Aquecimento antes do login (serviço do sistema; mesma abertura da sessão) | `wise/aquecimento.py`, `pacote/raiz/usr/lib/systemd/system/duiaos-wise-aquecimento.service` | `wise/aquecimento.py::def esperar_modelo`, `pacote/raiz/usr/lib/systemd/system/duiaos-wise-aquecimento.service::Type=exec` | W20 | main |
| Agir sem anunciar; fazer exatamente o que foi pedido | `wise/orquestrador.py` | `wise/orquestrador.py::sem anunciar antes`, `wise/orquestrador.py::def _usar_ferramenta` | W20 | main |
| Texto parcial no máximo 4x/s, numa área própria | `wise/interface/main.py` | `wise/interface/main.py::_tempo_parcial = QTimer(self, interval=250` | W12 | main |
| Gemini só com consentimento; chave no cofre | `wise/modelos/gemini.py`, `wise/segredos.py` | `wise/segredos.py::Secret Service` | W1 | main |
| Auditoria de tudo em SQLite | `wise/auditoria.py` | `wise/auditoria.py::Tudo o que o Wise faz fica registrado` | W1 | main |

## Ferramentas

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Consultas do computador (uso, programas mais pesados com consumo real, rede, atualizações, pastas) | `wise/ferramentas/sistema.py` | `wise/ferramentas/sistema.py::def programas_mais_pesados` | W1/W12 | main |
| Ações N2 com cartão de aprovação (preparar → aprovar → executar) | `wise/orquestrador.py`, `wise/interface/Wise.qml` | `wise/orquestrador.py::def _com_aprovacao`, `wise/interface/Wise.qml::component CartaoAprovacao` | W16 | main |
| Instalar, remover e atualizar pelo duiaos-agente | `wise/ferramentas/aplicativos.py`, `wise/agente_do_sistema.py` | `wise/agente_do_sistema.py::org.duiaos.Agente1` | W2 | main |
| Previsão do tempo (MET Norway) e cidade escolhida | `wise/ferramentas/clima.py` | `wise/ferramentas/clima.py::api.met.no`, `wise/ferramentas/clima.py::def definir_cidade` | W13 | main |
| Agenda: computador, .ics, CalDAV, Google, Microsoft | `wise/agenda/`, `wise/ferramentas/agenda.py` | `wise/agenda/fontes.py::class CalDav`, `wise/agenda/oauth.py::code_challenge_method` | W14 | main |
| Usar o computador: ler e acionar janelas (AT-SPI), abrir apps, digitar, ver a tela | `wise/computador/`, `wise/ferramentas/computador.py` | `wise/computador/acessibilidade.py::def ler(`, `wise/ferramentas/computador.py::ARRISCADAS` | W15 | main |
| Senhas nunca lidas nem preenchidas | `wise/computador/acessibilidade.py`, `wise/ferramentas/computador.py` | `wise/computador/acessibilidade.py::(senha, não lida)`, `wise/ferramentas/computador.py::não escrevo em campos de senha` | W15 | main |
| Diagnóstico no registro do sistema (falhas com rastro, rodadas, tempos; conteúdo só no nível desenvolvimento) e "Não ficou bom" | `wise/diagnostico.py`, `wise/interface/` | `wise/diagnostico.py::def _sem_conteudo`, `wise/interface/Wise.qml::Não ficou bom` | W17→W19 | main |
| Uso agregado: pedidos por provedor, ferramentas usadas e reclamações (sem conteúdo) | `wise/diagnostico.py`, `wise/orquestrador.py` | `wise/diagnostico.py::def uso(`, `wise/orquestrador.py::wise_ferramenta` | W20 | main |
| "Não ficou bom" e "Enviar agora" pedem o envio ao coletor do sistema (duiaos-relatorios) | `wise/diagnostico.py` | `wise/diagnostico.py::duiaos-relatorios.service` | W19 | main |
| Argumentos que precisam vir da pessoa; nomes sem acento | `wise/orquestrador.py`, `wise/ferramentas/base.py` | `wise/orquestrador.py::def _inventado`, `wise/ferramentas/base.py::def chave_de_argumento` | W18 | main |
| Ligar e desligar Wi-Fi e Bluetooth; energia recusa ação trocada | `wise/ferramentas/conexoes.py`, `wise/ferramentas/energia_e_ilha.py` | `wise/ferramentas/conexoes.py::def ligar_ou_desligar`, `wise/ferramentas/energia_e_ilha.py::def conferir_energia` | W20 | main |
| Aplicativo que não existe para o DuiaOS: motivo, versão web e equivalentes | `wise/ferramentas/alternativas.py`, `wise/ferramentas/aplicativos.py` | `wise/ferramentas/alternativas.py::alternativas_para_instalar`, `wise/ferramentas/aplicativos.py::def _existem` | W20 | main |
| Energia (bloquear, reiniciar, desligar, Windows) e fixar na Ilha | `wise/ferramentas/energia_e_ilha.py` | `wise/ferramentas/energia_e_ilha.py::reiniciar_no_windows`, `wise/ferramentas/energia_e_ilha.py::def fixar_na_ilha` | W18 | main |

## Processo

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
