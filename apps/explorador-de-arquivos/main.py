#!/usr/bin/env python3
"""DuiaOS — Explorador de Arquivos.

Navega pelas pastas da pessoa (Início, Área de Trabalho, Documentos, Downloads,
Imagens, Música, Vídeos), pelos aplicativos instalados, pela Lixeira e pelos
discos e pendrives. Ícones (com miniaturas) ou lista; copiar, recortar, colar,
renomear, nova pasta, mover para a Lixeira e restaurar, "Abrir com", busca nas
subpastas, informações e atalhos de teclado.

A interface fica em ExploradorDeArquivos.qml; as operações, em operacoes.py.

Uso:
  main.py [PASTA | aplicativos: | lixeira:]      abre uma janela (padrão: Início)
  main.py PASTA --captura ARQUIVO [--lista]      salva uma imagem da janela e sai
"""
import os
import subprocess
import sys
import threading
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))
import operacoes  # noqa: E402  (também põe shell/comum no caminho)
import aplicativos  # noqa: E402
import interface  # noqa: E402
import pastas  # noqa: E402
import tipos  # noqa: E402

from PySide6.QtCore import (QFileSystemWatcher, QMimeData, QObject, Property, QTimer, QUrl,  # noqa: E402
                            Signal, Slot)
from PySide6.QtGui import QGuiApplication, QIcon  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

APLICATIVOS = "aplicativos:"
LIXEIRA = "lixeira:"
BUSCA = "busca:"


class Explorador(QObject):
    mudou = Signal()
    itensMudaram = Signal()
    tarefaMudou = Signal()
    aviso = Signal(str)
    renomearNovo = Signal(str)
    _pronto = Signal(str, object)

    def __init__(self, inicial):
        super().__init__()
        self._local, self._itens, self._erro = "", [], ""
        self._historico, self._posicao = [], -1
        self._visualizacao = pastas.ler_preferencia("explorador", "visualizacao", "icones")
        self._ordem = pastas.ler_preferencia("explorador", "ordem", "nome")
        self._ocultos = pastas.ler_preferencia("explorador", "ocultos", "nao") == "sim"
        self._busca, self._buscando, self._origem_busca = "", False, ""
        self._tarefa = {"ativa": False, "titulo": "", "progresso": 0.0}
        self._cancelar = False
        self._discos = []
        self._transferencia, self._recortar = [], False
        self._vigia = QFileSystemWatcher(self)
        self._vigia.directoryChanged.connect(lambda _c: self._atrasar.start())
        self._atrasar = QTimer(self, singleShot=True, interval=250, timeout=self.recarregar)
        self._pronto.connect(self._ao_pronto)
        self._timer_discos = QTimer(self, interval=4000, timeout=self.atualizarDiscos)
        self._timer_discos.start()
        self.atualizarDiscos()
        self.abrir(inicial)

    # ------------------------------------------------------------ navegação
    def _em_fundo(self, nome, funcao, *args):
        def tarefa():
            try:
                resultado = funcao(*args)
            except operacoes.ErroDeArquivo as erro:
                resultado = erro
            except Exception as erro:            # nunca derrubar a janela
                resultado = operacoes.ErroDeArquivo(f"Algo deu errado: {erro}")
            self._pronto.emit(nome, resultado)
        threading.Thread(target=tarefa, daemon=True).start()

    def _ao_pronto(self, nome, resultado):
        if nome == "busca":
            if self._local != BUSCA:
                return
            self._buscando = False
            self._itens = [] if isinstance(resultado, Exception) else resultado
            self.itensMudaram.emit()
            self.mudou.emit()
            return
        if nome == "tarefa":
            self._tarefa = {"ativa": False, "titulo": "", "progresso": 1.0}
            self.tarefaMudou.emit()
            if isinstance(resultado, Exception):
                self.aviso.emit(str(resultado))
            self.recarregar()
            return
        if nome == "aviso":
            if isinstance(resultado, Exception):
                self.aviso.emit(str(resultado))
            elif resultado:
                self.aviso.emit(resultado)
            self.atualizarDiscos()
            self.recarregar()

    @Slot(str)
    def abrir(self, destino):
        """Abre uma pasta (ou aplicativos:/lixeira:) na janela, guardando o histórico."""
        destino = destino or str(pastas.INICIO)
        if destino.startswith("file://"):
            destino = QUrl(destino).toLocalFile()
        if destino not in (APLICATIVOS, LIXEIRA):
            destino = os.path.expanduser(destino)
            if not Path(destino).is_dir():
                if Path(destino).exists():                  # arquivo: abre a pasta dele
                    destino = str(Path(destino).parent)
                else:
                    self.aviso.emit("Esta pasta não existe.")
                    return
            destino = str(Path(destino).resolve())
        self._historico = self._historico[: self._posicao + 1] + [destino]
        self._posicao = len(self._historico) - 1
        self._ir(destino)

    def _ir(self, destino):
        self._busca = ""
        self._local = destino
        for caminho in self._vigia.directories():
            self._vigia.removePath(caminho)
        if destino not in (APLICATIVOS, LIXEIRA, BUSCA):
            self._vigia.addPath(destino)
        elif destino == LIXEIRA:
            (pastas.LIXEIRA / "files").mkdir(parents=True, exist_ok=True)
            self._vigia.addPath(str(pastas.LIXEIRA / "files"))
        self.recarregar()

    @Slot()
    def recarregar(self):
        self._erro = ""
        if self._local == BUSCA:
            return
        try:
            if self._local == APLICATIVOS:
                self._itens = [{"nome": a["nome"], "caminho": a["id"], "pasta": False, "oculto": False,
                                "icone": "aplicativos", "iconeApp": a["icone"], "tipo": a["descricao"] or "Aplicativo",
                                "tamanho": -1, "tamanhoTexto": "—", "modificado": 0, "modificadoTexto": "",
                                "miniatura": "", "app": True}
                               for a in aplicativos.listar_aplicativos()]
            elif self._local == LIXEIRA:
                self._itens = operacoes.listar_lixeira()
            else:
                self._itens = operacoes.listar(self._local, self._ocultos, self._ordem)
        except operacoes.ErroDeArquivo as erro:
            self._itens, self._erro = [], str(erro)
        self.itensMudaram.emit()
        self.mudou.emit()

    @Slot()
    def voltar(self):
        if self._posicao > 0:
            self._posicao -= 1
            self._ir(self._historico[self._posicao])

    @Slot()
    def avancar(self):
        if self._posicao < len(self._historico) - 1:
            self._posicao += 1
            self._ir(self._historico[self._posicao])

    @Slot()
    def subir(self):
        if self._local not in (APLICATIVOS, LIXEIRA, BUSCA) and self._local != "/":
            self.abrir(str(Path(self._local).parent))

    @Slot(str)
    def irPara(self, texto):
        """Caminho digitado na barra (Ctrl+L)."""
        texto = texto.strip()
        if texto.lower() in ("aplicativos", "aplicativos:"):
            self.abrir(APLICATIVOS)
        elif texto.lower() in ("lixeira", "lixeira:"):
            self.abrir(LIXEIRA)
        else:
            self.abrir(texto)

    # --------------------------------------------------------------- busca
    @Slot(str)
    def buscar(self, texto):
        texto = texto.strip()
        if not texto:
            if self._local == BUSCA:
                self._ir(self._origem_busca or str(pastas.INICIO))
            return
        if self._local != BUSCA:
            if self._local in (APLICATIVOS, LIXEIRA):
                return                                    # filtrado no próprio QML
            self._origem_busca = self._local
        self._local, self._busca, self._buscando = BUSCA, texto, True
        self._itens = []
        self.itensMudaram.emit()
        self.mudou.emit()
        self._em_fundo("busca", operacoes.buscar, self._origem_busca, texto, self._ocultos)

    # ---------------------------------------------------- abrir arquivos
    @Slot(str)
    def abrirItem(self, caminho):
        item = next((i for i in self._itens if i["caminho"] == caminho), None)
        if item and item.get("app"):
            app = aplicativos.ler_desktop(caminho)
            if app:
                aplicativos.iniciar(aplicativos.comando_de_exec(app))
                interface.registrar_uso("uso.aplicativo_aberto", aplicativo=caminho, por="central")
            return
        if self._local == LIXEIRA:
            self.aviso.emit("Restaure o item para abri-lo.")
            return
        if Path(caminho).is_dir():
            self.abrir(caminho)
        elif not aplicativos.abrir_arquivo(caminho):
            self.aviso.emit("Não há um aplicativo para abrir este arquivo.")

    @Slot(str, result="QVariantList")
    def aplicativosPara(self, caminho):
        """Aplicativos para o "Abrir com"."""
        tipo = tipos.mime(caminho) if not Path(caminho).is_dir() else "inode/directory"
        lista = aplicativos.aplicativos_para_tipo(tipo)
        return [{"id": a["id"], "nome": a["nome"], "icone": a["icone"]} for a in lista]

    @Slot(str, str)
    def abrirCom(self, id_desktop, caminho):
        app = aplicativos.ler_desktop(id_desktop)
        if app:
            aplicativos.iniciar(aplicativos.comando_de_exec(app, [caminho]))

    @Slot(str, str)
    def definirPadrao(self, id_desktop, caminho):
        """Torna o aplicativo o padrão para este tipo de arquivo (xdg-mime)."""
        tipo = tipos.mime(caminho)
        self._em_fundo("aviso", lambda: subprocess.run(["xdg-mime", "default", id_desktop, tipo], check=False,
                                                       capture_output=True) and "Aplicativo padrão alterado.")

    @Slot()
    def abrirTerminalAqui(self):
        if self._local not in (APLICATIVOS, LIXEIRA, BUSCA):
            aplicativos.iniciar(["foot", "--working-directory", self._local])

    # -------------------------------------------------------- operações
    @Slot(result=str)
    def novaPasta(self):
        if self._local in (APLICATIVOS, LIXEIRA, BUSCA):
            return ""
        try:
            caminho = operacoes.nova_pasta(self._local)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
            return ""
        self.recarregar()
        self.renomearNovo.emit(caminho)
        return caminho

    @Slot(str, str, result=bool)
    def renomear(self, caminho, nome):
        try:
            operacoes.renomear(caminho, nome)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
            return False
        self.recarregar()
        return True

    def _por_na_area(self, caminhos, recortar):
        self._transferencia, self._recortar = list(caminhos), recortar
        dados = QMimeData()
        dados.setUrls([QUrl.fromLocalFile(c) for c in caminhos])
        # Formato que outros gerenciadores de arquivos do Linux entendem (copiar/recortar)
        texto = ("cut" if recortar else "copy") + "\n" + "\n".join(QUrl.fromLocalFile(c).toString() for c in caminhos)
        dados.setData("x-special/gnome-copied-files", texto.encode())
        dados.setText("\n".join(caminhos))
        QGuiApplication.clipboard().setMimeData(dados)
        self.mudou.emit()

    @Slot("QVariantList")
    def copiar(self, caminhos):
        if self._local != APLICATIVOS and caminhos:
            self._por_na_area(caminhos, False)
            self.aviso.emit(f"{len(caminhos)} {'item copiado' if len(caminhos) == 1 else 'itens copiados'}.")

    @Slot("QVariantList")
    def recortar(self, caminhos):
        if self._local not in (APLICATIVOS, LIXEIRA) and caminhos:
            self._por_na_area(caminhos, True)

    @Slot()
    def colar(self):
        if self._local in (APLICATIVOS, LIXEIRA, BUSCA):
            return
        dados = QGuiApplication.clipboard().mimeData()
        caminhos, recortar = self._transferencia, self._recortar
        if dados is not None and dados.hasUrls():
            de_fora = [u.toLocalFile() for u in dados.urls() if u.isLocalFile()]
            if de_fora and set(de_fora) != set(caminhos):
                caminhos = de_fora
                especial = bytes(dados.data("x-special/gnome-copied-files")).decode(errors="ignore")
                recortar = especial.startswith("cut")
        if not caminhos:
            return
        self._transferir(caminhos, self._local, recortar)
        if recortar:
            self._transferencia, self._recortar = [], False
            QGuiApplication.clipboard().clear()

    def _transferir(self, caminhos, destino, mover):
        self._cancelar = False
        titulo = ("Movendo " if mover else "Copiando ") + (f"“{Path(caminhos[0]).name}”" if len(caminhos) == 1
                                                             else f"{len(caminhos)} itens")
        self._tarefa = {"ativa": True, "titulo": titulo, "progresso": 0.0}
        self.tarefaMudou.emit()

        def progresso(fracao, _nome):
            self._tarefa = {"ativa": True, "titulo": titulo, "progresso": fracao}
            self.tarefaMudou.emit()

        self._em_fundo("tarefa", operacoes.transferir, caminhos, destino, mover, progresso, lambda: self._cancelar)

    @Slot("QVariantList", str)
    def soltar(self, urls, destino):
        """Arrastar e soltar sobre uma pasta (move no mesmo disco, como os outros sistemas)."""
        caminhos = [QUrl(u).toLocalFile() if str(u).startswith("file:") else str(u) for u in urls]
        destino = destino or self._local
        if caminhos and destino not in (APLICATIVOS, LIXEIRA, BUSCA):
            mesmo_disco = all(os.stat(c).st_dev == os.stat(destino).st_dev for c in caminhos if os.path.exists(c))
            self._transferir(caminhos, destino, mesmo_disco)

    @Slot()
    def cancelarTarefa(self):
        self._cancelar = True

    @Slot("QVariantList")
    def moverParaLixeira(self, caminhos):
        if not caminhos or self._local in (APLICATIVOS, LIXEIRA):
            return
        try:
            operacoes.mover_para_lixeira(caminhos)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        else:
            self.aviso.emit("Movido para a Lixeira." if len(caminhos) == 1 else f"{len(caminhos)} itens movidos para a Lixeira.")
        self.recarregar()

    @Slot("QVariantList")
    def excluirPermanentemente(self, caminhos):
        try:
            if self._local == LIXEIRA:
                nomes = [i["nomeNaLixeira"] for i in self._itens if i["caminho"] in caminhos]
                operacoes.excluir_da_lixeira(nomes)
            else:
                operacoes.excluir_permanentemente(caminhos)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        self.recarregar()

    @Slot("QVariantList")
    def restaurar(self, caminhos):
        nomes = [i["nomeNaLixeira"] for i in self._itens if i["caminho"] in caminhos and "nomeNaLixeira" in i]
        try:
            operacoes.restaurar(nomes)
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        else:
            self.aviso.emit("Restaurado." if len(nomes) == 1 else f"{len(nomes)} itens restaurados.")
        self.recarregar()

    @Slot()
    def esvaziarLixeira(self):
        try:
            operacoes.esvaziar_lixeira()
        except operacoes.ErroDeArquivo as erro:
            self.aviso.emit(str(erro))
        self.recarregar()

    @Slot("QVariantList")
    def copiarCaminho(self, caminhos):
        QGuiApplication.clipboard().setText("\n".join(caminhos))
        self.aviso.emit("Caminho copiado.")

    @Slot(str, result="QVariantMap")
    def informacoes(self, caminho):
        item = next((i for i in self._itens if i["caminho"] == caminho), None) or operacoes.item_de(caminho) or {}
        info = dict(item)
        if item.get("pasta"):
            try:
                quantos = len(os.listdir(caminho))
                info["conteudo"] = f"{quantos} {'item' if quantos == 1 else 'itens'}"
            except OSError:
                info["conteudo"] = ""
        try:
            estado = os.stat(caminho)
            info["permissao"] = "Leitura e escrita" if os.access(caminho, os.W_OK) else "Somente leitura"
            info["criadoTexto"] = operacoes.descrever_data(estado.st_ctime)
        except OSError:
            pass
        info["local"] = item.get("local") or str(Path(caminho).parent)
        return info

    # ------------------------------------------------------------ discos
    @Slot()
    def atualizarDiscos(self):
        externos = operacoes.dispositivos_externos()
        montados = {d["caminho"] for d in externos if d["montado"]}
        outros = [d for d in operacoes.discos_montados() if d["caminho"] not in montados]
        discos = externos + [{**d, "montado": True} for d in outros]
        if discos != self._discos:
            self._discos = discos
            self.mudou.emit()

    @Slot(str)
    def abrirDisco(self, dispositivo):
        disco = next((d for d in self._discos if d["dispositivo"] == dispositivo), None)
        if not disco:
            return
        if disco["montado"]:
            self.abrir(disco["caminho"])
            return

        def montar():
            resultado = subprocess.run(["udisksctl", "mount", "--no-user-interaction", "-b", dispositivo],
                                       capture_output=True, text=True, timeout=20, check=False)
            return "" if resultado.returncode == 0 else operacoes.ErroDeArquivo("Não foi possível abrir o disco.")
        self._em_fundo("aviso", montar)
        QTimer.singleShot(1500, lambda: self._abrir_quando_montar(dispositivo, 8))

    def _abrir_quando_montar(self, dispositivo, tentativas):
        self.atualizarDiscos()
        disco = next((d for d in self._discos if d["dispositivo"] == dispositivo), None)
        if disco and disco["montado"]:
            self.abrir(disco["caminho"])
        elif tentativas > 0:
            QTimer.singleShot(1000, lambda: self._abrir_quando_montar(dispositivo, tentativas - 1))

    @Slot(str)
    def ejetar(self, dispositivo):
        disco = next((d for d in self._discos if d["dispositivo"] == dispositivo), None)
        if disco and self._local.startswith(disco["caminho"] or "\0"):
            self.abrir(str(pastas.INICIO))

        def ejetar():
            resultado = subprocess.run(["udisksctl", "unmount", "--no-user-interaction", "-b", dispositivo],
                                       capture_output=True, text=True, timeout=20, check=False)
            if resultado.returncode != 0:
                return operacoes.ErroDeArquivo("O disco está em uso. Feche os arquivos abertos dele e tente de novo.")
            subprocess.run(["udisksctl", "power-off", "--no-user-interaction", "-b", dispositivo],
                           capture_output=True, timeout=20, check=False)
            return "Pode remover o disco com segurança."
        self._em_fundo("aviso", ejetar)

    # ------------------------------------------------------- preferências
    @Slot(str)
    def definirVisualizacao(self, modo):
        if modo in ("icones", "lista"):
            self._visualizacao = modo
            pastas.gravar_preferencia("explorador", "visualizacao", modo)
            self.mudou.emit()

    @Slot(str)
    def definirOrdem(self, ordem):
        if ordem in ("nome", "data", "tamanho", "tipo"):
            self._ordem = ordem
            pastas.gravar_preferencia("explorador", "ordem", ordem)
            self.recarregar()

    @Slot()
    def alternarOcultos(self):
        self._ocultos = not self._ocultos
        pastas.gravar_preferencia("explorador", "ocultos", "sim" if self._ocultos else "nao")
        self.recarregar()

    # ------------------------------------------------------- propriedades
    def _titulo(self):
        if self._local == APLICATIVOS:
            return "Aplicativos"
        if self._local == LIXEIRA:
            return "Lixeira"
        if self._local == BUSCA:
            return f"Busca: “{self._busca}”"
        if self._local == str(pastas.INICIO):
            return "Início"
        favorito = next((f for f in pastas.favoritos() if f["caminho"] == self._local), None)
        if favorito:
            return favorito["nome"]
        return Path(self._local).name or "Computador"

    def _trilha(self):
        if self._local in (APLICATIVOS, LIXEIRA, BUSCA):
            return [{"nome": self._titulo(), "caminho": self._local}]
        caminho = Path(self._local)
        inicio = pastas.INICIO
        partes = []
        if caminho == inicio or inicio in caminho.parents:
            partes.append({"nome": "Início", "caminho": str(inicio)})
            for parte in caminho.relative_to(inicio).parts:
                partes.append({"nome": parte, "caminho": str(Path(partes[-1]["caminho"]) / parte)})
        else:
            partes.append({"nome": "Computador", "caminho": "/"})
            for parte in caminho.parts[1:]:
                partes.append({"nome": parte, "caminho": str(Path(partes[-1]["caminho"]) / parte)})
        return partes

    def _status(self):
        quantos = len([i for i in self._itens if self._ocultos or not i["oculto"]])
        texto = f"{quantos} {'item' if quantos == 1 else 'itens'}"
        if self._local not in (APLICATIVOS, LIXEIRA, BUSCA):
            livre = operacoes.espaco_livre(self._local)
            if livre:
                texto += " · " + livre
        return texto

    local = Property(str, lambda self: self._local, notify=mudou)
    titulo = Property(str, _titulo, notify=mudou)
    trilha = Property("QVariantList", _trilha, notify=mudou)
    itens = Property("QVariantList", lambda self: self._itens, notify=itensMudaram)
    erro = Property(str, lambda self: self._erro, notify=mudou)
    status = Property(str, _status, notify=mudou)
    especial = Property(str, lambda self: {APLICATIVOS: "aplicativos", LIXEIRA: "lixeira", BUSCA: "busca"}.get(self._local, ""), notify=mudou)
    podeVoltar = Property(bool, lambda self: self._posicao > 0, notify=mudou)
    podeAvancar = Property(bool, lambda self: self._posicao < len(self._historico) - 1, notify=mudou)
    podeSubir = Property(bool, lambda self: self._local not in (APLICATIVOS, LIXEIRA, BUSCA, "/"), notify=mudou)
    podeColar = Property(bool, lambda self: bool(self._transferencia) or (QGuiApplication.clipboard().mimeData() is not None
                                                                          and QGuiApplication.clipboard().mimeData().hasUrls()), notify=mudou)
    visualizacao = Property(str, lambda self: self._visualizacao, notify=mudou)
    ordem = Property(str, lambda self: self._ordem, notify=mudou)
    ocultos = Property(bool, lambda self: self._ocultos, notify=mudou)
    buscando = Property(bool, lambda self: self._buscando, notify=mudou)
    textoBusca = Property(str, lambda self: self._busca, notify=mudou)
    favoritos = Property("QVariantList", lambda self: pastas.favoritos(), constant=True)
    discos = Property("QVariantList", lambda self: self._discos, notify=mudou)
    lixeiraCheia = Property(bool, lambda self: any(os.scandir(pastas.LIXEIRA / "files")) if (pastas.LIXEIRA / "files").is_dir() else False, notify=itensMudaram)
    tarefa = Property("QVariantMap", lambda self: self._tarefa, notify=tarefaMudou)
    recortados = Property("QVariantList", lambda self: self._transferencia if self._recortar else [], notify=mudou)


def argumento(nome, padrao=""):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv and sys.argv.index(nome) + 1 < len(sys.argv) else padrao


def main():
    captura = argumento("--captura")
    if captura:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    inicial = next((a for a in sys.argv[1:] if not a.startswith("--") and a != captura), "")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Explorador de Arquivos")
    app.setDesktopFileName("duiaos-explorador-de-arquivos")
    interface.ligar_registro("duiaos-explorador-de-arquivos")
    QIcon.setThemeName(QIcon.themeName() or "hicolor")

    explorador = Explorador(inicial)
    if "--lista" in sys.argv:
        explorador._visualizacao = "lista"
    engine = QQmlApplicationEngine()
    interface.preparar(engine)
    engine.rootContext().setContextProperty("explorador", explorador)
    # Menus na Barra de Recursos (Arquivo, Editar, Exibir, Ir; menu_do_app.py, ADR 059)
    import menu_do_app
    menu = menu_do_app.criar("explorador_de_arquivos", [])
    engine.rootContext().setContextProperty("menuDoApp", menu)
    engine.rootContext().setContextProperty("capturaArquivo", captura)
    engine.load(PASTA / "ExploradorDeArquivos.qml")
    if not engine.rootObjects():
        sys.exit(1)
    codigo = app.exec()
    del engine
    sys.exit(codigo)


if __name__ == "__main__":
    main()
