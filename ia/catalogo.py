"""DuiaOS — catálogo de modelos de IA local e regras de memória (ADR 030).

Só lógica, sem D-Bus nem rede: usado pelo serviço (servico.py), pelo
cliente de linha de comando e pelos testes.
"""
import json
import math
from pathlib import Path

CATALOGO = Path(__file__).with_name("catalogo.json")

# Memória além do arquivo do modelo: contexto da conversa e o próprio Ollama
FOLGA_GB = 2.5
# Fração da memória do computador que um modelo pode ocupar sem travar o resto
LIMITE_BLOQUEIO = 0.9
LIMITE_AVISO = 0.6


def carregar(caminho=CATALOGO):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def memoria_total_gb(meminfo="/proc/meminfo"):
    """Memória RAM do computador em GB (0.0 se não der para ler)."""
    try:
        for linha in Path(meminfo).read_text().splitlines():
            if linha.startswith("MemTotal:"):
                return round(int(linha.split()[1]) / 1024 / 1024, 1)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def memoria_necessaria_gb(download_gb):
    return round(download_gb + FOLGA_GB, 1)


def avaliar(download_gb, memoria_gb):
    """(cabe, aviso): se o modelo pode ser usado neste computador e por quê não."""
    necessaria = memoria_necessaria_gb(download_gb)
    if memoria_gb <= 0:
        return True, ""
    if necessaria > memoria_gb * LIMITE_BLOQUEIO:
        return False, (f"Precisa de cerca de {math.ceil(necessaria)} GB de memória; "
                       f"este computador tem {round(memoria_gb)} GB.")
    if necessaria > memoria_gb * LIMITE_AVISO:
        return True, "Usa boa parte da memória: o computador pode ficar lento enquanto responde."
    return True, ""


def modelos(catalogo):
    """Todos os modelos do catálogo, com a família e a licença resolvidas."""
    for familia in catalogo["familias"]:
        for modelo in familia["modelos"]:
            yield familia, modelo, modelo.get("licenca", familia["licenca"])


def procurar(catalogo, id_modelo):
    """O modelo do catálogo com esse id, ou None (só modelos do catálogo são aceitos)."""
    for _familia, modelo, _licenca in modelos(catalogo):
        if modelo["id"] == id_modelo:
            return modelo
    return None


def montar(catalogo, instalados, ativo, memoria_gb):
    """Catálogo para as interfaces: cada modelo com instalado, ativo, cabe, aviso e licença."""
    licencas = catalogo.get("licencas", {})
    familias = []
    for familia in catalogo["familias"]:
        itens = []
        for modelo in familia["modelos"]:
            id_licenca = modelo.get("licenca", familia["licenca"])
            licenca = licencas.get(id_licenca, {"nome": id_licenca, "livre": False, "url": ""})
            cabe, aviso = avaliar(modelo["download_gb"], memoria_gb)
            itens.append({
                **modelo,
                "familia": familia["nome"],
                "licenca": {"id": id_licenca, **licenca},
                "memoria_gb": memoria_necessaria_gb(modelo["download_gb"]),
                "instalado": modelo["id"] in instalados,
                "ativo": modelo["id"] == ativo,
                "padrao": modelo["id"] == catalogo.get("padrao"),
                "cabe": cabe,
                "aviso": aviso,
            })
        familias.append({k: v for k, v in familia.items() if k != "modelos"} | {"modelos": itens})
    return familias
