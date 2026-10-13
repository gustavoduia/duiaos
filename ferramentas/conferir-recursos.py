#!/usr/bin/env python3
"""Confere que nenhum recurso já entregue sumiu ou voltou a uma versão antiga.

Onde rodar: no ambiente do Claude (antes de todo pull request) ou 🍎 MAC.

  python3 ferramentas/conferir-recursos.py            # confere este repositório
  python3 ferramentas/conferir-recursos.py --listar   # mostra o inventário

Lê docs/continuidade/RECURSOS.md. Cada linha da tabela tem uma ou mais
conferências na coluna "Conferência", no formato `arquivo::texto`: o arquivo
precisa existir e conter o texto. O texto é algo que só a versão atual do
recurso tem (ex.: o comentário "carinha de robô" no Carinha.qml do Wise). Se
alguém partir de uma branch antiga e trouxer a versão velha de volta, a
conferência falha e o PR não sai.

Ao criar ou mudar um recurso: acrescente ou atualize a linha em RECURSOS.md
na mesma mudança.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONTINUIDADE = RAIZ / "docs" / "continuidade"
INVENTARIO = CONTINUIDADE / "RECURSOS.md"
# Todos os inventários ficam aqui (o duiaos é o repositório oficial do projeto, ADR 043); os do Wise e do
# site conferem os arquivos desses repositórios, clonados ao lado deste (../duiaos-wise, ../duiaos-websites).
INVENTARIOS = [
    ("duiaos", INVENTARIO, RAIZ),
    ("duiaos-wise", CONTINUIDADE / "RECURSOS-WISE.md", RAIZ.parent / "duiaos-wise"),
    ("duiaos-websites", CONTINUIDADE / "RECURSOS-WEBSITES.md", RAIZ.parent / "duiaos-websites"),
]
CONFERENCIA = re.compile(r"`([^`]+?)::([^`]+)`")


def ler_inventario(arquivo=INVENTARIO):
    """[(recurso, [(caminho, texto)])] das linhas da tabela com conferência."""
    itens = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if not linha.startswith("|") or "::" not in linha:
            continue
        colunas = [c.strip() for c in linha.strip("|").split("|")]
        conferencias = CONFERENCIA.findall(linha)
        if conferencias:
            itens.append((colunas[0], conferencias))
    return itens


def conferir(raiz=RAIZ, arquivo=INVENTARIO):
    """Lista de problemas (vazia = tudo certo)."""
    problemas = []
    for recurso, conferencias in ler_inventario(arquivo):
        for caminho, texto in conferencias:
            alvo = Path(raiz) / caminho
            if not alvo.is_file():
                problemas.append(f"{recurso}: falta o arquivo {caminho}")
            elif texto not in alvo.read_text(encoding="utf-8", errors="ignore"):
                problemas.append(f"{recurso}: {caminho} não tem mais \"{texto}\" (versão antiga ou removida?)")
    return problemas


def main():
    if not INVENTARIO.exists():
        print(f"Sem inventário em {INVENTARIO}", file=sys.stderr)
        return 1
    codigo = 0
    for nome, arquivo, raiz in INVENTARIOS:
        if not arquivo.exists():
            continue
        itens = ler_inventario(arquivo)
        if "--listar" in sys.argv:
            print(f"# {nome}")
            for recurso, conferencias in itens:
                print(f"- {recurso}: " + ", ".join(c for c, _ in conferencias))
            continue
        if not raiz.is_dir():
            print(f"{nome}: repositório não está em {raiz} — conferência pulada (clone-o ao lado do duiaos).")
            continue
        problemas = conferir(raiz, arquivo)
        if problemas:
            print(f"{nome}: RECURSOS EM RISCO — não envie esta mudança antes de entender cada item:")
            for p in problemas:
                print("  ✗ " + p)
            codigo = 1
            continue
        total = sum(len(c) for _, c in itens)
        print(f"{nome}: {len(itens)} recursos, {total} conferências, nenhum problema.")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
