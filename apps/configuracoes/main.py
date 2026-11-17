#!/usr/bin/env python3
"""DuiaOS — Configurações.

Seções: Wi-Fi, Bluetooth, Notificações, Som, Tela, Bateria e energia, Aparência
(modo escuro), Papel de parede, Tela de Descanso, Barra e Ilha, Usuário e senha (com a
foto da conta), Data e hora, Idioma e teclado, Aplicativos padrão, Atualizações (pelo
duiaos-agente), Privacidade, Inteligência artificial e Sobre este computador.

Os controles do dia a dia (Wi-Fi, som, brilho…) vêm de shell/comum/controles.py,
os mesmos da Barra de Recursos. O que precisa de permissão de administrador
(fuso horário, teclado do sistema, nome do computador, senha) passa pelo polkit:
regras do DuiaOS liberam a pessoa que está no computador e é administradora, e a
troca de senha confere a senha atual (/usr/lib/duiaos/conta).

Uso:
  main.py [--secao NOME]              abre (seções: wifi, bluetooth, notificacoes, som, tela,
                                      energia, aparencia, papel, descanso, barra, usuario,
                                      data, teclado, padroes, atualizacoes, privacidade, ia, sobre)
  main.py --demonstracao [--secao NOME] [--captura ARQUIVO]
"""
import fcntl
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

PASTA = Path(__file__).resolve().parent
for _comum in (Path(os.environ.get("DUIAOS_SHELL", "/usr/share/duiaos/shell")) / "comum",
               PASTA.parents[1] / "shell" / "comum"):
    if (_comum / "controles.py").is_file():
        sys.path.insert(0, str(_comum))
        break
sys.path.insert(0, str(PASTA))

import aplicativos  # noqa: E402
import controles  # noqa: E402
import interface  # noqa: E402
import pastas  # noqa: E402
import sessao  # noqa: E402
import sistema as comum  # noqa: E402

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

DEMONSTRACAO = "--demonstracao" in sys.argv
SECOES = ("wifi", "bluetooth", "notificacoes", "som", "tela", "energia", "aparencia", "papel", "descanso", "barra",
          "usuario", "data", "teclado", "padroes", "armazenamento", "atualizacoes", "privacidade", "ia", "wise", "sobre")
PASTA_FUNDOS = pastas.DADOS / "duiaos" / "fundos"          # imagens e vídeos importados
EXTENSOES_FUNDO = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mkv", ".mov", ".m4v")
AGENTE = ("org.duiaos.Agente1", "/org/duiaos/Agente1")
AJUDANTE_CONTA = "/usr/lib/duiaos/conta"
AJUDANTE_PAPEL_ENTRADA = "/usr/lib/duiaos/papel-entrada"
ARQUIVO_PEDIDO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-configuracoes.secao"

# Aplicativos padrão: categoria → (rótulo, tipos MIME)
PADROES = {
    "navegador": ("Navegador", ["x-scheme-handler/http", "x-scheme-handler/https", "text/html"]),
    "email": ("E-mail", ["x-scheme-handler/mailto"]),
    "pdf": ("Documentos PDF", ["application/pdf"]),
    "imagens": ("Imagens", ["image/png", "image/jpeg", "image/webp", "image/gif"]),
    "musica": ("Música", ["audio/mpeg", "audio/ogg", "audio/flac", "audio/x-wav"]),
    "video": ("Vídeos", ["video/mp4", "video/x-matroska", "video/webm"]),
    "texto": ("Textos", ["text/plain"]),
    "pastas": ("Pastas", ["inode/directory"]),
}


def executar(*comando, entrada=None, tempo=10):
    return controles.executar(*comando, entrada=entrada, tempo=tempo)


# ------------------------------------------------------- leitura do sistema

def procurar_ao_abrir(etapa):
    """Atualizações abertas pelo ícone da barra ou pela notificação: procura e mostra o resumo, a não ser que já
    esteja procurando, mostrando um resumo, instalando ou mostrando o resultado de uma instalação."""
    return etapa in ("inicio", "em-dia", "erro")


def ler_sobre():
    info = {"sistema": comum.versao(), "computador": platform.node(), "processador": "", "memoria": "",
            "graficos": "", "disco": "", "nucleo": platform.release(), "arquitetura": platform.machine()}
    try:
        for linha in Path("/proc/cpuinfo").read_text().splitlines():
            if linha.startswith("model name"):
                info["processador"] = re.sub(r"\s+", " ", linha.split(":", 1)[1]).strip()
                break
        info["processador"] += f" ({os.cpu_count()} núcleos)"
    except OSError:
        pass
    try:
        for linha in Path("/proc/meminfo").read_text().splitlines():
            if linha.startswith("MemTotal:"):
                info["memoria"] = f"{round(int(linha.split()[1]) / 1024 / 1024)} GB"
                break
    except (OSError, ValueError):
        pass
    _, pci = executar("lspci", tempo=3)
    for linha in pci.splitlines():
        if re.search(r"VGA compatible|3D controller|Display controller", linha):
            info["graficos"] = re.sub(r"\s*\(rev [0-9a-f]+\)", "", linha.split(": ", 1)[-1])
            break
    try:
        uso = shutil.disk_usage("/")
        info["disco"] = (f"{round(uso.free / 1e9)} GB livres de {round(uso.total / 1e9)} GB")
    except OSError:
        pass
    return info


def ler_padrao(tipo):
    _, saida = executar("xdg-mime", "query", "default", tipo, tempo=3)
    return saida.strip()


def ler_fusos():
    _, saida = executar("timedatectl", "list-timezones", tempo=5)
    return [f for f in saida.splitlines() if f]


def ler_data():
    _, saida = executar("timedatectl", "show", tempo=3)
    dados = dict(linha.split("=", 1) for linha in saida.splitlines() if "=" in linha)
    return {"fuso": dados.get("Timezone", ""), "automatica": dados.get("NTP", "no") == "yes"}


def ler_telas():
    _, saida = executar("wlr-randr", tempo=3)
    return sessao.interpretar_wlr_randr(saida)


def _catalogo_do_repositorio():
    """Demonstração: o catálogo gerado das fichas do repositório (ferramentas/atualizacoes.py)."""
    sys.path.insert(0, str(PASTA.parents[1] / "ferramentas"))
    try:
        import atualizacoes as fichas
        return fichas.catalogo()
    except Exception:          # noqa: BLE001
        return {"atualizacoes": []}


def recomendacoes_de_limpeza():
    """O que dá para apagar com segurança na conta da pessoa, com o tamanho de cada coisa."""
    import armazenamento as ar
    lista = []
    lixeira = ar.tamanho_da_pasta(pastas.LIXEIRA, limite_s=10) if pastas.LIXEIRA.is_dir() else 0
    if lixeira:
        lista.append({"id": "lixeira", "titulo": "Esvaziar a Lixeira", "tamanho": lixeira, "acao": "Esvaziar",
                      "texto": "O que você já apagou continua ocupando espaço até esvaziar a Lixeira."})
    cache = sum(c["tamanho"] for c in ar.caches())
    if cache > 50 * 1024 * 1024:
        lista.append({"id": "caches", "titulo": "Arquivos temporários dos aplicativos", "tamanho": cache, "acao": "Revisar",
                      "texto": "Cópias que navegadores e aplicativos guardam para abrir mais rápido. Eles refazem o que precisarem."})
    antigos = ar.antigos(pastas.pasta("DOWNLOAD"))
    if antigos:
        lista.append({"id": "antigos", "titulo": "Downloads antigos", "tamanho": sum(a["tamanho"] for a in antigos), "acao": "Revisar",
                      "texto": f"{len(antigos)} {'arquivo' if len(antigos) == 1 else 'arquivos'} em Downloads sem uso há mais de 90 dias."})
    grandes = ar.maiores_por_categoria(pastas.INICIO, "grandes", minimo=500 * 1000 ** 2, pular=[pastas.INICIO / ".cache", pastas.LIXEIRA])
    if grandes:
        lista.append({"id": "grandes", "titulo": "Arquivos grandes", "tamanho": sum(a["tamanho"] for a in grandes), "acao": "Revisar",
                      "texto": f"{len(grandes)} {'arquivo' if len(grandes) == 1 else 'arquivos'} com mais de 500 MB na sua pasta pessoal."})
    if ar.tem_flatpak_da_pessoa():
        lista.append({"id": "flatpak", "titulo": "Ambientes do Flathub sem uso", "tamanho": 0, "acao": "Limpar",
                      "texto": "Partes que aplicativos já removidos usavam. O Flathub remove só o que nenhum aplicativo usa."})
    lista.append({"id": "duplicados", "titulo": "Arquivos repetidos", "tamanho": 0, "acao": "Procurar",
                  "texto": "Procura cópias iguais do mesmo arquivo na sua pasta pessoal (leva alguns segundos)."})
    return lista


def armazenamento_de_exemplo():
    gb = 1000 ** 3
    return {"carregando": False, "sistema": {"total": 256 * gb, "usado": 231 * gb, "livre": 25 * gb},
            "dispositivos": [
                {"nome": "Disco do sistema", "montado": "/", "caminho": "/dev/nvme0n1p5", "sistema": "ext4", "total": 256 * gb,
                 "usado": 231 * gb, "livre": 25 * gb, "removivel": False, "nivel": "pouco", "modelo": "SAMSUNG MZVLB256"},
                {"nome": "Windows", "montado": "", "caminho": "/dev/nvme0n1p3", "sistema": "ntfs", "total": 180 * gb, "usado": 0, "livre": 0,
                 "removivel": False, "nivel": "", "modelo": "SAMSUNG MZVLB256"},
                {"nome": "PENDRIVE", "montado": "/media/gustavo/PENDRIVE", "caminho": "/dev/sda1", "sistema": "vfat", "total": 32 * gb,
                 "usado": 9 * gb, "livre": 23 * gb, "removivel": True, "nivel": "ok", "modelo": "SanDisk"}],
            "uso": [{"id": "aplicativos", "nome": "Aplicativos", "tamanho": 38 * gb}, {"id": "videos", "nome": "Vídeos", "tamanho": 61 * gb},
                    {"id": "ia", "nome": "Modelos de IA (Wise)", "tamanho": 9 * gb}, {"id": "pictures", "nome": "Imagens", "tamanho": 27 * gb},
                    {"id": "download", "nome": "Downloads", "tamanho": 22 * gb}, {"id": "documents", "nome": "Documentos", "tamanho": 12 * gb},
                    {"id": "music", "nome": "Música", "tamanho": 8 * gb}, {"id": "cache", "nome": "Arquivos temporários (caches)", "tamanho": 6 * gb},
                    {"id": "lixeira", "nome": "Lixeira", "tamanho": 4 * gb}, {"id": "pessoal", "nome": "Outros arquivos seus", "tamanho": 14 * gb},
                    {"id": "sistema", "nome": "Sistema e outros", "tamanho": 30 * gb}],
            "recomendacoes": [
                {"id": "antigos", "titulo": "Downloads antigos", "tamanho": 14 * gb, "acao": "Revisar",
                 "texto": "37 arquivos em Downloads sem uso há mais de 90 dias."},
                {"id": "caches", "titulo": "Arquivos temporários dos aplicativos", "tamanho": 6 * gb, "acao": "Revisar",
                 "texto": "Cópias que navegadores e aplicativos guardam para abrir mais rápido. Eles refazem o que precisarem."},
                {"id": "lixeira", "titulo": "Esvaziar a Lixeira", "tamanho": 4 * gb, "acao": "Esvaziar",
                 "texto": "O que você já apagou continua ocupando espaço até esvaziar a Lixeira."},
                {"id": "apt", "titulo": "Pacotes de instalação já usados", "tamanho": int(1.8 * gb), "acao": "Limpar",
                 "texto": "Cópias dos pacotes que o sistema já instalou. Podem ser apagadas: baixam de novo se precisar."},
                {"id": "duplicados", "titulo": "Arquivos repetidos", "tamanho": 0, "acao": "Procurar",
                 "texto": "Procura cópias iguais do mesmo arquivo na sua pasta pessoal (leva alguns segundos)."}],
            "lista": {"tipo": "", "titulo": "", "itens": [], "carregando": False}}


def lista_de_exemplo(tipo):
    mb = 1000 ** 2
    nomes = {"videos": [("Viagem Gramado 2025.mp4", 4200), ("Aniversário.mov", 2900), ("Tutorial gravado.mkv", 1300)],
             "programas": [("GIMP", 1368), ("LibreOffice", 620), ("VLC", 95)]}
    return [{"caminho": f"/home/demo/Vídeos/{n}" if tipo != "programas" else f"flathub:org.exemplo.{n}", "nome": n,
             "tamanho": t * mb, "pasta": "/home/demo/Vídeos" if tipo != "programas" else "Flathub", "mudou": 1760000000}
            for n, t in nomes.get(tipo, nomes["videos"])]


def detalhar_plano(plano):
    """Plano do duiaos-agente → o que mostrar: fichas do DuiaOS e pacotes do Debian com descrição e selo de segurança."""
    import atualizacoes_sistema as at
    import tipos
    mudancas = plano.get("mudancas", {})
    todas = mudancas.get("atualizar", []) + mudancas.get("instalar", [])
    if not todas:
        return {"etapa": "em-dia", "mensagem": "Não há nada para atualizar agora."}
    origens = {p["pacote"]: p for p in at.simular()}
    duiaos = [m for m in todas if m["pacote"].startswith("duiaos-")]
    debian = [m for m in todas if not m["pacote"].startswith("duiaos-")]
    descricoes = at.descricoes([m["pacote"] for m in debian])
    publicado = at.baixar_catalogo(at.endereco_do_catalogo())
    instalado = at.ler_catalogo_instalado()
    fichas = at.fichas_pendentes(publicado, instalado, duiaos)
    com_ficha = {p for f in fichas for p in f.get("pacotes", [])}
    lista_debian = []
    for m in debian:
        origem = origens.get(m["pacote"], {})
        lista_debian.append({"pacote": m["pacote"], "de": m.get("de", ""), "para": m.get("para", ""),
                             "descricao": descricoes.get(m["pacote"], ""), "origem": origem.get("origem", ""),
                             "seguranca": origem.get("seguranca", False)})
    lista_debian.sort(key=lambda p: (not p["seguranca"], p["pacote"]))
    reiniciar = at.maior_reinicio(fichas)
    if any(p["pacote"].startswith(("linux-image", "systemd", "libc6")) for p in debian):
        reiniciar = "computador"
    nomes = {"nao": "Não é preciso reiniciar", "sessao": "Saia e entre de novo na sessão", "computador": "Reinicie o computador"}
    return {"etapa": "pronta", "plano": plano["id"], "quantidade": len(todas), "estimativa": plano.get("estimativa_s", 0),
            "baixar": tipos.tamanho_legivel(plano.get("baixar_bytes", 0)), "reiniciar": reiniciar, "reiniciarNome": nomes[reiniciar],
            "duiaos": fichas, "debian": lista_debian, "quantidadeSeguranca": sum(1 for p in lista_debian if p["seguranca"]),
            "duiaosSemFicha": [f"{m['pacote']} {m.get('para', '')}" for m in duiaos if m["pacote"] not in com_ficha]}


# =========================================================================== Qt

class Ajustes(QObject):
    mudou = Signal()
    secaoMudou = Signal()
    atualizacaoMudou = Signal()
    aviso = Signal(str)
    _pronto = Signal(str, object)

    def __init__(self, secao):
        super().__init__()
        self._secao = secao if secao in SECOES else "wifi"
        self._sobre, self._telas, self._padroes, self._fusos = {}, [], {}, []
        self._data = {"fuso": "", "automatica": True}
        self._apps_por_categoria = {}
        self._papeis = sessao.papeis_do_sistema()
        self._atualizacao = {"etapa": "inicio"}
        self._pronto.connect(self._ao_pronto)
        if DEMONSTRACAO:
            self._demonstracao()
            if self._secao == "atualizacoes" and "--atualizando" in sys.argv:
                import time as _tempo
                self._atualizacao = {"etapa": "atualizando", "fracao": 0.62, "mensagem": "Installed linux-image-6.12.117+deb13-amd64 (amd64)",
                                     "etapaAtual": "Preparando a inicialização do sistema (initramfs)", "inicio": int(_tempo.time()) - 431,
                                     "estimativa": 290, "registro": "20261114-184900-0123456789abcdef.log",
                                     "alerta": "Está demorando: “Preparando a inicialização do sistema (initramfs)” há 5 min sem novidade. "
                                               "Isso pode ser normal com o kernel; o DuiaOS espera até 30 min."}
            elif self._secao == "atualizacoes":
                QTimer.singleShot(100, self.procurarAtualizacoes)
        else:
            if self._secao == "atualizacoes":
                QTimer.singleShot(300, self._mostrar_resumo_de_atualizacoes)
            self._em_fundo("sobre", ler_sobre)
            self._em_fundo("telas", ler_telas)
            self._em_fundo("data", ler_data)
            self._em_fundo("padroes", self._ler_padroes)
            # Outra chamada (ex.: um balão da Barra) pede uma seção com a janela já aberta
            self._vigia = QTimer(self, interval=500, timeout=self._ver_pedido)
            self._vigia.start()
            self._vigia_agente = QTimer(self, interval=10000, timeout=self._conferir_agente)
            self._vigia_agente.start()

    def _demonstracao(self):
        self._sobre = {"sistema": "DuiaOS 0.3.0 (Zoinho)", "computador": "duiaos", "processador": "11th Gen Intel Core i5-1135G7 @ 2.40GHz (8 núcleos)",
                       "memoria": "16 GB", "graficos": "Intel Iris Xe Graphics", "disco": "182 GB livres de 240 GB",
                       "nucleo": "6.12.48-amd64", "arquitetura": "x86_64"}
        self._telas = [{"nome": "eDP-1", "descricao": "Tela do notebook", "ligada": True, "modo": "1920x1080@60.000",
                        "escala": 1.25, "modos": [{"valor": "1920x1080@60.000", "rotulo": "1920 × 1080 (60 Hz)", "preferido": True},
                                                   {"valor": "1600x900@60.000", "rotulo": "1600 × 900 (60 Hz)", "preferido": False},
                                                   {"valor": "1280x720@60.000", "rotulo": "1280 × 720 (60 Hz)", "preferido": False}]}]
        self._data = {"fuso": "America/Sao_Paulo", "automatica": True}
        self._fusos = ["America/Sao_Paulo", "America/Manaus", "America/Recife", "America/Fortaleza", "Europe/Lisbon"]
        self._padroes = {"navegador": "firefox-esr.desktop", "pastas": "duiaos-explorador-de-arquivos.desktop"}
        self._apps_por_categoria = {"navegador": [{"id": "firefox-esr.desktop", "nome": "Firefox"}, {"id": "chromium.desktop", "nome": "Chromium"}],
                                    "pastas": [{"id": "duiaos-explorador-de-arquivos.desktop", "nome": "Explorador de Arquivos"}]}

    def _em_fundo(self, nome, funcao, *args):
        def tarefa():
            try:
                resultado = funcao(*args)
            except Exception as erro:              # nunca derrubar a janela
                resultado = erro
            self._pronto.emit(nome, resultado)
        threading.Thread(target=tarefa, daemon=True).start()

    def _ao_pronto(self, nome, resultado):
        if nome.startswith("armazenamento"):
            self._ao_armazenamento(nome, resultado)
            return
        if isinstance(resultado, Exception):
            return
        if nome == "aviso-papel":
            if resultado:
                self.aviso.emit(resultado)
            self.mudou.emit()
            return
        if nome == "aviso":
            if resultado:
                self.aviso.emit(resultado)
            self._em_fundo("data", ler_data)
            return
        if nome == "detalhes":
            self._atualizacao = resultado
            self.atualizacaoMudou.emit()
            return
        if nome == "registro":
            self._registro = resultado
            self.atualizacaoMudou.emit()
            return
        if nome == "flathub":
            self._flathub = resultado
            self.atualizacaoMudou.emit()
            return
        if nome == "fusos":
            self._fusos = resultado
        elif nome == "sobre":
            self._sobre = resultado
        elif nome == "telas":
            self._telas = resultado
        elif nome == "data":
            self._data = resultado
        elif nome == "padroes":
            self._padroes, self._apps_por_categoria = resultado
        self.mudou.emit()

    def _ver_pedido(self):
        try:
            secao = ARQUIVO_PEDIDO.read_text().strip()
            ARQUIVO_PEDIDO.unlink()
        except OSError:
            return
        if secao in SECOES:
            self.irPara(secao)
        if secao == "atualizacoes":
            self._mostrar_resumo_de_atualizacoes()
        janela = QGuiApplication.topLevelWindows()
        if janela:
            janela[0].requestActivate()

    def _mostrar_resumo_de_atualizacoes(self):
        """Aberta por fora (dois cliques no ícone da barra, a notificação): já mostra o resumo do que há."""
        if procurar_ao_abrir(self._atualizacao.get("etapa")):
            self.procurarAtualizacoes()

    # -------------------------------------------------------------- seções
    @Slot(str)
    def irPara(self, secao):
        if secao in SECOES and secao != self._secao:
            self._secao = secao
            self.secaoMudou.emit()
            if secao == "data" and not self._fusos and not DEMONSTRACAO:
                self._em_fundo("fusos", ler_fusos)
            if secao == "tela" and not DEMONSTRACAO:
                self._em_fundo("telas", ler_telas)

    # --------------------------------------------------------------- tela
    @Slot(str, str, float)
    def definirTela(self, nome, modo, escala):
        pastas.gravar_preferencia("telas", nome + ".modo", modo)
        pastas.gravar_preferencia("telas", nome + ".escala", f"{escala:g}")
        if not DEMONSTRACAO:
            def aplicar():
                codigo, _ = executar(*sessao.comando_tela(nome, modo, escala))
                return "" if codigo == 0 else "Não foi possível mudar a tela."
            self._em_fundo("aviso", aplicar)
            QTimer.singleShot(1200, lambda: self._em_fundo("telas", ler_telas))

    @Slot(str, str)
    def definirHorarioLuz(self, inicio, fim):
        self._controles.definirHorarioLuzNoturna(inicio, fim)
        self.mudou.emit()

    luzInicio = Property(str, lambda self: pastas.ler_preferencia("luz-noturna", "inicio", "19:00"), notify=mudou)
    luzFim = Property(str, lambda self: pastas.ler_preferencia("luz-noturna", "fim", "06:30"), notify=mudou)

    # ------------------------------------------------------------ estilo
    @Slot(str)
    def definirEstilo(self, estilo):
        """Estilo da interface (ADR 052). Na sessão vale na hora; na Tela de Entrada (de todas as
        contas), pelo ajudante de administrador — sem ser administrador, ela fica como está."""
        if estilo not in ("padrao", "futurista"):
            return
        interface.aparencia().definirEstilo(estilo)
        if DEMONSTRACAO:
            return

        def mudar():
            subprocess.run(["pkexec", AJUDANTE_PAPEL_ENTRADA, "estilo", estilo], capture_output=True, timeout=60, check=False)
            return ""
        self._em_fundo("aviso-papel", mudar)

    # ---------------------------------------------------- papel de parede
    # Alvo (ADR 051): "area" (área de trabalho: todas as telas, uma tela escolhida ou estendida),
    # "bloqueio" (Tela de Bloqueio) ou "entrada" (Tela de Entrada, de todas as contas).
    def _secao_area(self):
        import papel
        area = papel.ler_area(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)
        tela = getattr(self, "_tela_papel", "")
        return f"papel-de-parede:{tela}" if area["telas"] == "separado" and tela else "papel-de-parede"

    @Slot(str)
    def escolherAlvoPapel(self, alvo):
        if alvo in ("area", "bloqueio", "entrada"):
            self._alvo_papel = alvo
            self.mudou.emit()

    @Slot(str)
    def escolherTelaPapel(self, nome):
        self._tela_papel = nome
        self.mudou.emit()

    def _gravar_papel(self, chave, valor):
        """Grava uma opção do papel do alvo escolhido."""
        alvo = getattr(self, "_alvo_papel", "area")
        if alvo == "area":
            pastas.gravar_preferencia(self._secao_area(), chave, valor)
        elif alvo == "bloqueio":
            pastas.gravar_preferencia("papel-bloqueio", "modo", "proprio")
            pastas.gravar_preferencia("papel-bloqueio", chave, valor)
        self.mudou.emit()          # a Área de Trabalho vê a preferência mudar e troca o fundo na hora

    @Slot(str)
    def definirPapel(self, arquivo):
        """Uma imagem, vídeo ou cor (#RRGGBB) para o alvo escolhido."""
        import papel
        if arquivo.startswith("file://"):
            arquivo = arquivo[7:]
        alvo = getattr(self, "_alvo_papel", "area")
        cor = arquivo.startswith("#")
        if alvo in ("bloqueio", "entrada") and not cor and not arquivo.lower().endswith(papel.EXTENSOES_IMAGEM):
            self.aviso.emit("As Telas de Entrada e de Bloqueio usam fotos (JPG, PNG ou WebP), não vídeos nem GIFs.")
            return
        if alvo == "entrada":
            atual = self._papel_entrada()
            if cor:
                self._entrada("imagem-cor", atual["ajuste"], arquivo, atual["desfocar"])
            else:
                self._entrada("imagem", atual["ajuste"], atual["cor"], atual["desfocar"], arquivo)
            return
        if cor:
            self._gravar_papel("cor", arquivo)
            self._gravar_papel("arquivo", "")
        else:
            self._gravar_papel("arquivo", arquivo)

    @Slot(str)
    def definirAjuste(self, ajuste):
        import papel
        if ajuste not in papel.AJUSTES:
            return
        if getattr(self, "_alvo_papel", "area") == "entrada":
            atual = self._papel_entrada()
            # Com o papel do DuiaOS, o ajudante precisa de uma imagem: manda a do DuiaOS
            self._entrada("opcoes" if atual["modo"] == "proprio" else "imagem", ajuste, atual["cor"], atual["desfocar"],
                          atual["arquivo"])
        else:
            self._gravar_papel("ajuste", ajuste)

    @Slot(str)
    def definirCorDasBordas(self, cor):
        """Cor que aparece em volta da imagem (ajustar, centralizar) — sem trocar a imagem."""
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", cor):
            return
        if getattr(self, "_alvo_papel", "area") == "entrada":
            atual = self._papel_entrada()
            self._entrada("opcoes" if atual["modo"] == "proprio" else "imagem", atual["ajuste"], cor, atual["desfocar"],
                          atual["arquivo"])
        else:
            self._gravar_papel("cor", cor)

    @Slot(str)
    def definirModoTelas(self, modo):
        import papel
        if modo in papel.MODOS_TELAS:
            pastas.gravar_preferencia("papel-de-parede", "telas", modo)
            if modo == "separado" and not getattr(self, "_tela_papel", ""):
                telas = self._telas_papel()
                self._tela_papel = telas[0]["nome"] if telas else ""
            self.mudou.emit()

    @Slot(int)
    def definirAlternar(self, minutos):
        import papel
        if minutos in papel.INTERVALOS:
            pastas.gravar_preferencia("papel-de-parede", "alternar", str(minutos))
            self.mudou.emit()

    @Slot(bool)
    def definirDesfocar(self, ligado):
        alvo = getattr(self, "_alvo_papel", "area")
        if alvo == "entrada":
            atual = self._papel_entrada()
            if atual["modo"] == "padrao":
                self._entrada("padrao", desfocar=ligado)
            else:
                self._entrada("opcoes", atual["ajuste"], atual["cor"], ligado)
        elif alvo == "bloqueio":
            pastas.gravar_preferencia("papel-bloqueio", "desfocar", "sim" if ligado else "nao")
            self.mudou.emit()

    @Slot(str, str)
    def definirAcesso(self, chave, valor):
        """Tom azul e brilho das Telas de Bloqueio e de Entrada (estilo futurista; ADR 056).
        chave: veu (0–100), brilho (radial | linear | nenhum) ou brilho_extra (sim | nao)."""
        import papel
        alvo = getattr(self, "_alvo_papel", "area")
        if alvo not in ("bloqueio", "entrada") or chave not in ("veu", "brilho", "brilho_extra"):
            return
        atual = (self._papel_entrada() if alvo == "entrada" else papel.ler_bloqueio(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO))
        novo = dict(atual.get("acesso") or papel.ACESSO_PADRAO)
        novo["brilho_extra"] = "sim" if novo.get("brilho_extra") else "nao"
        novo[chave] = valor
        novo = papel.acesso({k: str(v) for k, v in novo.items()})          # valida
        if alvo == "bloqueio":
            pastas.gravar_preferencia("papel-bloqueio", "veu", str(novo["veu"]))
            pastas.gravar_preferencia("papel-bloqueio", "brilho", novo["brilho"])
            pastas.gravar_preferencia("papel-bloqueio", "brilho_extra", "sim" if novo["brilho_extra"] else "nao")
            self.mudou.emit()
        elif DEMONSTRACAO:
            self._entrada_demo = {**self._papel_entrada(), "acesso": novo}
            self.mudou.emit()
        else:
            self._rodar_ajudante_da_entrada(["acesso", str(novo["veu"]), novo["brilho"], "sim" if novo["brilho_extra"] else "nao"], b"")

    @Slot()
    def usarPapelDaArea(self):
        """Bloqueio: volta a seguir a área de trabalho. Entrada: copia o papel da área de trabalho."""
        import papel
        alvo = getattr(self, "_alvo_papel", "area")
        area = papel.ler_area(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)["padrao"]
        if alvo == "bloqueio":
            pastas.gravar_preferencia("papel-bloqueio", "modo", "area")
            self.mudou.emit()
        elif alvo == "entrada":
            if area["arquivo"] and not area["arquivo"].lower().endswith(papel.EXTENSOES_IMAGEM):
                self.aviso.emit("O papel da área de trabalho é um vídeo ou GIF; a Tela de Entrada usa fotos.")
                return
            atual = self._papel_entrada()
            if area["arquivo"]:
                self._entrada("imagem", area["ajuste"], area["cor"], atual["desfocar"], area["arquivo"])
            else:
                self._entrada("imagem-cor", area["ajuste"], area["cor"], atual["desfocar"])

    @Slot()
    def entradaPadrao(self):
        self._entrada("padrao", desfocar=self._papel_entrada()["desfocar"])

    def _papel_entrada(self):
        import papel
        if DEMONSTRACAO:
            return getattr(self, "_entrada_demo", {"modo": "padrao", "arquivo": str(sessao.PAPEL_PADRAO), "cor": sessao.COR_PADRAO,
                                                   "ajuste": "preencher", "desfocar": False})
        return papel.ler_entrada(papel.ENTRADA_CONF, sessao.PAPEL_PADRAO)

    def _entrada(self, acao, ajuste="preencher", cor="#E8F0FE", desfocar=False, arquivo=""):
        """Tela de Entrada: /usr/lib/duiaos/papel-entrada pelo pkexec (administrador)."""
        sim = "sim" if desfocar else "nao"
        if DEMONSTRACAO:
            self._entrada_demo = ({"modo": "padrao", "arquivo": str(sessao.PAPEL_PADRAO), "cor": sessao.COR_PADRAO,
                                   "ajuste": "preencher", "desfocar": desfocar} if acao == "padrao" else
                                  {"modo": "proprio", "arquivo": arquivo or self._papel_entrada()["arquivo"], "cor": cor,
                                   "ajuste": ajuste, "desfocar": desfocar})
            self.mudou.emit()
            return
        if acao == "padrao":
            argumentos, dados = ["padrao", sim], b""
        elif acao == "opcoes":
            argumentos, dados = ["opcoes", ajuste, cor, sim], b""
        else:
            if acao == "imagem-cor":
                # Uma cor lisa: uma imagem pequena dessa cor
                from PySide6.QtGui import QColor, QImage
                from PySide6.QtCore import QBuffer, QByteArray, QIODevice
                figura = QImage(64, 64, QImage.Format_RGB32)
                figura.fill(QColor(cor))
                bruto, buffer = QByteArray(), None
                buffer = QBuffer(bruto)
                buffer.open(QIODevice.WriteOnly)
                figura.save(buffer, "PNG")
                dados = bytes(bruto)
            else:
                try:
                    dados = Path(arquivo).read_bytes()
                except OSError:
                    self.aviso.emit("Não consegui ler essa imagem.")
                    return
            argumentos = ["imagem", ajuste, cor, sim]

        self._rodar_ajudante_da_entrada(argumentos, dados)

    def _rodar_ajudante_da_entrada(self, argumentos, dados):
        def mudar():
            processo = subprocess.run(["pkexec", AJUDANTE_PAPEL_ENTRADA, *argumentos], input=dados,
                                      capture_output=True, timeout=120, check=False)
            if processo.returncode == 0:
                return ""
            if processo.returncode in (126, 127):
                return "Só um administrador deste computador pode mudar a Tela de Entrada."
            return "Não deu para mudar a Tela de Entrada (a imagem precisa ser JPG, PNG ou WebP de até 40 MB)."
        self._em_fundo("aviso-papel", mudar)

    def _telas_papel(self):
        if DEMONSTRACAO:
            return [{"nome": "eDP-1", "rotulo": "Tela do notebook", "x": 0, "y": 0, "largura": 1920, "altura": 1080},
                    {"nome": "HDMI-A-1", "rotulo": "Monitor (HDMI-A-1)", "x": 1920, "y": 0, "largura": 2560, "altura": 1440}]
        telas = []
        for tela in QGuiApplication.screens():
            g = tela.geometry()
            nome = tela.name()
            embutida = nome.startswith(("eDP", "LVDS", "DSI"))
            modelo = (tela.model() or tela.manufacturer() or "").strip()
            telas.append({"nome": nome, "rotulo": "Tela do notebook" if embutida else (f"{modelo} ({nome})" if modelo else f"Monitor ({nome})"),
                          "x": g.x(), "y": g.y(), "largura": g.width(), "altura": g.height()})
        return telas

    def _papel_info(self):
        """Tudo o que a página mostra: o alvo, as telas, o papel em edição e os das três telas."""
        import papel
        area = papel.ler_area(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)
        alvo = getattr(self, "_alvo_papel", "area")
        telas = self._telas_papel()
        tela = getattr(self, "_tela_papel", "") or (telas[0]["nome"] if telas else "")
        if alvo == "area":
            atual = papel.papel_da_tela(area, tela) if area["telas"] == "separado" else area["padrao"]
        elif alvo == "bloqueio":
            atual = papel.ler_bloqueio(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)
        else:
            atual = self._papel_entrada()
        estendido = papel.recorte_estendido(telas, tela) if area["telas"] == "estender" else None
        return {"alvo": alvo, "telas": telas, "tela": tela, "modoTelas": area["telas"], "alternar": area["alternar"],
                "atual": atual, "estendido": estendido or {}, "porTela": {t["nome"]: papel.papel_da_tela(area, t["nome"]) for t in telas},
                "bloqueioModo": papel.ler_bloqueio(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)["modo"],
                "tamanhoImagem": tamanho_imagem(atual.get("arquivo", ""))}

    papelInfo = Property("QVariantMap", _papel_info, notify=mudou)

    @Slot(result="QVariantList")
    def imagensDoUsuario(self):
        pasta = pastas.pasta("PICTURES")
        try:
            arquivos = sorted((p for p in pasta.rglob("*") if p.suffix.lower() in sessao.EXTENSOES_DE_IMAGEM),
                              key=lambda p: p.stat().st_mtime, reverse=True)[:24]
        except OSError:
            return []
        return [str(p) for p in arquivos]

    papeis = Property("QVariantList", lambda self: self._papeis, constant=True)
    papelAtual = Property(str, lambda self: pastas.ler_preferencia("papel-de-parede", "arquivo", str(sessao.PAPEL_PADRAO)), notify=mudou)
    corAtual = Property(str, lambda self: pastas.ler_preferencia("papel-de-parede", "cor", sessao.COR_PADRAO), notify=mudou)

    # ------------------------------------------------------- barra e ilha
    @Slot(str)
    def definirPosicaoBarra(self, posicao):
        if not DEMONSTRACAO:
            aplicativos.iniciar([sys.executable, str(comum.PASTA_SHELL / "barra-de-recursos" / "main.py"), "--posicao", posicao])
        QTimer.singleShot(300, self.mudou.emit)

    @Slot("QVariantList")
    def definirOrdemIcones(self, ordem):
        if DEMONSTRACAO:
            self._ordem_demo = list(ordem)
            self.mudou.emit()
            return
        sys.path.insert(0, str(comum.PASTA_SHELL / "barra-de-recursos"))
        import configparser
        arquivo = pastas.CONFIG / "duiaos" / "barra-de-recursos.conf"
        config = configparser.ConfigParser()
        config.read(arquivo)
        if not config.has_section("barra"):
            config.add_section("barra")
        config.set("barra", "icones", ",".join(ordem))
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with open(arquivo, "w", encoding="utf-8") as saida:
            saida.write("# DuiaOS — Barra de Recursos (Configurações › Barra e Ilha)\n")
            config.write(saida)
        self.mudou.emit()

    def _config_barra(self):
        import configparser
        config = configparser.ConfigParser()
        config.read(pastas.CONFIG / "duiaos" / "barra-de-recursos.conf")
        posicao = config.get("barra", "posicao", fallback="topo")
        padrao = "wise,wifi,som,bateria,bluetooth,brilho,luz"
        ordem = getattr(self, "_ordem_demo", None) or [i for i in config.get("barra", "icones", fallback=padrao).split(",") if i]
        return posicao, ordem

    def _efeitos_ilha(self):
        pasta = str(comum.PASTA_SHELL / "ilha-de-aplicativos")
        if pasta not in sys.path:
            sys.path.insert(0, pasta)
        import efeitos
        return efeitos

    def _opcoes_ilha(self):
        import configparser
        config = configparser.ConfigParser()
        config.read(pastas.PREFERENCIAS, encoding="utf-8")
        secao = dict(config.items("ilha")) if config.has_section("ilha") else {}
        return self._efeitos_ilha().ler_opcoes({**secao, **getattr(self, "_ilha_demo", {})})

    @Slot(str, str)
    def definirOpcaoIlha(self, chave, valor):
        """Opções da Ilha de Aplicativos (preferencias.conf [ilha]); a Ilha aplica na hora."""
        texto = self._efeitos_ilha().texto_da_opcao(chave, valor)
        if texto is None:
            return
        if DEMONSTRACAO:
            self._ilha_demo = {**getattr(self, "_ilha_demo", {}), chave: texto}
        else:
            pastas.gravar_preferencia("ilha", chave, texto)
        self.mudou.emit()

    opcoesIlha = Property("QVariantMap", _opcoes_ilha, notify=mudou)
    posicaoBarra = Property(str, lambda self: self._config_barra()[0], notify=mudou)
    ordemIcones = Property("QVariantList", lambda self: self._config_barra()[1], notify=mudou)

    # ------------------------------------------------------------ energia
    @Slot(str, int)
    def definirMinutos(self, chave, minutos):
        if chave in ("bloquear", "repousar"):
            pastas.gravar_preferencia("energia", chave, str(max(0, int(minutos))))
            self.mudou.emit()
            if not DEMONSTRACAO:
                self._em_fundo("x", sessao.aplicar_bloqueio)

    bloquearApos = Property(int, lambda self: int(pastas.ler_preferencia("energia", "bloquear", "10") or 10), notify=mudou)
    repousarApos = Property(int, lambda self: int(pastas.ler_preferencia("energia", "repousar", "0") or 0), notify=mudou)

    # ------------------------------------------------------------ usuário
    @Slot(str)
    def definirNome(self, nome):
        nome = nome.strip()
        if not nome or any(c in nome for c in ":,\n"):
            self.aviso.emit("Use um nome sem dois-pontos nem vírgulas.")
            return
        if DEMONSTRACAO:
            return
        def trocar():
            codigo, _ = executar("pkexec", AJUDANTE_CONTA, "nome", entrada=nome + "\n", tempo=60)
            return "Nome alterado." if codigo == 0 else "Não foi possível alterar o nome."
        self._em_fundo("aviso", trocar)

    @Slot(str, str, str)
    def trocarSenha(self, atual, nova, repetida):
        if nova != repetida:
            self.aviso.emit("As duas senhas novas não são iguais.")
            return
        if len(nova) < 6:
            self.aviso.emit("A senha nova precisa ter pelo menos 6 caracteres.")
            return
        if DEMONSTRACAO:
            return
        def trocar():
            codigo, _ = executar("pkexec", AJUDANTE_CONTA, "senha", entrada=atual + "\n" + nova + "\n", tempo=60)
            if codigo == 0:
                return "Senha alterada."
            if codigo == 3:
                return "A senha atual não confere."
            return "Não foi possível alterar a senha."
        self._em_fundo("aviso", trocar)

    usuario = Property("QVariantMap", lambda self: comum.usuario_atual(), notify=mudou)

    # ------------------------------------------------------- data e hora
    @Slot(str)
    def definirFuso(self, fuso):
        if fuso in self._fusos and not DEMONSTRACAO:
            self._em_fundo("aviso", lambda: "" if executar("timedatectl", "set-timezone", fuso)[0] == 0
                           else "Não foi possível mudar o fuso horário.")
        self._data = {**self._data, "fuso": fuso}
        self.mudou.emit()

    @Slot(bool)
    def definirHoraAutomatica(self, ligar):
        if not DEMONSTRACAO:
            self._em_fundo("aviso", lambda: "" if executar("timedatectl", "set-ntp", "true" if ligar else "false")[0] == 0
                           else "Não foi possível mudar o acerto automático.")
        self._data = {**self._data, "automatica": ligar}
        self.mudou.emit()

    data = Property("QVariantMap", lambda self: self._data, notify=mudou)
    fusos = Property("QVariantList", lambda self: self._fusos, notify=mudou)

    # --------------------------------------------------------- teclado
    @Slot(str)
    def definirTeclado(self, layout):
        if layout not in controles.LAYOUTS or DEMONSTRACAO:
            return
        nome, _, variante = layout.partition(":")
        modelo = "abnt2" if nome == "br" else "pc105"
        def trocar():
            codigo, _ = executar("localectl", "set-x11-keymap", nome, modelo, variante)
            return ("O teclado novo vale a partir da próxima entrada." if codigo == 0
                    else "Não foi possível mudar o teclado.")
        self._em_fundo("aviso", trocar)

    # ------------------------------------------------- aplicativos padrão
    def _ler_padroes(self):
        padroes, por_categoria = {}, {}
        todos = aplicativos.listar_aplicativos()
        for categoria, (_, tipos_mime) in PADROES.items():
            padroes[categoria] = ler_padrao(tipos_mime[0])
            por_categoria[categoria] = [{"id": a["id"], "nome": a["nome"], "icone": a["icone"]} for a in todos
                                        if any(t in a["tipos"] for t in tipos_mime)]
        return padroes, por_categoria

    @Slot(str, str)
    def definirPadrao(self, categoria, id_desktop):
        if categoria not in PADROES:
            return
        self._padroes[categoria] = id_desktop
        self.mudou.emit()
        if not DEMONSTRACAO:
            self._em_fundo("aviso", lambda: "" if executar("xdg-mime", "default", id_desktop, *PADROES[categoria][1])[0] == 0
                           else "Não foi possível mudar o aplicativo padrão.")

    padroes = Property("QVariantMap", lambda self: self._padroes, notify=mudou)
    appsPorCategoria = Property("QVariantMap", lambda self: self._apps_por_categoria, notify=mudou)
    categoriasPadrao = Property("QVariantList", lambda self: [{"id": k, "nome": v[0]} for k, v in PADROES.items()], constant=True)

    # ------------------------------------------------------------- outros
    @Slot(str)
    def abrirApp(self, nome):
        if not DEMONSTRACAO:
            comum.abrir_app_duiaos(nome)

    @Slot(str)
    def definirNomeComputador(self, nome):
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$", nome):
            self.aviso.emit("Use só letras sem acento, números e hífen, sem espaços.")
            return
        if DEMONSTRACAO:
            return
        def trocar():
            codigo, _ = executar("hostnamectl", "set-hostname", nome)
            return "Nome do computador alterado." if codigo == 0 else "Não foi possível alterar o nome do computador."
        self._em_fundo("aviso", trocar)
        self._sobre = {**self._sobre, "computador": nome}
        self.mudou.emit()


    # ------------------------------------------------- fundos importados
    @Slot(str, str)
    def importarFundo(self, url, destino):
        """Copia uma imagem ou vídeo escolhido para a pasta do DuiaOS e usa como papel de parede ou descanso."""
        origem = Path(url[7:] if url.startswith("file://") else url)
        from urllib.parse import unquote
        origem = Path(unquote(str(origem)))
        if origem.suffix.lower() not in EXTENSOES_FUNDO or not origem.is_file():
            self.aviso.emit("Escolha uma imagem (JPG, PNG, WebP, GIF) ou um vídeo (MP4, WebM, MKV, MOV).")
            return
        PASTA_FUNDOS.mkdir(parents=True, exist_ok=True)
        import operacoes_fundo
        alvo = operacoes_fundo.copiar_sem_sobrescrever(origem, PASTA_FUNDOS)
        if destino == "descanso":
            self.definirDescanso(str(alvo))
        else:
            self.definirPapel(str(alvo))
        self.mudou.emit()

    def _importados(self):
        try:
            return [str(p) for p in sorted(PASTA_FUNDOS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                    if p.suffix.lower() in EXTENSOES_FUNDO]
        except OSError:
            return []

    fundosImportados = Property("QVariantList", _importados, notify=mudou)

    # ---------------------------------------------------- tela de descanso
    @Slot(str)
    def definirDescanso(self, arquivo):
        pastas.gravar_preferencia("descanso", "arquivo", arquivo[7:] if arquivo.startswith("file://") else arquivo)
        self.mudou.emit()

    @Slot(int)
    def definirMinutosDescanso(self, minutos):
        pastas.gravar_preferencia("descanso", "minutos", str(max(0, int(minutos))))
        self.mudou.emit()
        if not DEMONSTRACAO:
            self._em_fundo("x", sessao.aplicar_bloqueio)

    @Slot(bool)
    def definirRelogioDescanso(self, ligar):
        pastas.gravar_preferencia("descanso", "relogio", "sim" if ligar else "nao")
        self.mudou.emit()

    @Slot()
    def testarDescanso(self):
        if not DEMONSTRACAO:
            aplicativos.iniciar([sys.executable, str(comum.PASTA_SHELL / "descanso" / "main.py")])

    descansoArquivo = Property(str, lambda self: pastas.ler_preferencia("descanso", "arquivo", ""), notify=mudou)
    descansoMinutos = Property(int, lambda self: int(pastas.ler_preferencia("descanso", "minutos", "0") or 0), notify=mudou)
    descansoRelogio = Property(bool, lambda self: pastas.ler_preferencia("descanso", "relogio", "sim") == "sim", notify=mudou)

    # -------------------------------------------------------- notificações
    @Slot(bool)
    def definirNaoPerturbe(self, ligar):
        pastas.gravar_preferencia("notificacoes", "nao_perturbe", "sim" if ligar else "nao")
        self.mudou.emit()

    @Slot()
    def testarNotificacao(self):
        if not DEMONSTRACAO:
            aplicativos.iniciar(["notify-send", "-a", "Configurações", "-i", "duiaos-configuracoes",
                                 "Notificações funcionando", "É assim que os avisos aparecem no DuiaOS."])

    naoPerturbe = Property(bool, lambda self: pastas.ler_preferencia("notificacoes", "nao_perturbe", "nao") == "sim", notify=mudou)

    # ---------------------------------------------------------------- foto
    @Slot(str)
    def definirFoto(self, origem):
        """Foto da conta: de um arquivo (url) ou "#RRGGBB" (avatar com a inicial nessa cor)."""
        import operacoes_fundo
        try:
            png = operacoes_fundo.foto_redonda(origem, self.usuario["nome"])
        except ValueError as erro:
            self.aviso.emit(str(erro))
            return
        try:
            (Path.home() / ".face").write_bytes(png)       # padrão de outros programas
        except OSError:
            pass
        if DEMONSTRACAO:
            return
        def gravar():
            try:
                resultado = subprocess.run(["pkexec", AJUDANTE_CONTA, "foto"], input=png, capture_output=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired):
                return "Não foi possível salvar a foto."
            return "Foto da conta alterada." if resultado.returncode == 0 else "Não foi possível salvar a foto."
        self._em_fundo("aviso", gravar)
        QTimer.singleShot(1500, self.mudou.emit)

    fotoConta = Property(str, lambda self: comum.foto(comum.usuario_atual()["usuario"]), notify=mudou)

    # --------------------------------------------------------- atualizações
    def _agente(self, metodo, *argumentos, ao_responder=None, ao_falhar=None, tempo=300000):
        from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusPendingCallWatcher
        mensagem = QDBusMessage.createMethodCall(AGENTE[0], AGENTE[1], AGENTE[0], metodo)
        mensagem.setArguments(list(argumentos))
        vigia = QDBusPendingCallWatcher(QDBusConnection.systemBus().asyncCall(mensagem, tempo), self)
        self._vigias = getattr(self, "_vigias", []) + [vigia]

        def terminou(v):
            self._vigias.remove(v)
            if v.isError() and ao_falhar:
                ao_falhar(v.error().message() if "ServiceUnknown" not in v.error().name()
                          else "O agente do sistema não respondeu.")
            elif v.isError():
                if v.error().name().endswith(".Ocupado"):
                    # Já há uma atualização rodando (de outra janela ou do Wise): acompanha ela, sem começar outra
                    self.acompanharAgente()
                elif metodo == "Configurar":
                    self.aviso.emit(v.error().message())       # ex.: só administrador muda
                elif metodo in ("EspacoDoSistema", "LimparSistema"):
                    if metodo == "LimparSistema":
                        self.aviso.emit(v.error().message())
                    self._mudar_armaz(carregando=False, trabalho={})
                    return v.deleteLater()
                elif metodo in ("Registros", "LerRegistro", "Estado"):
                    self._registro_aberto = {"titulo": "Registro", "texto": v.error().message()} if metodo == "LerRegistro" else getattr(self, "_registro_aberto", {})
                else:
                    self._atualizacao = {**self._atualizacao, "etapa": "erro", "mensagem": v.error().message()}
                self.atualizacaoMudou.emit()
            elif ao_responder:
                ao_responder(v.reply().arguments())
            v.deleteLater()
        vigia.finished.connect(terminou)

    def _ligar_agente(self):
        if getattr(self, "_agente_ligado", False) or DEMONSTRACAO:
            return
        from PySide6.QtDBus import QDBusConnection
        self._agente_ligado = QDBusConnection.systemBus().connect(AGENTE[0], AGENTE[1], AGENTE[0], "Mudou",
                                                                  self, "1aoMudarAgente(QString)")

    @Slot(str)
    def aoMudarAgente(self, texto):
        import json
        try:
            estado = json.loads(texto)
        except ValueError:
            return
        self._aplicar_estado(estado)

    def _aplicar_estado(self, estado, ao_abrir=False):
        """Estado do duiaos-agente → tela: andamento (com início, previsão, etapa e alerta) ou o resultado."""
        import time as _tempo
        tarefa, ultima = estado.get("tarefa"), estado.get("ultima")
        if not tarefa and self._atualizacao.get("etapa") == "atualizando" and not ao_abrir:
            # O agente não tem mais a tarefa e não disse como acabou: não deixa a tela parada
            if not ultima or ultima.get("id") != self._atualizacao.get("id", ultima.get("id")):
                self._sem_tarefa = getattr(self, "_sem_tarefa", 0) + 1
                if self._sem_tarefa >= 3 and not ultima:
                    self._atualizacao = {"etapa": "erro", "fracao": 1.0, "registro": self._atualizacao.get("registro", ""),
                                         "mensagem": "O serviço de atualização parou sem dizer como terminou. "
                                                     "Procure de novo: o DuiaOS conclui o que tiver ficado pela metade."}
                    self.atualizacaoMudou.emit()
                    return
        if tarefa:
            self._sem_tarefa = 0
        if tarefa and tarefa.get("acao") == "atualizar_sistema":
            self._atualizacao = {**self._atualizacao, "etapa": "atualizando", "fracao": tarefa.get("fracao", 0.0),
                                 "mensagem": tarefa.get("mensagem", ""), "etapaAtual": tarefa.get("etapa", ""),
                                 "alerta": tarefa.get("alerta", ""), "inicio": tarefa.get("inicio", 0),
                                 "estimativa": tarefa.get("estimativa_s", 0), "registro": tarefa.get("registro", ""),
                                 "estadoAgente": tarefa.get("estado", "")}
        elif ultima and ultima.get("acao") == "atualizar_sistema" and (
                self._atualizacao.get("etapa") == "atualizando"
                or (ao_abrir and _tempo.time() - ultima.get("quando", 0) < 3600 and self._atualizacao.get("etapa") == "inicio")):
            resultado = ultima.get("resultado")
            etapa = {"ok": "concluida", "cancelada": "inicio"}.get(resultado, "erro")
            self._atualizacao = {"etapa": etapa, "mensagem": ultima.get("mensagem", ""), "fracao": 1.0,
                                 "registro": ultima.get("registro", ""), "duracao": ultima.get("duracao_s", 0),
                                 "resultado": resultado}
        self.atualizacaoMudou.emit()

    def _conferir_agente(self):
        """Enquanto atualiza, pergunta o estado a cada 10 s (caso um sinal se perca ou o agente reinicie)."""
        if self._atualizacao.get("etapa") != "atualizando" or DEMONSTRACAO:
            return
        import json
        self._agente("Estado", ao_responder=lambda a: self._aplicar_estado(json.loads(a[0])), tempo=20000)

    @Slot()
    def acompanharAgente(self):
        """Ao abrir a página: mostra a atualização que estiver rodando (ou a última, se recente)."""
        if DEMONSTRACAO:
            return
        self._ligar_agente()
        import json
        self._agente("Estado", ao_responder=lambda a: self._aplicar_estado(json.loads(a[0]), ao_abrir=True), tempo=20000)

    @Slot()
    def listarRegistros(self):
        import json
        if DEMONSTRACAO:
            self._registros = [{"nome": "20261114-184900-0123456789abcdef.log", "quando": 1763156940, "acao": "atualizar_sistema",
                                "resultado": "erro", "duracao_s": 1820,
                                "mensagem": "A etapa “Preparando a inicialização do sistema (initramfs)” ficou parada por 30 minutos e foi interrompida."},
                               {"nome": "20261114-151200-fedcba9876543210.log", "quando": 1763143920, "acao": "atualizar_sistema",
                                "resultado": "ok", "duracao_s": 214, "mensagem": "Sistema atualizado."}]
            self.atualizacaoMudou.emit()
            return
        def recebeu(argumentos):
            self._registros = json.loads(argumentos[0])
            self.atualizacaoMudou.emit()
        self._agente("Registros", ao_responder=recebeu, tempo=20000)

    @Slot(str)
    def abrirRegistro(self, nome):
        self._registro_aberto = {"titulo": "Registro " + nome.removesuffix(".log"), "nome": nome, "texto": "Carregando…"}
        self.atualizacaoMudou.emit()
        if DEMONSTRACAO:
            self._registro_aberto["texto"] = ("18:49:00 DuiaOS — atualizar_sistema {}\n18:49:31 [andamento 62%] Installed linux-image-6.12.117+deb13-amd64\n"
                                              "18:54:31 (5 min sem novidade)\n19:19:33 [vigia] 30 min sem saída; interrompendo a etapa: update-initramfs\n")
            self.atualizacaoMudou.emit()
            return
        def recebeu(argumentos):
            if getattr(self, "_registro_aberto", {}).get("nome") == nome:
                self._registro_aberto = {**self._registro_aberto, "texto": argumentos[0]}
                self.atualizacaoMudou.emit()
        self._agente("LerRegistro", nome, ao_responder=recebeu, tempo=20000)

    @Slot()
    def fecharRegistro(self):
        self._registro_aberto = {}
        self.atualizacaoMudou.emit()

    registros = Property("QVariantList", lambda self: getattr(self, "_registros", []), notify=atualizacaoMudou)
    registroAberto = Property("QVariantMap", lambda self: getattr(self, "_registro_aberto", {}) or {}, notify=atualizacaoMudou)

    # ---------------------------------------------- armazenamento (ADR 060)
    armazenamentoMudou = Signal()

    def _armazenamento(self):
        return getattr(self, "_armaz", {"carregando": True, "dispositivos": [], "uso": [], "recomendacoes": [], "trabalho": {},
                                        "lista": {"tipo": "", "titulo": "", "itens": [], "carregando": False}})

    def _mudar_armaz(self, **mudar):
        self._armaz = {**self._armazenamento(), **mudar}
        self.armazenamentoMudou.emit()

    def _trabalhar(self, texto, total=0):
        """Uma limpeza começou: a página mostra o andamento (e trava os outros botões) até terminar."""
        import time as _time
        self._mudar_armaz(trabalho={"texto": texto, "feito": 0, "total": total, "inicio": _time.time()})

    def _progresso(self, feito, total):
        """Chamado da linha de fundo: o sinal leva o andamento para a linha da interface."""
        self._pronto.emit("armazenamento-progresso", {"feito": feito, "total": total})

    @Slot()
    def medirArmazenamento(self):
        """Mede tudo de novo (discos, uso por categoria e o que dá para limpar), em segundo plano."""
        import armazenamento as ar
        self._mudar_armaz(carregando=True)
        if DEMONSTRACAO:
            self._mudar_armaz(**armazenamento_de_exemplo())
            if "--lista" in sys.argv:                       # demonstração de uma lista (ex.: --lista videos)
                self.listarArmazenamento(argumento("--lista", "videos"))
            if "--limpando" in sys.argv:                    # demonstração do andamento de uma limpeza
                self._trabalhar("Movendo para a Lixeira…", 12)
                self._mudar_armaz(trabalho={**self._armazenamento()["trabalho"], "feito": 5})
            return

        def medir():
            discos = ar.dispositivos()
            sistema = next((d for d in discos if d["montado"] == "/"), None)
            usuario = {chave: pastas.pasta(chave) for chave in pastas.PADRAO}
            uso = ar.uso_por_categoria(pastas.INICIO, usuario, pastas.LIXEIRA, os.environ.get("XDG_CACHE_HOME") or pastas.INICIO / ".cache",
                                       disco=sistema)
            return {"dispositivos": discos, "uso": uso, "sistema": sistema or {}}
        self._em_fundo("armazenamento-medir", medir)
        self._em_fundo("armazenamento-recomendacoes", recomendacoes_de_limpeza)
        self._agente("EspacoDoSistema", ao_responder=lambda r: self._ao_armazenamento("armazenamento-sistema", r[0]))

    def _ao_armazenamento(self, nome, resultado):
        import json as _json
        if isinstance(resultado, Exception):
            self.aviso.emit(("Não consegui terminar a limpeza: " if nome == "armazenamento-feito" else
                             "Não consegui medir o armazenamento: ") + str(resultado)[:120])
            self._mudar_armaz(carregando=False, trabalho={})
            return
        if nome == "armazenamento-progresso":
            if self._armazenamento().get("trabalho"):
                self._mudar_armaz(trabalho={**self._armazenamento()["trabalho"], **resultado})
            return
        if nome == "armazenamento-medir":
            self._mudar_armaz(carregando=False, **resultado)
        elif nome == "armazenamento-recomendacoes":
            atual = [r for r in self._armazenamento()["recomendacoes"] if r.get("id") in ("apt", "registros")]
            self._mudar_armaz(recomendacoes=sorted(resultado + atual, key=lambda r: -r.get("tamanho", 0)))
        elif nome == "armazenamento-sistema":
            dados = _json.loads(resultado)
            extras = [{"id": "apt", "titulo": "Pacotes de instalação já usados", "tamanho": dados.get("apt", 0), "acao": "Limpar",
                       "texto": "Cópias dos pacotes que o sistema já instalou. Podem ser apagadas: baixam de novo se precisar."},
                      {"id": "registros", "titulo": "Registros antigos do sistema", "tamanho": dados.get("registros", 0), "acao": "Limpar",
                       "texto": "Histórico técnico do sistema. Os registros mais recentes ficam."}]
            atual = [r for r in self._armazenamento()["recomendacoes"] if r.get("id") not in ("apt", "registros")]
            self._mudar_armaz(recomendacoes=sorted(atual + [e for e in extras if e["tamanho"] > 1024 * 1024],
                                                   key=lambda r: -r.get("tamanho", 0)))
        elif nome == "armazenamento-lista":
            self._mudar_armaz(lista={**self._armazenamento()["lista"], **resultado, "carregando": False})
        elif nome == "armazenamento-feito":
            if isinstance(resultado, dict) and resultado.get("protegidos"):
                self._mover_protegidos(resultado.get("texto", ""), resultado["protegidos"], resultado.get("explicacao", ""))
                return
            self._mudar_armaz(trabalho={})
            if resultado:
                self.aviso.emit(resultado)
            self.medirArmazenamento()

    @Slot(str)
    def listarArmazenamento(self, tipo):
        """Uma lista para escolher o que apagar: um tipo de arquivo (videos, imagens…), "grandes", "antigos"
        (Downloads), "duplicados", "caches" ou "programas"."""
        import armazenamento as ar
        if not tipo:                                        # "Voltar": fecha a lista
            self._mudar_armaz(lista={"tipo": "", "titulo": "", "itens": [], "carregando": False})
            return
        titulos = {"grandes": "Arquivos grandes", "antigos": "Downloads com mais de 90 dias", "duplicados": "Arquivos repetidos",
                   "caches": "Arquivos temporários dos aplicativos", "programas": "Aplicativos instalados",
                   **{k: v[0] for k, v in ar.CATEGORIAS.items()}}
        self._mudar_armaz(lista={"tipo": tipo, "titulo": titulos.get(tipo, tipo), "itens": [], "carregando": True})
        if DEMONSTRACAO:
            self._mudar_armaz(lista={"tipo": tipo, "titulo": titulos.get(tipo, tipo), "itens": lista_de_exemplo(tipo), "carregando": False})
            return

        def listar():
            ocultas = [pastas.INICIO / ".cache", pastas.LIXEIRA]
            if tipo == "antigos":
                itens = ar.antigos(pastas.pasta("DOWNLOAD"))
            elif tipo == "duplicados":
                itens = []
                for grupo in ar.duplicados(pastas.INICIO, pular=ocultas)[:80]:
                    for extra in grupo["arquivos"][1:]:          # o primeiro fica: os outros são as cópias
                        itens.append({"caminho": extra, "nome": os.path.basename(extra), "tamanho": grupo["tamanho"],
                                      "pasta": os.path.dirname(extra), "detalhe": "Igual a " + grupo["arquivos"][0]})
            elif tipo == "caches":
                itens = [{**c, "pasta": c["caminho"]} for c in ar.caches()]
            elif tipo == "programas":
                itens = [{**p, "caminho": p["id_loja"], "pasta": "Flathub" if p["fonte"] == "flathub" else "Debian"}
                         for p in ar.programas_por_tamanho()]
            else:
                itens = ar.maiores_por_categoria(pastas.INICIO, tipo, pular=ocultas)
            return {"tipo": tipo, "itens": itens}
        self._em_fundo("armazenamento-lista", listar)

    @Slot(str, "QVariantList")
    def apagarDoArmazenamento(self, tipo, caminhos):
        """Apaga o que a pessoa marcou: arquivos vão para a Lixeira; caches são apagados de vez."""
        import armazenamento as ar
        caminhos = [str(c) for c in caminhos]
        if DEMONSTRACAO or not caminhos:
            return
        from tipos import tamanho_legivel

        total = len(caminhos)
        self._trabalhar("Apagando os arquivos temporários…" if tipo == "caches" else "Movendo para a Lixeira…", total)

        def apagar():
            if tipo == "caches":
                liberado = 0
                for n, caminho in enumerate(caminhos, 1):
                    liberado += ar.apagar_caches([caminho])
                    self._progresso(n, total)
                return "Liberados " + tamanho_legivel(liberado) + "."
            op = ar.operacoes_do_explorador()
            tamanho = sum(os.path.getsize(c) for c in caminhos if os.path.isfile(c))
            protegidos, explicacao = [], ""
            for n, caminho in enumerate(caminhos, 1):
                try:
                    op.mover_para_lixeira([caminho])
                except op.SemPermissao as erro:
                    # A pasta é de outro usuário (ex.: root): o agente move, com autorização (ADR 068)
                    protegidos += erro.caminhos
                    explicacao = explicacao or str(erro)
                self._progresso(n, total)
            movidos = len(caminhos) - len(protegidos)
            texto = (f"{movidos} {'item foi' if movidos == 1 else 'itens foram'} para a Lixeira ({tamanho_legivel(tamanho)}). "
                     "Esvazie a Lixeira para liberar o espaço.") if movidos else ""
            if protegidos:
                return {"texto": texto, "protegidos": protegidos, "explicacao": explicacao}
            return texto
        self._em_fundo("armazenamento-feito", apagar)

    def _mover_protegidos(self, texto, protegidos, explicacao):
        """Itens em pastas de outro usuário: o duiaos-agente os move para a Lixeira desta pessoa, com a
        autorização de administrador (polkit), como o Finder do macOS faz (ADR 068)."""
        import json as _json
        self._trabalhar("Movendo para a Lixeira os arquivos de pastas do sistema…")

        def respondeu(resposta):
            resultado = _json.loads(resposta[0])
            movidos, recusados = resultado.get("movidos", []), resultado.get("recusados", [])
            partes = [t for t in (texto,) if t]
            if movidos:
                partes.append(f"{len(movidos)} {'item' if len(movidos) == 1 else 'itens'} de pastas do sistema "
                              f"{'foi' if len(movidos) == 1 else 'foram'} para a Lixeira.")
            if recusados:
                partes.append(recusados[0]["motivo"])
            self._ao_armazenamento("armazenamento-feito", " ".join(partes))

        def falhou(mensagem):
            self._ao_armazenamento("armazenamento-feito", " ".join(t for t in (texto, explicacao, mensagem) if t))
        self._agente("MoverParaLixeira", _json.dumps(protegidos), ao_responder=respondeu, ao_falhar=falhou)

    @Slot(str)
    def limparRecomendacao(self, ident):
        """Botão de uma recomendação de limpeza."""
        import armazenamento as ar
        from tipos import tamanho_legivel
        if DEMONSTRACAO:
            self.aviso.emit("Demonstração: nada foi apagado.")
            return
        textos = {"lixeira": "Esvaziando a Lixeira…", "flatpak": "Removendo o que o Flathub não usa mais…",
                  "apt": "Apagando os pacotes de instalação já usados…", "registros": "Apagando os registros antigos do sistema…"}
        if ident in textos:
            self._trabalhar(textos[ident])
        if ident == "lixeira":
            def esvaziar():
                # Item por item, para a página mostrar o andamento (uma Lixeira grande leva tempo)
                op = ar.operacoes_do_explorador()
                arquivos, infos = op._pastas_lixeira(None)
                itens = []
                for pasta in (arquivos, infos):
                    try:
                        itens += [pasta / n for n in os.listdir(pasta)]
                    except OSError:
                        pass
                for n, item in enumerate(itens, 1):
                    op.excluir_permanentemente([item])
                    if n % 5 == 0 or n == len(itens):
                        self._progresso(n, len(itens))
                return "A Lixeira foi esvaziada."
            self._em_fundo("armazenamento-feito", esvaziar)
        elif ident == "flatpak":
            self._em_fundo("armazenamento-feito", lambda: "Liberados " + tamanho_legivel(ar.remover_flatpak_sem_uso()) + ".")
        elif ident in ("apt", "registros"):
            import json as _json
            self._agente("LimparSistema", _json.dumps({ident: True}),
                         ao_responder=lambda r: self._ao_armazenamento(
                             "armazenamento-feito", "Liberados " + tamanho_legivel(_json.loads(r[0]).get("liberado", 0)) + "."))
        elif ident in ("caches", "antigos", "grandes", "duplicados"):
            self.listarArmazenamento(ident)

    @Slot(str)
    def abrirNaLoja(self, id_loja):
        if not DEMONSTRACAO:
            comum.abrir_app_duiaos("loja", "--pagina", "app:" + id_loja)

    @Slot(str)
    def mostrarNoExplorador(self, caminho):
        if not DEMONSTRACAO:
            comum.abrir_app_duiaos("explorador-de-arquivos", caminho)

    armazenamento = Property("QVariantMap", _armazenamento, notify=armazenamentoMudou)

    # ---------------------------------------------- atualização automática (ADR 058)
    def _modo_automatico(self):
        import atualizacao_automatica as aa
        return getattr(self, "_modo_automatico_demo", aa.MODO_PADRAO) if DEMONSTRACAO else aa.ler_modo()

    @Slot(str)
    def definirAtualizacaoAutomatica(self, modo):
        """Vale para o computador todo: grava pelo duiaos-agente (administrador, pelo polkit)."""
        import atualizacao_automatica as aa
        if modo not in aa.MODOS:
            return
        if DEMONSTRACAO:
            self._modo_automatico_demo = modo
            self.atualizacaoMudou.emit()
            return
        import json
        self._agente("Configurar", json.dumps({"modo": modo}), ao_responder=lambda _r: self.atualizacaoMudou.emit())
        QTimer.singleShot(1500, self.atualizacaoMudou.emit)

    atualizacaoAutomatica = Property(str, _modo_automatico, notify=atualizacaoMudou)
    explicacaoAtualizacaoAutomatica = Property(str, lambda self: __import__("atualizacao_automatica").EXPLICACOES[self._modo_automatico()],
                                               notify=atualizacaoMudou)

    @Slot()
    def procurarAtualizacoes(self):
        self._atualizacao = {"etapa": "procurando", "mensagem": "Procurando atualizações…"}
        self.atualizacaoMudou.emit()
        self._procurar_flathub()
        if DEMONSTRACAO:
            catalogo = _catalogo_do_repositorio()["atualizacoes"]
            self._atualizacao = {
                "etapa": "pronta", "plano": "demo", "quantidade": 7, "estimativa": 290, "baixar": "148,2 MB", "reiniciar": "computador",
                "reiniciarNome": "Reinicie o computador",
                "duiaos": catalogo[:3],
                "debian": [{"pacote": "firefox-esr", "de": "128.5.0esr-1~deb13u1", "para": "128.6.0esr-1~deb13u1", "seguranca": True,
                            "descricao": "Navegador web Mozilla Firefox (versão de suporte estendido)", "origem": "Debian-Security:13/stable-security"},
                           {"pacote": "libc6", "de": "2.41-11", "para": "2.41-12", "seguranca": False,
                            "descricao": "Biblioteca C do GNU: bibliotecas compartilhadas", "origem": "Debian:13.2/stable"},
                           {"pacote": "tzdata", "de": "2025b-4", "para": "2025c-0+deb13u1", "seguranca": False,
                            "descricao": "Dados de fuso horário", "origem": "Debian:13.2/stable-updates"}],
                "quantidadeSeguranca": 1, "duiaosSemFicha": []}
            self.atualizacaoMudou.emit()
            return
        self._ligar_agente()

        def respondeu(argumentos):
            import json
            plano = json.loads(argumentos[0])
            if plano.get("recusa"):
                self._atualizacao = {"etapa": "erro", "mensagem": plano["recusa"]["mensagem"]}
                self.atualizacaoMudou.emit()
                return
            self._atualizacao = {"etapa": "procurando", "mensagem": "Lendo o que cada atualização traz…"}
            self.atualizacaoMudou.emit()
            self._em_fundo("detalhes", detalhar_plano, plano)
        self._agente("Preparar", "atualizar_sistema", '{"forcar": true}', ao_responder=respondeu)

    def _procurar_flathub(self):
        """Aplicativos do Flathub com versão nova: atualizam pela Duia App Store (ADR 049)."""
        if DEMONSTRACAO:
            self._flathub = 2
            return
        if not shutil.which("flatpak"):
            return

        def contar():
            saida = subprocess.run(["flatpak", "remote-ls", "--updates", "--app", "--columns=application"],
                                   capture_output=True, text=True, timeout=120, check=False).stdout
            return len({linha.strip() for linha in saida.splitlines() if "." in linha})
        self._em_fundo("flathub", contar)

    @Slot()
    def abrirLojaAtualizacoes(self):
        comum.abrir_app_duiaos("loja", "--pagina", "atualizacoes")

    atualizacoesFlathub = Property(int, lambda self: getattr(self, "_flathub", 0), notify=atualizacaoMudou)

    @Slot()
    def atualizarAgora(self):
        plano = self._atualizacao.get("plano")
        if not plano or self._atualizacao.get("etapa") == "atualizando":
            return                                     # um clique só: o mesmo plano não é enviado duas vezes
        import time as _tempo
        self._atualizacao = {**self._atualizacao, "etapa": "atualizando", "fracao": 0.0, "mensagem": "Começando",
                             "inicio": int(_tempo.time()), "estimativa": self._atualizacao.get("estimativa", 0),
                             "etapaAtual": "Conferindo o que vai mudar", "alerta": "", "plano": ""}
        self.atualizacaoMudou.emit()
        if not DEMONSTRACAO:
            self._agente("Executar", plano)

    @Slot()
    def cancelarAtualizacao(self):
        if not DEMONSTRACAO:
            self._agente("Cancelar")

    @Slot(str)
    def verMudancas(self, pacote):
        """Registro de mudanças (changelog) de um pacote do Debian."""
        import atualizacoes_sistema as at
        self._registro = {"pacote": pacote, "texto": "Baixando o registro de mudanças…"}
        self.atualizacaoMudou.emit()
        if DEMONSTRACAO:
            self._registro = {"pacote": pacote, "texto": pacote + " (nova versão) stable-security; urgency=medium\n\n  * Corrige falhas de segurança.\n"}
            self.atualizacaoMudou.emit()
            return
        self._em_fundo("registro", lambda: {"pacote": pacote, "texto": at.registro_de_mudancas(pacote)})

    @Slot()
    def fecharMudancas(self):
        self._registro = {}
        self.atualizacaoMudou.emit()

    def _historico(self):
        import atualizacoes_sistema as at
        if DEMONSTRACAO:
            return _catalogo_do_repositorio()["atualizacoes"]
        return at.ler_catalogo_instalado()

    atualizacao = Property("QVariantMap", lambda self: getattr(self, "_atualizacao", {"etapa": "inicio"}), notify=atualizacaoMudou)
    registroDeMudancas = Property("QVariantMap", lambda self: getattr(self, "_registro", {}) or {}, notify=atualizacaoMudou)
    historicoAtualizacoes = Property("QVariantList", _historico, notify=atualizacaoMudou)

    secao = Property(str, lambda self: self._secao, notify=secaoMudou)
    sobre = Property("QVariantMap", lambda self: self._sobre, notify=mudou)
    telas = Property("QVariantList", lambda self: self._telas, notify=mudou)
    wise = Property(bool, lambda self: comum.wise_instalado() or DEMONSTRACAO, constant=True)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)


def tamanho_imagem(arquivo):
    """'1920 × 1080' (lido do cabeçalho, sem abrir a imagem inteira) ou ''."""
    if not arquivo or not Path(arquivo).is_file():
        return ""
    from PySide6.QtGui import QImageReader
    tamanho = QImageReader(arquivo).size()
    return f"{tamanho.width()} × {tamanho.height()}" if tamanho.isValid() else ""


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    secao = argumento("--secao", "wifi")
    captura = argumento("--captura")
    if not DEMONSTRACAO:
        # Uma janela só: com ela aberta, só pede a seção e sai
        trava = open(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-configuracoes.lock", "w")
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            ARQUIVO_PEDIDO.write_text(secao)
            sys.exit(0)
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Configurações")
    app.setDesktopFileName("duiaos-configuracoes")
    interface.ligar_registro("duiaos-configuracoes")

    ajustes = Ajustes(secao)
    if DEMONSTRACAO and "--papel" in sys.argv:          # demonstração da página do papel de parede
        ajustes._alvo_papel = argumento("--papel", "area")
    estado = controles.Controles(demonstracao=DEMONSTRACAO)
    ajustes._controles = estado
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    contexto = engine.rootContext()
    contexto.setContextProperty("ajustes", ajustes)
    # Menus na Barra de Recursos (menu_do_app.py, ADR 059)
    import menu_do_app
    menu = menu_do_app.criar("configuracoes", [])          # guardado numa variável: sem isso o Python o descarta
    contexto.setContextProperty("menuDoApp", menu)
    contexto.setContextProperty("controles", estado)
    # Inteligência Artificial e Wise (ADR 063)
    from ia import InteligenciaArtificial
    ia = InteligenciaArtificial(DEMONSTRACAO)
    ia.aviso.connect(ajustes.aviso)
    contexto.setContextProperty("ia", ia)
    contexto.setContextProperty("capturaArquivo", captura)
    contexto.setContextProperty("caminhoComum", str(comum.PASTA_SHELL / "comum"))
    engine.load(PASTA / "Configuracoes.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
