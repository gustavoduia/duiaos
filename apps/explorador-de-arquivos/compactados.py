"""DuiaOS — Explorador de Arquivos: descompactar arquivos (.zip, .tar.*, .gz, .bz2, .xz, .7z, .rar).

Como o Utilitário de Compactação do macOS e o "Extrair aqui" do GNOME:
- o conteúdo vai para a mesma pasta do arquivo compactado;
- se dentro há um item só (uma pasta ou um arquivo), ele aparece direto ali;
- se há vários, eles vão para uma pasta com o nome do arquivo ("Fotos.zip" → "Fotos");
- nada é sobrescrito: nomes repetidos viram "Fotos (2)".

Segurança: nenhum item sai da pasta de destino (caminhos com "..", caminhos absolutos e links
que apontam para fora são recusados). A extração acontece numa pasta temporária escondida ao
lado do arquivo e só aparece pronta; se der erro ou for cancelada, a pasta temporária é apagada.

.zip e .tar.* usam a biblioteca do Python; .7z e .rar usam o 7-Zip (comando 7z), se instalado. O .rar
precisa também do 7zip-rar, que fica na seção non-free do Debian (ADR 067).
"""
import bz2
import datetime
import gzip
import lzma
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

import operacoes
from operacoes import ErroDeArquivo

# Do mais longo para o mais curto: ".tar.gz" antes de ".gz"
EXTENSOES_TAR = (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz", ".tbz2", ".txz", ".tar")
EXTENSOES_SIMPLES = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}
EXTENSOES_7Z = (".7z", ".rar")
EXTENSOES = EXTENSOES_TAR + (".zip",) + tuple(EXTENSOES_SIMPLES) + EXTENSOES_7Z
BLOCO = 1024 * 1024


def extensao(caminho):
    """Extensão de arquivo compactado que o DuiaOS sabe abrir ("" se não for um)."""
    nome = Path(caminho).name.lower()
    for ext in EXTENSOES:
        if nome.endswith(ext) and len(nome) > len(ext):
            return ext
    return ""


def eh_compactado(caminho):
    return extensao(caminho) != ""


def nome_sem_extensao(caminho):
    nome = Path(caminho).name
    ext = extensao(nome)
    return nome[: len(nome) - len(ext)] if ext else Path(nome).stem


def _7z():
    return shutil.which("7z") or shutil.which("7za") or shutil.which("7zz")


# ------------------------------------------------------------ segurança

def _destino_seguro(raiz, nome):
    """Caminho do item dentro da raiz; ErroDeArquivo se tentar sair dela."""
    nome = nome.replace("\\", "/")
    partes = [p for p in nome.split("/") if p not in ("", ".")]
    if nome.startswith("/") or ".." in partes or not partes:
        raise ErroDeArquivo(f"O arquivo compactado tem um item com caminho inseguro (“{nome}”) e não foi aberto.")
    return raiz.joinpath(*partes)


def _nome_do_zip(info):
    """Nome do item como a pessoa vê no Windows: zips sem a marca de UTF-8 guardam os nomes na
    página de código do DOS (no Brasil, a 850); o Python lê como 437 e os acentos viram lixo."""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        bruto = info.filename.encode("cp437")
    except UnicodeEncodeError:
        return info.filename
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("cp850")


# ------------------------------------------------------------ formatos

def _extrair_zip(arquivo, raiz, avisar, cancelado):
    try:
        zipado = zipfile.ZipFile(arquivo)
    except zipfile.BadZipFile:
        raise ErroDeArquivo("O arquivo compactado está danificado ou não é um .zip de verdade.")
    with zipado:
        infos = zipado.infolist()
        total = sum(i.file_size for i in infos) or 1
        feito = 0
        if any(i.flag_bits & 0x1 for i in infos):
            raise ErroDeArquivo("Este arquivo compactado tem senha. Por enquanto o DuiaOS não abre arquivos com senha.")
        for info in infos:
            if cancelado and cancelado():
                raise ErroDeArquivo("Operação cancelada.")
            alvo = _destino_seguro(raiz, _nome_do_zip(info))
            modo = (info.external_attr >> 16) & 0xFFFF
            if info.is_dir():
                alvo.mkdir(parents=True, exist_ok=True)
                continue
            alvo.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(modo):
                destino_link = zipado.read(info).decode("utf-8", "replace")
                _criar_link(raiz, alvo, destino_link)
                continue
            with zipado.open(info) as entrada, open(alvo, "wb") as saida:
                while True:
                    if cancelado and cancelado():
                        raise ErroDeArquivo("Operação cancelada.")
                    bloco = entrada.read(BLOCO)
                    if not bloco:
                        break
                    saida.write(bloco)
                    feito += len(bloco)
                    avisar(feito / total)
            if modo & 0o111:                       # programas continuam executáveis
                os.chmod(alvo, 0o755)
            try:
                momento = datetime.datetime(*info.date_time).timestamp()
                os.utime(alvo, (momento, momento))
            except (ValueError, OverflowError, OSError):
                pass


def _criar_link(raiz, alvo, destino_link):
    """Link simbólico só se apontar para dentro do que foi extraído."""
    final = (alvo.parent / destino_link).resolve() if not destino_link.startswith("/") else Path(destino_link)
    if destino_link.startswith("/") or not (final == raiz.resolve() or raiz.resolve() in final.parents):
        return                                     # aponta para fora: ignorado
    os.symlink(destino_link, alvo)


def _extrair_tar(arquivo, raiz, avisar, cancelado):
    try:
        pacote = tarfile.open(arquivo)
    except (tarfile.TarError, OSError, EOFError, lzma.LZMAError):
        raise ErroDeArquivo("O arquivo compactado está danificado ou num formato desconhecido.")
    with pacote:
        try:
            membros = pacote.getmembers()
        except (tarfile.TarError, EOFError, OSError, lzma.LZMAError):
            raise ErroDeArquivo("O arquivo compactado está danificado.")
        total = sum(m.size for m in membros) or 1
        feito = 0
        for membro in membros:
            if cancelado and cancelado():
                raise ErroDeArquivo("Operação cancelada.")
            _destino_seguro(raiz, membro.name)    # recusa ".." e caminhos absolutos com mensagem clara
            try:
                # filtro "data" (PEP 706): sem links para fora, sem dispositivos, sem setuid
                pacote.extract(membro, raiz, filter="data")
            except tarfile.FilterError:
                continue                           # link para fora ou arquivo especial: ignorado
            except (tarfile.TarError, EOFError, lzma.LZMAError):
                raise ErroDeArquivo("O arquivo compactado está danificado.")
            feito += membro.size
            avisar(feito / total)


def _extrair_simples(arquivo, raiz, abrir, avisar, cancelado):
    alvo = raiz / nome_sem_extensao(arquivo)
    total = max(Path(arquivo).stat().st_size, 1)
    try:
        with abrir(arquivo, "rb") as entrada, open(alvo, "wb") as saida:
            while True:
                if cancelado and cancelado():
                    raise ErroDeArquivo("Operação cancelada.")
                bloco = entrada.read(BLOCO)
                if not bloco:
                    break
                saida.write(bloco)
                # posição no arquivo compactado (o tamanho final não é conhecido)
                lido = getattr(getattr(entrada, "fileobj", None), "tell", lambda: 0)() or 0
                avisar(min(0.99, lido / total))
    except (OSError, EOFError, lzma.LZMAError) as erro:
        if isinstance(erro, ErroDeArquivo):
            raise
        raise ErroDeArquivo("O arquivo compactado está danificado.")


def _extrair_7z(arquivo, raiz, avisar, cancelado):
    programa = _7z()
    if not programa:
        raise ErroDeArquivo("Para abrir arquivos .7z e .rar falta o 7-Zip (pacote 7zip).")
    # -p- : nunca perguntar senha (sem terminal); -bsp1: andamento na saída padrão
    processo = subprocess.Popen([programa, "x", "-y", "-p-", "-bsp1", "-bso0", "-bse1", f"-o{raiz}", "--", str(arquivo)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    saida = b""
    while True:
        pedaco = processo.stdout.read1(4096) if hasattr(processo.stdout, "read1") else processo.stdout.read(4096)
        if not pedaco:
            break
        saida = (saida + pedaco)[-8192:]
        porcentos = re.findall(rb"(\d{1,3})%", pedaco)
        if porcentos:
            avisar(min(1.0, int(porcentos[-1]) / 100))
        if cancelado and cancelado():
            processo.kill()
            processo.wait()
            raise ErroDeArquivo("Operação cancelada.")
    codigo = processo.wait()
    if codigo != 0:
        texto = saida.decode("utf-8", "replace").lower()
        if "password" in texto or "encrypted" in texto:
            raise ErroDeArquivo("Este arquivo compactado tem senha. Por enquanto o DuiaOS não abre arquivos com senha.")
        if arquivo.lower().endswith(".rar") and ("unsupported" in texto or "cannot open" in texto):
            # o 7-Zip do Debian (main) não traz o descompactador de RAR: ele fica no 7zip-rar (non-free)
            raise ErroDeArquivo("Para abrir arquivos .rar falta o suporte a RAR do 7-Zip (pacote 7zip-rar).")
        raise ErroDeArquivo("O arquivo compactado está danificado ou num formato desconhecido.")
    # Mesmo cuidado dos outros formatos: nada de links que apontam para fora
    for pasta, subpastas, arquivos in os.walk(raiz):
        for nome in subpastas + arquivos:
            item = Path(pasta) / nome
            if item.is_symlink():
                destino_link = os.readlink(item)
                final = (item.parent / destino_link).resolve()
                if destino_link.startswith("/") or not (raiz.resolve() in final.parents or final == raiz.resolve()):
                    item.unlink()


# ------------------------------------------------------------ principal

def descompactar(arquivo, progresso=None, cancelado=None):
    """Descompacta na pasta do arquivo. Devolve o caminho do que apareceu (pasta ou arquivo).

    progresso(fração 0–1) é chamado durante a extração; cancelado() → True interrompe.
    """
    arquivo = Path(arquivo)
    ext = extensao(arquivo)
    if not ext:
        raise ErroDeArquivo("Este arquivo não é um arquivo compactado que o DuiaOS saiba abrir.")
    if not arquivo.is_file():
        raise ErroDeArquivo("O arquivo compactado não existe mais.")
    pasta = arquivo.parent
    if not os.access(pasta, os.W_OK):
        raise ErroDeArquivo("Você não tem permissão para criar arquivos nesta pasta.")

    def avisar(fracao):
        if progresso:
            progresso(max(0.0, min(1.0, fracao)))

    try:
        temporaria = Path(tempfile.mkdtemp(prefix=".descompactando-", dir=pasta))
    except OSError as erro:
        raise ErroDeArquivo(f"Não foi possível descompactar aqui ({erro.strerror}).")
    try:
        if ext == ".zip":
            _extrair_zip(arquivo, temporaria, avisar, cancelado)
        elif ext in EXTENSOES_TAR:
            _extrair_tar(arquivo, temporaria, avisar, cancelado)
        elif ext in EXTENSOES_SIMPLES:
            # .tar.gz com outro nome (ex.: "pacote.gz" que é um tar) também abre como pasta
            if tarfile.is_tarfile(arquivo):
                _extrair_tar(arquivo, temporaria, avisar, cancelado)
            else:
                _extrair_simples(arquivo, temporaria, EXTENSOES_SIMPLES[ext], avisar, cancelado)
        else:
            _extrair_7z(str(arquivo), temporaria, avisar, cancelado)

        conteudo = sorted(temporaria.iterdir())
        if not conteudo:
            raise ErroDeArquivo("O arquivo compactado está vazio.")
        if len(conteudo) == 1:
            unico = conteudo[0]
            resultado = pasta / operacoes.nome_livre(pasta, unico.name)
            os.rename(unico, resultado)
        else:
            resultado = pasta / operacoes.nome_livre(pasta, nome_sem_extensao(arquivo) or "Arquivos")
            os.rename(temporaria, resultado)
            os.chmod(resultado, 0o755 & ~_umask())
        avisar(1.0)
        return str(resultado)
    except ErroDeArquivo:
        raise
    except PermissionError:
        raise ErroDeArquivo("Sem permissão para descompactar aqui.")
    except OSError as erro:
        if erro.errno == 28:
            raise ErroDeArquivo("Não há espaço livre suficiente para descompactar.")
        raise ErroDeArquivo(f"Não foi possível descompactar ({erro.strerror}).")
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)


def _umask():
    atual = os.umask(0)
    os.umask(atual)
    return atual
