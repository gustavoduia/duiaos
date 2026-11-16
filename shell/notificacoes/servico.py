"""DuiaOS — serviço de notificações no D-Bus da sessão (padrão org.freedesktop.Notifications 1.2,
o mesmo de todos os sistemas Linux: notify-send, navegadores e aplicativos GTK/Qt avisam por ele).

Também responde em org.duiaos.Notificacoes1 (mesmo objeto): Limpar() e Remover(id), usados pelo
histórico da Barra de Recursos.

Sem Qt aqui: roda numa linha própria com o laço do GLib e avisa a interface por funções.
"""
import threading

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

NOME = "org.freedesktop.Notifications"
CAMINHO = "/org/freedesktop/Notifications"
XML = """
<node>
  <interface name="org.freedesktop.Notifications">
    <method name="GetCapabilities"><arg type="as" direction="out"/></method>
    <method name="Notify">
      <arg type="s" name="app_name" direction="in"/>
      <arg type="u" name="replaces_id" direction="in"/>
      <arg type="s" name="app_icon" direction="in"/>
      <arg type="s" name="summary" direction="in"/>
      <arg type="s" name="body" direction="in"/>
      <arg type="as" name="actions" direction="in"/>
      <arg type="a{sv}" name="hints" direction="in"/>
      <arg type="i" name="expire_timeout" direction="in"/>
      <arg type="u" name="id" direction="out"/>
    </method>
    <method name="CloseNotification"><arg type="u" name="id" direction="in"/></method>
    <method name="GetServerInformation">
      <arg type="s" name="name" direction="out"/><arg type="s" name="vendor" direction="out"/>
      <arg type="s" name="version" direction="out"/><arg type="s" name="spec_version" direction="out"/>
    </method>
    <signal name="NotificationClosed"><arg type="u" name="id"/><arg type="u" name="reason"/></signal>
    <signal name="ActionInvoked"><arg type="u" name="id"/><arg type="s" name="action_key"/></signal>
  </interface>
  <interface name="org.duiaos.Notificacoes1">
    <method name="Limpar"/>
    <method name="Remover"><arg type="i" name="id" direction="in"/></method>
  </interface>
</node>
"""

# Motivos do fechamento (especificação): 1 venceu, 2 a pessoa fechou, 3 o programa pediu
VENCEU, FECHADA, PEDIDO = 1, 2, 3


import re  # noqa: E402

# Dica própria do DuiaOS: abrir uma tela do sistema ao clicar no balão (ex.: "configuracoes:atualizacoes").
# Só aplicativos do DuiaOS e uma seção com letras e hífen: nada de comandos arbitrários por notificação.
ABRIR_PERMITIDO = re.compile(r"^(configuracoes|loja|explorador-de-arquivos|central-de-ia)(:[a-z-]{1,40})?$")


def interpretar(app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout):
    """Notify → dicionário simples para a interface."""
    urgencia = hints.get("urgency", 1)
    try:
        urgencia = int(urgencia)
    except (TypeError, ValueError):
        urgencia = 1
    imagem = hints.get("image-path") or hints.get("image_path") or ""
    pares = [(actions[i], actions[i + 1]) for i in range(0, len(actions) - 1, 2)]
    return {
        "app": app_name or "Aplicativo",
        "substitui": int(replaces_id),
        "icone": str(imagem or app_icon or hints.get("desktop-entry", "") or ""),
        "titulo": summary,
        "texto": body,
        "acoes": [{"chave": c, "rotulo": r} for c, r in pares if c != "default"],
        "temPadrao": any(c == "default" for c, _ in pares),
        "urgencia": urgencia,
        "tempo": int(expire_timeout),
        "residente": bool(hints.get("resident", False)),
        "abrir": str(hints.get("x-duiaos-abrir", "")) if ABRIR_PERMITIDO.match(str(hints.get("x-duiaos-abrir", ""))) else "",
    }


class Servico:
    """Dono do nome org.freedesktop.Notifications. ao_notificar(id, dados), ao_fechar(id), ao_limpar(),
    ao_remover(id) são chamadas nesta linha; a interface deve passá-las para a dela."""

    def __init__(self, ao_notificar, ao_fechar, ao_limpar, ao_remover):
        self.ao_notificar, self.ao_fechar, self.ao_limpar, self.ao_remover = ao_notificar, ao_fechar, ao_limpar, ao_remover
        self.conexao = None
        self._proximo = 1
        self._trava = threading.Lock()
        self.pronto = threading.Event()
        self.erro = ""

    def iniciar(self):
        threading.Thread(target=self._rodar, daemon=True).start()
        self.pronto.wait(10)
        return not self.erro

    def _rodar(self):
        contexto = GLib.MainContext.new()
        contexto.push_thread_default()
        try:
            self.conexao = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            info = Gio.DBusNodeInfo.new_for_xml(XML)
            for interface in info.interfaces:
                self.conexao.register_object(CAMINHO, interface, self._chamada, None, None)
            resposta = self.conexao.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                                              "RequestName", GLib.Variant("(su)", (NOME, 4)),  # 4 = não esperar na fila
                                              GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NONE, -1, None)
            if resposta.unpack()[0] not in (1, 4):      # 1 = dono; 4 = já era
                self.erro = "Outro serviço de notificações já está rodando."
        except GLib.Error as erro:
            self.erro = erro.message
        self.pronto.set()
        if self.erro:
            return
        GLib.MainLoop.new(contexto, False).run()

    def _chamada(self, _conexao, _remetente, _caminho, interface, metodo, parametros, invocacao):
        if metodo == "GetCapabilities":
            invocacao.return_value(GLib.Variant("(as)", (["body", "actions", "icon-static", "persistence"],)))
        elif metodo == "GetServerInformation":
            invocacao.return_value(GLib.Variant("(ssss)", ("DuiaOS", "DuiaOS", "1.0", "1.2")))
        elif metodo == "Notify":
            dados = interpretar(*parametros.unpack())
            with self._trava:
                if dados["substitui"] > 0:
                    identificador = dados["substitui"]
                else:
                    identificador = self._proximo
                    self._proximo += 1
            invocacao.return_value(GLib.Variant("(u)", (identificador,)))
            self.ao_notificar(identificador, dados)
        elif metodo == "CloseNotification":
            identificador = parametros.unpack()[0]
            invocacao.return_value(None)
            self.ao_fechar(identificador)
            self.fechada(identificador, PEDIDO)
        elif metodo == "Limpar":
            invocacao.return_value(None)
            self.ao_limpar()
        elif metodo == "Remover":
            invocacao.return_value(None)
            self.ao_remover(parametros.unpack()[0])
        else:
            invocacao.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", metodo)

    # Sinais (o GDBusConnection pode ser usado de qualquer linha)
    def fechada(self, identificador, motivo):
        if self.conexao:
            self.conexao.emit_signal(None, CAMINHO, NOME, "NotificationClosed", GLib.Variant("(uu)", (identificador, motivo)))

    def acao(self, identificador, chave):
        if self.conexao:
            self.conexao.emit_signal(None, CAMINHO, NOME, "ActionInvoked", GLib.Variant("(us)", (identificador, chave)))
