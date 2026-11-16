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
  main.py --demonstracao [--painel NOME] [--captura ARQUIVO]
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
INDICADORES_PADRAO = "wise,wifi,som,bateria,bluetooth,brilho,luz"
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


def aplicativo_em_foco():
    """Nome do aplicativo da janela em foco (wlr-foreign-toplevel pelo wlrctl), ou ''."""
    try:
        saida = subprocess.run(["wlrctl", "toplevel", "list"], capture_output=True, text=True,
                               timeout=2, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    ids = []
    for linha in saida.splitlines():
        app_id = linha.split(":", 1)[0].strip()
        if app_id and app_id not in ids:
            ids.append(app_id)
    for app_id in ids[:16]:
        try:
            focado = subprocess.run(["wlrctl", "toplevel", "find", "app_id:" + app_id, "state:focused"],
                                    capture_output=True, timeout=2, check=False).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            continue
        if focado:
            app = aplicativos.ler_desktop(app_id + ".desktop")
            if not app:
                app = next((a for a in aplicativos.listar_aplicativos()
                            if a["classe"] == app_id.lower() or a["id"].lower().endswith("." + app_id.lower() + ".desktop")), None)
            return app["nome"] if app else app_id.split(".")[-1].capitalize()
    return ""


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


class Sistema(QObject):
    """O que a barra mostra além dos controles: Wise, aplicativo em uso, usuário, notificações, ações."""

    mudou = Signal()
    painelMudou = Signal()
    notificacoesMudaram = Signal()
    _foco = Signal(str)

    def __init__(self):
        super().__init__()
        self._wise = comum.wise_instalado() or DEMONSTRACAO
        self._wise_estado = "descansando" if DEMONSTRACAO else ""
        self._app = "Explorador de Arquivos" if DEMONSTRACAO else ""
        self._usuario = comum.usuario_atual()["nome"]
        self._windows = False
        self._painel, self._ancora, self._confirmar = "", 0.0, ""
        self._historico, self._marca_historico = [], 0.0
        self._foco.connect(self._ao_foco)
        if DEMONSTRACAO:
            self._historico = [
                {"id": 3, "app": "Wise", "titulo": "Sua agenda de amanhã", "texto": "Reunião às 9h e dentista às 15h.", "quando": "12:40",
                 "tipoIcone": "", "valorIcone": ""},
                {"id": 2, "app": "Explorador de Arquivos", "titulo": "Cópia concluída", "texto": "12 itens copiados.", "quando": "11:02",
                 "tipoIcone": "", "valorIcone": ""}]
        if not DEMONSTRACAO:
            self._timer_wise = QTimer(self, interval=1000, timeout=self.atualizar_wise)
            self._timer_wise.start()
            self._timer_foco = QTimer(self, interval=1500, timeout=self._buscar_foco)
            self._timer_foco.start()
            threading.Thread(target=self._ver_windows, daemon=True).start()
            self._timer_notificacoes = QTimer(self, interval=1000, timeout=self._ver_historico)
            self._timer_notificacoes.start()

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
        threading.Thread(target=lambda: self._foco.emit(aplicativo_em_foco()), daemon=True).start()

    def _ao_foco(self, nome):
        if nome != self._app:
            self._app = nome
            self.mudou.emit()

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
