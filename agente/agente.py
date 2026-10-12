#!/usr/bin/env python3
"""DuiaOS — duiaos-agente: o serviço privilegiado mínimo (ADR 034, W2 do Wise).

Faz, como root, só as ações de uma lista fechada (plano.ACOES): atualizar o
sistema, instalar e remover aplicativos pelo apt. Fala pelo D-Bus do sistema
(org.duiaos.Agente1) em dois passos:

  Preparar(acao, argumentos_json) -> plano_json
      Sem autorização: só simula ("apt-get -s") e devolve o impacto
      {"id", "acao", "argumentos", "resumo", "mudancas", "baixar_bytes",
       "espaco_bytes", "recusa"}. Nada muda no sistema.
  Executar(id)
      Precisa do polkit (org.duiaos.agente.<acao>) e de um plano preparado pela
      mesma pessoa há menos de 10 minutos. Simula de novo: se o impacto mudou,
      recusa (a pessoa aprovou outra coisa). Depois executa e confere.
  Estado() -> {"tarefa": {...} ou null, "ultima": {...} ou null}
  Cancelar()   só enquanto baixa (parar no meio da instalação estraga pacotes)
  sinal Mudou(json)   o mesmo de Estado, no máximo 2 vezes por segundo

Quem aprova é a pessoa, na interface do Wise (ou de outro programa do
sistema); este serviço confere que a ação é permitida e registra tudo em
/var/log/duiaos-agente/acoes.jsonl.

Uso: agente.py [--sessao] [--sem-polkit] [--simular-apt]   (as três para testes)
"""
import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plano as pl  # noqa: E402
from plano import Recusa  # noqa: E402

NOME = "org.duiaos.Agente1"
CAMINHO = "/org/duiaos/Agente1"
VALIDADE_PLANO = 600            # segundos
INTERVALO_UPDATE = 300          # apt-get update no máximo a cada 5 min
REGISTRO = Path(os.environ.get("LOGS_DIRECTORY", "/var/log/duiaos-agente")) / "acoes.jsonl"

XML = """
<node>
  <interface name="org.duiaos.Agente1">
    <method name="Preparar">
      <arg name="acao" type="s" direction="in"/>
      <arg name="argumentos" type="s" direction="in"/>
      <arg name="plano" type="s" direction="out"/>
    </method>
    <method name="Executar"><arg name="id" type="s" direction="in"/></method>
    <method name="Estado"><arg name="json" type="s" direction="out"/></method>
    <method name="Cancelar"/>
    <signal name="Mudou"><arg name="json" type="s"/></signal>
  </interface>
</node>
"""

AMBIENTE_APT = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8",
                "DEBIAN_FRONTEND": "noninteractive", "APT_LISTCHANGES_FRONTEND": "none",
                "NEEDRESTART_MODE": "l"}
OPCOES_APT = ["-y", "-q", "-o", "DPkg::Lock::Timeout=120",
              "-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold"]


class Apt:
    """Chamadas ao apt. Separado para os testes trocarem por um de mentira."""

    def rodar(self, argumentos, tempo=300):
        r = subprocess.run(argumentos, capture_output=True, text=True, env=AMBIENTE_APT, timeout=tempo,
                           check=False)
        return r.returncode, r.stdout, r.stderr

    def atualizar_listas(self):
        codigo, _saida, erro = self.rodar(["apt-get", "-q", "-o", "DPkg::Lock::Timeout=60", "update"], tempo=300)
        if codigo != 0:
            raise Recusa("SemRede", "Não consegui consultar os repositórios (sem internet?). "
                                    + (erro.strip().splitlines() or [""])[-1][:160])

    def simular(self, comando):
        codigo, saida, erro = self.rodar(["apt-get", "-s", "-q", *comando])
        if codigo != 0:
            linhas = [l for l in erro.splitlines() if l.startswith("E:")] or erro.splitlines() or [""]
            raise Recusa("Impossivel", "O apt não aceita esta ação: " + linhas[-1][:200])
        return saida

    def politica(self, pacote):
        return self.rodar(["apt-cache", "policy", pacote], tempo=60)[1]

    def mostrar(self, pacotes):
        if not pacotes:
            return ""
        return self.rodar(["apt-cache", "show", "--no-all-versions", *pacotes], tempo=60)[1]

    def instalados(self):
        return self.rodar(["dpkg-query", "-W", "-f", "${Package}\t${Essential}\t${Priority}\n"], tempo=60)[1]

    def executar(self, comando, ao_progresso, ao_processo):
        """Roda o apt de verdade; ao_progresso(fracao, mensagem). Devolve (código, fim da saída)."""
        leitura, escrita = os.pipe()
        processo = subprocess.Popen(["apt-get", *OPCOES_APT, "-o", f"APT::Status-Fd={escrita}", *comando],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=AMBIENTE_APT,
                                    pass_fds=(escrita,), text=True)
        os.close(escrita)
        ao_processo(processo)
        saida = []
        leitor = threading.Thread(target=lambda: saida.extend(processo.stdout), daemon=True)
        leitor.start()
        with os.fdopen(leitura, "r", errors="replace") as status:
            for linha in status:
                fracao, mensagem = pl.ler_progresso(linha)
                if fracao is not None:
                    ao_progresso(fracao, mensagem)
        codigo = processo.wait()
        leitor.join(5)
        return codigo, "".join(saida[-40:])


class AptDeMentira(Apt):
    """--simular-apt: nada muda no sistema; serve para testar a interface do Wise."""

    def atualizar_listas(self):
        time.sleep(0.2)

    def simular(self, comando):
        if comando[0] == "full-upgrade":
            return "Inst exemplo [1.0-1] (1.1-1 DuiaOS:teste [all])\n"
        if comando[0] == "install":
            return f"Inst {comando[-1]} (1.0-1 Debian:13/stable [amd64])\n"
        return f"Remv {comando[-1]} [1.0-1]\n"

    def politica(self, pacote):
        instalado = "1.0-1" if pacote.startswith("instalado") else "(none)"
        return f"{pacote}:\n  Installed: {instalado}\n  Candidate: 1.0-1\n"

    def mostrar(self, pacotes):
        return "".join(f"Package: {p}\nSize: 1048576\nInstalled-Size: 4096\n\n" for p in pacotes)

    def instalados(self):
        return "libc6\tyes\trequired\nduiaos-shell\tno\toptional\n"

    def executar(self, comando, ao_progresso, ao_processo):
        for i in range(1, 11):
            time.sleep(0.05)
            ao_progresso(i / 10, f"Passo {i} de 10")
        return 0, "ok"


class Agente:
    def __init__(self, apt=None, usar_polkit=True, registro=REGISTRO):
        self.apt = apt or Apt()
        self.usar_polkit = usar_polkit
        self.registro = Path(registro)
        self.conexao = None
        self.planos = {}
        self.tarefa = None
        self.ultima = None
        self._trava = threading.Lock()      # um apt por vez
        self._processo = None
        self._ultimo_update = 0.0
        self._ultimo_sinal = 0.0
        self.ultimo_uso = time.monotonic()

    # --------------------------------------------------------------- estado
    def estado(self):
        return {"tarefa": self.tarefa, "ultima": self.ultima}

    def mudou(self, forcar=True):
        agora = time.monotonic()
        if not forcar and agora - self._ultimo_sinal < 0.5:
            return
        self._ultimo_sinal = agora
        dados = json.dumps(self.estado(), ensure_ascii=False)
        def emitir():
            if self.conexao is not None:
                self.conexao.emit_signal(None, CAMINHO, NOME, "Mudou", GLib.Variant("(s)", (dados,)))
            return False
        GLib.idle_add(emitir)

    def registrar(self, evento, **dados):
        linha = json.dumps({"quando": int(time.time()), "evento": evento, **dados}, ensure_ascii=False)
        try:
            self.registro.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registro, "a", encoding="utf-8") as arquivo:
                arquivo.write(linha + "\n")
        except OSError as erro:
            print(f"duiaos-agente: não consegui registrar: {erro}", file=sys.stderr, flush=True)

    # --------------------------------------------------------------- planos
    def _simular(self, acao, argumentos):
        """Simulação completa: (mudanças, resumo, recusa, baixar, espaço)."""
        if acao == "atualizar_sistema" and time.monotonic() - self._ultimo_update > INTERVALO_UPDATE:
            self.apt.atualizar_listas()
            self._ultimo_update = time.monotonic()
        instalado = candidato = ""
        if "pacote" in argumentos:
            instalado, candidato = pl.ler_politica(self.apt.politica(argumentos["pacote"]))
        mudancas = {"instalar": [], "atualizar": [], "remover": []}
        recusa = None
        try:
            if acao == "instalar_aplicativo" and (instalado or not candidato):
                raise Recusa("Previa", "")            # avaliar() explica
            if acao == "remover_aplicativo" and not instalado:
                raise Recusa("Previa", "")
            mudancas = pl.ler_simulacao(self.apt.simular(pl.comando_apt(acao, argumentos)))
        except Recusa as erro:
            if erro.codigo != "Previa":
                recusa = erro
        resumo, recusa_plano = pl.avaliar(acao, argumentos, mudancas, pl.ler_protegidos(self.apt.instalados()),
                                          instalado, candidato)
        recusa = recusa or recusa_plano
        novos = [m["pacote"] for m in mudancas["instalar"] + mudancas["atualizar"]]
        baixar, espaco = pl.tamanhos(self.apt.mostrar(novos[:400]))
        return mudancas, resumo, recusa, baixar, espaco

    def preparar(self, acao, argumentos, uid):
        argumentos = pl.validar(acao, argumentos)
        with self._trava:
            mudancas, resumo, recusa, baixar, espaco = self._simular(acao, argumentos)
        agora = time.time()
        self.planos = {k: v for k, v in self.planos.items() if agora - v["quando"] < VALIDADE_PLANO}
        plano = {"id": secrets.token_hex(8), "acao": acao, "argumentos": argumentos, "resumo": resumo,
                 "mudancas": mudancas, "baixar_bytes": baixar, "espaco_bytes": espaco,
                 "recusa": {"codigo": recusa.codigo, "mensagem": str(recusa)} if recusa else None}
        if not recusa:
            self.planos[plano["id"]] = {**plano, "uid": uid, "quando": agora}
        self.registrar("preparado", uid=uid, acao=acao, argumentos=argumentos, resumo=resumo,
                       recusa=plano["recusa"])
        return plano

    @staticmethod
    def _assinatura(mudancas):
        return sorted((k, m["pacote"], m["para"]) for k, lista in mudancas.items() for m in lista)

    def executar(self, id_plano, uid, autorizado):
        plano = self.planos.get(id_plano)
        if not plano or time.time() - plano["quando"] > VALIDADE_PLANO:
            raise Recusa("Vencido", "Esta aprovação venceu. Peça de novo para eu conferir o que mudou.")
        if plano["uid"] != uid and uid != 0:
            raise Recusa("NaoAutorizado", "Este plano foi preparado por outra pessoa.")
        if not autorizado(f"org.duiaos.agente.{plano['acao']}"):
            raise Recusa("NaoAutorizado", "Sem autorização para esta ação (use a sessão no computador ou sudo).")
        if self.tarefa:
            raise Recusa("Ocupado", "Já estou fazendo outra ação no sistema. Espere ela terminar.")
        del self.planos[id_plano]
        self.tarefa = {"id": id_plano, "acao": plano["acao"], "argumentos": plano["argumentos"],
                       "resumo": plano["resumo"], "estado": "conferindo", "fracao": 0.0, "mensagem": "",
                       "uid": uid, "inicio": int(time.time())}
        self.mudou()
        threading.Thread(target=self._rodar, args=(plano,), daemon=True).start()

    def _rodar(self, plano):
        acao, argumentos = plano["acao"], plano["argumentos"]
        resultado, mensagem, detalhe = "erro", "", ""
        try:
            with self._trava:
                # Confere de novo: a pessoa aprovou ESTE impacto
                mudancas, _resumo, recusa, _b, _e = self._simular(acao, argumentos)
                if recusa:
                    raise recusa
                if self._assinatura(mudancas) != self._assinatura(plano["mudancas"]):
                    raise Recusa("Mudou", "O que esta ação faria mudou desde a aprovação. Peça de novo.")
                self.tarefa.update(estado="executando", mensagem="Começando")
                self.mudou()
                codigo, detalhe = self.apt.executar(pl.comando_apt(acao, argumentos), self._progresso,
                                                    self._guardar_processo)
                self._processo = None
                if self.tarefa.get("cancelado"):
                    resultado, mensagem = "cancelada", "Cancelado antes de instalar. Nada mudou."
                elif codigo != 0:
                    mensagem = f"O apt terminou com erro (detalhes em {self.registro})."
                else:
                    self.tarefa.update(estado="verificando", fracao=1.0, mensagem="Conferindo")
                    self.mudou()
                    resultado, mensagem = self._verificar(acao, argumentos)
        except Recusa as erro:
            resultado, mensagem = "recusada", str(erro)
        except Exception as erro:  # noqa: BLE001
            mensagem = f"Falha interna: {erro}"[:300]
        self.ultima = {"id": plano["id"], "acao": acao, "argumentos": argumentos, "resultado": resultado,
                       "mensagem": mensagem, "quando": int(time.time())}
        self.registrar("executado", uid=self.tarefa["uid"] if self.tarefa else None, acao=acao,
                       argumentos=argumentos, resultado=resultado, mensagem=mensagem, saida=detalhe[-2000:])
        self.tarefa = None
        self.mudou()

    def _progresso(self, fracao, mensagem):
        if self.tarefa:
            self.tarefa.update(fracao=fracao, mensagem=mensagem)
            self.mudou(forcar=False)

    def _guardar_processo(self, processo):
        self._processo = processo

    def _verificar(self, acao, argumentos):
        if acao == "atualizar_sistema":
            sobrou = pl.ler_simulacao(self.apt.simular(["full-upgrade"]))
            if sobrou["atualizar"]:
                return "ok", f"Atualizado. {len(sobrou['atualizar'])} pacote(s) ficaram para depois."
            return "ok", "Sistema atualizado."
        instalado, _ = pl.ler_politica(self.apt.politica(argumentos["pacote"]))
        if acao == "instalar_aplicativo":
            return ("ok", f"{argumentos['pacote']} instalado ({instalado}).") if instalado else \
                ("erro", f"O apt terminou, mas {argumentos['pacote']} não aparece instalado.")
        return ("ok", f"{argumentos['pacote']} removido.") if not instalado else \
            ("erro", f"O apt terminou, mas {argumentos['pacote']} continua instalado.")

    def cancelar(self):
        if not self.tarefa:
            return
        self.ultimo_uso = time.monotonic()
        if self.tarefa["estado"] == "executando" and self.tarefa["fracao"] >= 0.5:
            raise Recusa("NoMeio", "Já estou instalando: parar agora estragaria pacotes. Falta pouco.")
        self.tarefa["cancelado"] = True
        if self._processo and self._processo.poll() is None:
            self._processo.send_signal(signal.SIGINT)

    # --------------------------------------------------------------- D-Bus
    def _uid(self, remetente):
        return self.conexao.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
            "GetConnectionUnixUser", GLib.Variant("(s)", (remetente,)),
            GLib.VariantType("(u)"), Gio.DBusCallFlags.NONE, -1, None).unpack()[0]

    def _autorizador(self, remetente, uid):
        def autorizado(acao_polkit):
            if not self.usar_polkit or uid == 0:
                return True
            parametros = GLib.Variant("((sa{sv})sa{ss}us)", (
                ("system-bus-name", {"name": GLib.Variant("s", remetente)}), acao_polkit, {}, 0, ""))
            try:
                resultado = self.conexao.call_sync(
                    "org.freedesktop.PolicyKit1", "/org/freedesktop/PolicyKit1/Authority",
                    "org.freedesktop.PolicyKit1.Authority", "CheckAuthorization", parametros,
                    GLib.VariantType("((bba{ss}))"), Gio.DBusCallFlags.NONE, 30000, None)
            except GLib.Error as erro:
                print(f"duiaos-agente: polkit não respondeu: {erro.message}", file=sys.stderr, flush=True)
                return False
            return bool(resultado.unpack()[0][0])
        return autorizado

    def ao_chamar(self, _conexao, remetente, _caminho, _interface, metodo, parametros, invocacao):
        self.ultimo_uso = time.monotonic()
        # Preparar demora (simula o apt): roda fora do laço do D-Bus
        def responder():
            try:
                uid = self._uid(remetente)
                if metodo == "Estado":
                    valor = GLib.Variant("(s)", (json.dumps(self.estado(), ensure_ascii=False),))
                elif metodo == "Preparar":
                    acao, texto = parametros.unpack()
                    try:
                        argumentos = json.loads(texto or "{}")
                    except ValueError as erro:
                        raise Recusa("Invalido", "Os argumentos não são JSON válido.") from erro
                    valor = GLib.Variant("(s)", (json.dumps(self.preparar(acao, argumentos, uid),
                                                            ensure_ascii=False),))
                elif metodo == "Executar":
                    self.executar(parametros.unpack()[0], uid, self._autorizador(remetente, uid))
                    valor = None
                elif metodo == "Cancelar":
                    self.cancelar()
                    valor = None
                else:
                    raise Recusa("Invalido", f"Método desconhecido: {metodo}")
                GLib.idle_add(lambda: (invocacao.return_value(valor), False)[1])
            except Recusa as recusa:
                nome, texto = f"{NOME}.Erro.{recusa.codigo}", str(recusa)
                GLib.idle_add(lambda: (invocacao.return_dbus_error(nome, texto), False)[1])
            except Exception as erro:  # noqa: BLE001
                texto = f"Falha interna: {erro}"[:300]
                GLib.idle_add(lambda: (invocacao.return_dbus_error(f"{NOME}.Erro.Interno", texto), False)[1])
        threading.Thread(target=responder, daemon=True).start()


def main():
    argumentos = argparse.ArgumentParser(description="Agente do sistema do DuiaOS")
    argumentos.add_argument("--sessao", action="store_true", help="barramento da sessão (testes)")
    argumentos.add_argument("--sem-polkit", action="store_true", help="não pedir autorização (testes)")
    argumentos.add_argument("--simular-apt", action="store_true", help="não mexe no sistema (testes)")
    argumentos.add_argument("--registro", default=str(REGISTRO))
    opcoes = argumentos.parse_args()

    agente = Agente(AptDeMentira() if opcoes.simular_apt else Apt(), usar_polkit=not opcoes.sem_polkit,
                    registro=opcoes.registro)
    laco = GLib.MainLoop()
    info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]

    def ao_conectar(conexao, _nome):
        agente.conexao = conexao
        conexao.register_object(CAMINHO, info, agente.ao_chamar, None, None)

    def ao_perder_nome(_conexao, _nome):
        print("duiaos-agente: não consegui o nome org.duiaos.Agente1 no D-Bus.", file=sys.stderr)
        laco.quit()

    # Sem uso por 10 minutos e sem tarefa: sai (o D-Bus abre de novo quando preciso)
    def ocioso():
        if agente.tarefa is None and time.monotonic() - agente.ultimo_uso > VALIDADE_PLANO:
            laco.quit()
            return False
        return True
    GLib.timeout_add_seconds(60, ocioso)

    barramento = Gio.BusType.SESSION if opcoes.sessao else Gio.BusType.SYSTEM
    Gio.bus_own_name(barramento, NOME, Gio.BusNameOwnerFlags.NONE, ao_conectar, None, ao_perder_nome)
    laco.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
