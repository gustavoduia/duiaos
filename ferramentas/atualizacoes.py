#!/usr/bin/env python3
"""DuiaOS — fichas de atualização (atualizacoes/DUIA-AAAA-NNNN.md) e o catálogo que os computadores leem (ADR 046).

Uso (na raiz do repositório):
  python3 ferramentas/atualizacoes.py nova                 cria a próxima ficha (modelo) e mostra o caminho
  python3 ferramentas/atualizacoes.py conferir             confere todas as fichas; sai com erro se alguma está errada
  python3 ferramentas/atualizacoes.py catalogo SAIDA.json  gera o catálogo (usado pelo construir.sh e pelo workflow)

Onde rodar: 🍎 MAC ou no ambiente do Claude (precisa do git para a data de publicação).
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "atualizacoes"
CODIGO = re.compile(r"^DUIA-(\d{4})-(\d{4})$")
TIPOS = {"novidade": "Novidade", "melhoria": "Melhoria", "correcao": "Correção", "seguranca": "Segurança"}
IMPORTANCIAS = {"recomendada": "Recomendada", "importante": "Importante", "critica": "Crítica"}
REINICIAR = {"nao": "Não é preciso reiniciar", "sessao": "Saia e entre de novo na sessão",
             "computador": "Reinicie o computador"}
PACOTES = {"duiaos-identidade", "duiaos-shell", "duiaos-ia", "duiaos-agente", "duiaos-relatorios", "duiaos-desktop",
           "duiaos-ollama", "duiaos-wise", "duiaos-voz", "duiaos-motor-web", "duiaos-motor-web-chromium",
           "duiaos-ora", "duiaos-mailbox"}
OBRIGATORIOS = ("codigo", "titulo", "data", "tipo", "importancia", "pacotes", "reiniciar", "resumo")
SECOES = ("O que muda", "Detalhes", "Observações")


class FichaErrada(Exception):
    pass


def ler_ficha(caminho):
    """Lê uma ficha: {campos..., "descricao", "detalhes": [...], "observacoes"}. Levanta FichaErrada."""
    caminho = Path(caminho)
    texto = caminho.read_text(encoding="utf-8")
    partes = texto.split("---", 2)
    if len(partes) < 3 or partes[0].strip():
        raise FichaErrada(f"{caminho.name}: falta o cabeçalho entre linhas ---")
    campos = {}
    for linha in partes[1].strip().splitlines():
        if not linha.strip():
            continue
        if ":" not in linha:
            raise FichaErrada(f"{caminho.name}: linha sem 'campo: valor': {linha}")
        chave, valor = linha.split(":", 1)
        campos[chave.strip()] = valor.strip()
    for chave in OBRIGATORIOS:
        if not campos.get(chave):
            raise FichaErrada(f"{caminho.name}: falta o campo '{chave}'")
    if not CODIGO.match(campos["codigo"]) or caminho.stem != campos["codigo"]:
        raise FichaErrada(f"{caminho.name}: o código deve ser DUIA-AAAA-NNNN e igual ao nome do arquivo")
    if campos["tipo"] not in TIPOS:
        raise FichaErrada(f"{caminho.name}: tipo deve ser um de {', '.join(TIPOS)}")
    if campos["importancia"] not in IMPORTANCIAS:
        raise FichaErrada(f"{caminho.name}: importância deve ser uma de {', '.join(IMPORTANCIAS)}")
    if campos["reiniciar"] not in REINICIAR:
        raise FichaErrada(f"{caminho.name}: reiniciar deve ser um de {', '.join(REINICIAR)}")
    try:
        datetime.date.fromisoformat(campos["data"])
    except ValueError:
        raise FichaErrada(f"{caminho.name}: data no formato AAAA-MM-DD")
    pacotes = [p.strip() for p in campos["pacotes"].split(",") if p.strip()]
    desconhecidos = [p for p in pacotes if p not in PACOTES]
    if not pacotes or desconhecidos:
        raise FichaErrada(f"{caminho.name}: pacotes desconhecidos: {', '.join(desconhecidos) or '(nenhum)'}")
    if campos.get("publicada") and not re.match(r"^\d{14}$", campos["publicada"]):
        raise FichaErrada(f"{caminho.name}: publicada no formato AAAAMMDDhhmmss (UTC)")

    secoes, atual = {}, None
    for linha in partes[2].splitlines():
        titulo = re.match(r"^##\s+(.+?)\s*$", linha)
        if titulo:
            atual = titulo.group(1)
            if atual not in SECOES:
                raise FichaErrada(f"{caminho.name}: seção desconhecida '## {atual}' (use {', '.join(SECOES)})")
            secoes[atual] = []
        elif atual:
            secoes[atual].append(linha)
    if "O que muda" not in secoes or not "\n".join(secoes["O que muda"]).strip():
        raise FichaErrada(f"{caminho.name}: falta a seção '## O que muda'")
    detalhes = [l[2:].strip() for l in secoes.get("Detalhes", []) if l.startswith("- ")]
    if not detalhes:
        raise FichaErrada(f"{caminho.name}: falta a seção '## Detalhes' com itens '- '")

    def paragrafos(linhas):
        return "\n\n".join(" ".join(b.split()) for b in "\n".join(linhas).strip().split("\n\n") if b.strip())

    return {
        "codigo": campos["codigo"], "titulo": campos["titulo"], "data": campos["data"],
        "tipo": campos["tipo"], "tipoNome": TIPOS[campos["tipo"]],
        "importancia": campos["importancia"], "importanciaNome": IMPORTANCIAS[campos["importancia"]],
        "pacotes": pacotes, "reiniciar": campos["reiniciar"], "reiniciarNome": REINICIAR[campos["reiniciar"]],
        "resumo": campos["resumo"], "publicada": campos.get("publicada", ""),
        "descricao": paragrafos(secoes["O que muda"]), "detalhes": detalhes,
        "observacoes": paragrafos(secoes.get("Observações", [])),
    }


def fichas():
    return sorted(PASTA.glob("DUIA-*.md"))


def data_de_publicacao(caminho):
    """Data (UTC, AAAAMMDDhhmmss) do commit que criou a ficha; sem commit, agora."""
    try:
        saida = subprocess.run(["git", "-c", "safe.directory=*", "log", "--diff-filter=A", "--format=%cd", "--date=format-local:%Y%m%d%H%M%S",
                                "--", str(Path(caminho).relative_to(RAIZ))], capture_output=True, text=True,
                               cwd=RAIZ, env={"TZ": "UTC", "PATH": "/usr/bin:/bin:/usr/local/bin"}, check=False).stdout
    except OSError:
        saida = ""
    linhas = [l for l in saida.split() if l]
    return linhas[-1] if linhas else datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")


def conferir():
    erros, vistos = [], {}
    for caminho in fichas():
        try:
            ficha = ler_ficha(caminho)
        except FichaErrada as erro:
            erros.append(str(erro))
            continue
        ano, numero = CODIGO.match(ficha["codigo"]).groups()
        vistos.setdefault(ano, []).append(int(numero))
    for ano, numeros in vistos.items():
        esperado = list(range(1, len(numeros) + 1))
        if sorted(numeros) != esperado:
            erros.append(f"{ano}: números fora de sequência ou repetidos: {sorted(numeros)}")
    return erros


def catalogo():
    lista = []
    for caminho in fichas():
        ficha = ler_ficha(caminho)
        ficha["publicada"] = ficha["publicada"] or data_de_publicacao(caminho)
        lista.append(ficha)
    lista.sort(key=lambda f: (f["publicada"], f["codigo"]), reverse=True)
    return {"formato": 1, "atualizacoes": lista}


def nova():
    ano = datetime.date.today().year
    numeros = [int(CODIGO.match(c.stem).group(2)) for c in fichas() if CODIGO.match(c.stem) and c.stem[5:9] == str(ano)]
    codigo = f"DUIA-{ano}-{max(numeros, default=0) + 1:04d}"
    caminho = PASTA / f"{codigo}.md"
    caminho.write_text(f"""---
codigo: {codigo}
titulo:
data: {datetime.date.today().isoformat()}
tipo: melhoria
importancia: recomendada
pacotes: duiaos-shell
reiniciar: nao
resumo:
---

## O que muda


## Detalhes
-
""", encoding="utf-8")
    return caminho


def main(argumentos):
    if argumentos[:1] == ["nova"]:
        print(nova().relative_to(RAIZ))
        return 0
    if argumentos[:1] == ["conferir"]:
        erros = conferir()
        for erro in erros:
            print("ERRO:", erro)
        print(f"{len(fichas())} fichas de atualização, {'nenhum problema' if not erros else f'{len(erros)} problema(s)'}.")
        return 1 if erros else 0
    if argumentos[:1] == ["catalogo"] and len(argumentos) == 2:
        destino = Path(argumentos[1])
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(catalogo(), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Catálogo: {destino} ({len(fichas())} atualizações)")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
