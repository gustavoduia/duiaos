#!/usr/bin/env python3
"""DuiaOS — Barra de Recursos.

À esquerda: o símbolo do DuiaOS abre o Menu do DuiaOS (Sobre este computador,
Configurações, Central de Aplicativos, Explorador de Arquivos, Repousar,
Reiniciar, Desligar, Bloquear tela, Encerrar sessão) e o nome do aplicativo em
uso. O Wise fica nos ícones de controle da direita.

À direita: até 4 ícones de controle (Wise, Wi-Fi, som, bateria, Bluetooth,
brilho, luz noturna), uma seta que mostra os outros num balão, o botão da
Central de Controle e o relógio (abre o calendário). Cada ícone abre o próprio
balão.

A barra fica em BarraDeRecursos.qml (janela presa à borda) e Barra.qml (o
conteúdo); os balões, o menu e a Central de Controle ficam em Painel.qml, uma
camada por cima de tudo que fecha com um clique fora ou Esc.

Uso:
  main.py                         inicia a Barra de Recursos
  main.py --posicao LUGAR         muda a posição: topo, base, esquerda ou direita
  main.py --demonstracao [--painel NOME|appmenuN] [--captura ARQUIVO]   (appmenu0 = Arquivo, appmenu-1 = o nome do app)
                                  abre numa janela comum, com dados de exemplo
                                  (testar o visual sem a sessão do DuiaOS)
"""
import configparser
import fcntl
import os
import subprocess
import sys
import threading
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))
import sistema as comum  # noqa: E402

POSICOES = ("topo", "base", "esquerda", "direita")
INDICADORES = ("wise", "wifi", "som", "bateria", "bluetooth", "brilho", "luz")
# O Wise fica depois dos quatro visíveis (atrás da seta): ele já tem o botão à esquerda e o rosto no canto da tela
INDICADORES_PADRAO = "wifi,som,bateria,bluetooth,wise,brilho,luz"
MAXIMO_VISIVEIS = 4
PASTA_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos"
ARQUIVO_CONFIG = PASTA_CONFIG / "barra-de-recursos.conf"
DEMONSTRACAO = "--demonstracao" in sys.argv


def ler_config():
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    posicao = config.get("barra", "posicao", fallback="topo").strip().lower()
    ordem = [i.strip() for i in config.get("barra", "icones", fallback=INDICADORES_PADRAO).split(",")]
    ordem = [i for i in ordem if i in INDICADORES]
    ordem += [i for i in INDICADORES if i not in ordem]
    return (posicao if posicao in POSICOES else "topo"), ordem


def gravar_config(posicao=None, icones=None):
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config.read(ARQUIVO_CONFIG)
    if not config.has_section("barra"):
        config.add_section("barra")
    if posicao:
        config.set("barra", "posicao", posicao)
    if icones:
        config.set("barra", "icones", ",".join(icones))
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("# DuiaOS — Barra de Recursos. posicao: topo, base, esquerda ou direita\n")
        arquivo.write("# icones: ordem dos ícones à direita; os 4 primeiros que existirem aparecem, os outros\n")
        arquivo.write("# ficam no balão da seta (" + INDICADORES_PADRAO + ")\n")
        config.write(arquivo)


# Comando para mudar a posição, sem abrir a barra
if len(sys.argv) == 3 and sys.argv[1] == "--posicao":
    if sys.argv[2] not in POSICOES:
        sys.exit("Posição inválida. Use: " + ", ".join(POSICOES))
    gravar_config(posicao=sys.argv[2])
    print("Barra de Recursos: posição alterada para", sys.argv[2])
    sys.exit(0)

if not DEMONSTRACAO:
    # Uma instância só: se a barra já estiver aberta, não abre outra.
    _PASTA_EXECUCAO = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    _trava = open(os.path.join(_PASTA_EXECUCAO, "duiaos-barra-de-recursos.lock"), "w")
    try:
        fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("A Barra de Recursos já está aberta. Para reiniciar: reiniciar.sh")
        sys.exit(0)
    # A barra é uma "camada" do Wayland presa à borda da tela (layer-shell).
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import aplicativos  # noqa: E402
import controles  # noqa: E402
import interface  # noqa: E402


class Configuracao(QObject):
    """Preferências da Barra de Recursos, recarregadas quando o arquivo muda."""

    mudou = Signal()

    def __init__(self):
        super().__init__()
        if not DEMONSTRACAO and not ARQUIVO_CONFIG.exists():
            gravar_config(posicao="topo", icones=INDICADORES_PADRAO.split(","))
        self._posicao, self._ordem = ler_config() if not DEMONSTRACAO else ("topo", list(INDICADORES))
        if not DEMONSTRACAO:
            self._vigia = QFileSystemWatcher([str(PASTA_CONFIG), str(ARQUIVO_CONFIG)], self)
            self._vigia.directoryChanged.connect(self.recarregar)
            self._vigia.fileChanged.connect(self.recarregar)

    def recarregar(self, _caminho=None):
        if str(ARQUIVO_CONFIG) not in self._vigia.files() and ARQUIVO_CONFIG.exists():
            self._vigia.addPath(str(ARQUIVO_CONFIG))
        posicao, ordem = ler_config()
        if (posicao, ordem) != (self._posicao, self._ordem):
            self._posicao, self._ordem = posicao, ordem
            self.mudou.emit()

    posicao = Property(str, lambda self: self._posicao, notify=mudou)
    ordem = Property("QVariantList", lambda self: self._ordem, notify=mudou)
    maximoVisiveis = Property(int, lambda self: MAXIMO_VISIVEIS, constant=True)


def janela_em_foco():
    """(app_id, título, nome do aplicativo) da janela em foco (wlr-foreign-toplevel pelo wlrctl, numa
    chamada só), ou ("", "", "")."""
    try:
        saida = subprocess.run(["wlrctl", "toplevel", "list", "state:active"], capture_output=True, text=True,
                               timeout=2, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return "", "", ""
    linha = next((l for l in saida.splitlines() if l.strip()), "")
    app_id, _, titulo = linha.partition(":")
    app_id, titulo = app_id.strip(), titulo.strip()
    return (app_id, titulo, nome_do_aplicativo(app_id)) if app_id else ("", "", "")


_NOMES = {}


def nome_do_aplicativo(app_id):
    if app_id in _NOMES:                       # a lista de aplicativos não é lida a cada segundo
        return _NOMES[app_id]
    app = aplicativos.ler_desktop(app_id + ".desktop")
    if not app:
        app = next((a for a in aplicativos.listar_aplicativos()
                    if a["classe"] == app_id.lower() or a["id"].lower().endswith("." + app_id.lower() + ".desktop")), None)
    _NOMES[app_id] = app["nome"] if app else app_id.split(".")[-1].capitalize()
    return _NOMES[app_id]


def aplicativo_em_foco():
    """Nome do aplicativo da janela em foco, ou ''."""
    return janela_em_foco()[2]


HISTORICO_NOTIFICACOES = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-notificacoes.json"


def ler_historico():
    try:
        import json
        dados = json.loads(HISTORICO_NOTIFICACOES.read_text(encoding="utf-8"))
        return dados if isinstance(dados, list) else []
    except (OSError, ValueError):
        return []


def chamar_notificacoes(metodo, *argumentos):
    """Limpar/Remover no serviço de notificações do DuiaOS (shell/notificacoes)."""
    try:
        from PySide6.QtDBus import QDBusConnection, QDBusMessage
    except ImportError:
        return
    mensagem = QDBusMessage.createMethodCall("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                                             "org.duiaos.Notificacoes1", metodo)
    mensagem.setArguments(list(argumentos))
    QDBusConnection.sessionBus().asyncCall(mensagem)


AVISADOS = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "duiaos" / "atualizacoes-avisadas.json"


def ler_avisados():
    try:
        import json
        dados = json.loads(AVISADOS.read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_avisados(dados):
    try:
        import json
        AVISADOS.parent.mkdir(parents=True, exist_ok=True)
        AVISADOS.write_text(json.dumps(dados), encoding="utf-8")
    except OSError:
        pass


def inicio_da_sessao():
    """Quando a sessão começou: o início do labwc (o autostart passa LABWC_PID); senão, agora."""
    import time
    try:
        return os.stat(f"/proc/{int(os.environ['LABWC_PID'])}").st_ctime
    except (KeyError, ValueError, OSError):
        return time.time()


def notificar(titulo, texto, origem="Atualizações", destino="configuracoes:atualizacoes", botao="Ver atualizações", urgencia=1):
    """Balão de notificação; clicar abre a tela do destino (x-duiaos-abrir), por padrão Configurações › Atualizações."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        conexao = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        dicas = {"x-duiaos-abrir": GLib.Variant("s", destino),
                 "desktop-entry": GLib.Variant("s", "duiaos-configuracoes"), "urgency": GLib.Variant("y", urgencia)}
        conexao.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications", "org.freedesktop.Notifications",
                          "Notify", GLib.Variant("(susssasa{sv}i)", (origem, 0, "", titulo, texto,
                                                                     ["default", "Ver", "abrir", botao], dicas, -1)),
                          None, Gio.DBusCallFlags.NONE, 5000, None)
    except Exception as erro:                  # noqa: BLE001 — sem o serviço de notificações, fica o ícone
        print("Barra: aviso não enviado:", erro, file=sys.stderr, flush=True)


AGENTE_DE_SENHAS = None


def vigiar_portal(objeto_rede, mandar=None):
    """Rede com página de login (hotel, aeroporto, café): avisa uma vez quando a conexão cai nesse estado.
    O NetworkManager descobre testando um endereço do Debian (network-manager-config-connectivity-debian)."""
    mandar = mandar or (lambda: notificar("Esta rede pede login", "Abra a página de login para usar a internet (comum em hotéis, "
                                          "aeroportos e cafés).", origem="Rede e Internet", destino="configuracoes:rede", botao="Fazer login"))
    estado = {"antes": objeto_rede.property("conectividade")}

    def mudou():
        agora = objeto_rede.property("conectividade")
        if agora == "portal" and estado["antes"] != "portal":
            mandar()
        estado["antes"] = agora
    objeto_rede.mudou.connect(mudou)
    return mudou


ARQUIVO_ESPACO_AVISADO = AVISADOS.parent / "espaco-avisado.json"


def ver_espaco(arquivo=None, mandar=None, medir=None, agora=None):
    """Monitor de espaço (ADR 060): mede os discos e manda os avisos de pouco espaço e de disco cheio.
    Os avisos já mandados ficam num arquivo, para não repetir a cada medição nem a cada sessão."""
    import json
    import armazenamento
    arquivo = Path(arquivo or ARQUIVO_ESPACO_AVISADO)
    mandar = mandar or (lambda a: notificar(a["titulo"], a["texto"], origem="Armazenamento", destino="configuracoes:armazenamento",
                                            botao="Liberar espaço", urgencia=2 if a["urgente"] else 1))
    try:
        avisados = json.loads(arquivo.read_text())
    except (OSError, ValueError):
        avisados = {}
    avisos, novos = armazenamento.avisos_de_espaco((medir or armazenamento.dispositivos)(), avisados, agora)
    for aviso in avisos:
        mandar(aviso)
        registrar("aviso", "pouco espaço em disco", componente="barra.espaco", disco=aviso["montado"], estado=aviso["nivel"])
    if novos != avisados:
        try:
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_text(json.dumps(novos))
        except OSError:
            pass
    return avisos


def registrar(nivel, texto, componente="barra.menus", **dados):
    """Evento nos relatórios do DuiaOS (duiaos_registro), sem nada se ele não estiver instalado."""
    try:
        import duiaos_registro
        getattr(duiaos_registro, nivel)(componente, texto, **dados)
    except (ImportError, AttributeError, TypeError):
        pass


def _item(rotulo, atalho="", ativo=True, marcado=None, itens=None):
    tipo = "submenu" if itens else ("marcavel" if marcado is not None else "item")
    return {"id": abs(hash(rotulo)) % 10000 + 1, "rotulo": rotulo, "tipo": tipo, "ativo": ativo, "marcado": bool(marcado),
            "atalho": atalho, "itens": itens or []}


_SEP = {"id": -1, "rotulo": "", "tipo": "separador", "ativo": False, "marcado": False, "atalho": "", "itens": []}
MENUS_DE_EXEMPLO = [
    ("Arquivo", [_item("Novo", "Ctrl+N"), _item("Abrir…", "Ctrl+O"),
                 _item("Abrir recente", itens=[_item("Relatório de outubro.odt"), _item("Orçamento 2026.ods")]), _SEP,
                 _item("Salvar", "Ctrl+S"), _item("Salvar como…", "Ctrl+Shift+S"), _SEP, _item("Imprimir…", "Ctrl+P"), _SEP,
                 _item("Sair", "Ctrl+Q")]),
    ("Editar", [_item("Desfazer", "Ctrl+Z", ativo=False), _item("Refazer", "Ctrl+Shift+Z", ativo=False), _SEP,
                _item("Recortar", "Ctrl+X"), _item("Copiar", "Ctrl+C"), _item("Colar", "Ctrl+V"), _SEP,
                _item("Selecionar tudo", "Ctrl+A"), _item("Localizar…", "Ctrl+F")]),
    ("Exibir", [_item("Barra de ferramentas", marcado=True), _item("Barra de status", marcado=True),
                _item("Régua", marcado=False), _SEP, _item("Ampliar", "Ctrl++"), _item("Reduzir", "Ctrl+-")]),
    ("Formatar", [_item("Negrito", "Ctrl+B"), _item("Itálico", "Ctrl+I"), _item("Sublinhado", "Ctrl+U")]),
    ("Ajuda", [_item("Ajuda do aplicativo", "F1"), _item("Sobre")]),
]


class Sistema(QObject):
    """O que a barra mostra além dos controles: Wise, aplicativo em uso, usuário, notificações, ações."""

    mudou = Signal()
    painelMudou = Signal()
    notificacoesMudaram = Signal()
    menusMudaram = Signal()
    atualizacaoMudou = Signal()
    pedirBalaoAtualizacao = Signal()       # chegou um conjunto novo de atualizações: a barra mostra o balão do ícone
    _foco = Signal(str, str, str)
    _menus = Signal(str, "QVariantList")
    _menus_duiaos = Signal(str, str, "QVariantList")
    _itens = Signal(int, "QVariantList")

    def __init__(self):
        super().__init__()
        self._wise = comum.wise_instalado() or DEMONSTRACAO
        self._wise_estado = "descansando" if DEMONSTRACAO else ""
        self._app = "Editor de Texto" if DEMONSTRACAO else ""
        self._usuario = comum.usuario_atual()["nome"]
        self._windows = False
        self._painel, self._ancora, self._confirmar = "", 0.0, ""
        self._historico, self._marca_historico = [], 0.0
        self._foco.connect(self._ao_foco)
        # Menu do aplicativo em foco (menus.py, ADR 057)
        self._janela = ("", "")                # (app_id, título) da janela dona dos menus
        self._titulos_menu, self._itens_menu, self._menu_aberto = [], [], -2
        self._menus.connect(self._ao_menus)
        self._menus_duiaos.connect(self._ao_menus_duiaos)
        self._fonte_duiaos = ("", [])         # aplicativo do DuiaOS em foco: (nome no D-Bus, menus) — menu_do_app.py
        self._itens.connect(self._ao_itens)
        self._leitor = None
        self._atualizacao = {"icone": DEMONSTRACAO, "dica": "3 atualizações disponíveis" if DEMONSTRACAO else "",
                             "balao": {"titulo": "Atualizações disponíveis" if DEMONSTRACAO else "",
                                       "texto": "3 atualizações para o seu computador, inclui novidades do DuiaOS." if DEMONSTRACAO else ""}}
        self._inicio_da_sessao = inicio_da_sessao()
        if DEMONSTRACAO:
            self._titulos_menu = [nome for nome, _itens in MENUS_DE_EXEMPLO]
            self._historico = [
                {"id": 3, "app": "Wise", "titulo": "Sua agenda de amanhã", "texto": "Reunião às 9h e dentista às 15h.", "quando": "12:40",
                 "tipoIcone": "", "valorIcone": ""},
                {"id": 2, "app": "Explorador de Arquivos", "titulo": "Cópia concluída", "texto": "12 itens copiados.", "quando": "11:02",
                 "tipoIcone": "", "valorIcone": ""}]
        if not DEMONSTRACAO:
            self._timer_wise = QTimer(self, interval=1000, timeout=self.atualizar_wise)
            self._timer_wise.start()
            import menus
            self._leitor = menus.ProcessoDeMenus(lambda app, nomes: self._menus.emit(app, list(nomes)),
                                                 lambda indice, itens: self._itens.emit(indice, list(itens)),
                                                 ao_registro=registrar)
            self._apps_sem_menu = set()
            self._timer_foco = QTimer(self, interval=1000, timeout=self._buscar_foco)
            self._timer_foco.start()
            threading.Thread(target=self._ver_windows, daemon=True).start()
            self._timer_notificacoes = QTimer(self, interval=1000, timeout=self._ver_historico)
            self._timer_notificacoes.start()
            # Atualização automática (ADR 058): ícone ao lado do relógio e avisos
            self._timer_atualizacao = QTimer(self, interval=30000, timeout=self._ver_atualizacao)
            self._timer_atualizacao.start()
            QTimer.singleShot(5000, self._ver_atualizacao)
            # Monitor de espaço em disco (ADR 060): a cada 5 minutos, numa linha à parte (lsblk pode demorar)
            self._timer_espaco = QTimer(self, interval=300000,
                                        timeout=lambda: threading.Thread(target=ver_espaco, daemon=True).start())
            self._timer_espaco.start()
            QTimer.singleShot(20000, lambda: threading.Thread(target=ver_espaco, daemon=True).start())

    def _ver_historico(self):
        try:
            marca = HISTORICO_NOTIFICACOES.stat().st_mtime
        except OSError:
            marca = 0.0
        if marca != self._marca_historico:
            self._marca_historico = marca
            self._historico = ler_historico()
            self.notificacoesMudaram.emit()

    @Slot()
    def limparNotificacoes(self):
        self._historico = []
        self.notificacoesMudaram.emit()
        if not DEMONSTRACAO:
            chamar_notificacoes("Limpar")

    @Slot(int)
    def removerNotificacao(self, identificador):
        self._historico = [h for h in self._historico if h.get("id") != identificador]
        self.notificacoesMudaram.emit()
        if not DEMONSTRACAO:
            chamar_notificacoes("Remover", identificador)

    @Slot(bool)
    def definirNaoPerturbe(self, ligar):
        import pastas
        pastas.gravar_preferencia("notificacoes", "nao_perturbe", "sim" if ligar else "nao")
        self.notificacoesMudaram.emit()

    def _nao_perturbe(self):
        import pastas
        return pastas.ler_preferencia("notificacoes", "nao_perturbe", "nao") == "sim"

    def _ver_windows(self):
        self._windows = comum.windows_disponivel()

    def _buscar_foco(self):
        if self._painel:                       # com um menu aberto, a janela em foco não muda os menus
            return
        threading.Thread(target=lambda: self._foco.emit(*janela_em_foco()), daemon=True).start()

    def _ao_foco(self, app_id, titulo, nome):
        if self._painel:
            return
        if app_id:
            self._janela = (app_id, titulo)
        if nome != self._app:
            self._app = nome
            self.mudou.emit()
        if app_id.startswith("duiaos-"):
            # Aplicativos do DuiaOS publicam os menus pelo D-Bus da sessão (menu_do_app.py, ADR 059)
            def ler():
                import menu_do_app
                nome, menus = menu_do_app.ler_da_sessao(app_id)
                self._menus_duiaos.emit(app_id, nome, menus)
            threading.Thread(target=ler, daemon=True).start()
        else:
            if self._fonte_duiaos[0]:
                self._fonte_duiaos = ("", [])
            if self._leitor:
                self._leitor.foco(app_id, titulo)

    # ---------------------------------------------------- atualização automática
    def _ver_atualizacao(self):
        import atualizacao_automatica as aa
        avisados = ler_avisados()
        agora = aa.avisos(aa.ler_estado(), aa.ler_modo(), avisados, aa.momento_do_inicio(), self._inicio_da_sessao)
        estado = {"icone": agora["icone"], "dica": agora["dica"], "balao": agora["balao"]}
        if estado != self._atualizacao:
            self._atualizacao = estado
            self.atualizacaoMudou.emit()
        for aviso in agora["notificacoes"]:
            tipo, valor = aviso["chave"]
            avisados[tipo] = valor
            if aviso.get("balao") and estado["icone"]:
                self.pedirBalaoAtualizacao.emit()      # a barra decide: balão no ícone ou, sem o ícone, a notificação
                continue
            threading.Thread(target=notificar, args=(aviso["titulo"], aviso["texto"]), daemon=True).start()
        if agora["notificacoes"]:
            gravar_avisados(avisados)

    atualizacaoIcone = Property(bool, lambda self: self._atualizacao["icone"], notify=atualizacaoMudou)
    atualizacaoDica = Property(str, lambda self: self._atualizacao["dica"], notify=atualizacaoMudou)
    balaoTitulo = Property(str, lambda self: self._atualizacao["balao"]["titulo"], notify=atualizacaoMudou)
    balaoTexto = Property(str, lambda self: self._atualizacao["balao"]["texto"], notify=atualizacaoMudou)

    @Slot()
    def notificarAtualizacao(self):
        """Reserva do balão quando a barra não mostra o ícone (barra na vertical): a notificação de sempre."""
        balao = self._atualizacao["balao"]
        if balao["titulo"] and not DEMONSTRACAO:
            threading.Thread(target=notificar, args=(balao["titulo"], balao["texto"] + " Clique para ver o resumo."),
                             daemon=True).start()

    # ---------------------------------------------------- menu do aplicativo
    def _ao_menus_duiaos(self, app_id, nome, menus):
        if self._painel.startswith("appmenu") or self._janela[0] != app_id:
            return
        self._fonte_duiaos = (nome, list(menus))
        titulos = [m["rotulo"] for m in menus]
        if titulos != self._titulos_menu:
            self._titulos_menu = titulos
            self.menusMudaram.emit()

    def _ao_menus(self, app_id, nomes):
        if self._painel.startswith("appmenu") or self._fonte_duiaos[0]:
            return
        nomes = list(nomes) if app_id else []
        # Para os relatórios: cada aplicativo sem barra de menus aparece uma vez por sessão
        if app_id and not nomes and app_id not in getattr(self, "_apps_sem_menu", {app_id}):
            self._apps_sem_menu.add(app_id)
            registrar("info", "Menus dos aplicativos: sem barra de menus pela acessibilidade", aplicativo=app_id,
                      motivo=self._leitor.motivos.get(app_id, "") if self._leitor else "")
        if nomes != self._titulos_menu:
            self._titulos_menu = nomes
            self.menusMudaram.emit()

    def _ao_itens(self, indice, itens):
        if indice == self._menu_aberto:
            self._itens_menu = list(itens) or [{"id": -1, "rotulo": "Este menu está vazio", "tipo": "item", "ativo": False,
                                                "marcado": False, "atalho": "", "itens": []}]
            self.menusMudaram.emit()

    @Slot(int, float)
    def abrirMenuDoAplicativo(self, indice, ancora):
        """Abre um menu do aplicativo em foco (-1 = o menu com o nome dele, com as ações da janela).
        Clicar de novo no mesmo fecha."""
        import menus
        nome = f"appmenu{indice}"
        if self._painel == nome:
            self.fecharPainel()
            return
        self._menu_aberto = indice
        if indice < 0:
            self._itens_menu = menus.menu_da_janela(self._app)
        elif DEMONSTRACAO:
            self._itens_menu = MENUS_DE_EXEMPLO[indice][1] if indice < len(MENUS_DE_EXEMPLO) else []
        elif self._fonte_duiaos[0]:
            menus = self._fonte_duiaos[1]
            self._itens_menu = list(menus[indice]["itens"]) if indice < len(menus) else []
        else:
            self._itens_menu = []                      # carregando: a linha do AT-SPI responde em seguida
            self._leitor.itens(indice)
        self._painel, self._ancora, self._confirmar = nome, ancora, ""
        self.painelMudou.emit()
        self.menusMudaram.emit()

    @Slot(float)
    def abrirMenuDoWise(self, ancora):
        """Botão direito no Wise (ADR 063): abrir, as duas páginas das Configurações e desligar (ou ligar)."""
        if self._painel == "appmenuwise":
            self.fecharPainel()
            return
        desligado = (Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / "duiaos-wise-desligado").exists()

        def item(ident, rotulo, tipo="item"):
            return {"id": ident, "rotulo": rotulo, "tipo": tipo, "ativo": True, "marcado": False, "atalho": "", "itens": []}
        self._menu_aberto = -2
        self._itens_menu = [item("wise:abrir", "Ligar e abrir o Wise" if desligado else "Abrir o Wise"),
                            item(-1, "", "separador"),
                            item("wise:configuracoes", "Configurações do Wise…"),
                            item("wise:ia", "Configurar a IA…")] + \
                           ([] if desligado else [item(-1, "", "separador"), item("wise:desligar", "Desligar o Wise")])
        self._painel, self._ancora, self._confirmar = "appmenuwise", ancora, ""
        self.painelMudou.emit()
        self.menusMudaram.emit()

    @Slot("QVariant")
    def acionarMenu(self, identificador):
        """Item escolhido num menu do aplicativo: as ações da janela (texto "janela:...") o DuiaOS faz;
        os outros são acionados no próprio aplicativo pelo AT-SPI, depois de devolver o foco a ele."""
        self.fecharPainel()
        if DEMONSTRACAO:
            print("Demonstração: menu", identificador, flush=True)
            return
        if isinstance(identificador, str) and identificador.startswith("wise:"):
            acao = identificador.split(":", 1)[1]
            if acao == "abrir":
                aplicativos.iniciar(["/usr/bin/duiaos-wise"])
            elif acao == "configuracoes":
                comum.abrir_app_duiaos("configuracoes", "--secao", "wise")
            elif acao == "ia":
                comum.abrir_app_duiaos("configuracoes", "--secao", "ia")
            elif acao == "desligar":
                # O Wise sai, a sessão não o reabre e a IA local sai da memória (volta ao abrir o Wise)
                aplicativos.iniciar(["/usr/bin/duiaos-wise", "--desligar"])
            return
        app_id, titulo = self._janela
        filtro = ["app_id:" + app_id] + (["title:" + titulo] if titulo else [])
        if isinstance(identificador, str) and identificador.startswith("janela:"):
            acao = identificador.split(":", 1)[1]
            if acao == "minimizar":
                aplicativos.iniciar(["sh", "-c", 'wlrctl toplevel focus "$@" && sleep 0.15 && exec "$0"',
                                     str(PASTA.parent / "ilha-de-aplicativos" / "minimizar.sh"), *filtro])
            elif acao == "expandir":
                aplicativos.iniciar(["wlrctl", "toplevel", "maximize", *filtro])
            elif acao == "fechar":
                aplicativos.iniciar(["wlrctl", "toplevel", "close", *filtro])
            elif acao == "encerrar":
                aplicativos.iniciar(["wlrctl", "toplevel", "close", "app_id:" + app_id])
            return
        if isinstance(identificador, str) and self._fonte_duiaos[0]:
            nome = self._fonte_duiaos[0]

            def devolver_foco_e_pedir():
                subprocess.run(["wlrctl", "toplevel", "focus", *filtro], timeout=2, check=False, capture_output=True)
                import menu_do_app
                menu_do_app.acionar_na_sessao(nome, identificador)
            threading.Thread(target=devolver_foco_e_pedir, daemon=True).start()
            return
        if self._leitor and isinstance(identificador, (int, float)) and identificador > 0:
            leitor, numero = self._leitor, int(identificador)

            def devolver_foco_e_acionar():
                subprocess.run(["wlrctl", "toplevel", "focus", *filtro], timeout=2, check=False, capture_output=True)
                import time
                time.sleep(0.12)                       # o compositor devolve o teclado à janela
                leitor.acionar(numero)
            threading.Thread(target=devolver_foco_e_acionar, daemon=True).start()

    titulosDoMenu = Property("QVariantList", lambda self: self._titulos_menu, notify=menusMudaram)
    itensDoMenu = Property("QVariantList", lambda self: self._itens_menu, notify=menusMudaram)

    def atualizar_wise(self):
        estado = comum.estado_wise()
        instalado = comum.wise_instalado()
        if (estado, instalado) != (self._wise_estado, self._wise):
            self._wise_estado, self._wise = estado, instalado
            self.mudou.emit()

    # ------------------------------------------------------------- painel
    @Slot(str, float)
    def abrirPainel(self, nome, ancora):
        """Abre o menu, um balão ou a Central de Controle; o mesmo nome de novo fecha."""
        if nome == self._painel:
            self.fecharPainel()
            return
        self._painel, self._ancora, self._confirmar = nome, ancora, ""
        self.painelMudou.emit()

    @Slot()
    def fecharPainel(self):
        if self._painel or self._confirmar:
            self._painel, self._confirmar = "", ""
            self.painelMudou.emit()

    # ------------------------------------------------------------- ações
    @Slot()
    def abrirWise(self):
        self.fecharPainel()
        comum.alternar_wise()

    @Slot(str)
    def abrir(self, destino):
        """Abre um aplicativo do sistema. destino: configuracoes[:secao], explorador[:pasta], central, sobre."""
        self.fecharPainel()
        if DEMONSTRACAO:
            return
        nome, _, detalhe = destino.partition(":")
        if nome == "configuracoes":
            comum.abrir_app_duiaos("configuracoes", *(["--secao", detalhe] if detalhe else []))
        elif nome == "sobre":
            comum.abrir_app_duiaos("configuracoes", "--secao", "sobre")
        elif nome == "explorador":
            comum.abrir_app_duiaos("explorador-de-arquivos", *([detalhe] if detalhe else []))
        elif nome == "central":
            aplicativos.iniciar(["sh", str(PASTA.parent / "ilha-de-aplicativos" / "alternar-central.sh")])
        desktop = {"configuracoes": "duiaos-configuracoes.desktop", "sobre": "duiaos-configuracoes.desktop",
                   "explorador": "duiaos-explorador-de-arquivos.desktop"}.get(nome)
        if desktop:
            interface.registrar_uso("uso.aplicativo_aberto", aplicativo=desktop, por="barra")

    @Slot(str)
    def pedirEnergia(self, acao):
        """Repousar e Bloquear agem na hora; Reiniciar, Desligar e Encerrar sessão pedem confirmação."""
        if acao in ("suspender", "bloquear"):
            self.fecharPainel()
            if not DEMONSTRACAO:
                comum.executar_energia(acao)
            return
        self._painel, self._confirmar = "", acao
        self.painelMudou.emit()

    @Slot()
    def confirmarEnergia(self):
        acao = self._confirmar
        self.fecharPainel()
        if acao and not DEMONSTRACAO:
            comum.executar_energia(acao)

    historico = Property("QVariantList", lambda self: self._historico, notify=notificacoesMudaram)
    naoPerturbe = Property(bool, _nao_perturbe, notify=notificacoesMudaram)
    wise = Property(bool, lambda self: self._wise, notify=mudou)
    wiseEstado = Property(str, lambda self: self._wise_estado, notify=mudou)
    aplicativoEmFoco = Property(str, lambda self: self._app, notify=mudou)
    usuario = Property(str, lambda self: self._usuario, constant=True)
    windows = Property(bool, lambda self: self._windows, notify=mudou)
    painel = Property(str, lambda self: self._painel, notify=painelMudou)
    ancora = Property(float, lambda self: self._ancora, notify=painelMudou)
    confirmacao = Property(str, lambda self: self._confirmar, notify=painelMudou)


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    if DEMONSTRACAO:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen" if "--captura" in sys.argv else "")
    app = QGuiApplication(sys.argv)
    interface.ligar_registro("duiaos-barra-de-recursos")
    # A integração layer-shell vale só para este painel: sem isto, os programas
    # abertos daqui (Wise, aplicativos Qt) herdariam a variável e virariam
    # "painéis" sem barra de título, sem botões e sem redimensionar.
    os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)
    app.setApplicationName("duiaos-barra-de-recursos")

    configuracao = Configuracao()
    sistema = Sistema()
    estado = controles.Controles(demonstracao=DEMONSTRACAO)
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    if not DEMONSTRACAO:
        interface.aparencia().vigiar_horario()          # modo Automático: claro de dia, escuro à noite
    contexto = engine.rootContext()
    contexto.setContextProperty("configuracao", configuracao)
    contexto.setContextProperty("sistema", sistema)
    contexto.setContextProperty("controles", estado)
    # Rede e Internet (ADR 069): cabo, Wi-Fi e VPN no mesmo indicador, e o aviso de rede que pede login
    import rede_interface
    objeto_rede = rede_interface.Rede(demonstracao=DEMONSTRACAO)
    contexto.setContextProperty("rede", objeto_rede)
    vigiar_portal(objeto_rede)
    # Agente de senhas (ADR 070): responde quando o NetworkManager pede uma senha (Wi-Fi, rede corporativa, VPN)
    global AGENTE_DE_SENHAS
    if not DEMONSTRACAO:
        import agente_de_senhas
        AGENTE_DE_SENHAS = agente_de_senhas.Agente()
        AGENTE_DE_SENHAS.iniciar()
    contexto.setContextProperty("papelDeParede", comum.papel_de_parede())
    contexto.setContextProperty("capturaArquivo", argumento("--captura"))
    contexto.setContextProperty("painelInicial", argumento("--painel"))
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "BarraDeRecursos.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine                       # fecha o QML antes dos objetos do Python
    sys.exit(codigo)


if __name__ == "__main__":
    main()
