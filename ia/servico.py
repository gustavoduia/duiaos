#!/usr/bin/env python3
"""DuiaOS — serviço de IA do sistema (duiaos-ia, ADRs 029 e 030).

Guarda qual é o modelo de IA local ativo (um só para o sistema inteiro) e
baixa, ativa e remove modelos do catálogo pelo Ollama. Fala pelo D-Bus do
sistema (org.duiaos.IA1); quem pede mudança precisa da autorização
org.duiaos.ia.gerenciar do polkit (a pessoa sentada no computador tem).

Estado público (sem D-Bus): /var/lib/duiaos-ia/estado.json, legível por todos:
  {"ativo", "padrao", "endereco", "tarefa": {...} ou null, "ultima": {...} ou null}
O Wise e outros programas leem dali o modelo ativo e o progresso de download.

Uso: servico.py [--sessao] [--sem-polkit] [--pasta DIR] [--ollama URL] [--memoria-gb N]
  (--sessao, --sem-polkit e --memoria-gb são para testes, no barramento da sessão)
"""
import argparse
import json
import os
import shutil
import sys
import threading
import time
from pathlib import Path

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo as cat  # noqa: E402
from motor_ollama import Cancelado, ErroOllama, Ollama  # noqa: E402

NOME = "org.duiaos.IA1"
CAMINHO = "/org/duiaos/IA1"
ACAO_POLKIT = "org.duiaos.ia.gerenciar"
PASTA_MODELOS = "/usr/share/ollama"

XML = """
<node>
  <interface name="org.duiaos.IA1">
    <method name="Estado"><arg name="json" type="s" direction="out"/></method>
    <method name="Baixar"><arg name="modelo" type="s" direction="in"/></method>
    <method name="Ativar"><arg name="modelo" type="s" direction="in"/></method>
    <method name="Remover"><arg name="modelo" type="s" direction="in"/></method>
    <method name="Cancelar"/>
    <method name="GarantirPadrao"/>
    <signal name="Mudou"><arg name="json" type="s"/></signal>
  </interface>
</node>
"""


class Recusa(Exception):
    """Pedido recusado; vira um erro D-Bus org.duiaos.IA1.Erro.<codigo>."""

    def __init__(self, codigo, mensagem):
        super().__init__(mensagem)
        self.codigo = codigo


class Servico:
    def __init__(self, pasta, ollama, usar_polkit=True, memoria_gb=None):
        self.pasta = Path(pasta)
        self.ollama = ollama
        self.usar_polkit = usar_polkit
        self.catalogo = cat.carregar()
        self.memoria_gb = memoria_gb if memoria_gb is not None else cat.memoria_total_gb()
        self.conexao = None
        self.tarefa = None            # download em andamento
        self.ultima = None            # resultado do último download
        self._cancelar = threading.Event()
        self._ultimo_sinal = 0.0
        self._instalados = set()
        self._ollama_ok = False
        self.config = self._ler_config()

    # ------------------------------------------------------------ persistência
    def _ler_config(self):
        try:
            dados = json.loads((self.pasta / "config.json").read_text())
            if isinstance(dados, dict):
                return {"ativo": str(dados.get("ativo") or ""),
                        "padrao_tratado": bool(dados.get("padrao_tratado"))}
        except (OSError, ValueError):
            pass
        return {"ativo": "", "padrao_tratado": False}

    def _gravar(self, nome, dados):
        self.pasta.mkdir(parents=True, exist_ok=True)
        temporario = self.pasta / (nome + ".tmp")
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=1))
        os.chmod(temporario, 0o644)
        os.replace(temporario, self.pasta / nome)

    def _atualizar_instalados(self):
        try:
            self._instalados = self.ollama.instalados()
            self._ollama_ok = True
        except ErroOllama:
            self._ollama_ok = False

    def estado_publico(self):
        return {
            "versao": 1,
            "ativo": self.config["ativo"],
            "padrao": self.catalogo.get("padrao", ""),
            "endereco": self.ollama.endereco,
            "ollama": self._ollama_ok,
            "memoria_gb": self.memoria_gb,
            "tarefa": self.tarefa,
            "ultima": self.ultima,
            # Modelos do catálogo já baixados: as telas sabem na hora quando um entra ou sai
            "instalados": sorted(m["id"] for _f, m, _l in cat.modelos(self.catalogo) if m["id"] in self._instalados),
            "atualizado": int(time.time()),
        }

    def estado_completo(self):
        return self.estado_publico() | {
            "familias": cat.montar(self.catalogo, self._instalados, self.config["ativo"],
                                   self.memoria_gb),
        }

    def mudou(self, recarregar=True):
        """Grava o estado público e avisa os clientes pelo sinal Mudou."""
        if recarregar:
            self._atualizar_instalados()
        self._gravar("config.json", self.config)
        self._gravar("estado.json", self.estado_publico())
        if self.conexao:
            self.conexao.emit_signal(None, CAMINHO, NOME, "Mudou",
                                     GLib.Variant("(s)", (json.dumps(self.estado_publico()),)))

    def conferir_ollama(self):
        """A cada 10 s: modelos baixados ou apagados por fora (ex.: "ollama rm") também avisam as telas."""
        if not self.tarefa:
            antes = (self._instalados, self._ollama_ok)
            self._atualizar_instalados()
            if (self._instalados, self._ollama_ok) != antes:
                self.mudou(recarregar=False)
        return True

    # ------------------------------------------------------------ autorização
    def autorizado(self, remetente):
        if not self.usar_polkit:
            return True
        uid = self.conexao.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
            "GetConnectionUnixUser", GLib.Variant("(s)", (remetente,)),
            GLib.VariantType("(u)"), Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
        if uid == 0:
            return True
        parametros = GLib.Variant("((sa{sv})sa{ss}us)", (
            ("system-bus-name", {"name": GLib.Variant("s", remetente)}),
            ACAO_POLKIT, {}, 0, ""))
        try:
            resultado = self.conexao.call_sync(
                "org.freedesktop.PolicyKit1", "/org/freedesktop/PolicyKit1/Authority",
                "org.freedesktop.PolicyKit1.Authority", "CheckAuthorization", parametros,
                GLib.VariantType("((bba{ss}))"), Gio.DBusCallFlags.NONE, 30000, None)
        except GLib.Error as erro:
            # Ex.: o polkit recusa a consulta se a ação não declarar este serviço
            # como dono (org.freedesktop.policykit.owner). Fica no journal.
            print(f"duiaos-ia: polkit não respondeu a autorização: {erro.message}", file=sys.stderr, flush=True)
            return False
        return bool(resultado.unpack()[0][0])

    # ------------------------------------------------------------ ações
    def _modelo(self, id_modelo):
        modelo = cat.procurar(self.catalogo, id_modelo)
        if not modelo:
            raise Recusa("Invalido", f"{id_modelo!r} não está no catálogo de modelos do DuiaOS.")
        return modelo

    def _exigir_ollama(self):
        self._atualizar_instalados()
        if not self._ollama_ok:
            raise Recusa("SemOllama", "A IA local (Ollama) não está respondendo. "
                                      "Veja: systemctl status ollama")

    def baixar(self, id_modelo, automatico=False):
        modelo = self._modelo(id_modelo)
        if self.tarefa:
            raise Recusa("Ocupado", f"Já há um download em andamento ({self.tarefa['modelo']}).")
        cabe, aviso = cat.avaliar(modelo["download_gb"], self.memoria_gb)
        if not cabe:
            raise Recusa("SemMemoria", aviso)
        pasta = PASTA_MODELOS if os.path.isdir(PASTA_MODELOS) else str(self.pasta)
        livre_gb = shutil.disk_usage(pasta).free / 1024 ** 3
        if livre_gb < modelo["download_gb"] * 1.1 + 1:
            raise Recusa("SemEspaco", f"Faltam cerca de {modelo['download_gb'] * 1.1 + 1 - livre_gb:.0f} GB "
                                      "livres no disco para baixar este modelo.")
        self._cancelar.clear()
        self.tarefa = {"tipo": "baixar", "modelo": id_modelo, "automatico": automatico,
                       "concluido": 0, "total": int(modelo["download_gb"] * 1024 ** 3),
                       "fracao": 0.0, "status": "iniciando", "inicio": int(time.time())}
        self.ultima = None
        threading.Thread(target=self._baixar, args=(id_modelo,), daemon=True).start()
        self.mudou(recarregar=False)

    def _baixar(self, id_modelo):
        try:
            if not self.ollama.esperar(60):
                raise ErroOllama("A IA local (Ollama) não está respondendo.")
            self.ollama.baixar(id_modelo,
                               lambda c, t, s: GLib.idle_add(self._progresso, c, t, s),
                               self._cancelar.is_set)
            GLib.idle_add(self._fim, id_modelo, "ok", "")
        except Cancelado:
            GLib.idle_add(self._fim, id_modelo, "cancelado", "Download cancelado.")
        except ErroOllama as erro:
            GLib.idle_add(self._fim, id_modelo, "erro", str(erro))
        except Exception as erro:  # noqa: BLE001 — qualquer falha vira mensagem, o serviço segue
            GLib.idle_add(self._fim, id_modelo, "erro", f"Falha inesperada: {erro}"[:200])

    def _progresso(self, concluido, total, status):
        if not self.tarefa:
            return False
        if total > 0:
            self.tarefa["concluido"], self.tarefa["total"] = concluido, total
            self.tarefa["fracao"] = round(min(concluido / total, 1.0), 4)
        mudou_status = status != self.tarefa["status"]
        self.tarefa["status"] = status
        agora = time.monotonic()
        if mudou_status or agora - self._ultimo_sinal >= 0.5:     # no máximo 2 avisos por segundo
            self._ultimo_sinal = agora
            self.mudou(recarregar=False)
        return False

    def _fim(self, id_modelo, resultado, mensagem):
        automatico = bool(self.tarefa and self.tarefa.get("automatico"))
        self.tarefa = None
        self.ultima = {"modelo": id_modelo, "resultado": resultado, "mensagem": mensagem,
                       "quando": int(time.time())}
        self._atualizar_instalados()
        if resultado == "ok":
            if automatico or id_modelo == self.catalogo.get("padrao"):
                self.config["padrao_tratado"] = True
            # Sem modelo ativo (1º login, por exemplo): o que acabou de chegar vira o ativo
            if not self.config["ativo"] or self.config["ativo"] not in self._instalados or automatico:
                self.config["ativo"] = id_modelo
        self.mudou(recarregar=False)
        return False

    def ativar(self, id_modelo):
        self._modelo(id_modelo)
        self._exigir_ollama()
        if id_modelo not in self._instalados:
            raise Recusa("NaoInstalado", f"Baixe {id_modelo} antes de ativá-lo.")
        self.config["ativo"] = id_modelo
        self.config["padrao_tratado"] = True
        self.mudou(recarregar=False)

    def remover(self, id_modelo):
        self._modelo(id_modelo)
        if self.tarefa and self.tarefa["modelo"] == id_modelo:
            raise Recusa("Ocupado", "Cancele o download antes de remover este modelo.")
        if id_modelo == self.config["ativo"]:
            raise Recusa("Ativo", "Este é o modelo ativo do sistema. Ative outro antes de removê-lo.")
        self._exigir_ollama()
        try:
            self.ollama.remover(id_modelo)
        except ErroOllama as erro:
            raise Recusa("SemOllama", str(erro)) from erro
        self.config["padrao_tratado"] = True
        self.mudou()

    def cancelar(self):
        if self.tarefa:
            self._cancelar.set()

    def garantir_padrao(self):
        """1º login: sem modelo ativo, ativa o padrão ou começa a baixá-lo."""
        self._atualizar_instalados()
        if not self._ollama_ok or self.tarefa:
            return
        ativo = self.config["ativo"]
        if ativo and ativo in self._instalados:
            return
        padrao = self.catalogo.get("padrao", "")
        if padrao in self._instalados:
            self.config["ativo"] = padrao
            self.mudou(recarregar=False)
            return
        # Outro modelo do catálogo já baixado (ex.: o ativo foi apagado por fora): usa o primeiro
        for _familia, modelo, _licenca in cat.modelos(self.catalogo):
            if modelo["id"] in self._instalados:
                self.config["ativo"] = modelo["id"]
                self.mudou(recarregar=False)
                return
        if self.config["padrao_tratado"] and ativo:
            return
        # O padrão; se não couber na memória deste computador, um menor da mesma família
        recusa = None
        for candidato in [padrao] + list(self.catalogo.get("padrao_alternativas", [])):
            try:
                self.baixar(candidato, automatico=True)
                return
            except Recusa as erro:
                recusa = recusa or erro
                if erro.codigo != "SemMemoria":
                    break
        self.ultima = {"modelo": padrao, "resultado": "erro", "mensagem": str(recusa),
                       "quando": int(time.time())}
        self.mudou(recarregar=False)

    # ------------------------------------------------------------ D-Bus
    def ao_chamar(self, _conexao, remetente, _caminho, _interface, metodo, parametros, invocacao):
        try:
            if metodo == "Estado":
                self._atualizar_instalados()
                invocacao.return_value(GLib.Variant("(s)", (json.dumps(self.estado_completo()),)))
                return
            # GarantirPadrao só aplica a regra do sistema (o modelo padrão quando
            # não há nenhum ativo): não escolhe nada, por isso não pede autorização.
            if metodo != "GarantirPadrao" and not self.autorizado(remetente):
                raise Recusa("NaoAutorizado", "Sem autorização para mudar a IA do sistema "
                                              "(use a sessão no computador ou sudo).")
            argumentos = parametros.unpack()
            if metodo == "Baixar":
                self.baixar(argumentos[0])
            elif metodo == "Ativar":
                self.ativar(argumentos[0])
            elif metodo == "Remover":
                self.remover(argumentos[0])
            elif metodo == "Cancelar":
                self.cancelar()
            elif metodo == "GarantirPadrao":
                self.garantir_padrao()
            else:
                raise Recusa("Invalido", f"Método desconhecido: {metodo}")
            invocacao.return_value(None)
        except Recusa as recusa:
            invocacao.return_dbus_error(f"{NOME}.Erro.{recusa.codigo}", str(recusa))
        except Exception as erro:  # noqa: BLE001
            invocacao.return_dbus_error(f"{NOME}.Erro.Interno", f"Falha interna: {erro}"[:300])


def main():
    argumentos = argparse.ArgumentParser(description="Serviço de IA do DuiaOS")
    argumentos.add_argument("--sessao", action="store_true", help="usar o barramento da sessão (testes)")
    argumentos.add_argument("--sem-polkit", action="store_true", help="não pedir autorização (testes)")
    argumentos.add_argument("--pasta", default=os.environ.get("STATE_DIRECTORY", "/var/lib/duiaos-ia"))
    argumentos.add_argument("--ollama", default=os.environ.get("DUIAOS_IA_OLLAMA", "http://127.0.0.1:11434"))
    argumentos.add_argument("--memoria-gb", type=float, help="memória fingida (testes)")
    opcoes = argumentos.parse_args()

    servico = Servico(opcoes.pasta, Ollama(opcoes.ollama), usar_polkit=not opcoes.sem_polkit,
                      memoria_gb=opcoes.memoria_gb)
    laco = GLib.MainLoop()
    info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]

    def ao_conectar(conexao, _nome):
        servico.conexao = conexao
        conexao.register_object(CAMINHO, info, servico.ao_chamar, None, None)

    def ao_receber_nome(_conexao, _nome):
        servico.mudou()            # grava o estado público assim que o serviço sobe
        GLib.timeout_add_seconds(10, servico.conferir_ollama)

    def ao_perder_nome(_conexao, _nome):
        print("duiaos-ia: não consegui o nome org.duiaos.IA1 no D-Bus.", file=sys.stderr)
        laco.quit()

    barramento = Gio.BusType.SESSION if opcoes.sessao else Gio.BusType.SYSTEM
    Gio.bus_own_name(barramento, NOME, Gio.BusNameOwnerFlags.NONE,
                     ao_conectar, ao_receber_nome, ao_perder_nome)
    laco.run()
    return 1


if __name__ == "__main__":
    sys.exit(main())
