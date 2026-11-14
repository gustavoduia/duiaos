"""DuiaOS — Explorador de Arquivos: operações com arquivos, sem interface (testadas em testes/).

- listar uma pasta (com tipo, tamanho, data e miniatura);
- Lixeira no padrão freedesktop.org (~/.local/share/Trash: files/ e info/*.trashinfo),
  a mesma que outros programas do Linux usam;
- copiar e mover com progresso, sem sobrescrever (nomes "arquivo (2).txt");
- nova pasta, renomear, busca nas subpastas, discos e pendrives montados.
"""
import datetime
import os
import shutil
import sys
import urllib.parse
from pathlib import Path

_COMUM = [Path(os.environ.get("DUIAOS_SHELL", "/usr/share/duiaos/shell")) / "comum",
          Path(__file__).resolve().parents[2] / "shell" / "comum"]
for _pasta in _COMUM:
    if (_pasta / "tipos.py").is_file():
        sys.path.insert(0, str(_pasta))
        break
import pastas  # noqa: E402
import tipos  # noqa: E402

CARACTERES_PROIBIDOS = ("/", "\0")


class ErroDeArquivo(Exception):
    """Erro com mensagem pronta para a pessoa ler."""


def descrever_data(momento, agora=None):
    """'Hoje, 14:05', 'Ontem, 09:12' ou '12/10/2026, 18:30'."""
    data = datetime.datetime.fromtimestamp(momento)
    agora = agora or datetime.datetime.now()
    if data.date() == agora.date():
        return "Hoje, " + data.strftime("%H:%M")
    if data.date() == (agora - datetime.timedelta(days=1)).date():
        return "Ontem, " + data.strftime("%H:%M")
    return data.strftime("%d/%m/%Y, %H:%M")


def item_de(caminho, nome=None, info_lixeira=None):
    """Dicionário de um arquivo ou pasta para a interface."""
    caminho = Path(caminho)
    nome = nome or caminho.name
    try:
        estado = caminho.stat()
        eh_pasta = caminho.is_dir()
    except OSError:
        try:
            estado = caminho.lstat()             # link quebrado
        except OSError:
            return None
        eh_pasta = False
    icone, descricao, miniatura = tipos.tipo(caminho, eh_pasta)
    tamanho = -1 if eh_pasta else estado.st_size
    item = {
        "nome": nome,
        "caminho": str(caminho),
        "pasta": eh_pasta,
        "oculto": nome.startswith("."),
        "icone": icone,
        "tipo": descricao,
        "tamanho": tamanho,
        "tamanhoTexto": "—" if eh_pasta else tipos.tamanho_legivel(tamanho),
        "modificado": estado.st_mtime,
        "modificadoTexto": descrever_data(estado.st_mtime),
        "miniatura": caminho.as_uri() if miniatura and estado.st_size < 40_000_000 else "",
        "link": caminho.is_symlink(),
    }
    if info_lixeira:
        item.update(info_lixeira)
    return item


def chave_de_ordem(campo):
    import unicodedata

    def sem_acento(texto):
        return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)).casefold()

    if campo == "data":
        return lambda i: (not i["pasta"], -i["modificado"])
    if campo == "tamanho":
        return lambda i: (not i["pasta"], -i["tamanho"], sem_acento(i["nome"]))
    if campo == "tipo":
        return lambda i: (not i["pasta"], sem_acento(i["tipo"]), sem_acento(i["nome"]))
    return lambda i: (not i["pasta"], sem_acento(i["nome"]))


def listar(pasta, ocultos=False, ordem="nome"):
    """Conteúdo de uma pasta, pastas primeiro. Levanta ErroDeArquivo se não dá para abrir."""
    pasta = Path(pasta)
    try:
        nomes = os.listdir(pasta)
    except PermissionError:
        raise ErroDeArquivo("Você não tem permissão para abrir esta pasta.")
    except FileNotFoundError:
        raise ErroDeArquivo("Esta pasta não existe mais.")
    except OSError as erro:
        raise ErroDeArquivo(f"Não foi possível abrir a pasta ({erro.strerror}).")
    itens = []
    for nome in nomes:
        if not ocultos and (nome.startswith(".") or nome.endswith("~")):
            continue
        item = item_de(pasta / nome, nome)
        if item:
            itens.append(item)
    itens.sort(key=chave_de_ordem(ordem))
    return itens


def buscar(pasta, texto, ocultos=False, limite=500):
    """Arquivos cujo nome contém o texto, nesta pasta e nas de dentro (até 'limite')."""
    import unicodedata

    def normal(t):
        return "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c)).casefold()

    alvo = normal(texto.strip())
    achados = []
    if not alvo:
        return achados
    for raiz, subpastas, arquivos in os.walk(pasta):
        if not ocultos:
            subpastas[:] = [s for s in subpastas if not s.startswith(".")]
        for nome in subpastas + arquivos:
            if not ocultos and nome.startswith("."):
                continue
            if alvo in normal(nome):
                item = item_de(Path(raiz) / nome, nome)
                if item:
                    item["local"] = str(Path(raiz))
                    achados.append(item)
                    if len(achados) >= limite:
                        return achados
    achados.sort(key=chave_de_ordem("nome"))
    return achados


# ------------------------------------------------------------------ nomes

def validar_nome(nome):
    nome = nome.strip()
    if not nome:
        raise ErroDeArquivo("O nome não pode ficar vazio.")
    if nome in (".", ".."):
        raise ErroDeArquivo("Este nome é reservado pelo sistema.")
    if any(c in nome for c in CARACTERES_PROIBIDOS):
        raise ErroDeArquivo("O nome não pode ter barra (/).")
    if len(nome.encode()) > 255:
        raise ErroDeArquivo("O nome é longo demais.")
    return nome


def nome_livre(pasta, nome):
    """'foto.png' → 'foto (2).png' se já existir, e assim por diante."""
    pasta = Path(pasta)
    if not (pasta / nome).exists() and not (pasta / nome).is_symlink():
        return nome
    caminho = Path(nome)
    base, extensao = (caminho.stem, caminho.suffix) if not nome.startswith(".") or nome.count(".") > 1 else (nome, "")
    if base.endswith(".tar"):
        base, extensao = base[:-4], ".tar" + extensao
    numero = 2
    while True:
        candidato = f"{base} ({numero}){extensao}"
        if not (pasta / candidato).exists():
            return candidato
        numero += 1


def nova_pasta(pasta, nome="Nova pasta"):
    nome = nome_livre(pasta, validar_nome(nome))
    try:
        (Path(pasta) / nome).mkdir()
    except PermissionError:
        raise ErroDeArquivo("Você não tem permissão para criar pastas aqui.")
    except OSError as erro:
        raise ErroDeArquivo(f"Não foi possível criar a pasta ({erro.strerror}).")
    return str(Path(pasta) / nome)


def renomear(caminho, novo_nome):
    caminho = Path(caminho)
    novo_nome = validar_nome(novo_nome)
    if novo_nome == caminho.name:
        return str(caminho)
    destino = caminho.with_name(novo_nome)
    if destino.exists():
        raise ErroDeArquivo(f"Já existe um item chamado “{novo_nome}” aqui.")
    try:
        caminho.rename(destino)
    except PermissionError:
        raise ErroDeArquivo("Você não tem permissão para renomear este item.")
    except OSError as erro:
        raise ErroDeArquivo(f"Não foi possível renomear ({erro.strerror}).")
    return str(destino)


# --------------------------------------------------------- copiar e mover

def _tamanho_total(caminhos):
    total = 0
    for caminho in caminhos:
        caminho = Path(caminho)
        if caminho.is_dir() and not caminho.is_symlink():
            for raiz, _, arquivos in os.walk(caminho):
                for nome in arquivos:
                    try:
                        total += (Path(raiz) / nome).lstat().st_size
                    except OSError:
                        pass
        else:
            try:
                total += caminho.lstat().st_size
            except OSError:
                pass
    return max(total, 1)


def transferir(caminhos, destino, mover=False, progresso=None, cancelado=None):
    """Copia (ou move) para a pasta destino, sem sobrescrever. Devolve os caminhos novos.

    progresso(fração 0–1, nome) é chamado durante a cópia; cancelado() → True interrompe.
    """
    destino = Path(destino)
    if not destino.is_dir():
        raise ErroDeArquivo("A pasta de destino não existe.")
    total = _tamanho_total(caminhos)
    feito = [0]
    novos = []

    def avisar(nome):
        if progresso:
            progresso(min(1.0, feito[0] / total), nome)

    def copiar_arquivo(origem, alvo):
        if cancelado and cancelado():
            raise ErroDeArquivo("Operação cancelada.")
        if origem.is_symlink():
            os.symlink(os.readlink(origem), alvo)
            return
        with open(origem, "rb") as entrada, open(alvo, "wb") as saida:
            while True:
                if cancelado and cancelado():
                    raise ErroDeArquivo("Operação cancelada.")
                bloco = entrada.read(1024 * 1024)
                if not bloco:
                    break
                saida.write(bloco)
                feito[0] += len(bloco)
                avisar(origem.name)
        shutil.copystat(origem, alvo, follow_symlinks=False)

    def copiar_arvore(origem, alvo):
        alvo.mkdir()
        for filho in origem.iterdir():
            if filho.is_dir() and not filho.is_symlink():
                copiar_arvore(filho, alvo / filho.name)
            else:
                copiar_arquivo(filho, alvo / filho.name)
        shutil.copystat(origem, alvo)

    for caminho in caminhos:
        origem = Path(caminho)
        if not origem.exists() and not origem.is_symlink():
            continue
        if origem.is_dir() and (destino.resolve() == origem.resolve() or origem.resolve() in destino.resolve().parents):
            raise ErroDeArquivo("Não dá para colocar uma pasta dentro dela mesma.")
        if mover and origem.parent.resolve() == destino.resolve():
            novos.append(str(origem))            # mover para a mesma pasta: nada a fazer
            continue
        alvo = destino / nome_livre(destino, origem.name)
        try:
            if mover:
                try:
                    os.rename(origem, alvo)       # mesmo disco: instantâneo
                    feito[0] += _tamanho_total([alvo])
                    avisar(origem.name)
                    novos.append(str(alvo))
                    continue
                except OSError:
                    pass                          # outro disco: copia e apaga
            if origem.is_dir() and not origem.is_symlink():
                copiar_arvore(origem, alvo)
            else:
                copiar_arquivo(origem, alvo)
            if mover:
                if origem.is_dir() and not origem.is_symlink():
                    shutil.rmtree(origem)
                else:
                    origem.unlink()
        except PermissionError:
            raise ErroDeArquivo(f"Sem permissão para {'mover' if mover else 'copiar'} “{origem.name}”.")
        except OSError as erro:
            if erro.errno == 28:
                raise ErroDeArquivo("Não há espaço livre suficiente no destino.")
            raise ErroDeArquivo(f"Não foi possível {'mover' if mover else 'copiar'} “{origem.name}” ({erro.strerror}).")
        novos.append(str(alvo))
    if progresso:
        progresso(1.0, "")
    return novos


def excluir_permanentemente(caminhos):
    for caminho in caminhos:
        caminho = Path(caminho)
        try:
            if caminho.is_dir() and not caminho.is_symlink():
                shutil.rmtree(caminho)
            else:
                caminho.unlink()
        except FileNotFoundError:
            continue
        except PermissionError:
            raise ErroDeArquivo(f"Sem permissão para excluir “{caminho.name}”.")
        except OSError as erro:
            raise ErroDeArquivo(f"Não foi possível excluir “{caminho.name}” ({erro.strerror}).")


# ------------------------------------------------------------------ Lixeira

def _pastas_lixeira(lixeira=None):
    lixeira = Path(lixeira or pastas.LIXEIRA)
    return lixeira / "files", lixeira / "info"


def mover_para_lixeira(caminhos, lixeira=None, agora=None):
    """Move para a Lixeira e grava o .trashinfo (caminho original e data). Devolve os nomes na Lixeira."""
    arquivos, infos = _pastas_lixeira(lixeira)
    arquivos.mkdir(parents=True, exist_ok=True)
    infos.mkdir(parents=True, exist_ok=True)
    agora = agora or datetime.datetime.now()
    nomes = []
    for caminho in caminhos:
        caminho = Path(caminho).absolute()
        if not caminho.exists() and not caminho.is_symlink():
            continue
        nome = nome_livre(arquivos, caminho.name)
        while (infos / (nome + ".trashinfo")).exists():
            nome = nome_livre(arquivos, nome + "_")
        info = infos / (nome + ".trashinfo")
        info.write_text("[Trash Info]\n"
                        f"Path={urllib.parse.quote(str(caminho))}\n"
                        f"DeletionDate={agora.strftime('%Y-%m-%dT%H:%M:%S')}\n", encoding="utf-8")
        try:
            try:
                os.rename(caminho, arquivos / nome)
            except OSError as erro:
                if erro.errno != 18:              # EXDEV: outro disco
                    raise
                if caminho.is_dir() and not caminho.is_symlink():
                    shutil.copytree(caminho, arquivos / nome, symlinks=True)
                    shutil.rmtree(caminho)
                else:
                    shutil.copy2(caminho, arquivos / nome, follow_symlinks=False)
                    caminho.unlink()
        except PermissionError:
            info.unlink(missing_ok=True)
            raise ErroDeArquivo(f"Sem permissão para mover “{caminho.name}” para a Lixeira.")
        except OSError as erro:
            info.unlink(missing_ok=True)
            raise ErroDeArquivo(f"Não foi possível mover “{caminho.name}” para a Lixeira ({erro.strerror}).")
        nomes.append(nome)
    return nomes


def ler_trashinfo(arquivo):
    caminho, data = "", ""
    try:
        for linha in Path(arquivo).read_text(encoding="utf-8", errors="replace").splitlines():
            if linha.startswith("Path="):
                caminho = urllib.parse.unquote(linha[5:])
            elif linha.startswith("DeletionDate="):
                data = linha[13:]
    except OSError:
        pass
    return caminho, data


def listar_lixeira(lixeira=None):
    arquivos, infos = _pastas_lixeira(lixeira)
    itens = []
    try:
        nomes = os.listdir(arquivos)
    except OSError:
        return []
    for nome in nomes:
        original, data = ler_trashinfo(infos / (nome + ".trashinfo"))
        try:
            momento = datetime.datetime.strptime(data, "%Y-%m-%dT%H:%M:%S")
            data_texto = descrever_data(momento.timestamp())
        except ValueError:
            data_texto = ""
        item = item_de(arquivos / nome, Path(original).name if original else nome,
                       {"original": original, "nomeNaLixeira": nome, "excluidoTexto": data_texto,
                        "local": str(Path(original).parent) if original else ""})
        if item:
            itens.append(item)
    itens.sort(key=chave_de_ordem("nome"))
    return itens


def restaurar(nomes_na_lixeira, lixeira=None):
    """Devolve à pasta original (recriada se preciso; com outro nome se já existir lá)."""
    arquivos, infos = _pastas_lixeira(lixeira)
    restaurados = []
    for nome in nomes_na_lixeira:
        info = infos / (nome + ".trashinfo")
        original, _ = ler_trashinfo(info)
        if not original:
            raise ErroDeArquivo(f"Não sei de onde veio “{nome}”.")
        original = Path(original)
        original.parent.mkdir(parents=True, exist_ok=True)
        alvo = original.parent / nome_livre(original.parent, original.name)
        try:
            shutil.move(str(arquivos / nome), str(alvo))
        except OSError as erro:
            raise ErroDeArquivo(f"Não foi possível restaurar “{original.name}” ({erro.strerror}).")
        info.unlink(missing_ok=True)
        restaurados.append(str(alvo))
    return restaurados


def excluir_da_lixeira(nomes_na_lixeira, lixeira=None):
    arquivos, infos = _pastas_lixeira(lixeira)
    excluir_permanentemente([arquivos / n for n in nomes_na_lixeira])
    for nome in nomes_na_lixeira:
        (infos / (nome + ".trashinfo")).unlink(missing_ok=True)


def esvaziar_lixeira(lixeira=None):
    arquivos, infos = _pastas_lixeira(lixeira)
    for pasta in (arquivos, infos):
        try:
            nomes = os.listdir(pasta)
        except OSError:
            continue
        excluir_permanentemente([pasta / n for n in nomes])


# ---------------------------------------------------- discos e pendrives

def discos_montados(arquivo_mounts="/proc/mounts"):
    """Discos e pendrives que a pessoa pode abrir (montados em /media ou /run/media)."""
    discos = []
    try:
        linhas = Path(arquivo_mounts).read_text().splitlines()
    except OSError:
        return discos
    for linha in linhas:
        partes = linha.split()
        if len(partes) < 3:
            continue
        dispositivo, ponto = partes[0], partes[1].replace("\\040", " ")
        if not ponto.startswith(("/media/", "/run/media/")):
            continue
        discos.append({"nome": Path(ponto).name, "caminho": ponto, "dispositivo": dispositivo,
                       "removivel": ponto.startswith(("/media/", "/run/media/"))})
    return discos


def espaco_livre(caminho):
    try:
        estado = shutil.disk_usage(caminho)
    except OSError:
        return ""
    return tipos.tamanho_legivel(estado.free) + " livres"


def interpretar_lsblk(texto):
    """'lsblk -J -o PATH,LABEL,MOUNTPOINT,HOTPLUG,TYPE,SIZE,FSTYPE' → pendrives e discos externos com
    sistema de arquivos (montados ou não)."""
    import json
    try:
        dados = json.loads(texto)
    except ValueError:
        return []
    externos = []

    def visitar(dispositivo, externo):
        externo = externo or dispositivo.get("hotplug") in (True, "1", 1)
        if dispositivo.get("fstype") and dispositivo.get("type") in ("part", "disk") and externo:
            ponto = dispositivo.get("mountpoint") or ""
            rotulo = dispositivo.get("label") or ("Disco de " + (dispositivo.get("size") or "").replace(".", ","))
            externos.append({"nome": rotulo, "dispositivo": dispositivo.get("path", ""), "caminho": ponto,
                             "montado": bool(ponto), "removivel": True})
        for filho in dispositivo.get("children") or []:
            visitar(filho, externo)

    for dispositivo in dados.get("blockdevices", []):
        visitar(dispositivo, False)
    return externos


def dispositivos_externos():
    import subprocess
    try:
        saida = subprocess.run(["lsblk", "-J", "-o", "PATH,LABEL,MOUNTPOINT,HOTPLUG,TYPE,SIZE,FSTYPE"],
                               capture_output=True, text=True, timeout=4, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return interpretar_lsblk(saida)
