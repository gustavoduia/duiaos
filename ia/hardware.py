"""DuiaOS — o que o computador oferece para a IA local (só leitura, sem root).

Num computador sem placa de vídeo dedicada, a IA local roda no processador:
- ler o pedido ("prefill") depende de quantos núcleos e de quais instruções
  vetoriais o processador tem (AVX2, AVX-512, AVX-VNNI);
- escrever a resposta depende da velocidade da memória RAM (cada palavra nova
  lê o modelo inteiro da memória), por isso modelo menor = resposta mais rápida.

O llama.cpp (dentro do Ollama) divide o trabalho entre linhas de execução
("threads") que se esperam a cada passo: se uma delas fica num núcleo lento
(núcleo de eficiência dos Intel híbridos) ou disputando o núcleo com outro
programa, todas esperam. Por isso o número de threads importa e é medido
(servico.py, calibração).
"""
import os
import re
from pathlib import Path

CPU = Path("/sys/devices/system/cpu")


def _ler(caminho, padrao=""):
    try:
        return Path(caminho).read_text().strip()
    except OSError:
        return padrao


def _lista_de_cpus(texto):
    """'0-3,8,10-11' -> {0, 1, 2, 3, 8, 10, 11}."""
    cpus = set()
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            inicio, fim = parte.split("-", 1)
            cpus.update(range(int(inicio), int(fim) + 1))
        else:
            cpus.add(int(parte))
    return cpus


def nucleos(raiz=CPU):
    """{"logicos", "fisicos", "desempenho", "eficiencia"}: núcleos físicos (sem
    hyper-threading) e, nos Intel híbridos (12ª geração em diante), quantos são
    de desempenho (P) e de eficiência (E)."""
    raiz = Path(raiz)
    logicos = 0
    fisicos = set()
    for pasta in sorted(raiz.glob("cpu[0-9]*")):
        if _ler(pasta / "online", "1") == "0":
            continue
        logicos += 1
        pacote = _ler(pasta / "topology/physical_package_id", "0")
        nucleo = _ler(pasta / "topology/core_id", pasta.name)
        fisicos.add((pacote, nucleo))
    logicos = logicos or os.cpu_count() or 1
    resultado = {"logicos": logicos, "fisicos": len(fisicos) or logicos, "desempenho": 0, "eficiencia": 0}
    # Intel híbrido: /sys/devices/cpu_core (P) e /sys/devices/cpu_atom (E)
    p_cpus = _ler(raiz.parent.parent / "cpu_core/cpus")
    e_cpus = _ler(raiz.parent.parent / "cpu_atom/cpus")
    if p_cpus and e_cpus:
        p = _lista_de_cpus(p_cpus)
        # P tem hyper-threading (2 lógicos por núcleo); conta núcleos físicos
        nucleos_p = {(_ler(raiz / f"cpu{c}/topology/physical_package_id", "0"),
                      _ler(raiz / f"cpu{c}/topology/core_id", str(c))) for c in p}
        resultado["desempenho"] = len(nucleos_p)
        resultado["eficiencia"] = len(_lista_de_cpus(e_cpus))
    return resultado


def processador(cpuinfo="/proc/cpuinfo"):
    """{"modelo", "instrucoes"}: nome do processador e instruções vetoriais úteis para a IA."""
    texto = _ler(cpuinfo)
    modelo = ""
    bandeiras = set()
    for linha in texto.splitlines():
        if not modelo and linha.startswith("model name"):
            modelo = linha.split(":", 1)[1].strip()
        elif linha.startswith(("flags", "Features")) and not bandeiras:
            bandeiras = set(linha.split(":", 1)[1].split())
    if not modelo:                                   # ARM costuma não ter "model name"
        for linha in texto.splitlines():
            if linha.startswith(("Hardware", "CPU part")):
                modelo = linha.split(":", 1)[1].strip()
                break
    interessantes = [nome for chave, nome in (
        ("avx2", "AVX2"), ("fma", "FMA"), ("avx512f", "AVX-512"), ("avx512_vnni", "AVX-512 VNNI"),
        ("avx_vnni", "AVX-VNNI"), ("amx_int8", "AMX"), ("asimddp", "NEON dotprod"), ("sve", "SVE"),
        ("i8mm", "I8MM")) if chave in bandeiras]
    return {"modelo": re.sub(r"\s+", " ", modelo) or "desconhecido", "instrucoes": interessantes}


def placas_de_video(drm="/sys/class/drm"):
    """Placas de vídeo vistas pelo sistema: [{"fabricante", "dispositivo"}] (ids PCI)."""
    fabricantes = {"0x8086": "Intel", "0x1002": "AMD", "0x10de": "NVIDIA"}
    placas = []
    for cartao in sorted(Path(drm).glob("card[0-9]")):
        fabricante = _ler(cartao / "device/vendor")
        if fabricante:
            placas.append({"fabricante": fabricantes.get(fabricante, fabricante),
                           "dispositivo": _ler(cartao / "device/device")})
    return placas


def threads_candidatas(n):
    """Números de threads que vale medir. Começa pelo que costuma ser o melhor:
    só os núcleos de desempenho (Intel híbrido) ou todos os físicos; e um a menos,
    que deixa um núcleo livre para a área de trabalho (a tela não disputa com a IA)."""
    base = n["desempenho"] or n["fisicos"]
    candidatas = [base]
    if base >= 4:
        candidatas.append(base - 1)
    if n["desempenho"] and n["fisicos"] > base:
        candidatas.append(n["fisicos"])              # P + E, para conferir
    return list(dict.fromkeys(c for c in candidatas if c >= 1))


def assinatura():
    """Identifica o hardware: se mudar (outro computador, mais memória), mede de novo."""
    n = nucleos()
    from catalogo import memoria_total_gb
    return f"{processador()['modelo']}|{n['fisicos']}|{n['desempenho']}|{round(memoria_total_gb())}"
