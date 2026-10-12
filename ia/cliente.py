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
  duiaos-ia medir               mede a velocidade do modelo ativo neste computador

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


def medir(conexao):
    """Mede carregamento, leitura do pedido e geração do modelo ativo (duas vezes:
    a segunda mostra o ganho com o modelo e o começo da conversa já na memória)."""
    import time
    import urllib.request
    estado = json.loads(chamar(conexao, "Estado")[0])
    modelo, endereco = estado.get("ativo"), estado.get("endereco", "http://127.0.0.1:11434")
    if not modelo:
        print("Nenhum modelo ativo.")
        return 1
    print(f"Modelo ativo: {modelo} · {'já' if estado.get('carregado') else 'ainda não'} carregado na memória\n")
    abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    instrucoes = ("Você é o Wise, o assistente do DuiaOS. Responda em português do Brasil, "
                  "de forma simples e curta. " * 8)            # um começo de conversa de tamanho realista
    corpo = {"model": modelo, "stream": False, "think": False, "options": {"num_predict": 80},
             "messages": [{"role": "system", "content": instrucoes},
                          {"role": "user", "content": "Em uma frase: o que um sistema operacional faz?"}]}
    for rodada in ("1ª pergunta", "2ª pergunta"):
        inicio = time.monotonic()
        pedido = urllib.request.Request(endereco + "/api/chat", data=json.dumps(corpo).encode(),
                                        headers={"Content-Type": "application/json"})
        with abridor.open(pedido, timeout=600) as resposta:
            r = json.load(resposta)
        total = time.monotonic() - inicio
        seg = lambda chave: r.get(chave, 0) / 1e9  # noqa: E731 — nanossegundos para segundos
        leitura = r.get("prompt_eval_count", 0) / seg("prompt_eval_duration") if seg("prompt_eval_duration") else 0
        geracao = r.get("eval_count", 0) / seg("eval_duration") if seg("eval_duration") else 0
        print(f"{rodada}: {total:.1f} s no total")
        print(f"  carregar o modelo:     {seg('load_duration'):6.1f} s")
        print(f"  ler o pedido:          {seg('prompt_eval_duration'):6.1f} s  "
              f"({r.get('prompt_eval_count', 0)} pedaços, {leitura:.0f}/s)")
        print(f"  primeira palavra em:   {seg('load_duration') + seg('prompt_eval_duration'):6.1f} s")
        print(f"  escrever a resposta:   {seg('eval_duration'):6.1f} s  ({r.get('eval_count', 0)} pedaços, {geracao:.1f}/s)")
    print("\nPara ver se a placa de vídeo está ajudando: journalctl -u ollama | grep 'inference compute'")
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
        elif comando == "medir":
            return medir(conexao)
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
