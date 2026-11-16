"""DuiaOS — espaço e armazenamento (Configurações › Armazenamento e os avisos de pouco espaço; ADR 060).

Só mede e sugere; quem apaga é a pessoa, escolhendo. Arquivos da pessoa vão para a Lixeira (dá para
voltar atrás); caches são apagados de verdade (os aplicativos os refazem); o que é do sistema (pacotes
baixados do apt, registros antigos) passa pelo duiaos-agente, com a autorização do polkit.

Tudo aqui roda fora da linha da interface (as medições podem levar alguns segundos numa pasta grande)
e tem limite de tempo e de arquivos, para nunca travar.
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

# ------------------------------------------------------------------ tipos de arquivo

CATEGORIAS = {
    "videos": ("Vídeos", ("mp4", "mkv", "avi", "mov", "webm", "m4v", "wmv", "flv", "mpg", "mpeg", "3gp", "ts")),
    "imagens": ("Imagens", ("jpg", "jpeg", "png", "gif", "webp", "heic", "heif", "bmp", "tif", "tiff", "raw", "cr2", "nef",
                            "arw", "dng", "svg", "psd", "xcf")),
    "musica": ("Música e áudio", ("mp3", "flac", "ogg", "opus", "wav", "m4a", "aac", "wma", "aiff")),
    "documentos": ("Documentos", ("pdf", "doc", "docx", "odt", "xls", "xlsx", "ods", "ppt", "pptx", "odp", "txt", "md", "rtf",
                                  "csv", "epub")),
    "compactados": ("Compactados", ("zip", "rar", "7z", "tar", "gz", "tgz", "bz2", "xz", "zst")),
    "instaladores": ("Instaladores e imagens de disco", ("deb", "rpm", "appimage", "iso", "img", "exe", "msi", "dmg", "flatpakref")),
    "copias": ("Cópias de segurança", ("bak", "old", "orig", "backup", "bkp", "swp")),
}
_POR_EXTENSAO = {ext: chave for chave, (_nome, extensoes) in CATEGORIAS.items() for ext in extensoes}


def classificar(nome):
    """Categoria de um arquivo pelo nome (ou "outros"). Arquivos terminados em ~ são cópias de segurança."""
    if nome.endswith("~"):
        return "copias"
    return _POR_EXTENSAO.get(nome.rsplit(".", 1)[-1].lower() if "." in nome else "", "outros")


# ------------------------------------------------------------------ medir

def andar(raiz, limite_s=20.0, limite_arquivos=400_000, mesmo_disco=True, pular=()):
    """Gera (caminho, tamanho em disco, momento da última mudança) de cada arquivo sob `raiz`, sem
    seguir atalhos e sem passar para outro disco. Para no limite de tempo ou de arquivos."""
    raiz = Path(raiz)
    try:
        dispositivo = raiz.stat().st_dev
    except OSError:
        return
    pular = {Path(p) for p in pular}
    fim = time.monotonic() + limite_s
    pilha, contados = [raiz], 0
    vistos = set()          # arquivos com mais de um nome (o Flathub guarda tudo assim) contam uma vez só
    while pilha:
        pasta = pilha.pop()
        if pasta in pular:
            continue
        try:
            entradas = list(os.scandir(pasta))
        except OSError:
            continue
        for entrada in entradas:
            try:
                info = entrada.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISDIR(info.st_mode):
                if not mesmo_disco or info.st_dev == dispositivo:
                    pilha.append(Path(entrada.path))
            elif stat.S_ISREG(info.st_mode):
                contados += 1
                if info.st_nlink > 1:
                    if (info.st_dev, info.st_ino) in vistos:
                        continue
                    vistos.add((info.st_dev, info.st_ino))
                yield entrada.path, info.st_blocks * 512, info.st_mtime
        if contados >= limite_arquivos or time.monotonic() > fim:
            return


def tamanho_da_pasta(raiz, **opcoes):
    return sum(tamanho for _c, tamanho, _m in andar(raiz, **opcoes))


# ------------------------------------------------------------------ dispositivos

def ler_lsblk(texto):
    """Saída de "lsblk -J -b -o ..." → lista de partições e discos com sistema de arquivos."""
    try:
        dados = json.loads(texto)
    except ValueError:
        return []
    achados = []

    def visitar(no, disco):
        filhos = no.get("children") or []
        if no.get("type") == "disk":
            disco = no
        if no.get("fstype") and no.get("fstype") not in ("swap", "LVM2_member", "crypto_LUKS") and not filhos:
            achados.append({"caminho": no.get("path", ""), "rotulo": no.get("label") or "", "sistema": no.get("fstype") or "",
                            "tamanho": int(no.get("size") or 0), "montado": no.get("mountpoint") or "",
                            "removivel": bool(disco and (disco.get("rm") in (True, "1", 1) or disco.get("tran") == "usb")),
                            "modelo": ((disco or {}).get("model") or "").strip()})
        for filho in filhos:
            visitar(filho, disco)
    for no in dados.get("blockdevices", []):
        visitar(no, None)
    return achados


def dispositivos(rodar=None, uso=shutil.disk_usage):
    """Discos e pendrives: {nome, caminho, montado, total, usado, livre, removivel, sistema, nivel}."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, text=True, timeout=10, check=False).stdout)
    lista = []
    for parte in ler_lsblk(rodar(["lsblk", "-J", "-b", "-o", "NAME,PATH,SIZE,FSTYPE,MOUNTPOINT,LABEL,MODEL,RM,TYPE,TRAN"])):
        if parte["montado"] in ("/boot/efi", "/boot"):
            continue                                          # pequenas e do sistema: não ajudam a pessoa
        total, usado, livre = parte["tamanho"], 0, 0
        if parte["montado"] and not parte["montado"].startswith("[SWAP"):
            try:
                medida = uso(parte["montado"])
                total, usado, livre = medida.total, medida.used, medida.free
            except OSError:
                pass
        if parte["montado"] == "/":
            nome = "Disco do sistema"
        elif parte["sistema"] in ("ntfs", "ntfs3") and not parte["removivel"]:
            nome = parte["rotulo"] or "Windows"
        else:
            nome = parte["rotulo"] or parte["modelo"] or Path(parte["caminho"]).name
        lista.append({**parte, "nome": nome, "total": total, "usado": usado, "livre": livre,
                      "nivel": nivel(livre, total) if parte["montado"] else ""})
    if not any(d["montado"] == "/" for d in lista):
        # Sem o lsblk (ou com a raiz num volume que ele não mostra): o disco do sistema vem direto do "/"
        try:
            medida = uso("/")
            lista.append({"caminho": "", "rotulo": "", "sistema": "", "tamanho": medida.total, "montado": "/", "removivel": False,
                          "modelo": "", "nome": "Disco do sistema", "total": medida.total, "usado": medida.used,
                          "livre": medida.free, "nivel": nivel(medida.free, medida.total)})
        except OSError:
            pass
    lista.sort(key=lambda d: (d["montado"] != "/", d["removivel"], d["nome"]))
    return lista


# ------------------------------------------------------------------ nível e avisos

POUCO_FRACAO, POUCO_BYTES = 0.10, 10 * 1000 ** 3       # pouco espaço: menos de 10 GB livres (ou de 10% num disco pequeno)
CHEIO_FRACAO, CHEIO_BYTES = 0.05, 1 * 1000 ** 3        # cheio: menos de 1 GB livre (ou de 5% num disco pequeno)


def nivel(livre, total):
    """"cheio", "pouco" ou "ok". Num disco grande vale a quantidade livre; num pequeno, a porcentagem."""
    if total <= 0:
        return "ok"
    if livre < min(CHEIO_BYTES, total * CHEIO_FRACAO):
        return "cheio"
    if livre < min(POUCO_BYTES, total * POUCO_FRACAO):
        return "pouco"
    return "ok"
    if livre < min(CHEIO_BYTES, total * 0.05) or livre / total < CHEIO_FRACAO:
        return "cheio"
    if livre < min(POUCO_BYTES, total * 0.15) or livre / total < POUCO_FRACAO:
        return "pouco"
    return "ok"


def avisos_de_espaco(discos, avisados, agora=None):
    """Que avisos mandar agora. discos: [{nome, montado, livre, total}]; avisados: {montado: [nivel, quando]}.
    Avisa ao entrar num nível pior, e repete o "cheio" a cada 4 horas e o "pouco" a cada 24 horas
    enquanto continuar assim. Devolve ([{titulo, texto, urgente, montado, nivel}], avisados atualizados)."""
    agora = agora or time.time()
    novos, saida = dict(avisados), []
    for disco in discos:
        montado = disco.get("montado")
        if not montado or disco.get("removivel"):
            continue
        atual = nivel(disco.get("livre", 0), disco.get("total", 0))
        anterior, quando = (avisados.get(montado) or ["ok", 0])[:2]
        if atual == "ok":
            novos.pop(montado, None)
            continue
        intervalo = 4 * 3600 if atual == "cheio" else 24 * 3600
        piorou = atual == "cheio" and anterior != "cheio" or atual == "pouco" and anterior == "ok"
        if piorou or agora - quando >= intervalo:
            from tipos import tamanho_legivel
            livre = tamanho_legivel(disco.get("livre", 0))
            nome = disco.get("nome") or montado
            if atual == "cheio":
                saida.append({"titulo": f"{nome} está cheio", "urgente": True, "montado": montado, "nivel": atual,
                              "texto": f"Só restam {livre}. Aplicativos podem parar de funcionar e as atualizações não "
                                       "vão instalar. Clique para liberar espaço."})
            else:
                saida.append({"titulo": f"Pouco espaço em {nome}", "urgente": False, "montado": montado, "nivel": atual,
                              "texto": f"Restam {livre} livres. Clique para ver o que dá para apagar com segurança."})
            novos[montado] = [atual, agora]
    return saida, novos


# ------------------------------------------------------------------ uso por categoria

def pasta_da_ia():
    for pasta in (Path("/usr/share/ollama/.ollama/models"), Path("/var/lib/ollama/models"), Path("/var/lib/ollama"),
                  Path.home() / ".ollama" / "models"):
        if pasta.is_dir():
            return pasta
    return None


def pastas_do_flathub():
    return (Path.home() / ".local/share/flatpak", Path("/var/lib/flatpak"))


def tamanho_dos_aplicativos(rodar=None):
    """Aplicativos e bibliotecas instalados: pacotes do Debian (Installed-Size) e do Flathub."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, text=True, timeout=30, check=False).stdout)
    debian = sum(int(l) * 1024 for l in rodar(["dpkg-query", "-W", "-f=${Installed-Size}\\n"]).split() if l.isdigit())
    flathub = 0
    for pasta in pastas_do_flathub():
        if pasta.is_dir():
            flathub += tamanho_da_pasta(pasta, limite_s=15)
    return debian + flathub


def uso_por_categoria(inicio=None, pastas_usuario=None, lixeira=None, cache=None, medir=None, aplicativos=None,
                      ia=None, disco=None):
    """O disco do sistema dividido: [{id, nome, tamanho}], do maior para o menor, mais "sistema" (o resto
    do que está usado). As pastas da pessoa vêm de pastas_usuario {DOCUMENTS: Path, ...}."""
    medir = medir or (lambda p: tamanho_da_pasta(p, limite_s=20))
    inicio = Path(inicio or Path.home())
    nomes = {"DOCUMENTS": "Documentos", "PICTURES": "Imagens", "VIDEOS": "Vídeos", "MUSIC": "Música",
             "DOWNLOAD": "Downloads", "DESKTOP": "Área de Trabalho"}
    partes, medidas = [], set()
    for chave, caminho in (pastas_usuario or {}).items():
        if chave in nomes and caminho and Path(caminho).is_dir() and Path(caminho) != inicio:
            partes.append({"id": chave.lower(), "nome": nomes[chave], "tamanho": medir(caminho)})
            medidas.add(Path(caminho))
    for ident, nome, caminho in (("lixeira", "Lixeira", lixeira), ("cache", "Arquivos temporários (caches)", cache)):
        if caminho and Path(caminho).is_dir():
            partes.append({"id": ident, "nome": nome, "tamanho": medir(caminho)})
            medidas.add(Path(caminho))
    if ia is not None or pasta_da_ia():
        caminho = ia if ia is not None else pasta_da_ia()
        if caminho and Path(caminho).is_dir():
            partes.append({"id": "ia", "nome": "Modelos de IA (Wise)", "tamanho": medir(caminho)})
            medidas.add(Path(caminho))
    partes.append({"id": "aplicativos", "nome": "Aplicativos", "tamanho": aplicativos if aplicativos is not None else tamanho_dos_aplicativos()})
    # O resto da pasta pessoal (configurações, outras pastas), sem o que já entrou em outra parte: os
    # aplicativos do Flathub da pessoa ficam em ~/.local/share/flatpak e eram contados duas vezes — a soma
    # passava do usado e a barra cortava as últimas partes (16/11)
    medidas.update(pastas_do_flathub())
    resto = sum(t for c, t, _m in andar(inicio, limite_s=20, pular=medidas))
    partes.append({"id": "pessoal", "nome": "Outros arquivos seus", "tamanho": resto})
    if disco:
        conhecido = sum(p["tamanho"] for p in partes)
        partes.append({"id": "sistema", "nome": "Sistema e outros", "tamanho": max(0, disco["usado"] - conhecido)})
    return sorted([p for p in partes if p["tamanho"] > 0], key=lambda p: -p["tamanho"])


# ------------------------------------------------------------------ o que dá para apagar

def maiores_por_categoria(inicio, categoria, limite=60, minimo=1024 * 1024, pular=()):
    """Os maiores arquivos de um tipo (ou de qualquer tipo, com categoria "grandes") na pasta pessoal."""
    achados = []
    for caminho, tamanho, mudou in andar(inicio, limite_s=25, pular=pular):
        if tamanho < minimo or "/." in caminho[len(str(inicio)):]:
            continue                                         # pastas escondidas (configurações) ficam de fora
        if categoria in ("grandes", classificar(os.path.basename(caminho))):
            achados.append({"caminho": caminho, "nome": os.path.basename(caminho), "tamanho": tamanho, "mudou": int(mudou),
                            "pasta": os.path.dirname(caminho), "categoria": classificar(os.path.basename(caminho))})
    return sorted(achados, key=lambda a: -a["tamanho"])[:limite]


def antigos(pasta, dias=90, agora=None, limite=200):
    """Arquivos de uma pasta (ex.: Downloads) sem mudança há mais de `dias` dias."""
    agora = agora or time.time()
    corte = agora - dias * 86400
    achados = [{"caminho": c, "nome": os.path.basename(c), "tamanho": t, "mudou": int(m), "pasta": os.path.dirname(c),
                "categoria": classificar(os.path.basename(c))}
               for c, t, m in andar(pasta, limite_s=15) if m < corte]
    return sorted(achados, key=lambda a: -a["tamanho"])[:limite]


def duplicados(inicio, minimo=1024 * 1024, limite_s=40, pular=()):
    """Grupos de arquivos iguais (mesmo conteúdo) na pasta pessoal, a partir de `minimo` bytes.
    Compara o tamanho, depois o começo e o fim, e só então o conteúdo inteiro. [{tamanho, arquivos: [...]}]"""
    fim = time.monotonic() + limite_s
    por_tamanho = {}
    for caminho, _disco, _m in andar(inicio, limite_s=limite_s / 2, pular=pular):
        if "/." in caminho[len(str(inicio)):]:
            continue
        try:
            tamanho = os.path.getsize(caminho)
        except OSError:
            continue
        if tamanho >= minimo:
            por_tamanho.setdefault(tamanho, []).append(caminho)

    def resumo(caminho, inteiro):
        h = hashlib.blake2b(digest_size=16)
        try:
            with open(caminho, "rb") as arquivo:
                if inteiro:
                    for bloco in iter(lambda: arquivo.read(1 << 20), b""):
                        h.update(bloco)
                        if time.monotonic() > fim:
                            return None
                else:
                    h.update(arquivo.read(65536))
                    arquivo.seek(max(0, os.path.getsize(caminho) - 65536))
                    h.update(arquivo.read(65536))
        except OSError:
            return None
        return h.hexdigest()
    grupos = []
    for tamanho, caminhos in sorted(por_tamanho.items(), key=lambda par: -par[0]):
        if len(caminhos) < 2 or time.monotonic() > fim:
            continue
        rapidos = {}
        for c in caminhos:
            chave = resumo(c, False)
            if chave:
                rapidos.setdefault(chave, []).append(c)
        for candidatos in rapidos.values():
            if len(candidatos) < 2:
                continue
            completos = {}
            for c in candidatos:
                chave = resumo(c, True)
                if chave:
                    completos.setdefault(chave, []).append(c)
            for iguais in completos.values():
                if len(iguais) > 1:
                    grupos.append({"tamanho": tamanho, "arquivos": sorted(iguais, key=lambda c: (len(c), c))})
    return grupos


def caches(pasta_cache=None):
    """As pastas de cache (~/.cache) do maior para o menor: [{nome, caminho, tamanho}]."""
    pasta_cache = Path(pasta_cache or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    itens = []
    try:
        entradas = list(os.scandir(pasta_cache))
    except OSError:
        return []
    for entrada in entradas:
        if entrada.name in ("duiaos",):                      # o próprio DuiaOS usa (avisos já dados, dicas do início)
            continue
        caminho = Path(entrada.path)
        tamanho = tamanho_da_pasta(caminho, limite_s=5) if entrada.is_dir(follow_symlinks=False) else (
            entrada.stat(follow_symlinks=False).st_blocks * 512)
        if tamanho > 0:
            itens.append({"nome": NOMES_DE_CACHE.get(entrada.name, entrada.name), "caminho": str(caminho), "tamanho": tamanho})
    return sorted(itens, key=lambda i: -i["tamanho"])


NOMES_DE_CACHE = {"mozilla": "Firefox", "google-chrome": "Google Chrome", "chromium": "Chromium", "thumbnails": "Miniaturas de imagens",
                  "pip": "Pacotes do Python (pip)", "fontconfig": "Fontes", "mesa_shader_cache": "Placa de vídeo",
                  "mesa_shader_cache_db": "Placa de vídeo", "flatpak": "Flathub", "BraveSoftware": "Brave", "vlc": "VLC",
                  "gstreamer-1.0": "Vídeo e áudio (GStreamer)", "yarn": "Yarn", "npm": "npm", "qtshadercache-x86_64-little_endian-lp64": "Qt"}


def apagar_caches(caminhos, pasta_cache=None):
    """Apaga as pastas de cache escolhidas, só dentro de ~/.cache. Devolve quanto liberou."""
    pasta_cache = Path(pasta_cache or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache").resolve()
    liberado = 0
    for caminho in caminhos:
        alvo = Path(caminho).resolve()
        if alvo.parent != pasta_cache or alvo.name == "duiaos":
            continue                                         # nunca fora de ~/.cache
        liberado += tamanho_da_pasta(alvo, limite_s=10) if alvo.is_dir() else (alvo.stat().st_size if alvo.exists() else 0)
        if alvo.is_dir() and not alvo.is_symlink():
            shutil.rmtree(alvo, ignore_errors=True)
        else:
            try:
                alvo.unlink()
            except OSError:
                pass
    return liberado


def tem_flatpak_da_pessoa():
    return bool(shutil.which("flatpak")) and (Path.home() / ".local/share/flatpak/runtime").is_dir()


def remover_flatpak_sem_uso(rodar=None):
    """Remove os ambientes do Flathub que nenhum aplicativo usa mais (na conta da pessoa; o próprio
    flatpak decide o que está sem uso). Devolve quanto liberou."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, text=True, timeout=600, check=False))
    pasta = Path.home() / ".local/share/flatpak"
    antes = tamanho_da_pasta(pasta, limite_s=15) if pasta.is_dir() else 0
    rodar(["flatpak", "uninstall", "--user", "--unused", "--noninteractive", "-y"])
    depois = tamanho_da_pasta(pasta, limite_s=15) if pasta.is_dir() else 0
    return max(0, antes - depois)


def programas_por_tamanho(rodar=None, aplicativos=None):
    """Aplicativos instalados do maior para o menor: [{nome, id_loja, tamanho, fonte}]. O id é o da Duia App
    Store (debian:PACOTE ou flathub:ID), que abre a página do aplicativo com o botão Remover."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, text=True, timeout=30, check=False).stdout)
    lista = []
    # Flathub
    for linha in rodar(["env", "LC_ALL=C", "flatpak", "list", "--user", "--app", "--columns=name,application,size"]).splitlines():
        partes = linha.split("\t")
        if len(partes) == 3:
            lista.append({"nome": partes[0], "id_loja": "flathub:" + partes[1], "fonte": "flathub",
                          "tamanho": _ler_tamanho_flatpak(partes[2])})
    # Debian: os pacotes que têm um atalho no menu (aplicativos de verdade, não bibliotecas)
    if aplicativos is None:
        import aplicativos as modulo
        aplicativos = modulo.listar_aplicativos()
    desktops = {Path(a.get("arquivo") or "").name: a.get("nome") for a in aplicativos if a.get("arquivo")}
    if desktops:
        donos = rodar(["dpkg-query", "-S"] + [f"/usr/share/applications/{d}" for d in desktops]).splitlines()
        pacotes = {}
        for linha in donos:
            if ":" in linha and "/usr/share/applications/" in linha:
                pacote, caminho = linha.split(":", 1)
                pacotes.setdefault(pacote.strip(), desktops.get(Path(caminho.strip()).name, pacote))
        if pacotes:
            tamanhos = rodar(["dpkg-query", "-W", "-f=${Package}\\t${Installed-Size}\\n"] + list(pacotes))
            for linha in tamanhos.splitlines():
                pacote, _, kib = linha.partition("\t")
                if pacote in pacotes and kib.strip().isdigit() and not pacote.startswith("duiaos-"):
                    lista.append({"nome": pacotes[pacote], "id_loja": "debian:" + pacote, "fonte": "debian",
                                  "tamanho": int(kib) * 1024})
    return sorted(lista, key=lambda a: -a["tamanho"])


def _ler_tamanho_flatpak(texto):
    import re
    m = re.search(r"([\d.,]+)\W*([kMGT]?B)", texto)
    if not m:
        return 0
    return int(float(m.group(1).replace(",", ".")) * {"B": 1, "kB": 1000, "KB": 1000, "MB": 1000 ** 2,
                                                       "GB": 1000 ** 3, "TB": 1000 ** 4}.get(m.group(2), 1))


def operacoes_do_explorador():
    """As operações de arquivo do Explorador (Lixeira com o .trashinfo, para dar para restaurar)."""
    import sys
    for pasta in (Path("/usr/share/duiaos/explorador-de-arquivos"), Path(__file__).resolve().parents[2] / "apps" / "explorador-de-arquivos"):
        if (pasta / "operacoes.py").is_file():
            if str(pasta) not in sys.path:
                sys.path.insert(0, str(pasta))
            break
    import operacoes
    return operacoes
