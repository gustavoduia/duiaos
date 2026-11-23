"""DuiaOS — contador no ícone do aplicativo na Ilha (o balão vermelho de "não lidas", ADR 077).

Usa o sinal que o Linux já conhece (o mesmo do Dock do Ubuntu e do KDE), para valer também com
aplicativos de fora:

    sinal  com.canonical.Unity.LauncherEntry.Update(s app_uri, a{sv} propriedades)
           app_uri       "application://duiaos-mailbox.desktop"
           propriedades  count (x) e count-visible (b)

O aplicativo chama publicar("duiaos-mailbox.desktop", 3); a Ilha chama ouvir(funcao) e recebe
funcao("duiaos-mailbox.desktop", 3) — numa linha à parte (o laço do GLib), então quem é Qt passa
adiante por um sinal. Sem D-Bus (demonstração, testes), as duas funções não fazem nada.
"""
import threading

INTERFACE = "com.canonical.Unity.LauncherEntry"
CAMINHO = "/com/duiaos/contador"


def uri_do(desktop_id):
    desktop_id = desktop_id if desktop_id.endswith(".desktop") else desktop_id + ".desktop"
    return "application://" + desktop_id


def ler_sinal(uri, propriedades):
    """(desktop_id, número) a partir do sinal; o número é 0 quando o contador não deve aparecer."""
    desktop_id = uri.removeprefix("application://")
    visivel = bool(propriedades.get("count-visible", False))
    try:
        numero = int(propriedades.get("count", 0))
    except (TypeError, ValueError):
        numero = 0
    return desktop_id, (max(0, numero) if visivel else 0)


def _gio():
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        return Gio, GLib
    except (ImportError, ValueError):
        return None, None


_barramento = None


def publicar(desktop_id, numero):
    """Mostra (numero > 0) ou esconde (0) o contador no ícone do aplicativo. Devolve se conseguiu."""
    global _barramento
    Gio, GLib = _gio()
    if Gio is None:
        return False
    try:
        if _barramento is None:
            _barramento = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        numero = max(0, int(numero))
        _barramento.emit_signal(None, CAMINHO, INTERFACE, "Update", GLib.Variant(
            "(sa{sv})", (uri_do(desktop_id), {"count": GLib.Variant("x", numero),
                                              "count-visible": GLib.Variant("b", numero > 0)})))
        _barramento.flush_sync(None)
        return True
    except Exception:  # noqa: BLE001 — sem sessão D-Bus: o contador só não aparece
        return False


def ouvir(funcao):
    """Chama funcao(desktop_id, numero) a cada sinal de contador da sessão. Devolve se conseguiu."""
    Gio, GLib = _gio()
    if Gio is None:
        return False
    try:
        barramento = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except Exception:  # noqa: BLE001
        return False

    def recebido(_conexao, _remetente, _caminho, _interface, _sinal, parametros):
        try:
            uri, propriedades = parametros.unpack()
            funcao(*ler_sinal(uri, propriedades))
        except Exception:  # noqa: BLE001 — sinal mal formado de outro programa
            pass

    contexto = GLib.MainContext.new()

    def laco():
        contexto.push_thread_default()
        barramento.signal_subscribe(None, INTERFACE, "Update", None, None, Gio.DBusSignalFlags.NONE, recebido)
        GLib.MainLoop(contexto).run()

    threading.Thread(target=laco, daemon=True, name="duiaos-contador").start()
    return True
