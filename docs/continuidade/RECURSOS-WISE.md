# Wise — Inventário de recursos entregues (não pode regredir)

Mora no `duiaos` (ADR 043) e confere os arquivos do repositório `duiaos-wise`, clonado ao lado
(`python3 ferramentas/conferir-recursos.py` no `duiaos`; nos testes do Wise também). Mesmas regras do
`RECURSOS.md`: cada linha tem uma conferência `arquivo::texto que só a versão atual tem`; recurso novo ou mudado →
linha nova ou atualizada no mesmo envio.

## Presença e visual

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Rosto do Wise (vidro, visor e olhos de luz; aberto, feliz, pensando, ouvindo, falando, descansando; pulinho) | `wise/interface/Carinha.qml` | `wise/interface/Carinha.qml::o rosto do Wise (botão flutuante e cabeçalho da janela)`, `wise/interface/Carinha.qml::function pular()` | ADR 063 | main |
| Rosto animado só pela placa de vídeo (corpo pintado uma vez; não disputa o processador com a IA) | `wise/interface/Carinha.qml` | `wise/interface/Carinha.qml::O corpo é pintado uma vez (Canvas)` | ADR 063 | main |
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
| Aquecimento antes do login (serviço do sistema; mesma abertura da sessão) | `wise/aquecimento.py`, `pacote/raiz/usr/lib/systemd/system/duiaos-wise-aquecimento.service` | `wise/aquecimento.py::def esperar_modelo`, `pacote/raiz/usr/lib/systemd/system/duiaos-wise-aquecimento.service::Type=exec`, `pacote/raiz/usr/lib/systemd/system/duiaos-wise-aquecimento.service::Environment=HOME=/tmp` | W20 | main |
| Agir sem anunciar; fazer exatamente o que foi pedido | `wise/orquestrador.py` | `wise/orquestrador.py::sem anunciar antes`, `wise/orquestrador.py::def _usar_ferramenta` | W20 | main |
| Texto fluido: parciais a cada 80 ms e letras reveladas com rastro, como no Claude | `wise/interface/` | `wise/interface/main.py::_tempo_parcial = QTimer(self, interval=80`, `wise/interface/main.py::def concluirEscrita`, `wise/interface/Wise.qml::parcialCompleto` | ADR 063 | main |
| Motor e modelo da conversa (Local, Gemini, OpenAI) lidos do ia.conf do sistema; janela sem página de configurações | `wise/motores.py, wise/modelos/` | `wise/motores.py::def modelo_preferido`, `wise/modelos/__init__.py::def definir_sessao`, `wise/modelos/openai.py::class `, `wise/interface/main.py::def escolherMotor` | ADR 063 | main |
| Voz: um processo duiaos-voz servir para tudo (modelos carregados uma vez, pré-carga, fala frase a frase, escuta com motivo quando não entende, teste do microfone, eventos no diagnóstico) | `wise/voz.py, wise/interface/main.py` | `wise/voz.py::class Servico`, `wise/voz.py::def preparar`, `wise/interface/main.py::def testarMicrofone`, `wise/interface/main.py::def _registrar_voz`, `testes/test_motores_e_voz.py::def test_fala_e_escuta_pelo_servico_do_sistema` | ADR 063, 065 | main |
| Aquecimento sempre pronto: no boot também para o modelo que não fica sempre na memória (tenta de novo com o Ollama subindo); reaquece quando o modelo volta para a memória; aquece na intenção (janela aberta, microfone) | `wise/aquecimento.py`, `wise/interface/main.py` | `wise/aquecimento.py::estado.carregado or estado.manter != -1`, `wise/aquecimento.py::TENTATIVAS = 4`, `wise/interface/main.py::self._aquecido_para = None`, `wise/interface/main.py::self._aquecer_se_preciso(intencao=True)`, `testes/test_voz_em_tempo_real.py::def test_reaquece_quando_o_modelo_volta_para_a_memoria` | ADR 079 | main |
| Voz em tempo real: trechos para a voz (o 1º em "Claro!" ou na 1ª vírgula; depois por frase), sem cortar números, horas e abreviações | `wise/voz.py` | `wise/voz.py::def trechos_prontos`, `wise/voz.py::PRIMEIRA_VIRGULA = 18`, `testes/test_voz_em_tempo_real.py::def test_primeiro_trecho_curto_sai_na_hora` | ADR 079 | main |
| Resposta falada de conversa: pedido pelo microfone leva o aviso no fim (o começo da conversa não muda) e é sempre respondido em voz | `wise/orquestrador.py`, `wise/interface/main.py` | `wise/orquestrador.py::NOTA_FALADA = (`, `wise/interface/main.py::(self._config.falar_respostas or self._pedido_falado)`, `testes/test_voz_em_tempo_real.py::def test_pedido_pelo_microfone_pede_resposta_de_conversa_sem_mudar_o_comeco` | ADR 079 | main |
| Conversa por voz mãos livres (volta a ouvir ao terminar de falar; silêncio, escrever, cancelar ou fechar encerra; preferência conversa_continua pelo D-Bus) | `wise/interface/main.py`, `wise/configuracao.py` | `wise/interface/main.py::def _ouvir_na_conversa`, `wise/configuracao.py::conversa_continua: bool = True`, `testes/test_voz_em_tempo_real.py::def test_conversa_por_voz_volta_a_ouvir_e_silencio_encerra` | ADR 079 | main |
| Voz natural pela nuvem (OpenAI gpt-4o-mini-tts ou Gemini TTS, com o motor ligado; trechos em paralelo, som enquanto chega, voz local de reserva; voz_na_nuvem) | `wise/voz_nuvem.py`, `wise/interface/main.py` | `wise/voz_nuvem.py::class FalaNuvem`, `wise/voz_nuvem.py::def motor_da_voz`, `wise/interface/main.py::def _motor_da_voz`, `testes/test_voz_nuvem.py::def test_nuvem_recusou_a_voz_local_continua` | ADR 080 | main |
| Medição dos modelos locais (processador e placa de vídeo; começo do Wise, ferramenta certa, escrita) | `wise/medir.py`, `wise/__main__.py` | `wise/medir.py::def medir`, `wise/__main__.py::--medir-modelos`, `testes/test_medir_modelos.py::def test_mede_no_processador_e_na_placa_e_aponta_o_mais_rapido` | ADR 080 | main |
| Entender a fala pela nuvem (gpt-transcribe ou Gemini com a fala gravada pelo duiaos-voz; local de reserva por até 3 s; ouvir_na_nuvem) | `wise/ouvido_nuvem.py`, `wise/interface/main.py` | `wise/ouvido_nuvem.py::def transcrever`, `wise/interface/main.py::def _concluir_escuta`, `wise/interface/main.py::ESPERA_DA_NUVEM_MS`, `testes/test_ouvir_melhor.py::def test_texto_da_nuvem_vale_quando_chega_depois_do_local` | ADR 081 | main |
| Volume do microfone ajustado sozinho (estourado abaixa, baixo sobe, pelo wpctl) | `wise/microfone.py` | `wise/microfone.py::def novo_volume`, `testes/test_ouvir_melhor.py::def test_estourado_abaixa_baixo_sobe_bom_fica` | ADR 081 | main |
| Wise no D-Bus da sessão (Estado, Definir, Acao, Mudou) para as Configurações | `wise/servico.py` | `wise/servico.py::org.duiaos.Wise1` | ADR 063 | main |
| Desligar o Wise (--desligar: sai, pausa a IA local e não volta até ser aberto) | `wise/interface/main.py` | `wise/interface/main.py::--desligar`, `wise/interface/main.py::ARQUIVO_DESLIGADO` | ADR 063 | main |
| Gemini só com consentimento; chave no cofre | `wise/modelos/gemini.py`, `wise/segredos.py` | `wise/segredos.py::Secret Service` | W1 | main |
| Auditoria de tudo em SQLite | `wise/auditoria.py` | `wise/auditoria.py::Tudo o que o Wise faz fica registrado` | W1 | main |

## Ferramentas

| Recurso | Onde | Conferência | Desde | Situação |
| --- | --- | --- | --- | --- |
| Consultas do computador (uso, programas mais pesados com consumo real, rede, atualizações, pastas) | `wise/ferramentas/sistema.py` | `wise/ferramentas/sistema.py::def programas_mais_pesados` | W1/W12 | main |
| Diagnóstico da rede e ligar/desligar VPN pelo módulo de rede das Configurações | `wise/ferramentas/conexoes.py` | `wise/ferramentas/conexoes.py::def diagnosticar_rede`, `wise/ferramentas/conexoes.py::def ligar_vpn`, `testes/test_desempenho_e_aplicativos.py::class TestRede` | ADR 071 | main |
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
