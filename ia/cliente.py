#!/usr/bin/env python3
"""DuiaOS — duiaos-ia: a IA do sistema pela linha de comando.

Uso:
  duiaos-ia                     modelo ativo e download em andamento
  duiaos-ia catalogo            modelos do catálogo (* ativo, + baixado, x não cabe na memória)
  duiaos-ia baixar MODELO       baixa um modelo do catálogo (mostra o progresso)
  duiaos-ia ativar MODELO       passa a usar esse modelo no sistema inteiro
  duiaos-ia remover MODELO      apaga um modelo baixado (não o ativo)
  duiaos-ia cancelar            cancela o download em andamento
  duiaos-ia garantir-padrao     sem modelo ativo, ativa ou baixa o padrão (chamado no login)
  duiaos-ia diagnostico         relatório da velocidade da IA neste computador
                                (com sudo inclui memória RAM e registro do Ollama)
  duiaos-ia calibrar            mede de novo as opções mais rápidas para o modelo ativo

Pela sessão SSH, mudanças precisam de sudo (a autorização sem senha é só de
quem está sentado no computador).
"""
import json
import os
import re
import sys

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

NOME = "org.duiaos.IA1"
CAMINHO = "/org/duiaos/IA1"


def barramento():
    tipo = Gio.BusType.SESSION if os.environ.get("DUIAOS_IA_BARRAMENTO") == "sessao" else Gio.BusType.SYSTEM
    return Gio.bus_get_sync(tipo, None)


def chamar(conexao, metodo, *argumentos, tempo=30000):
    parametros = GLib.Variant("(" + "s" * len(argumentos) + ")", argumentos) if argumentos else None
    resposta = conexao.call_sync(NOME, CAMINHO, NOME, metodo, parametros, None,
                                 Gio.DBusCallFlags.NONE, tempo, None)
    return resposta.unpack() if resposta else ()


def mensagem_de_erro(erro):
    # Tira o "GDBus.Error:org.duiaos.IA1.Erro.X: " do começo
    return re.sub(r"^GDBus\.Error:[\w.]+:\s*", "", erro.message)


def gb(numero):
    return f"{numero / 1024 ** 3:.1f} GB"


def mostrar_estado(estado):
    print(f"Modelo ativo: {estado['ativo'] or 'nenhum'}")
    if not estado.get("ollama"):
        print("Aviso: a IA local (Ollama) não está respondendo.")
    tarefa = estado.get("tarefa")
    if tarefa:
        print(f"Baixando {tarefa['modelo']}: {tarefa['fracao'] * 100:.0f}% "
              f"({gb(tarefa['concluido'])} de {gb(tarefa['total'])})")
    ultima = estado.get("ultima")
    if ultima and ultima["resultado"] != "ok":
        print(f"Último download ({ultima['modelo']}): {ultima['mensagem']}")


def mostrar_catalogo(estado):
    print(f"Memória deste computador: {estado['memoria_gb']:.0f} GB\n")
    for familia in estado["familias"]:
        print(f"{familia['nome']} ({familia['autor']})")
        for modelo in familia["modelos"]:
            marca = "*" if modelo["ativo"] else "+" if modelo["instalado"] else "x" if not modelo["cabe"] else " "
            licenca = "" if modelo["licenca"]["livre"] else f"  [licença: {modelo['licenca']['nome']}]"
            print(f"  {marca} {modelo['id']:<18} {modelo['download_gb']:>5.1f} GB  {modelo['descricao']}{licenca}")
        print()
    print("* ativo   + baixado   x precisa de mais memória do que este computador tem")


def acompanhar(conexao, modelo):
    """Mostra o progresso do download até ele terminar."""
    laco = GLib.MainLoop()
    resultado = {"codigo": 1}

    def ao_mudar(_c, _r, _p, _i, _s, parametros):
        estado = json.loads(parametros.unpack()[0])
        tarefa = estado.get("tarefa")
        if tarefa and tarefa["modelo"] == modelo:
            print(f"\r{modelo}: {tarefa['fracao'] * 100:5.1f}%  ({gb(tarefa['concluido'])} de "
                  f"{gb(tarefa['total'])})  {tarefa['status'][:30]:<30}", end="", flush=True)
        elif not tarefa:
            ultima = estado.get("ultima") or {}
            print()
            if ultima.get("resultado") == "ok":
                print(f"{modelo} baixado. Modelo ativo: {estado['ativo']}")
                resultado["codigo"] = 0
            else:
                print(ultima.get("mensagem") or "O download terminou sem sucesso.")
            laco.quit()

    conexao.signal_subscribe(NOME, NOME, "Mudou", CAMINHO, None, Gio.DBusSignalFlags.NONE, ao_mudar)
    try:
        laco.run()
    except KeyboardInterrupt:
        print("\nO download continua no sistema. Para parar: duiaos-ia cancelar")
        return 0
    return resultado["codigo"]


def _executar(*comando):
    import subprocess
    try:
        return subprocess.run(comando, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def diagnostico(conexao):
    """Relatório para entender a velocidade da IA local neste computador: o que o
    hardware oferece, como o Ollama está usando, e uma medição do modelo ativo
    (pedido novo e pedido repetido). Com sudo, inclui o registro do Ollama e a
    memória RAM em detalhe."""
    import time
    import urllib.request
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hardware
    estado = json.loads(chamar(conexao, "Estado")[0])
    modelo, endereco = estado.get("ativo"), estado.get("endereco", "http://127.0.0.1:11434")
    opcoes = estado.get("opcoes") or {}
    n, cpu = hardware.nucleos(), hardware.processador()

    print("== Computador")
    print(f"Processador: {cpu['modelo']}")
    hibrido = f" ({n['desempenho']} de desempenho + {n['eficiencia']} de eficiência)" if n["desempenho"] else ""
    print(f"Núcleos: {n['fisicos']} físicos{hibrido}, {n['logicos']} lógicos")
    print(f"Instruções para IA: {', '.join(cpu['instrucoes']) or 'nenhuma das conhecidas'}")
    print(f"Memória RAM: {estado.get('memoria_gb', 0):.1f} GB")
    placas = hardware.placas_de_video()
    print("Placa de vídeo: " + (", ".join(f"{p['fabricante']} ({p['dispositivo']})" for p in placas) or "nenhuma vista"))
    if os.geteuid() == 0:
        pentes = [l.strip() for l in _executar("dmidecode", "-t", "memory").splitlines()
                  if re.match(r"\s*(Size|Configured Memory Speed|Locator):", l) and "No Module" not in l]
        if pentes:
            print("Pentes de memória (2 pentes iguais = canal duplo, até 2x mais rápido para escrever):")
            for linha in pentes:
                print("   " + linha)

    print("\n== IA do sistema")
    print(f"Modelo ativo: {modelo or 'nenhum'} · na memória: {'sim' if estado.get('carregado') else 'não'} · "
          f"fica na memória: {'sempre' if estado.get('manter') == -1 else estado.get('manter')}")
    print(f"Opções medidas para este computador: {opcoes or 'ainda não medidas'}"
          + (" (medindo agora…)" if estado.get("calibrando") else ""))
    for m in estado.get("medidas") or []:
        o = m.get("opcoes", {})
        jeito = "placa de vídeo" if o.get("num_gpu") else f"processador, {o.get('num_thread')} threads"
        print(f"   medido: {jeito:28s} ler {m['ler_por_s']:6.1f}/s · escrever {m['escrever_por_s']:5.1f}/s · "
              f"pedido típico {m['pedido_tipico_s']:.0f} s")
    if not modelo:
        return 1

    abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def pedir(caminho, corpo=None, tempo=900):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        pedido = urllib.request.Request(endereco + caminho, data=dados, headers={"Content-Type": "application/json"})
        with abridor.open(pedido, timeout=tempo) as resposta:
            return json.load(resposta)

    for m in pedir("/api/ps").get("models") or []:
        tamanho, vram = m.get("size", 0) / 1024 ** 3, m.get("size_vram", 0) / 1024 ** 3
        onde = f"{vram:.1f} GB na placa de vídeo" if placas and vram >= tamanho * 0.5 else "no processador"
        print(f"Carregado agora: {m.get('name')} · {tamanho:.1f} GB · {onde}")

    print("\n== Medição (o mesmo pedido duas vezes; a 2ª reaproveita o que já foi lido)")
    instrucoes = ("Você é o Wise, o assistente do DuiaOS. Responda em português do Brasil, "
                  "de forma simples e curta. " * 8)
    corpo = {"model": modelo, "stream": False, "think": False, "keep_alive": estado.get("manter", "30m"),
             "options": {**opcoes, "num_predict": 80, "temperature": 0, "seed": 1},
             "messages": [{"role": "system", "content": instrucoes},
                          {"role": "user", "content": "Em uma frase: o que um sistema operacional faz?"}]}
    for rodada in ("1ª vez", "2ª vez"):
        inicio = time.monotonic()
        r = pedir("/api/chat", corpo)
        total = time.monotonic() - inicio
        seg = lambda chave: r.get(chave, 0) / 1e9  # noqa: E731 — nanossegundos para segundos
        ler = r.get("prompt_eval_count", 0) / seg("prompt_eval_duration") if seg("prompt_eval_duration") else 0
        escrever = r.get("eval_count", 0) / seg("eval_duration") if seg("eval_duration") else 0
        print(f"{rodada}: {total:.1f} s no total · carregar {seg('load_duration'):.1f} s · "
              f"ler {r.get('prompt_eval_count', 0)} pedaços em {seg('prompt_eval_duration'):.1f} s ({ler:.0f}/s) · "
              f"escrever {r.get('eval_count', 0)} em {seg('eval_duration'):.1f} s ({escrever:.1f}/s)")

    if os.geteuid() == 0:
        print("\n== Registro do Ollama (desde que o computador ligou)")
        linhas = [l for l in _executar("journalctl", "-u", "ollama", "-b", "--no-pager", "-o", "cat").splitlines()
                  if re.search(r"inference compute|system_info|n_threads|offload|vulkan|error", l, re.I)]
        for linha in linhas[-12:]:
            print("   " + linha[:220])
    else:
        print("\n(Rode com sudo para incluir os pentes de memória e o registro do Ollama.)")
    return 0


def main(argv):
    comando = argv[1] if len(argv) > 1 else "estado"
    argumento = argv[2] if len(argv) > 2 else ""
    if comando in ("-h", "--help", "ajuda"):
        print(__doc__.strip())
        return 0
    try:
        conexao = barramento()
        if comando == "estado":
            mostrar_estado(json.loads(chamar(conexao, "Estado")[0]))
        elif comando == "catalogo":
            mostrar_catalogo(json.loads(chamar(conexao, "Estado")[0]))
        elif comando in ("baixar", "ativar", "remover") and argumento:
            chamar(conexao, comando.capitalize(), argumento, tempo=120000)
            if comando == "baixar":
                return acompanhar(conexao, argumento)
            print("Feito." if comando == "remover" else f"Modelo ativo: {argumento}")
        elif comando == "cancelar":
            chamar(conexao, "Cancelar")
        elif comando in ("diagnostico", "diagnóstico", "medir"):
            return diagnostico(conexao)
        elif comando == "calibrar":
            chamar(conexao, "Calibrar")
            print("Medindo (cerca de 1 minuto). Depois: duiaos-ia diagnostico")
        elif comando == "garantir-padrao":
            chamar(conexao, "GarantirPadrao", tempo=120000)
        else:
            print(__doc__.strip(), file=sys.stderr)
            return 2
    except GLib.Error as erro:
        print(mensagem_de_erro(erro), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
