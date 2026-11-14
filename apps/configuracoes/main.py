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
          "usuario", "data", "teclado", "padroes", "atualizacoes", "privacidade", "ia", "sobre")
PASTA_FUNDOS = pastas.DADOS / "duiaos" / "fundos"          # imagens e vídeos importados
EXTENSOES_FUNDO = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mkv", ".mov", ".m4v")
AGENTE = ("org.duiaos.Agente1", "/org/duiaos/Agente1")
AJUDANTE_CONTA = "/usr/lib/duiaos/conta"
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
        if isinstance(resultado, Exception):
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
        janela = QGuiApplication.topLevelWindows()
        if janela:
            janela[0].requestActivate()

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

    # ---------------------------------------------------- papel de parede
    @Slot(str)
    def definirPapel(self, arquivo):
        if arquivo.startswith("file://"):
            arquivo = arquivo[7:]
        if arquivo.startswith("#"):
            pastas.gravar_preferencia("papel-de-parede", "cor", arquivo)
            pastas.gravar_preferencia("papel-de-parede", "arquivo", "")
        else:
            pastas.gravar_preferencia("papel-de-parede", "arquivo", arquivo)
        self.mudou.emit()          # a Área de Trabalho vê a preferência mudar e troca o fundo na hora

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
    def _agente(self, metodo, *argumentos, ao_responder=None, tempo=300000):
        from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusPendingCallWatcher
        mensagem = QDBusMessage.createMethodCall(AGENTE[0], AGENTE[1], AGENTE[0], metodo)
        mensagem.setArguments(list(argumentos))
        vigia = QDBusPendingCallWatcher(QDBusConnection.systemBus().asyncCall(mensagem, tempo), self)
        self._vigias = getattr(self, "_vigias", []) + [vigia]

        def terminou(v):
            self._vigias.remove(v)
            if v.isError():
                if v.error().name().endswith(".Ocupado"):
                    # Já há uma atualização rodando (de outra janela ou do Wise): acompanha ela, sem começar outra
                    self.acompanharAgente()
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
        self._agente("Preparar", "atualizar_sistema", "{}", ao_responder=respondeu)

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
    estado = controles.Controles(demonstracao=DEMONSTRACAO)
    ajustes._controles = estado
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    contexto = engine.rootContext()
    contexto.setContextProperty("ajustes", ajustes)
    contexto.setContextProperty("controles", estado)
    contexto.setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / "Configuracoes.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
