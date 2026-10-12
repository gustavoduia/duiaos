#!/usr/bin/env python3
"""Lê os relatórios de "Ajude a melhorar o DuiaOS" (ADR 040) — para o Claude achar e priorizar falhas.

Onde rodar: no ambiente do Claude (ou no Mac), com o repositório privado gustavoduia/duiaos-diagnosticos
clonado ao lado (../duiaos-diagnosticos). Os dados são pessoais: nunca copie trechos para este repositório
público (issues, commits, testes) — descreva a causa com as suas palavras.

  python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos                 # resumo de todos os computadores
  python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos --horas 6 --maquina dell
  python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos --falha ASSINATURA   # rastro e onde aconteceu
  python3 ferramentas/ler-relatorios.py ../duiaos-diagnosticos --componente duiaos-wise --eventos
  python3 ferramentas/ler-relatorios.py relatorio.json                          # um relatório solto

Resumo: falhas agrupadas pela assinatura (quantas vezes, em quantos computadores, em quais versões),
erros e avisos mais repetidos, serviços que falharam e o perfil de cada computador.
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def carregar(caminhos, maquina=None, desde=0.0):
    relatorios = []
    for caminho in caminhos:
        caminho = Path(caminho)
        arquivos = [caminho] if caminho.is_file() else sorted((caminho / "maquinas").glob("*/*/*.json")) \
            if (caminho / "maquinas").is_dir() else sorted(caminho.rglob("*.json"))
        for arquivo in arquivos:
            if arquivo.name == "perfil.json":
                continue
            try:
                dados = json.loads(arquivo.read_text())
            except (OSError, ValueError):
                continue
            nome = dados.get("maquina") or dados.get("instalacao", "")[:12]
            if maquina and nome != maquina:
                continue
            if dados.get("periodo", {}).get("ate", 0) < desde:
                continue
            dados["_maquina"], dados["_arquivo"] = nome, str(arquivo)
            relatorios.append(dados)
    return sorted(relatorios, key=lambda r: r.get("periodo", {}).get("ate", 0))


def hora(t):
    return datetime.fromtimestamp(t).strftime("%d/%m %H:%M") if t else "?"


def curto(texto, limite=170):
    texto = " ".join(str(texto or "").split())
    return texto if len(texto) <= limite else texto[:limite] + "…"


def falhas_agrupadas(relatorios):
    grupos = {}
    for r in relatorios:
        for f in r.get("falhas", []):
            g = grupos.setdefault(f["assinatura"], {"assinatura": f["assinatura"], "tipo": f["tipo"],
                                                    "origem": f.get("origem"), "mensagem": f.get("mensagem"),
                                                    "programa": f.get("programa"), "contagem": 0,
                                                    "maquinas": set(), "versoes": set(), "primeira": f["primeira"],
                                                    "ultima": f["ultima"], "exemplo": f.get("exemplo")})
            g["contagem"] += f.get("contagem", 1)
            g["maquinas"].add(r["_maquina"])
            g["versoes"].add(r.get("versao_duiaos") or "?")
            g["primeira"] = min(g["primeira"], f["primeira"])
            if f["ultima"] >= g["ultima"]:
                g["ultima"], g["exemplo"] = f["ultima"], f.get("exemplo")
    return sorted(grupos.values(), key=lambda g: (-len(g["maquinas"]), -g["contagem"]))


def resumo(relatorios, raiz):
    if not relatorios:
        print("Nenhum relatório no período.")
        return
    maquinas = sorted({r["_maquina"] for r in relatorios})
    print(f"# Relatórios do DuiaOS — {hora(relatorios[0]['periodo']['de'])} a {hora(relatorios[-1]['periodo']['ate'])}")
    print(f"{len(relatorios)} relatório(s) de {len(maquinas)} computador(es): {', '.join(maquinas)}\n")

    falhas = falhas_agrupadas(relatorios)
    print(f"## Falhas ({sum(g['contagem'] for g in falhas)} em {len(falhas)} assinatura(s))")
    for g in falhas[:25]:
        quem = g["programa"] or g["origem"]
        print(f"- `{g['assinatura']}` {g['contagem']}× em {len(g['maquinas'])} computador(es) · {quem} · "
              f"versões {', '.join(sorted(g['versoes']))} · última {hora(g['ultima'])}")
        print(f"  {curto(g['mensagem'], 220)}")
    print()

    erros, avisos, servicos, contextos = Counter(), Counter(), Counter(), {}
    for r in relatorios:
        for e in r.get("eventos", []):
            chave = f"{e.get('origem')}: {curto(e.get('mensagem'), 150)}"
            vezes = e.get("repeticoes", 1)
            if e["tipo"] == "servico_falhou":
                nome = f"{e.get('unidade_afetada') or e.get('unidade') or e.get('origem')} ({e.get('resultado')})"
                servicos[nome] += vezes
                contextos.setdefault(nome, e.get("contexto") or [])
            elif e["tipo"] == "erro":
                erros[chave] += vezes
            elif e["tipo"] == "aviso":
                avisos[chave] += vezes
    for titulo, contador in (("Serviços que falharam", servicos), ("Erros mais repetidos", erros),
                             ("Avisos dos componentes do DuiaOS", avisos)):
        print(f"## {titulo} ({sum(contador.values())})")
        for texto, vezes in contador.most_common(15):
            print(f"- {vezes}× {texto}")
            for linha in (contextos.get(texto) or [])[-6:] if contador is servicos else []:
                print(f"    {curto(linha, 200)}")
        print()

    print("## Computadores")
    vistos = set()
    for r in reversed(relatorios):
        if r["_maquina"] in vistos:
            continue
        vistos.add(r["_maquina"])
        perfil = r.get("perfil")
        arquivo = Path(r["_arquivo"]).parents[1] / "perfil.json"
        if perfil is None and arquivo.exists():
            perfil = json.loads(arquivo.read_text())
        if not perfil:
            print(f"- {r['_maquina']}: sem perfil")
            continue
        p = perfil
        print(f"- {r['_maquina']}: DuiaOS {p.get('sistema', {}).get('version_id', '?')} · "
              f"{p.get('processador', {}).get('modelo', '?')} · {p.get('memoria_gb')} GB · "
              f"{', '.join(p.get('placas_de_video', [])) or 'vídeo ?'} · início {p.get('inicio_segundos')} s · "
              f"núcleo {p.get('nucleo')} · último relatório {hora(r['periodo']['ate'])}")


def detalhar_falha(relatorios, assinatura):
    for g in falhas_agrupadas(relatorios):
        if g["assinatura"].startswith(assinatura):
            print(f"# Falha {g['assinatura']} — {g['contagem']}× em {', '.join(sorted(g['maquinas']))}")
            print(f"Primeira {hora(g['primeira'])} · última {hora(g['ultima'])} · versões {', '.join(sorted(g['versoes']))}\n")
            exemplo = g.get("exemplo") or {}
            for chave in ("origem", "unidade", "programa", "sinal", "arquivo", "linha", "funcao", "dados"):
                if exemplo.get(chave):
                    print(f"{chave}: {exemplo[chave]}")
            print()
            print(exemplo.get("rastro") or exemplo.get("mensagem", ""))
            return 0
    print(f"Assinatura {assinatura} não encontrada.", file=sys.stderr)
    return 1


def listar_eventos(relatorios, componente):
    for r in relatorios:
        for e in r.get("eventos", []):
            if componente and e.get("origem") != componente:
                continue
            extra = f" {json.dumps(e['dados'], ensure_ascii=False)}" if e.get("dados") else ""
            vezes = f" (×{e['repeticoes']})" if e.get("repeticoes") else ""
            print(f"{hora(e.get('t'))} {r['_maquina']} [{e['tipo']}] {e.get('origem')} "
                  f"{e.get('evento', '')}: {curto(e.get('mensagem'), 400)}{vezes}{curto(extra, 600)}")
            for linha in e.get("contexto") or []:
                print(f"    {curto(linha, 300)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("caminhos", nargs="+")
    parser.add_argument("--maquina")
    parser.add_argument("--horas", type=float)
    parser.add_argument("--falha", help="assinatura (ou o começo dela)")
    parser.add_argument("--componente", help="ex.: duiaos-wise, duiaos-ia")
    parser.add_argument("--eventos", action="store_true", help="lista os eventos em ordem")
    args = parser.parse_args()
    desde = time.time() - args.horas * 3600 if args.horas else 0.0
    relatorios = carregar(args.caminhos, args.maquina, desde)
    if args.falha:
        return detalhar_falha(relatorios, args.falha)
    if args.eventos:
        listar_eventos(relatorios, args.componente)
        return 0
    resumo(relatorios, Path(args.caminhos[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
