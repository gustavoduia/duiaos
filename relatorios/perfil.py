"""Perfil do computador (como o Ubuntu Insights): hardware, firmware, versões e idioma.

Sem números de série, nome do computador, nomes de usuário ou endereços de rede. Coletado no primeiro
relatório, quando muda (ex.: depois de uma atualização) e uma vez por mês.
"""
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path

RAIZ = Path(os.environ.get("DUIAOS_RELATORIOS_RAIZ", "/"))
SECURE_BOOT = "sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"


def _ler(caminho, padrao=""):
    try:
        return (RAIZ / caminho).read_text(errors="ignore").strip()
    except OSError:
        return padrao


def _rodar(*comando):
    try:
        return subprocess.run(comando, capture_output=True, text=True, timeout=20,
                              env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C"}).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def sistema_operacional():
    dados = {}
    for linha in _ler("etc/os-release").splitlines() or _ler("usr/lib/os-release").splitlines():
        chave, _, valor = linha.partition("=")
        if chave in ("NAME", "VERSION_ID", "VERSION_CODENAME", "DEBIAN_CODENAME"):
            dados[chave.lower()] = valor.strip().strip('"')
    return dados


def pacotes():
    saida = _rodar("dpkg-query", "-W", "-f", "${Package} ${Version} ${db:Status-Abbrev}\n",
                   "duiaos*", "ollama", "linux-image-*", "mesa-vulkan-drivers", "labwc", "systemd")
    resultado = {}
    for linha in saida.splitlines():
        partes = linha.split(" ")
        if len(partes) >= 3 and partes[2].startswith("ii"):
            resultado[partes[0]] = partes[1]
    return resultado


def processador():
    texto = _ler("proc/cpuinfo")
    modelo = re.search(r"^model name\s*:\s*(.+)$", texto, re.M)
    flags = re.search(r"^(flags|Features)\s*:\s*(.+)$", texto, re.M)
    conjunto = set(flags.group(2).split()) if flags else set()
    return {"modelo": modelo.group(1).strip() if modelo else platform.processor() or platform.machine(),
            "arquitetura": platform.machine(), "nucleos": os.cpu_count(),
            "recursos": sorted(conjunto & {"avx2", "avx512f", "avx512_vnni", "avx_vnni", "asimd", "sve"})}


def memoria_gb():
    total = re.search(r"^MemTotal:\s+(\d+)", _ler("proc/meminfo"), re.M)
    return round(int(total.group(1)) / 1024 / 1024, 1) if total else None


def placas_de_video():
    placas = []
    for linha in _rodar("lspci", "-mm").splitlines():
        if re.search(r'"(VGA compatible controller|3D controller|Display controller)"', linha):
            partes = re.findall(r'"([^"]*)"', linha)
            if len(partes) >= 3:
                placas.append(f"{partes[1]} {partes[2]}")
    return placas


def discos():
    resultado = []
    pasta = RAIZ / "sys/block"
    for disco in sorted(pasta.iterdir()) if pasta.is_dir() else []:
        if disco.name.startswith(("loop", "ram", "zram", "dm-", "sr")):
            continue
        setores = _ler(f"sys/block/{disco.name}/size", "0")
        tipo = "nvme" if disco.name.startswith("nvme") else \
            ("hd" if _ler(f"sys/block/{disco.name}/queue/rotational") == "1" else "ssd")
        tamanho = round(int(setores or 0) * 512 / 1e9)
        if tamanho:
            resultado.append({"tipo": tipo, "gb": tamanho})
    return resultado


def firmware():
    uefi = (RAIZ / "sys/firmware/efi").is_dir()
    secure = None
    try:
        secure = (RAIZ / SECURE_BOOT).read_bytes()[-1:] == b"\x01"
    except OSError:
        pass
    return {"uefi": uefi, "secure_boot": secure, "fabricante": _ler("sys/class/dmi/id/sys_vendor"),
            "modelo": _ler("sys/class/dmi/id/product_name")}


def tempo_de_inicio():
    saida = _rodar("systemd-analyze", "time")
    total = re.search(r"=\s*(?:(\d+)min\s*)?([\d.]+)s", saida)
    if not total:
        return None
    return round(int(total.group(1) or 0) * 60 + float(total.group(2)), 1)


def idioma_e_fuso():
    idioma = re.search(r"^LANG=\"?([^\"\n]+)", _ler("etc/default/locale"), re.M)
    fuso = _ler("etc/timezone") or os.path.basename(os.path.realpath(RAIZ / "etc/localtime"))
    return {"idioma": idioma.group(1) if idioma else "", "fuso": fuso}


def coletar():
    return {"sistema": sistema_operacional(), "nucleo": platform.release(), "pacotes": pacotes(),
            "processador": processador(), "memoria_gb": memoria_gb(), "placas_de_video": placas_de_video(),
            "discos": discos(), "firmware": firmware(), "inicio_segundos": tempo_de_inicio(), **idioma_e_fuso()}


def resumo(perfil):
    """Muda quando algo que importa muda (o tempo de início varia a cada boot e fica de fora)."""
    estavel = {k: v for k, v in perfil.items() if k != "inicio_segundos"}
    return hashlib.sha1(json.dumps(estavel, sort_keys=True).encode()).hexdigest()
