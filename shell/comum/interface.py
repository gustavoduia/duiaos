"""DuiaOS — preparação comum das janelas QML da interface e dos aplicativos próprios.

    import interface
    interface.preparar(engine)      # import DuiaOS, ícones próprios e ícones do tema

Os aplicativos (apps/*) acham esta pasta por DUIAOS_SHELL, pela instalação
(/usr/share/duiaos/shell) ou pelo repositório (desenvolvimento).
"""
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))
import icones  # noqa: E402


def configurar_tema_de_icones():
    """Sem ambiente de desktop completo, o Qt não conhece as pastas de ícones do sistema."""
    from PySide6.QtGui import QIcon
    pastas_dados = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    pastas_icones = [str(Path.home() / ".local/share/icons"),
                     str(Path.home() / ".local/share/flatpak/exports/share/icons"),       # Flathub (ADR 049)
                     "/var/lib/flatpak/exports/share/icons"] + [p + "/icons" for p in pastas_dados if p]
    QIcon.setThemeSearchPaths(pastas_icones + QIcon.themeSearchPaths())
    QIcon.setFallbackSearchPaths(QIcon.fallbackSearchPaths() + ["/usr/share/pixmaps"])
    if not QIcon.themeName():
        QIcon.setThemeName("hicolor")


def provedor_icones_do_tema():
    """Entrega ao QML os ícones do tema (image://icone/nome ou caminho absoluto)."""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QIcon, QPixmap
    from PySide6.QtQuick import QQuickImageProvider

    class Icones(QQuickImageProvider):
        def __init__(self):
            super().__init__(QQuickImageProvider.ImageType.Pixmap)

        def requestPixmap(self, nome, tamanho, tamanho_pedido):
            lado = max(tamanho_pedido.width(), 48)
            icone = QIcon(nome) if nome.startswith("/") else QIcon.fromTheme(nome)
            if icone.isNull():
                return QPixmap()
            return icone.pixmap(QSize(lado, lado))

    return Icones()


def aparencia():
    """Objeto "aparencia" do QML (modo escuro e estilo), igual em todas as janelas e atualizado na hora."""
    global _APARENCIA
    if _APARENCIA is None:
        _APARENCIA = _criar_aparencia()
    return _APARENCIA


_APARENCIA = None


def _criar_aparencia():
    from PySide6.QtCore import QFileSystemWatcher, QObject, Property, QTimer, Signal, Slot
    import pastas

    class Aparencia(QObject):
        mudou = Signal()

        def __init__(self):
            super().__init__()
            self._escuro = pastas.ler_preferencia("aparencia", "modo", "claro") == "escuro"
            self._automatico = pastas.ler_preferencia("aparencia", "automatico", "nao") == "sim"
            self._estilo = self._ler_estilo()
            pastas.PREFERENCIAS.parent.mkdir(parents=True, exist_ok=True)
            self._vigia = QFileSystemWatcher([str(pastas.PREFERENCIAS.parent)], self)
            self._vigia.directoryChanged.connect(lambda _c: self._atraso.start())
            self._atraso = QTimer(self, singleShot=True, interval=150, timeout=self.recarregar)

        @staticmethod
        def _ler_estilo():
            return pastas.estilo_da_interface()

        def recarregar(self):
            escuro = pastas.ler_preferencia("aparencia", "modo", "claro") == "escuro"
            automatico = pastas.ler_preferencia("aparencia", "automatico", "nao") == "sim"
            estilo = self._ler_estilo()
            if escuro != self._escuro or estilo != self._estilo or automatico != self._automatico:
                self._escuro, self._estilo, self._automatico = escuro, estilo, automatico
                self.mudou.emit()

        @Slot(str)
        def definirEstilo(self, estilo):
            """Estilo da interface (ADR 052 e 054): "futurista" (Aurora, o inicial) ou "padrao" (Clássico). Vale na hora."""
            if estilo not in ("padrao", "futurista"):
                return
            pastas.gravar_preferencia("aparencia", "estilo", estilo)
            self.recarregar()
            import sessao
            import threading
            threading.Thread(target=sessao.aplicar_aparencia, daemon=True).start()

        @Slot(bool)
        def definirEscuro(self, escuro):
            self.definirModo("escuro" if escuro else "claro")

        @Slot(str)
        def definirModo(self, modo):
            """Modo da interface: "claro", "escuro" ou "automatico" (claro de dia, escuro à noite; ADR 056)."""
            if modo not in ("claro", "escuro", "automatico"):
                return
            import sessao
            import threading
            pastas.gravar_preferencia("aparencia", "automatico", "sim" if modo == "automatico" else "nao")
            if modo == "automatico":
                sessao.atualizar_modo_automatico()
            else:
                pastas.gravar_preferencia("aparencia", "modo", modo)
            self.recarregar()
            threading.Thread(target=sessao.aplicar_aparencia, daemon=True).start()

        def vigiar_horario(self):
            """Um programa da sessão (a Barra de Recursos) confere a cada minuto se o sol nasceu ou se pôs
            e, no modo Automático, troca o modo. Os outros programas veem a mudança pelo arquivo."""
            def conferir():
                import sessao
                import threading
                try:
                    if sessao.atualizar_modo_automatico():
                        self.recarregar()
                        threading.Thread(target=sessao.aplicar_aparencia, daemon=True).start()
                except Exception as erro:                   # nunca derruba a Barra por causa disto
                    print("Modo automático:", erro, file=sys.stderr)
            self._horario = QTimer(self, interval=60000, timeout=conferir)
            self._horario.start()
            QTimer.singleShot(4000, conferir)

        escuro = Property(bool, lambda self: self._escuro, notify=mudou)
        automatico = Property(bool, lambda self: self._automatico, notify=mudou)
        modo = Property(str, lambda self: "automatico" if self._automatico else ("escuro" if self._escuro else "claro"), notify=mudou)
        estilo = Property(str, lambda self: self._estilo, notify=mudou)

    return Aparencia()


def preparar(engine):
    configurar_tema_de_icones()
    configurar_texto()
    engine.addImportPath(str(PASTA / "qml"))
    icones.registrar(engine)
    engine.addImageProvider("icone", provedor_icones_do_tema())
    engine.rootContext().setContextProperty("aparencia", aparencia())


def configurar_texto():
    """Texto desenhado pelo FreeType, com os ajustes de pixel da fonte (ADR 068).

    O padrão do Qt Quick (campos de distância) foi feito para texto que gira e muda de escala; numa tela
    comum (densidade 1) ele deixa as letras pequenas borradas. O desenho nativo encaixa os traços nos
    pixels, como o GTK e o macOS fazem. Vale para todas as janelas criadas depois desta chamada."""
    from PySide6.QtQuick import QQuickWindow
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)


def registrar_uso(evento, **dados):
    """Uso agregado de "Ajude a melhorar o DuiaOS" (relatorios/uso.py). Sem o duiaos_registro, nada."""
    try:
        import duiaos_registro
    except ImportError:
        return
    duiaos_registro.info(evento, evento, **dados)


def ligar_registro(nome):
    try:
        import duiaos_registro
        duiaos_registro.ligar(nome, qt=True)
    except ImportError:
        pass


def chamar_agente(dono, metodo, argumentos, ao_responder=None, ao_falhar=None, tempo=300000):
    """Chama o duiaos-agente (D-Bus do sistema, org.duiaos.Agente1) sem travar a janela.

    ao_responder(lista de argumentos da resposta) ou ao_falhar(mensagem para a pessoa) rodam na linha
    da interface. `dono` é um QObject que vive enquanto a chamada estiver pendente."""
    from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusPendingCallWatcher
    mensagem = QDBusMessage.createMethodCall("org.duiaos.Agente1", "/org/duiaos/Agente1", "org.duiaos.Agente1", metodo)
    mensagem.setArguments(list(argumentos))
    vigia = QDBusPendingCallWatcher(QDBusConnection.systemBus().asyncCall(mensagem, tempo), dono)
    if not hasattr(dono, "_chamadas_ao_agente"):
        dono._chamadas_ao_agente = []              # guarda a referência até a resposta chegar
    dono._chamadas_ao_agente.append(vigia)

    def terminou(v):
        if v in dono._chamadas_ao_agente:
            dono._chamadas_ao_agente.remove(v)
        if v.isError():
            nome = v.error().name()
            if ao_falhar:
                ao_falhar(v.error().message() if "ServiceUnknown" not in nome and "NoReply" not in nome
                          else "O agente do sistema não respondeu.")
        elif ao_responder:
            ao_responder(v.reply().arguments())
        v.deleteLater()
    vigia.finished.connect(terminou)
