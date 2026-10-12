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
