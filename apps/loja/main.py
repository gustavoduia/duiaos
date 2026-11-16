#!/usr/bin/env python3
"""DuiaOS — Duia App Store (ADR 049).

A loja de aplicativos do DuiaOS: Descobrir (destaques e coleções), categorias,
busca, página de cada aplicativo (capturas de tela, descrição, licença e de onde
vem), Instalados e Atualizações.

Fontes (catalogo.py): os aplicativos do Debian (AppStream/DEP-11 que o apt baixa)
e os do Flathub (AppStream do flatpak). Instalar e remover:
  Debian   pelo duiaos-agente (Preparar mostra o que muda; Executar com o polkit)
  Flathub  pelo flatpak, na conta da pessoa (--user), sem senha

Uso:
  main.py [--pagina descobrir|instalados|atualizacoes|categoria:ID|busca:TEXTO|app:ID]
  main.py --demonstracao [--pagina ...] [--confirmar ID] [--captura ARQUIVO]
"""
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
for _comum in (Path(os.environ.get("DUIAOS_SHELL", "/usr/share/duiaos/shell")) / "comum",
               PASTA.parents[1] / "shell" / "comum"):
    if (_comum / "interface.py").is_file():
        sys.path.insert(0, str(_comum))
        break
sys.path.insert(0, str(PASTA))

import aplicativos  # noqa: E402
import catalogo  # noqa: E402
import interface  # noqa: E402
import sistema  # noqa: E402

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

DEMONSTRACAO = "--demonstracao" in sys.argv
AGENTE = ("org.duiaos.Agente1", "/org/duiaos/Agente1")
ARQUIVO_PEDIDO = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-loja.pedido"
MENSAGENS = {"loja_catalogo": "Catálogo da loja carregado", "loja_pedido": "Pedido na loja",
             "loja_flatpak_ok": "Flatpak concluído", "loja_flatpak_erro": "Flatpak terminou com erro",
             "loja_falha_em_fundo": "Falha numa tarefa da loja", "loja_abrir": "Aplicativo aberto pela loja"}


def registrar(nivel, evento, **dados):
    """Eventos no registro do sistema (duiaos_registro), quando existir."""
    try:
        import duiaos_registro
    except ImportError:
        return
    getattr(duiaos_registro, nivel)(evento, MENSAGENS.get(evento, evento), **dados)


def demonstracao_catalogo():
    """Catálogo de mentira para testes e capturas de tela (sem internet nem apt)."""
    def app(fonte, componente, pacote, nome, resumo, categorias, licenca="GPL-3.0-or-later", desenvolvedor="",
            verificado=False):
        dados = catalogo.montar(fonte, componente, pacote, nome, resumo,
                                f"{nome} é um aplicativo de exemplo da demonstração da Duia App Store.\n\n"
                                "• Funciona com o modo escuro\n• Recebe atualizações pela loja",
                                desenvolvedor or nome, licenca, categorias, "", [], "https://exemplo.invalid",
                                "1.0", verificado)
        return dados
    return [
        app("flathub", "org.libreoffice.LibreOffice", "org.libreoffice.LibreOffice", "LibreOffice",
            "Textos, planilhas e apresentações", ["Office"], "MPL-2.0", "The Document Foundation", True),
        app("flathub", "org.gimp.GIMP", "org.gimp.GIMP", "GIMP", "Editor de imagens", ["Graphics"], "GPL-3.0-or-later",
            "The GIMP team", True),
        app("flathub", "com.obsproject.Studio", "com.obsproject.Studio", "OBS Studio", "Grave e transmita ao vivo",
            ["AudioVideo"], "GPL-2.0-or-later", "OBS Project", True),
        app("flathub", "org.blender.Blender", "org.blender.Blender", "Blender", "Modelagem e animação 3D",
            ["Graphics"], "GPL-2.0-or-later", "Blender Foundation", True),
        app("flathub", "com.spotify.Client", "com.spotify.Client", "Spotify", "Música e podcasts",
            ["AudioVideo"], "LicenseRef-proprietary", "Spotify"),
        app("flathub", "org.telegram.desktop", "org.telegram.desktop", "Telegram", "Mensagens rápidas e seguras",
            ["Network"], "GPL-3.0-only", "Telegram FZ-LLC", True),
        app("flathub", "com.visualstudio.code", "com.visualstudio.code", "Visual Studio Code", "Editor de código",
            ["Development"], "LicenseRef-proprietary", "Microsoft"),
        app("flathub", "com.valvesoftware.Steam", "com.valvesoftware.Steam", "Steam", "Loja e biblioteca de jogos",
            ["Game"], "LicenseRef-proprietary", "Valve"),
        app("flathub", "org.inkscape.Inkscape", "org.inkscape.Inkscape", "Inkscape", "Desenho vetorial",
            ["Graphics"], "GPL-3.0-or-later", "Inkscape Project", True),
        app("flathub", "org.kde.kdenlive", "org.kde.kdenlive", "Kdenlive", "Editor de vídeo", ["AudioVideo"],
            "GPL-3.0-or-later", "KDE", True),
        app("flathub", "org.geogebra.GeoGebra", "org.geogebra.GeoGebra", "GeoGebra", "Matemática dinâmica",
            ["Education", "Science"], "LicenseRef-proprietary", "GeoGebra"),
        app("debian", "org.videolan.vlc", "vlc", "VLC", "Toca qualquer vídeo e música", ["AudioVideo"],
            "GPL-2.0-or-later", "VideoLAN"),
        app("debian", "org.mozilla.firefox", "firefox-esr", "Firefox ESR", "Navegador da Mozilla", ["Network"],
            "MPL-2.0", "Mozilla"),
        app("debian", "org.gnome.Mines", "gnome-mines", "Campo Minado", "Ache as minas sem explodir", ["Game"],
            "GPL-3.0-or-later", "GNOME"),
        app("debian", "org.stellarium.Stellarium", "stellarium", "Stellarium", "Planetário no computador",
            ["Education", "Science"], "GPL-2.0-or-later", "Stellarium"),
        app("debian", "geany.desktop", "geany", "Geany", "Editor de código leve", ["Development"]),
    ]


def sistema_tamanho(bytes_):
    import tipos
    return tipos.tamanho_legivel(bytes_)


class Loja(QObject):
    mudou = Signal()
    catalogoMudou = Signal()
    situacaoMudou = Signal()
    listaMudou = Signal()
    aviso = Signal(str)
    _pronto = Signal(str, object)
    _andamento = Signal(str, float, str)

    def __init__(self, pagina):
        super().__init__()
        self._apps, self._por_id, self._carregando, self._erro_flathub = [], {}, True, ""
        self._historico, self._pagina, self._app, self._busca = [], "descobrir", {}, ""
        self._instalados_debian, self._instalados_flathub, self._atualizaveis = {}, {}, []
        self._tarefas, self._confirmacao, self._processo = {}, {}, None
        self._vitrine = {"destaques": [], "colecoes": []}
        self._lista_atual, self._ids_lista = [], None
        self._pronto.connect(self._ao_pronto)
        self._andamento.connect(self._ao_andamento)
        for sinal in (self.mudou, self.catalogoMudou, self.situacaoMudou):
            sinal.connect(self._refazer_lista)
        self._pagina_inicial = pagina
        if DEMONSTRACAO:
            self._ao_pronto("catalogo", {"debian": [a for a in demonstracao_catalogo() if a["fonte"] == "debian"],
                                         "flathub": [a for a in demonstracao_catalogo() if a["fonte"] == "flathub"],
                                         "erro": ""})
            self._instalados_flathub = {"org.gimp.GIMP": {"versao": "2.10", "instalacao": "user"},
                                        "com.spotify.Client": {"versao": "1.2", "instalacao": "user"}}
            self._instalados_debian = {"vlc": "3.0.21", "firefox-esr": "128.4"}
            self._atualizaveis = ["com.spotify.Client"]
            self._tarefas = {"flathub:org.telegram.desktop": {"acao": "instalar", "fracao": 0.42,
                                                               "mensagem": "Baixando 42%"}}
        else:
            self._em_fundo("catalogo", self._carregar_catalogo)
            self._ligar_agente()
        self.irPara(pagina)
        if DEMONSTRACAO and "--confirmar" in sys.argv:
            self.instalar(argumento("--confirmar"))
        self._vigia_pedido = QTimer(self, interval=700, timeout=self._ler_pedido)
        if not DEMONSTRACAO:
            self._vigia_pedido.start()

    # ------------------------------------------------------------ em fundo
    def _em_fundo(self, nome, funcao, *argumentos):
        def tarefa():
            try:
                resultado = funcao(*argumentos)
            except Exception as erro:              # nunca derrubar a janela
                registrar("erro", "loja_falha_em_fundo", tarefa=nome, erro=str(erro)[:300])
                resultado = {"erro": f"Algo deu errado: {erro}"}
            self._pronto.emit(nome, resultado)
        threading.Thread(target=tarefa, daemon=True).start()

    @staticmethod
    def _carregar_catalogo():
        inicio = time.monotonic()
        debian = catalogo.carregar("debian")
        erro = catalogo.preparar_flathub()
        flathub = catalogo.carregar("flathub")
        registrar("info", "loja_catalogo", debian=len(debian), flathub=len(flathub),
                  segundos=round(time.monotonic() - inicio, 1), erro_flathub=erro)
        return {"debian": debian, "flathub": flathub, "erro": erro,
                "instalados_debian": catalogo.instalados_debian(), "instalados_flathub": catalogo.instalados_flathub()}

    # ------------------------------------------------------------ tamanho (ADR 059)
    def _pedir_tamanho(self, app):
        """O tamanho vem do apt ou do Flathub (pode levar alguns segundos): a página mostra "Calculando…"."""
        instalado = self._situacao_de(app) in ("instalado", "atualizavel")
        chave = (app["id"], instalado)
        if chave in getattr(self, "_tamanhos", {}):
            return
        self._tamanhos = getattr(self, "_tamanhos", {})
        if DEMONSTRACAO:
            self._tamanhos[chave] = ({"instalado": True, "instalar": 268_600_000} if instalado else
                                     {"baixar": 102_500_000, "instalar": 268_600_000, "detalhe": "Com 12 pacotes de que ele precisa"})
            self.mudou.emit()
            return
        self._tamanhos[chave] = None                    # calculando

        def calcular():
            if instalado:
                return {"chave": chave, "valor": {"instalado": True, "instalar": catalogo.tamanho_instalado(app)}}
            return {"chave": chave, "valor": catalogo.tamanho_do_app(app) or {}}
        self._em_fundo("tamanho", calcular)

    def _tamanho_atual(self):
        app = self._app
        if not app.get("id"):
            return {}
        instalado = self._situacao_de(app) in ("instalado", "atualizavel")
        valor = getattr(self, "_tamanhos", {}).get((app["id"], instalado), None)
        if valor is None:
            return {"texto": "Calculando…", "detalhe": "", "baixar": "", "instalar": ""}
        if not valor or (not valor.get("baixar") and not valor.get("instalar")):
            return {"texto": "—", "detalhe": "Não deu para saber agora (sem internet?)", "baixar": "", "instalar": ""}
        baixar = sistema_tamanho(valor.get("baixar", 0)) if valor.get("baixar") else ""
        instalar = sistema_tamanho(valor.get("instalar", 0)) if valor.get("instalar") else ""
        if valor.get("instalado"):
            return {"texto": instalar or "—", "detalhe": "Espaço que ocupa no computador", "baixar": "", "instalar": instalar}
        return {"texto": baixar or instalar, "detalhe": valor.get("detalhe", ""), "baixar": baixar, "instalar": instalar}

    tamanhoApp = Property("QVariantMap", _tamanho_atual, notify=mudou)

    def _ao_pronto(self, nome, resultado):
        if nome == "tamanho":
            if isinstance(resultado, dict) and "chave" in resultado:
                self._tamanhos[resultado["chave"]] = resultado["valor"]
                self.mudou.emit()
            return
        if nome == "catalogo":
            if "debian" not in resultado:
                self._erro_flathub = resultado.get("erro", "")
                self._carregando = False
                self.catalogoMudou.emit()
                return
            self._apps = catalogo.juntar(resultado["debian"], resultado["flathub"])
            self._por_id = {app["id"]: app for app in resultado["debian"] + resultado["flathub"]}
            self._erro_flathub = resultado.get("erro", "")
            self._vitrine = catalogo.vitrine(self._apps, catalogo.ler_destaques(PASTA / "destaques.json"))
            self._instalados_debian = resultado.get("instalados_debian", self._instalados_debian)
            self._instalados_flathub = resultado.get("instalados_flathub", self._instalados_flathub)
            self._carregando = False
            if self._app.get("id"):
                self._app = self._por_id.get(self._app["id"], self._app)
            self.catalogoMudou.emit()
            self.situacaoMudou.emit()
            pendente = getattr(self, "_pendente", "")
            if pendente:
                self._pendente = ""
                self.abrirApp(pendente)
            if not DEMONSTRACAO and catalogo.flatpak_disponivel():
                self._em_fundo("atualizacoes", catalogo.atualizacoes_flathub)
        elif nome == "instalados":
            self._instalados_debian, self._instalados_flathub = resultado
            self.situacaoMudou.emit()
        elif nome == "atualizacoes":
            self._atualizaveis = resultado if isinstance(resultado, list) else []
            self.situacaoMudou.emit()
        elif nome == "flatpak":
            id_app, codigo, mensagem = resultado
            tarefa = self._tarefas.pop(id_app, {})
            app = self._por_id.get(id_app, {})
            if codigo == 0:
                feito = {"instalar": "instalado", "remover": "removido", "atualizar": "atualizado"}.get(tarefa.get("acao"), "pronto")
                self._notificar(f"{app.get('nome', id_app)} foi {feito}.")
                registrar("info", "loja_flatpak_ok", app=id_app, acao=tarefa.get("acao"))
            elif codigo != -signal.SIGTERM:
                self.aviso.emit(f"Não deu para concluir: {mensagem or 'o flatpak parou com erro.'}")
                registrar("aviso", "loja_flatpak_erro", app=id_app, acao=tarefa.get("acao"), erro=mensagem[:300])
            self._processo = None
            self._recarregar_instalados()
            self._proxima_tarefa()

    def _recarregar_instalados(self):
        if DEMONSTRACAO:
            self.situacaoMudou.emit()
            return
        self._em_fundo("instalados", lambda: (catalogo.instalados_debian(), catalogo.instalados_flathub()))
        if catalogo.flatpak_disponivel():
            self._em_fundo("atualizacoes", catalogo.atualizacoes_flathub)

    def _notificar(self, texto):
        self.aviso.emit(texto)
        if shutil.which("notify-send") and not DEMONSTRACAO:
            subprocess.Popen(["notify-send", "-a", "Duia App Store", "-i", "duiaos-loja", "Duia App Store", texto],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ------------------------------------------------------------ navegação
    @Slot(str)
    def irPara(self, pagina):
        if pagina.startswith("app:"):
            self.abrirApp(pagina[4:])
            return
        if pagina.startswith("busca:"):
            self.buscar(pagina[6:])
            return
        if self._pagina != pagina or self._app:
            self._historico.append((self._pagina, self._app, self._busca))
        self._pagina, self._app = pagina, {}
        if pagina == "atualizacoes" and not DEMONSTRACAO:
            self._recarregar_instalados()
        self.mudou.emit()

    @Slot(str)
    def buscar(self, termo):
        self._busca = termo
        if termo.strip():
            if self._pagina != "busca":
                self._historico.append((self._pagina, self._app, ""))
            self._pagina, self._app = "busca", {}
        elif self._pagina == "busca":
            self._pagina = "descobrir"
        self.mudou.emit()

    @Slot(str)
    def abrirApp(self, id_app):
        app = self._por_id.get(id_app) or next((a for a in self._apps if a["componente"] == id_app), None)
        if not app and self._carregando:
            self._pendente = id_app                 # abre quando o catálogo chegar
            return
        if not app:
            self.aviso.emit("Este aplicativo não está no catálogo deste computador.")
            return
        self._historico.append((self._pagina, self._app, self._busca))
        self._pagina, self._app = "app", app
        self.mudou.emit()
        self._pedir_tamanho(app)

    @Slot()
    def voltar(self):
        if self._historico:
            self._pagina, self._app, self._busca = self._historico.pop()
        else:
            self._pagina, self._app = "descobrir", {}
        self.mudou.emit()

    def _ler_pedido(self):
        """Outra chamada de duiaos-loja (com a janela já aberta) pediu uma página."""
        try:
            pedido = ARQUIVO_PEDIDO.read_text().strip()
            ARQUIVO_PEDIDO.unlink()
        except OSError:
            return
        if pedido:
            self.irPara(pedido)
        self.mostrar.emit()

    mostrar = Signal()

    # ------------------------------------------------------------ listas
    def _refazer_lista(self):
        """Refaz a lista da página; só avisa a tela se os aplicativos mudaram (o andamento de uma
        instalação muda a situação várias vezes por segundo e não deve redesenhar a grade)."""
        lista = self._lista()
        ids = [a["id"] for a in lista]
        if ids != self._ids_lista:
            self._lista_atual, self._ids_lista = lista, ids
            self.listaMudou.emit()

    def _lista(self):
        if self._pagina == "busca":
            return catalogo.buscar(self._apps, self._busca)
        if self._pagina.startswith("categoria:"):
            categoria = self._pagina.split(":", 1)[1]
            lista = [a for a in self._apps if categoria in a["categorias"]]
            # Os verificados e os que têm ícone primeiro: a página fica com cara de loja
            return sorted(lista, key=lambda a: (not a["verificado"], not a["icone"], catalogo.normalizar(a["nome"])))[:400]
        if self._pagina == "instalados":
            return [a for a in self._todos() if self._situacao_de(a) in ("instalado", "atualizavel")]
        if self._pagina == "atualizacoes":
            return [a for a in self._todos() if self._situacao_de(a) == "atualizavel"]
        return []

    def _todos(self):
        """Todos os aplicativos das duas fontes (um mesmo aplicativo pode estar instalado pelas duas)."""
        return sorted(self._por_id.values(), key=lambda a: catalogo.normalizar(a["nome"]))

    def _situacao_de(self, app):
        if app["id"] in self._tarefas:
            return "andamento"
        if app["fonte"] == "debian":
            return "instalado" if app["pacote"] in self._instalados_debian else "disponivel"
        if app["pacote"] in self._instalados_flathub:
            return "atualizavel" if app["pacote"] in self._atualizaveis else "instalado"
        return "disponivel"

    def _situacao(self):
        """{id: situação} só do que não é "disponivel" (a interface usa "disponivel" como padrão)."""
        saida = {}
        for app in self._por_id.values():
            situacao = self._situacao_de(app)
            if situacao != "disponivel":
                saida[app["id"]] = situacao
        return saida

    def _categorias(self):
        contagem = {}
        for app in self._apps:
            for categoria in app["categorias"]:
                contagem[categoria] = contagem.get(categoria, 0) + 1
        return [{**c, "quantos": contagem.get(c["id"], 0)} for c in catalogo.CATEGORIAS]

    # ------------------------------------------------------------ instalar
    @Slot(str)
    def instalar(self, id_app):
        self._pedir("instalar", id_app)

    @Slot(str)
    def remover(self, id_app):
        self._pedir("remover", id_app)

    @Slot(str)
    def atualizar(self, id_app):
        self._pedir("atualizar", id_app)

    @Slot()
    def atualizarTudo(self):
        for id_flatpak in list(self._atualizaveis):
            self._pedir("atualizar", "flathub:" + id_flatpak)

    def _pedir(self, acao, id_app):
        app = self._por_id.get(id_app)
        if not app or id_app in self._tarefas:
            return
        registrar("info", "loja_pedido", acao=acao, app=id_app)
        if app["fonte"] == "debian":
            self._preparar_debian(acao, app)
            return
        if acao == "remover":
            self._confirmacao = {"app": app, "acao": "remover", "titulo": f"Remover {app['nome']}?",
                                 "texto": "O aplicativo sai deste computador. Seus arquivos e documentos ficam.",
                                 "botao": "Remover", "pronto": True}
            self.situacaoMudou.emit()
            return
        self._enfileirar_flatpak(acao, app)

    def _enfileirar_flatpak(self, acao, app):
        self._tarefas[app["id"]] = {"acao": acao, "fracao": 0.0, "mensagem": "Na fila", "fila": True}
        self.situacaoMudou.emit()
        if DEMONSTRACAO:
            return
        self._proxima_tarefa()

    def _proxima_tarefa(self):
        if self._processo is not None:
            return
        proxima = next(((i, t) for i, t in self._tarefas.items() if t.get("fila")), None)
        if not proxima:
            self.situacaoMudou.emit()
            return
        id_app, tarefa = proxima
        tarefa["fila"] = False
        tarefa["mensagem"] = "Começando"
        app = self._por_id[id_app]
        instalacao = self._instalados_flathub.get(app["pacote"], {}).get("instalacao", "user")
        escopo = "--system" if instalacao == "system" else "--user"
        comandos = {"instalar": ["flatpak", "install", "--user", "-y", catalogo.FLATHUB, app["pacote"]],
                    "remover": ["flatpak", "uninstall", escopo, "-y", app["pacote"]],
                    "atualizar": ["flatpak", "update", escopo, "-y", app["pacote"]]}
        self._processo = True
        threading.Thread(target=self._rodar_flatpak, args=(id_app, comandos[tarefa["acao"]], tarefa["acao"]),
                         daemon=True).start()
        self.situacaoMudou.emit()

    def _rodar_flatpak(self, id_app, comando, acao):
        """Roda o flatpak num pseudoterminal (só assim ele escreve a porcentagem) e manda o andamento."""
        import pty
        mestre, escravo = pty.openpty()
        try:
            processo = subprocess.Popen(comando, stdout=escravo, stderr=escravo, stdin=subprocess.DEVNULL,
                                        env={**os.environ, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "COLUMNS": "120"})
        except OSError as erro:
            os.close(mestre)
            os.close(escravo)
            self._pronto.emit("flatpak", (id_app, 1, str(erro)))
            return
        os.close(escravo)
        self._processo = processo
        ultima, resto = "", ""
        while True:
            try:
                dados = os.read(mestre, 4096)
            except OSError:                       # o processo fechou o terminal
                break
            if not dados:
                break
            partes = re.split(r"[\r\n]", resto + dados.decode("utf-8", "replace"))
            resto = partes.pop()
            for linha in partes:
                fracao, mensagem = catalogo.ler_linha_flatpak(linha, acao)
                texto = catalogo.limpar_terminal(linha)
                if texto:
                    ultima = texto
                if mensagem or fracao is not None:
                    self._andamento.emit(id_app, -1.0 if fracao is None else fracao, mensagem)
        os.close(mestre)
        codigo = processo.wait()
        self._pronto.emit("flatpak", (id_app, codigo, "" if codigo == 0 else ultima))

    def _ao_andamento(self, id_app, fracao, mensagem):
        tarefa = self._tarefas.get(id_app)
        if not tarefa:
            return
        if fracao >= 0:
            tarefa["fracao"] = max(tarefa.get("fracao", 0.0), min(fracao, 1.0))
        if mensagem:
            tarefa["mensagem"] = mensagem
        self.situacaoMudou.emit()

    @Slot(str)
    def cancelar(self, id_app):
        tarefa = self._tarefas.get(id_app)
        if not tarefa:
            return
        if tarefa.get("fila") or DEMONSTRACAO:
            self._tarefas.pop(id_app, None)
            self.situacaoMudou.emit()
        elif tarefa.get("agente"):
            self._agente("Cancelar")
        elif hasattr(self._processo, "terminate"):
            self._processo.terminate()

    # -------------------------------------------------- Debian pelo agente
    def _preparar_debian(self, acao, app):
        if acao == "atualizar":
            # Pacotes do Debian se atualizam com o sistema (Configurações › Atualizações)
            self.abrirAtualizacoesDoSistema()
            return
        nome_acao = "instalar_aplicativo" if acao == "instalar" else "remover_aplicativo"
        self._confirmacao = {"app": app, "acao": acao, "titulo": ("Instalar " if acao == "instalar" else "Remover ") + app["nome"] + "?",
                             "texto": "Conferindo o que vai mudar…", "botao": "Instalar" if acao == "instalar" else "Remover",
                             "pronto": False}
        self.situacaoMudou.emit()
        if DEMONSTRACAO:
            self._confirmacao.update({"texto": f"Instalar {app['pacote']} e mais 3 pacotes que ele precisa.\n"
                                               "Vai baixar 24 MB e ocupar 96 MB.", "pronto": True, "plano": "demo"})
            self.situacaoMudou.emit()
            return

        def respondeu(argumentos):
            plano = json.loads(argumentos[0])
            if not self._confirmacao or self._confirmacao.get("app", {}).get("id") != app["id"]:
                return                              # a pessoa já fechou a janela de confirmação
            if plano.get("recusa"):
                self._confirmacao = {**self._confirmacao, "texto": plano["recusa"]["mensagem"], "pronto": False,
                                     "recusa": True}
            else:
                partes = [plano.get("resumo", "")]
                if plano.get("baixar_bytes"):
                    partes.append(f"Vai baixar {tamanho(plano['baixar_bytes'])}")
                espaco = plano.get("espaco_bytes", 0)
                if espaco > 0:
                    partes.append(f"e ocupar {tamanho(espaco)}")
                elif espaco < 0:
                    partes.append(f"e liberar {tamanho(-espaco)}")
                texto = partes[0] + ("\n" + " ".join(partes[1:]) + "." if len(partes) > 1 else "")
                self._confirmacao = {**self._confirmacao, "texto": texto, "pronto": True, "plano": plano["id"]}
            self.situacaoMudou.emit()
        self._agente("Preparar", nome_acao, json.dumps({"pacote": app["pacote"]}), ao_responder=respondeu)

    @Slot()
    def confirmar(self):
        confirmacao, self._confirmacao = self._confirmacao, {}
        if not confirmacao.get("pronto"):
            self.situacaoMudou.emit()
            return
        app = confirmacao["app"]
        if app["fonte"] == "flathub":
            self._enfileirar_flatpak(confirmacao["acao"], app)
            return
        self._tarefas[app["id"]] = {"acao": confirmacao["acao"], "fracao": 0.0, "mensagem": "Começando", "agente": True}
        self.situacaoMudou.emit()
        if not DEMONSTRACAO:
            self._agente("Executar", confirmacao["plano"])

    @Slot()
    def fecharConfirmacao(self):
        self._confirmacao = {}
        self.situacaoMudou.emit()

    def _agente(self, metodo, *argumentos, ao_responder=None, tempo=300000):
        from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusPendingCallWatcher
        mensagem = QDBusMessage.createMethodCall(AGENTE[0], AGENTE[1], AGENTE[0], metodo)
        mensagem.setArguments(list(argumentos))
        vigia = QDBusPendingCallWatcher(QDBusConnection.systemBus().asyncCall(mensagem, tempo), self)
        self._vigias = getattr(self, "_vigias", []) + [vigia]

        def terminou(v):
            self._vigias.remove(v)
            if v.isError():
                texto = v.error().message() or "O serviço de instalação não respondeu."
                if metodo == "Preparar" and self._confirmacao:
                    self._confirmacao = {**self._confirmacao, "texto": texto, "pronto": False, "recusa": True}
                elif metodo == "Executar":
                    for id_app in [i for i, t in self._tarefas.items() if t.get("agente")]:
                        self._tarefas.pop(id_app)
                    self.aviso.emit(texto)
                self.situacaoMudou.emit()
            elif ao_responder:
                ao_responder(v.reply().arguments())
            v.deleteLater()
        vigia.finished.connect(terminou)

    def _ligar_agente(self):
        try:
            from PySide6.QtDBus import QDBusConnection
            QDBusConnection.systemBus().connect(AGENTE[0], AGENTE[1], AGENTE[0], "Mudou", self, "1aoMudarAgente(QString)")
        except Exception:                            # sem D-Bus do sistema (testes): a loja funciona só com o Flathub
            pass

    @Slot(str)
    def aoMudarAgente(self, texto):
        try:
            estado = json.loads(texto)
        except ValueError:
            return
        tarefa, ultima = estado.get("tarefa"), estado.get("ultima")
        acoes = {"instalar_aplicativo": "instalar", "remover_aplicativo": "remover"}
        if tarefa and tarefa.get("acao") in acoes:
            id_app = "debian:" + tarefa.get("argumentos", {}).get("pacote", "")
            self._tarefas[id_app] = {"acao": acoes[tarefa["acao"]], "fracao": tarefa.get("fracao", 0.0),
                                     "mensagem": tarefa.get("etapa") or tarefa.get("mensagem", ""), "agente": True}
            self.situacaoMudou.emit()
            return
        terminadas = [i for i, t in self._tarefas.items() if t.get("agente")]
        if terminadas and ultima and ultima.get("acao") in acoes:
            for id_app in terminadas:
                self._tarefas.pop(id_app)
            app = self._por_id.get("debian:" + (ultima.get("argumentos") or {}).get("pacote", ""), {})
            if ultima.get("resultado") == "ok":
                self._notificar(f"{app.get('nome', 'O aplicativo')} foi {'instalado' if ultima['acao'] == 'instalar_aplicativo' else 'removido'}.")
            elif ultima.get("resultado") != "cancelada":
                self.aviso.emit(ultima.get("mensagem") or "A instalação não terminou.")
            self._recarregar_instalados()

    @Slot()
    def abrirAtualizacoesDoSistema(self):
        if not DEMONSTRACAO:
            sistema.abrir_app_duiaos("configuracoes", "--secao", "atualizacoes")

    # ------------------------------------------------------------ abrir
    @Slot(str)
    def abrir(self, id_app):
        app = self._por_id.get(id_app)
        if not app or DEMONSTRACAO:
            return
        registrar("info", "loja_abrir", app=id_app)
        if app["fonte"] == "flathub":
            aplicativos.iniciar(["flatpak", "run", app["pacote"]])
            return
        entrada = aplicativos.ler_desktop(app["lancador"]) if app["lancador"] else None
        if entrada:
            aplicativos.iniciar(aplicativos.comando_de_exec(entrada))
        else:
            self.aviso.emit(f"Abra o {app['nome']} pela Central de Aplicativos.")

    @Slot(str)
    def abrirSite(self, endereco):
        if endereco.startswith(("https://", "http://")) and not DEMONSTRACAO:
            aplicativos.iniciar(["xdg-open", endereco])

    @Slot()
    def recarregarCatalogo(self):
        if DEMONSTRACAO:
            return
        self._carregando = True
        self.catalogoMudou.emit()
        self._em_fundo("catalogo", self._carregar_catalogo_forcado)

    @staticmethod
    def _carregar_catalogo_forcado():
        catalogo.preparar_flathub(forcar=True)
        return Loja._carregar_catalogo()

    # ------------------------------------------------------------ para o QML
    pagina = Property(str, lambda self: self._pagina, notify=mudou)
    app = Property("QVariantMap", lambda self: self._app, notify=mudou)
    termo = Property(str, lambda self: self._busca, notify=mudou)
    podeVoltar = Property(bool, lambda self: bool(self._historico) or self._pagina != "descobrir", notify=mudou)
    lista = Property("QVariantList", lambda self: self._lista_atual, notify=listaMudou)
    carregando = Property(bool, lambda self: self._carregando, notify=catalogoMudou)
    erroFlathub = Property(str, lambda self: self._erro_flathub, notify=catalogoMudou)
    vitrine = Property("QVariantMap", lambda self: self._vitrine, notify=catalogoMudou)
    categorias = Property("QVariantList", lambda self: self._categorias(), notify=catalogoMudou)
    totais = Property("QVariantMap", lambda self: {
        "debian": sum(1 for a in self._por_id.values() if a["fonte"] == "debian"),
        "flathub": sum(1 for a in self._por_id.values() if a["fonte"] == "flathub")}, notify=catalogoMudou)
    situacao = Property("QVariantMap", lambda self: self._situacao(), notify=situacaoMudou)
    tarefas = Property("QVariantMap", lambda self: self._tarefas, notify=situacaoMudou)
    confirmacao = Property("QVariantMap", lambda self: self._confirmacao, notify=situacaoMudou)
    instalados = Property("QVariantList", lambda self: [a for a in self._todos() if self._situacao_de(a) in ("instalado", "atualizavel")],
                          notify=situacaoMudou)
    numeroAtualizacoes = Property(int, lambda self: len(self._atualizaveis), notify=situacaoMudou)
    demonstracao = Property(bool, lambda self: DEMONSTRACAO, constant=True)

    @Slot(str, result="QVariantMap")
    def aplicativo(self, id_app):
        return self._por_id.get(id_app, {})

    @Slot(str, result=str)
    def nomeCategoria(self, id_categoria):
        return next((c["nome"] for c in catalogo.CATEGORIAS if c["id"] == id_categoria), id_categoria)

    @Slot("QVariantList", result="QVariantList")
    def nomesCategorias(self, ids):
        return [self.nomeCategoria(i) for i in ids]


def tamanho(bytes_):
    valor = float(abs(bytes_))
    for unidade in ("bytes", "KB", "MB", "GB"):
        if valor < 1000 or unidade == "GB":
            return f"{valor:.0f} {unidade}" if unidade in ("bytes", "KB") else f"{valor:.1f} {unidade}".replace(".", ",")
        valor /= 1000
    return ""


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    pagina = argumento("--pagina", "descobrir")
    captura = argumento("--captura")
    if not DEMONSTRACAO:
        # Uma janela só: com ela aberta, só pede a página e sai
        trava = open(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "duiaos-loja.lock", "w")
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            ARQUIVO_PEDIDO.write_text(pagina)
            sys.exit(0)
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Duia App Store")
    app.setDesktopFileName("duiaos-loja")
    interface.ligar_registro("duiaos-loja")

    loja = Loja(pagina)
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    contexto = engine.rootContext()
    contexto.setContextProperty("loja", loja)
    # Menus na Barra de Recursos (menu_do_app.py, ADR 059)
    import menu_do_app
    menu = menu_do_app.criar("loja", [])          # guardado numa variável: sem isso o Python o descarta
    contexto.setContextProperty("menuDoApp", menu)
    contexto.setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / "LojaDeAplicativos.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
