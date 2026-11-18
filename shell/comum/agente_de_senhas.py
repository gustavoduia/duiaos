"""DuiaOS — agente de senhas de rede (ADR 070): quem responde quando o NetworkManager pede uma senha.

O NetworkManager pede senhas a "agentes" registrados pela sessão (D-Bus do sistema, interface
org.freedesktop.NetworkManager.SecretAgent): senha da Wi-Fi trocada, Wi-Fi corporativo (802.1X), VPN com
senha a cada vez, chave do WireGuard, código do chip (PIN). No GNOME quem responde é o gnome-shell; no
DuiaOS, este agente, que roda dentro da Barra de Recursos (sempre aberta na sessão).

Para cada pedido ele abre a janela "Senha da rede" (shell/barra-de-recursos/senha_de_rede.py, um processo
à parte com uma janela comum) e devolve o que a pessoa digitou. "Lembrar" grava a senha na conexão (pelo
NetworkManager, como a senha da Wi-Fi comum), para não perguntar de novo.

OpenConnect (VPN de empresas: AnyConnect, GlobalProtect, Fortinet): o plugin não recebe senha, e sim um
"cookie" de sessão. O agente pede usuário e senha e roda "openconnect --authenticate" para obter o cookie
(login com página da empresa, SSO, não é suportado: precisaria de um navegador embutido).

Uso: Agente(rodar_janela=...).iniciar() numa linha própria (o GLib tem o seu laço, separado do Qt).
"""
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

IDENTIFICADOR = "org.duiaos.AgenteDeSenhas"
CAMINHO = "/org/freedesktop/NetworkManager/SecretAgent"
INTERFACE = "org.freedesktop.NetworkManager.SecretAgent"
PERMITIR_INTERACAO, PEDIR_NOVA = 0x1, 0x2

XML = f"""
<node>
  <interface name="{INTERFACE}">
    <method name="GetSecrets">
      <arg name="connection" type="a{{sa{{sv}}}}" direction="in"/>
      <arg name="connection_path" type="o" direction="in"/>
      <arg name="setting_name" type="s" direction="in"/>
      <arg name="hints" type="as" direction="in"/>
      <arg name="flags" type="u" direction="in"/>
      <arg name="secrets" type="a{{sa{{sv}}}}" direction="out"/>
    </method>
    <method name="CancelGetSecrets">
      <arg name="connection_path" type="o" direction="in"/>
      <arg name="setting_name" type="s" direction="in"/>
    </method>
    <method name="SaveSecrets">
      <arg name="connection" type="a{{sa{{sv}}}}" direction="in"/>
      <arg name="connection_path" type="o" direction="in"/>
    </method>
    <method name="DeleteSecrets">
      <arg name="connection" type="a{{sa{{sv}}}}" direction="in"/>
      <arg name="connection_path" type="o" direction="in"/>
    </method>
  </interface>
</node>
"""

JANELA = Path(__file__).resolve().parents[1] / "barra-de-recursos" / "senha_de_rede.py"


class SemSenha(Exception):
    """A pessoa cancelou (ou não dá para perguntar): o NetworkManager desiste desta tentativa."""


def _texto(valor):
    if isinstance(valor, (bytes, bytearray)):
        return bytes(valor).decode("utf-8", "replace")
    if isinstance(valor, list) and all(isinstance(v, int) for v in valor):
        return bytes(valor).decode("utf-8", "replace")          # SSID: lista de bytes
    return str(valor or "")


def pedido(conexao, configuracao, dicas=(), nova=False):
    """O que perguntar para um pedido do NetworkManager: {titulo, texto, campos:[{chave, rotulo, senha}], lembrar,
    tipo}. ValueError se for um pedido que este agente não sabe atender."""
    geral = conexao.get("connection", {})
    nome = _texto(geral.get("id")) or "esta rede"
    errou = " A senha anterior não funcionou." if nova else ""
    if configuracao == "802-11-wireless-security":
        sem_fio = conexao.get("802-11-wireless", {})
        ssid = _texto(sem_fio.get("ssid")) or nome
        gerencia = _texto(conexao.get(configuracao, {}).get("key-mgmt"))
        chave = "wep-key0" if gerencia == "none" else "psk"
        return {"titulo": "Senha da Wi-Fi", "texto": f"A rede “{ssid}” pede a senha.{errou}", "tipo": "wifi",
                "campos": [{"chave": chave, "rotulo": "Senha", "senha": True}], "lembrar": True}
    if configuracao == "802-1x":
        x = conexao.get("802-1x", {})
        metodos = [_texto(m) for m in x.get("eap", [])]
        campos = []
        if not _texto(x.get("identity")):
            campos.append({"chave": "identity", "rotulo": "Usuário", "senha": False})
        if "tls" in metodos and not ({"peap", "ttls"} & set(metodos)):
            campos.append({"chave": "private-key-password", "rotulo": "Senha do certificado", "senha": True})
        else:
            campos.append({"chave": "password", "rotulo": "Senha", "senha": True})
        return {"titulo": "Entrar na rede", "texto": f"A rede “{nome}” pede usuário e senha (rede corporativa ou da faculdade).{errou}",
                "tipo": "802-1x", "campos": campos, "lembrar": True}
    if configuracao == "wireguard":
        return {"titulo": "Chave da VPN", "texto": f"A VPN “{nome}” precisa da chave privada do WireGuard.{errou}", "tipo": "wireguard",
                "campos": [{"chave": "private-key", "rotulo": "Chave privada", "senha": True}], "lembrar": True}
    if configuracao in ("gsm", "cdma"):
        if any("pin" in d for d in dicas):
            return {"titulo": "Código do chip (PIN)", "texto": f"O chip da rede celular “{nome}” está bloqueado.{errou}", "tipo": "gsm",
                    "campos": [{"chave": "pin", "rotulo": "PIN", "senha": True}], "lembrar": True}
        return {"titulo": "Senha da rede celular", "texto": f"A operadora de “{nome}” pede a senha.{errou}", "tipo": "gsm",
                "campos": [{"chave": "password", "rotulo": "Senha", "senha": True}], "lembrar": True}
    if configuracao == "vpn":
        vpn = conexao.get("vpn", {})
        servico = _texto(vpn.get("service-type")).rsplit(".", 1)[-1]
        dados = {k: _texto(v) for k, v in (vpn.get("data") or {}).items()}
        if servico == "openvpn":
            campos = []
            tipo_conexao = dados.get("connection-type", "tls")
            if tipo_conexao in ("password", "password-tls"):
                if not dados.get("username"):
                    campos.append({"chave": "@username", "rotulo": "Usuário", "senha": False})
                campos.append({"chave": "password", "rotulo": "Senha", "senha": True})
            if tipo_conexao in ("tls", "password-tls") and dados.get("cert-pass-flags", "0") != "4":
                campos.append({"chave": "cert-pass", "rotulo": "Senha do certificado (se tiver)", "senha": True})
            return {"titulo": "Entrar na VPN", "texto": f"A VPN “{nome}” pede a sua senha.{errou}", "tipo": "openvpn",
                    "campos": campos or [{"chave": "password", "rotulo": "Senha", "senha": True}], "lembrar": tipo_conexao != "tls"}
        if servico == "openconnect":
            return {"titulo": "Entrar na VPN da empresa", "texto": f"Usuário e senha da VPN “{nome}” ({dados.get('gateway', '')}).{errou}",
                    "tipo": "openconnect", "lembrar": False, "gateway": dados.get("gateway", ""),
                    "protocolo": dados.get("protocol", "anyconnect"),
                    "campos": [{"chave": "usuario", "rotulo": "Usuário", "senha": False}, {"chave": "senha", "rotulo": "Senha", "senha": True}]}
    raise ValueError(f"pedido não atendido: {configuracao}")


def autenticar_openconnect(gateway, protocolo, usuario, senha, rodar=None):
    """'openconnect --authenticate' → os segredos do plugin {cookie, gateway, gwcert}. SemSenha se o login falhar."""
    rodar = rodar or (lambda c, e: subprocess.run(c, input=e, capture_output=True, text=True, timeout=60, check=False))
    comando = ["openconnect", "--authenticate", "--non-inter", "--passwd-on-stdin", f"--protocol={protocolo}",
               "--user", usuario, gateway]
    try:
        r = rodar(comando, senha + "\n")
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise SemSenha(f"o openconnect não respondeu: {erro}") from erro
    valores = dict(re.findall(r"^(COOKIE|HOST|CONNECT_URL|FINGERPRINT|RESOLVE)='?([^'\n]*)'?$", r.stdout, re.M))
    if r.returncode != 0 or "COOKIE" not in valores:
        raise SemSenha("usuário ou senha da VPN não aceitos")
    return {"cookie": valores["COOKIE"], "gateway": valores.get("CONNECT_URL") or valores.get("HOST", gateway),
            "gwcert": valores.get("FINGERPRINT", "")}


def abrir_janela(dados):
    """Abre a janela "Senha da rede" e devolve {valores, lembrar}; SemSenha se cancelar."""
    ambiente = {k: v for k, v in os.environ.items() if k != "QT_WAYLAND_SHELL_INTEGRATION"}   # janela comum, não painel
    try:
        r = subprocess.run([sys.executable, str(JANELA)], input=json.dumps(dados), capture_output=True, text=True,
                           timeout=600, env=ambiente, check=False)
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise SemSenha(str(erro)) from erro
    if r.returncode != 0 or not r.stdout.strip():
        raise SemSenha("cancelado")
    return json.loads(r.stdout)


def responder(pergunta, resposta, autenticar=autenticar_openconnect):
    """Resposta da janela → segredos no formato do NetworkManager {configuração: {chave: valor}}."""
    valores = resposta.get("valores", {})
    if pergunta["tipo"] == "openconnect":
        return {"vpn": {"secrets": autenticar(pergunta["gateway"], pergunta["protocolo"], valores.get("usuario", ""),
                                              valores.get("senha", ""))}}
    if pergunta["tipo"] == "openvpn":
        segredos = {k: v for k, v in valores.items() if not k.startswith("@") and v != ""}
        return {"vpn": {"secrets": segredos}}
    configuracao = {"wifi": "802-11-wireless-security", "802-1x": "802-1x", "wireguard": "wireguard", "gsm": "gsm"}[pergunta["tipo"]]
    return {configuracao: {k: v for k, v in valores.items() if v != ""}}


def lembrar(uuid, segredos, rodar=None):
    """Grava os segredos na conexão (flags 0: guardados pelo NetworkManager), para não perguntar de novo."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, timeout=15, check=False))
    args = []
    for configuracao, valores in segredos.items():
        if configuracao == "vpn":
            continue                      # a VPN guarda pelo próprio plugin: fica pedindo (senhas de VPN mudam)
        for chave, valor in valores.items():
            nome_nm = {"802-11-wireless-security": "wifi-sec"}.get(configuracao, configuracao)
            args += [f"{nome_nm}.{chave}", valor]
            flag = {"psk": "psk-flags", "wep-key0": "wep-key-flags", "password": "password-flags", "pin": "pin-flags",
                    "private-key": "private-key-flags", "private-key-password": "private-key-password-flags"}.get(chave)
            if flag:
                args += [f"{nome_nm}.{flag}", "0"]
    if args and uuid:
        rodar(["nmcli", "connection", "modify", uuid, *args])


class Agente:
    """O agente no D-Bus do sistema. `perguntar(dados) → {valores, lembrar}` é a janela (trocada nos testes)."""

    def __init__(self, perguntar=abrir_janela, ao_registrar=None):
        self.perguntar = perguntar
        self.ao_registrar = ao_registrar or (lambda ok: None)
        self.pedidos = []                 # (configuração, tipo) — para os testes e o diagnóstico

    def iniciar(self):
        threading.Thread(target=self._rodar, name="agente-de-senhas", daemon=True).start()

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
            conexao = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        except GLib.Error:
            self.ao_registrar(False)
            return
        info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]
        conexao.register_object(CAMINHO, info, lambda *a: self._chamada(Gio, GLib, *a), None, None)

        def registrar():
            try:
                conexao.call_sync("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/AgentManager",
                                  "org.freedesktop.NetworkManager.AgentManager", "Register", GLib.Variant("(s)", (IDENTIFICADOR,)),
                                  None, Gio.DBusCallFlags.NONE, 10000, None)
                self.ao_registrar(True)
            except GLib.Error:
                self.ao_registrar(False)
            return False
        sumiu = [False]
        registrar()

        def apareceu(*_):
            if sumiu[0]:                  # o NetworkManager reiniciou e esqueceu os agentes: registra de novo
                sumiu[0] = False
                registrar()
        Gio.bus_watch_name_on_connection(conexao, "org.freedesktop.NetworkManager", Gio.BusNameWatcherFlags.NONE,
                                         apareceu, lambda *_: sumiu.__setitem__(0, True))
        laco.run()

    def _chamada(self, Gio, GLib, _conexao, _remetente, _caminho, _interface, metodo, parametros, invocacao):  # noqa: N803
        if metodo != "GetSecrets":
            invocacao.return_value(None)
            return
        conexao, _caminho_conexao, configuracao, dicas, flags = parametros.unpack()

        def atender():
            try:
                if not flags & PERMITIR_INTERACAO:
                    raise SemSenha("sem interação")
                pergunta = pedido(conexao, configuracao, dicas, bool(flags & PEDIR_NOVA))
                self.pedidos.append((configuracao, pergunta["tipo"]))
                resposta = self.perguntar(pergunta)
                segredos = responder(pergunta, resposta)
                if resposta.get("lembrar") and pergunta.get("lembrar"):
                    lembrar(_texto(conexao.get("connection", {}).get("uuid")), segredos)
                variante = {cfg: {k: (GLib.Variant("a{ss}", v) if k == "secrets" else GLib.Variant("s", v)) for k, v in valores.items()}
                            for cfg, valores in segredos.items()}
                invocacao.return_value(GLib.Variant("(a{sa{sv}})", (variante,)))
            except (SemSenha, ValueError, KeyError) as erro:
                nome = "UserCanceled" if str(erro) == "cancelado" else "NoSecrets"
                invocacao.return_dbus_error(f"org.freedesktop.NetworkManager.SecretAgent.{nome}", str(erro)[:200])
        threading.Thread(target=atender, daemon=True).start()
