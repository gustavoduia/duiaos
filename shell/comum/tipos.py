"""DuiaOS — tipo de cada arquivo (ícone, descrição em português, se tem miniatura).

Usado pelo Explorador de Arquivos e pela pilha de Downloads da Ilha.
"""
import mimetypes
from pathlib import Path

IMAGENS_COM_MINIATURA = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

_POR_EXTENSAO = {
    # extensão: (ícone, descrição)
    ".pdf": ("pdf", "Documento PDF"),
    ".txt": ("documento", "Texto"), ".md": ("documento", "Texto (Markdown)"), ".rtf": ("documento", "Texto formatado"),
    ".doc": ("documento", "Documento do Word"), ".docx": ("documento", "Documento do Word"),
    ".odt": ("documento", "Documento de texto"),
    ".xls": ("planilha", "Planilha do Excel"), ".xlsx": ("planilha", "Planilha do Excel"),
    ".ods": ("planilha", "Planilha"), ".csv": ("planilha", "Tabela (CSV)"),
    ".ppt": ("apresentacao", "Apresentação do PowerPoint"), ".pptx": ("apresentacao", "Apresentação do PowerPoint"),
    ".odp": ("apresentacao", "Apresentação"),
    ".zip": ("compactado", "Arquivo compactado"), ".tar": ("compactado", "Arquivo compactado"),
    ".gz": ("compactado", "Arquivo compactado"), ".xz": ("compactado", "Arquivo compactado"),
    ".7z": ("compactado", "Arquivo compactado"), ".rar": ("compactado", "Arquivo compactado"),
    ".bz2": ("compactado", "Arquivo compactado"), ".zst": ("compactado", "Arquivo compactado"),
    ".deb": ("compactado", "Pacote de instalação"), ".iso": ("disco", "Imagem de disco"),
    ".py": ("codigo", "Código Python"), ".js": ("codigo", "Código JavaScript"), ".sh": ("terminal", "Script"),
    ".html": ("codigo", "Página da web"), ".css": ("codigo", "Folha de estilos"), ".json": ("codigo", "Dados (JSON)"),
    ".qml": ("codigo", "Código QML"), ".c": ("codigo", "Código C"), ".rs": ("codigo", "Código Rust"),
    ".desktop": ("aplicativos", "Atalho de aplicativo"),
}

_POR_GRUPO = {
    "image": ("imagem", "Imagem"),
    "audio": ("musica", "Áudio"),
    "video": ("video", "Vídeo"),
    "text": ("documento", "Texto"),
}


def tipo(caminho, eh_pasta=False):
    """(ícone, descrição, miniatura) para o arquivo."""
    if eh_pasta:
        return "pasta", "Pasta", False
    extensao = Path(caminho).suffix.lower()
    miniatura = extensao in IMAGENS_COM_MINIATURA
    if extensao in _POR_EXTENSAO:
        icone, descricao = _POR_EXTENSAO[extensao]
        return icone, descricao, miniatura
    mime, _ = mimetypes.guess_type(str(caminho))
    if mime:
        grupo = mime.split("/")[0]
        if grupo in _POR_GRUPO:
            icone, descricao = _POR_GRUPO[grupo]
            if extensao:
                descricao += " " + extensao[1:].upper()
            return icone, descricao, miniatura
    return "arquivo", ("Arquivo " + extensao[1:].upper()) if extensao else "Arquivo", False


def mime(caminho):
    tipo_mime, _ = mimetypes.guess_type(str(caminho))
    return tipo_mime or "application/octet-stream"


def tamanho_legivel(bytes_):
    if bytes_ < 0:
        return ""
    unidades = ["bytes", "KB", "MB", "GB", "TB"]
    valor = float(bytes_)
    for unidade in unidades:
        if valor < 1000 or unidade == unidades[-1]:
            if unidade == "bytes":
                return f"{int(valor)} {'byte' if int(valor) == 1 else 'bytes'}"
            return f"{valor:.1f} {unidade}".replace(".", ",")
        valor /= 1000
    return ""
