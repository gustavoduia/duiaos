#!/usr/bin/env python3
"""DuiaOS — Área de Trabalho: o papel de parede e os ícones da pasta Área de Trabalho.

Fica por baixo de todas as janelas (camada "background" do layer-shell), em cada tela.
- Papel de parede: imagem, imagem com movimento (GIF/WebP), vídeo (sem som, em laço) ou
  cor, escolhidos em Configurações › Papel de parede; muda na hora.
- Ícones (só na tela principal): os arquivos da pasta Área de Trabalho. Botão esquerdo
  seleciona (duplo clique abre); botão direito abre o menu de contexto do ícone ou da área
  de trabalho (Nova pasta, Colar, Mudar o papel de parede…). Ctrl/Shift para vários,
  Delete, F2, Ctrl+C/X/V, Enter.

Como os cliques caem aqui, o labwc não abre mais o menu dele (Reconfigurar/Sair).

Uso:
  main.py                                      inicia (uma por sessão)
  main.py --demonstracao [--menu fundo|item] [--captura ARQUIVO]
"""
import fcntl
import os
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent / "comum"))
for _explorador in (Path("/usr/share/duiaos/explorador-de-arquivos"), PASTA.parents[1] / "apps" / "explorador-de-arquivos"):
    if (_explorador / "operacoes.py").is_file():
        sys.path.insert(0, str(_explorador))
        break

DEMONSTRACAO = "--demonstracao" in sys.argv

if not DEMONSTRACAO:
    _trava = open(os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "duiaos-area-de-trabalho.lock"), "w")
    try:
        fcntl.flock(_trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("A Área de Trabalho já está aberta.")
        sys.exit(0)
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"

from PySide6.QtCore import QFileSystemWatcher, QMimeData, QObject, Property, QTimer, QUrl, Signal, Slot  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

import aplicativos  # noqa: E402
import interface  # noqa: E402
import operacoes  # noqa: E402
import papel  # noqa: E402
import pastas  # noqa: E402
import sessao  # noqa: E402
import sistema as comum  # noqa: E402


def papel_de_parede():
    """Configuração dos papéis de parede (papel.ler_area): todas as telas, uma para cada ou estendida."""
    return papel.ler_area(pastas.PREFERENCIAS, sessao.PAPEL_PADRAO)


def imagens_para_alternar():
    """Troca automática: as imagens do DuiaOS e as importadas (não os vídeos)."""
    lista = []
    for pasta in (sessao.PAPEIS_DO_SISTEMA, pastas.DADOS / "duiaos" / "fundos"):
        if pasta.is_dir():
            lista += sorted(str(p) for p in pasta.iterdir() if p.suffix.lower() in papel.EXTENSOES_IMAGEM)
    return lista


class Area(QObject):
    mudou = Signal()
    itensMudaram = Signal()
    aviso = Signal(str)
    renomearNovo = Signal(str)

    def __init__(self):
        super().__init__()
        self._pasta = pastas.pasta("DESKTOP")
        self._itens = []
        self._papel = papel_de_parede()
        self._posicao_barra = "topo"
        self._transferencia, self._recortar = [], False
        if DEMONSTRACAO:
            self._demonstracao()
            return
        self._pasta.mkdir(parents=True, exist_ok=True)
        self._vigia = QFileSystemWatcher([str(self._pasta), str(pastas.PREFERENCIAS.parent)], self)
        self._vigia.directoryChanged.connect(lambda _c: self._atraso.start())
        self._atraso = QTimer(self, singleShot=True, interval=250, timeout=self.recarregar)
        # Troca automática do papel de parede (Configurações › Papel de parede)
        self._alternar = QTimer(self, timeout=self._trocar_papel)
        self.recarregar()

    def _programar_troca(self):
        minutos = self._papel["alternar"] if self._papel["telas"] != "separado" else 0
        if minutos <= 0:
            self._alternar.stop()
        elif self._alternar.interval() != minutos * 60000 or not self._alternar.isActive():
            self._alternar.start(minutos * 60000)

    def _trocar_papel(self):
        proximo = papel.proximo_da_lista(imagens_para_alternar(), self._papel["padrao"]["arquivo"])
        if proximo:
            pastas.gravar_preferencia("papel-de-parede", "arquivo", proximo)   # a Tela de Bloqueio vê o mesmo
            self.recarregar()

    def _demonstracao(self):
        nomes = [("Projetos", True), ("Fotos da viagem", True), ("Contrato de aluguel.pdf", False),
                 ("Orçamento 2026.xlsx", False), ("Anotações.txt", False)]
        self._itens = []
        for nome, eh_pasta in nomes:
            import tipos
            icone, descricao, _ = tipos.tipo(nome, eh_pasta)
            self._itens.append({"nome": nome, "caminho": "/demo/" + nome, "pasta": eh_pasta, "icone": icone,
                                "tipo": descricao, "miniatura": "", "oculto": False})

    @Slot()
    def recarregar(self):
        papel_atual = papel_de_parede()
        try:
            itens = operacoes.listar(self._pasta, ordem=pastas.ler_preferencia("area-de-trabalho", "ordem", "nome"))
        except operacoes.ErroDeArquivo:
            itens = []
        posicao = comum_posicao_barra()
        if papel_atual != self._papel or posicao != self._posicao_barra:
            self._papel, self._posicao_barra = papel_atual, posicao
            self.mudou.emit()
        self._programar_troca()
        if itens != self._itens:
            self._itens = itens
            self.itensMudaram.emit()

    # ------------------------------------------------------------ ações
    @Slot(str)
    def abrir(self, caminho):
        if DEMONSTRACAO:
            return
        if caminho.endswith(".desktop"):
            app = aplicativos.ler_entrada(caminho)
            if app:
                aplicativos.iniciar(aplicativos.comando_de_exec(app))
                return
        if Path(caminho).is_dir():
            comum.abrir_app_duiaos("explorador-de-arquivos", caminho)
        elif not aplicativos.abrir_arquivo(caminho):
            self.aviso.emit("Não há um aplicativo para abrir este arquivo.")

    @Slot(str)
    def mostrarNoExplorador(self, caminho):
        if not DEMONSTRACAO:
            comum.abrir_app_duiaos("explorador-de-arquivos", caminho or str(self._pasta))

    @Slot(result=str)
    def novaPasta(self):
        if DEMONSTRACAO:
            return ""
        try:
            caminho = operacoes.nova_pasta(self._pasta)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
            return ""
        self.recarregar()
        self.renomearNovo.emit(caminho)
        return caminho

    @Slot(str, str)
    def renomear(self, caminho, nome):
        try:
            operacoes.renomear(caminho, nome)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        self.recarregar()

    @Slot("QVariantList")
    def moverParaLixeira(self, caminhos):
        if not caminhos or DEMONSTRACAO:
            return
        try:
            operacoes.mover_para_lixeira(caminhos)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        self.recarregar()

    def _area(self, caminhos, recortar):
        self._transferencia, self._recortar = list(caminhos), recortar
        dados = QMimeData()
        dados.setUrls([QUrl.fromLocalFile(c) for c in caminhos])
        texto = ("cut" if recortar else "copy") + "\n" + "\n".join(QUrl.fromLocalFile(c).toString() for c in caminhos)
        dados.setData("x-special/gnome-copied-files", texto.encode())
        QGuiApplication.clipboard().setMimeData(dados)

    @Slot("QVariantList")
    def copiar(self, caminhos):
        if caminhos:
            self._area(caminhos, False)

    @Slot("QVariantList")
    def recortar(self, caminhos):
        if caminhos:
            self._area(caminhos, True)

    @Slot()
    def colar(self):
        if DEMONSTRACAO:
            return
        dados = QGuiApplication.clipboard().mimeData()
        caminhos, recortar = self._transferencia, self._recortar
        if dados is not None and dados.hasUrls():
            de_fora = [u.toLocalFile() for u in dados.urls() if u.isLocalFile()]
            if de_fora and set(de_fora) != set(caminhos):
                caminhos = de_fora
                recortar = bytes(dados.data("x-special/gnome-copied-files")).decode(errors="ignore").startswith("cut")
        if not caminhos:
            return
        try:
            operacoes.transferir(caminhos, self._pasta, mover=recortar)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        if recortar:
            self._transferencia = []
        self.recarregar()

    @Slot(str)
    def definirOrdem(self, ordem):
        pastas.gravar_preferencia("area-de-trabalho", "ordem", ordem)
        self.recarregar()

    @Slot(str)
    def abrirConfiguracoes(self, secao):
        if not DEMONSTRACAO:
            comum.abrir_app_duiaos("configuracoes", "--secao", secao)

    @Slot()
    def abrirTerminal(self):
        if not DEMONSTRACAO:
            aplicativos.iniciar(["foot", "--working-directory", str(self._pasta)])

    itens = Property("QVariantList", lambda self: self._itens, notify=itensMudaram)
    papeis = Property("QVariantMap", lambda self: self._papel, notify=mudou)

    @Slot(str, result="QVariantMap")
    def papelDaTela(self, saida):
        return papel.papel_da_tela(self._papel, saida)
    posicaoBarra = Property(str, lambda self: self._posicao_barra, notify=mudou)
    ordem = Property(str, lambda self: pastas.ler_preferencia("area-de-trabalho", "ordem", "nome"), notify=itensMudaram)


def comum_posicao_barra():
    import configparser
    config = configparser.ConfigParser()
    config.read(pastas.CONFIG / "duiaos" / "barra-de-recursos.conf")
    return config.get("barra", "posicao", fallback="topo")


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    if DEMONSTRACAO and "--captura" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv)
    interface.ligar_registro("duiaos-area-de-trabalho")
    os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)     # programas abertos daqui são janelas comuns
    app.setApplicationName("duiaos-area-de-trabalho")
    area = Area()
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    contexto = engine.rootContext()
    contexto.setContextProperty("area", area)
    contexto.setContextProperty("capturaArquivo", argumento("--captura"))
    contexto.setContextProperty("menuInicial", argumento("--menu"))
    engine.load(PASTA / ("Demonstracao.qml" if DEMONSTRACAO else "AreaDeTrabalho.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
