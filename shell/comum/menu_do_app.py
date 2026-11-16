"""DuiaOS — menus dos aplicativos do próprio DuiaOS na Barra de Recursos (ADR 059).

Os aplicativos do DuiaOS são feitos em QML, sem barra de menus dentro da janela, então a Barra não
tem o que ler pela acessibilidade (barra-de-recursos/menus.py). Eles publicam os menus por um canal
próprio, no D-Bus da sessão:

    nome    org.duiaos.Menu.<chave>.p<processo>        ex.: org.duiaos.Menu.explorador_de_arquivos.p4242
    objeto  /org/duiaos/Menu      interface org.duiaos.Menu1
    Menus() -> s       JSON: [{"rotulo": "Arquivo", "itens": [itens no formato de menus.py]}]
    Ativo() -> b       se uma janela deste processo está em foco
    Acionar(s id)      a pessoa escolheu o item

No aplicativo: MenuDoApp(chave, menus) — o QML recebe o sinal acionado(id) e faz a ação (é ele que
sabe, por exemplo, o que está selecionado). definirMenus() troca os menus (itens ativados conforme o
momento). Sem Qt aqui dentro da linha do D-Bus: roda o laço do GLib à parte, como o serviço de
notificações.
"""
import json
import os
import re
import threading

PREFIXO = "org.duiaos.Menu."
INTERFACE = "org.duiaos.Menu1"
CAMINHO = "/org/duiaos/Menu"
XML = f"""
<node>
  <interface name="{INTERFACE}">
    <method name="Menus"><arg type="s" direction="out"/></method>
    <method name="Ativo"><arg type="b" direction="out"/></method>
    <method name="Acionar"><arg type="s" name="id" direction="in"/></method>
  </interface>
</node>
"""


def chave_do_app(app_id):
    """app_id do labwc (ex.: duiaos-explorador-de-arquivos) → a chave do nome no D-Bus."""
    chave = re.sub(r"^duiaos-", "", app_id or "")
    return re.sub(r"[^A-Za-z0-9_]", "_", chave)


def item(identificador, rotulo, atalho="", ativo=True, marcado=None, itens=None):
    """Um item no formato que a Barra mostra (o mesmo de barra-de-recursos/menus.py)."""
    if itens is not None:
        return {"id": identificador, "rotulo": rotulo, "tipo": "submenu", "ativo": ativo and bool(itens),
                "marcado": False, "atalho": "", "itens": itens}
    return {"id": identificador, "rotulo": rotulo, "tipo": "marcavel" if marcado is not None else "item",
            "ativo": ativo, "marcado": bool(marcado), "atalho": atalho, "itens": []}


SEPARADOR = {"id": -1, "rotulo": "", "tipo": "separador", "ativo": False, "marcado": False, "atalho": "", "itens": []}


def ids_validos(menus):
    """Todos os ids que podem ser acionados (itens que não são submenu nem separador)."""
    achados = set()

    def andar(itens):
        for i in itens:
            if i.get("tipo") == "submenu":
                andar(i.get("itens", []))
            elif i.get("tipo") != "separador" and i.get("ativo"):
                achados.add(str(i.get("id")))
    for menu in menus:
        andar(menu.get("itens", []))
    return achados


def criar(chave, menus):
    """O objeto para o aplicativo (precisa do Qt; importado só aqui para os testes do resto não precisarem).
    Guarde o objeto numa variável que dure o programa todo: passado direto ao QML, o Python o descarta."""
    from PySide6.QtCore import QObject, Signal, Slot
    from PySide6.QtGui import QGuiApplication

    class MenuDoApp(QObject):
        acionado = Signal(str)
        _pedido = Signal(str)

        def __init__(self):
            super().__init__()
            self._menus = list(menus)
            self._trava = threading.Lock()
            self._ativo = False
            self._pedido.connect(self.acionado)
            app = QGuiApplication.instance()
            if app is not None:
                app.applicationStateChanged.connect(self._estado)
                self._estado(app.applicationState())
            threading.Thread(target=self._rodar, name="menu-do-app", daemon=True).start()

        def _estado(self, estado):
            from PySide6.QtCore import Qt
            self._ativo = estado == Qt.ApplicationState.ApplicationActive

        @Slot("QVariantList")
        def definirMenus(self, novos):
            with self._trava:
                self._menus = list(novos)

        def menus_atuais(self):
            with self._trava:
                return list(self._menus)

        def _rodar(self):
            try:
                import gi
                gi.require_version("Gio", "2.0")
                from gi.repository import Gio, GLib
            except (ImportError, ValueError):
                return
            contexto = GLib.MainContext.new()
            contexto.push_thread_default()
            laco = GLib.MainLoop.new(contexto, False)
            try:
                conexao = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            except GLib.Error:
                return
            informacao = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]

            def chamada(_c, _remetente, _caminho, _interface, metodo, parametros, invocacao):
                if metodo == "Menus":
                    invocacao.return_value(GLib.Variant("(s)", (json.dumps(self.menus_atuais(), ensure_ascii=False),)))
                elif metodo == "Ativo":
                    invocacao.return_value(GLib.Variant("(b)", (self._ativo,)))
                elif metodo == "Acionar":
                    identificador = parametros.unpack()[0]
                    if identificador in ids_validos(self.menus_atuais()):
                        self._pedido.emit(identificador)
                    invocacao.return_value(None)
            conexao.register_object(CAMINHO, informacao, chamada, None, None)
            Gio.bus_own_name_on_connection(conexao, f"{PREFIXO}{chave}.p{os.getpid()}", Gio.BusNameOwnerFlags.NONE, None, None)
            laco.run()

    return MenuDoApp()


# --------------------------------------------------------------- o lado da Barra

def ler_da_sessao(app_id, tempo=1500):
    """Os menus do aplicativo do DuiaOS em foco: (nome no D-Bus, menus) ou ("", []).
    Com várias janelas do mesmo aplicativo (um processo para cada), vale a que está em foco."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        conexao = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        nomes = conexao.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ListNames",
                                  None, GLib.VariantType.new("(as)"), Gio.DBusCallFlags.NONE, tempo, None).unpack()[0]
    except Exception:                           # noqa: BLE001 — sem D-Bus: sem menus
        return "", []
    prefixo = f"{PREFIXO}{chave_do_app(app_id)}.p"
    candidatos = [n for n in nomes if n.startswith(prefixo)]

    def chamar(nome, metodo, tipo):
        return conexao.call_sync(nome, CAMINHO, INTERFACE, metodo, None, GLib.VariantType.new(tipo),
                                 Gio.DBusCallFlags.NONE, tempo, None).unpack()[0]
    escolhido = ""
    for nome in candidatos:
        try:
            if chamar(nome, "Ativo", "(b)"):
                escolhido = nome
                break
        except Exception:                       # noqa: BLE001
            continue
    if not escolhido and len(candidatos) == 1:
        escolhido = candidatos[0]
    if not escolhido:
        return "", []
    try:
        menus = json.loads(chamar(escolhido, "Menus", "(s)"))
        return escolhido, [m for m in menus if isinstance(m, dict) and m.get("rotulo")]
    except Exception:                           # noqa: BLE001
        return "", []


def acionar_na_sessao(nome, identificador, tempo=1500):
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        Gio.bus_get_sync(Gio.BusType.SESSION, None).call_sync(
            nome, CAMINHO, INTERFACE, "Acionar", GLib.Variant("(s)", (str(identificador),)), None,
            Gio.DBusCallFlags.NONE, tempo, None)
        return True
    except Exception:                           # noqa: BLE001
        return False
