"""DuiaOS — menu do aplicativo em foco na Barra de Recursos (Arquivo, Editar, Exibir…; ADR 057).

No Wayland não há um jeito comum de o aplicativo entregar o menu ao sistema, e o labwc não tem o
protocolo do KDE para isso. Mas os aplicativos descrevem as próprias janelas pela acessibilidade
(AT-SPI), que o DuiaOS mantém ligada (ADR 035): ali está a barra de menus, com cada menu, submenu,
item, atalho, item desativado e item marcado — mesmo com os menus fechados. Este módulo:

  1. acha a janela ativa entre as que se descrevem pelo AT-SPI;
  2. lê a barra de menus dela (só os títulos; cada menu é lido inteiro quando a pessoa o abre);
  3. aciona o item escolhido na Barra pelo próprio AT-SPI (como um leitor de tela faz).

Inspirado no noctalia-appmenu (Apache-2.0), que fez o mesmo para o compositor niri; o código é
nosso. Quem não tem barra de menus pelo AT-SPI (Firefox, aplicativos Electron, os do próprio
DuiaOS) fica com o menu da janela (Minimizar, Expandir, Fechar, Encerrar).

Aplicativos do GNOME (Gedit, Arquivos, Calculadora…) não têm barra de menus: o menu fica no botão ☰
da barra de título, um "popover" que o GTK descreve pelo AT-SPI mesmo fechado. Sem barra, ele vira um
menu "Menu" na Barra (ADR 061). Os itens que abrem uma página interna (ex.: "Exibir" no Gedit) só
mostram o conteúdo dela quando ela está aberta: na primeira vez, escolher o item abre o ☰ do
aplicativo já nessa página; depois disso, os itens da página aparecem como submenu na Barra.

Todo o acesso ao AT-SPI fica num processo à parte (python3 menus.py --servico), com tempo-limite
curto nas chamadas: a biblioteca do AT-SPI encerra o processo quando o barramento de acessibilidade
some, e um aplicativo travado pode demorar a responder — nada disso pode derrubar ou travar a Barra.
A Barra conversa com ele por linhas JSON (ProcessoDeMenus) e o reinicia se ele cair.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

# ------------------------------------------------------------------ texto

_TECLAS = {"primary": "Ctrl", "control": "Ctrl", "ctrl": "Ctrl", "shift": "Shift", "alt": "Alt", "mod1": "Alt",
           "super": "Super", "meta": "Super", "mod4": "Super"}
_NOMES_DE_TECLA = {"return": "Enter", "kp_enter": "Enter", "escape": "Esc", "delete": "Delete", "backspace": "Backspace",
                   "tab": "Tab", "space": "Espaço", "plus": "+", "minus": "-", "equal": "=", "comma": ",", "period": ".",
                   "slash": "/", "page_up": "PgUp", "page_down": "PgDn", "home": "Home", "end": "End", "insert": "Insert"}


def atalho(texto):
    """Atalho de um item, no formato que a Barra mostra ("Ctrl+Shift+S"), a partir do que o AT-SPI dá.
    GTK: "mnemônico;caminho;atalho" (ex.: "n;<Alt>a:n;<Primary>n"). Qt: "Ctrl+N", ou "Alt+B" quando o
    item só tem a letra sublinhada — isso não é um atalho de verdade e fica de fora."""
    if not texto:
        return ""
    partes = texto.split(";")
    if len(partes) >= 3:
        texto = partes[2]
    elif len(partes) == 2:
        texto = partes[1]
    texto = texto.strip()
    if not texto:
        return ""
    if "<" in texto:                                          # GTK: <Primary><Shift>s
        modificadores = [_TECLAS.get(m.lower(), m) for m in re.findall(r"<([^>]+)>", texto)]
        tecla = re.sub(r"<[^>]+>", "", texto)
    else:                                                     # Qt: Ctrl+Shift+S
        pedacos = [p for p in re.split(r"\+(?!$)", texto) if p]
        if len(pedacos) == 2 and pedacos[0].lower() == "alt" and len(pedacos[1]) == 1:
            return ""                                         # só a letra sublinhada
        modificadores = [_TECLAS.get(p.lower(), p) for p in pedacos[:-1]]
        tecla = pedacos[-1] if pedacos else ""
    if not tecla:
        return ""
    tecla = _NOMES_DE_TECLA.get(tecla.lower(), tecla.upper() if len(tecla) == 1 else tecla)
    vistos = []
    for m in modificadores:
        if m not in vistos:
            vistos.append(m)
    return "+".join(vistos + [tecla])


def rotulo(texto):
    """Nome do item sem as marcas de letra sublinhada que alguns aplicativos deixam (_ e &)."""
    texto = (texto or "").replace("&&", "\0").replace("&", "").replace("\0", "&")
    return re.sub(r"_(?=\w)", "", texto).strip()


# ------------------------------------------------------------------ árvore
# As funções abaixo só usam este pequeno "contrato" de um nó, para os testes trocarem o AT-SPI
# por nós de mentira: papel(n), nome(n), filhos(n), estados(n) (conjunto de nomes), tecla(n).

PAPEL_BARRA, PAPEL_MENU, PAPEL_POPUP = "menu bar", "menu", "popup menu"
PAPEIS_ITEM = {"menu item", "check menu item", "radio menu item", "tearoff menu item"}
PAPEL_SEPARADOR = "separator"


class Arvore:
    """Contrato sobre os nós do AT-SPI (a versão de mentira dos testes tem os mesmos métodos)."""

    def __init__(self, atspi):
        self.A = atspi

    def papel(self, n):
        return n.get_role_name()

    def nome(self, n):
        return n.get_name() or ""

    def filhos(self, n, limite=400):
        return [n.get_child_at_index(i) for i in range(min(n.get_child_count(), limite))]

    def quantos_filhos(self, n):
        return n.get_child_count()

    def descricao(self, n):
        return n.get_description() or ""

    def estados(self, n):
        conjunto = n.get_state_set()
        return {nome for nome in ("ENABLED", "SENSITIVE", "VISIBLE", "CHECKED", "CHECKABLE", "ACTIVE", "SHOWING")
                if conjunto.contains(getattr(self.A.StateType, nome))}

    def tecla(self, n):
        try:
            acao = n.get_action_iface()
            return acao.get_key_binding(0) if acao and acao.get_n_actions() else ""
        except Exception:                                    # noqa: BLE001 — aplicativo sem a interface
            return ""

    def acionar(self, n):
        acao = n.get_action_iface()
        if not acao or not acao.get_n_actions():
            return False
        return bool(acao.do_action(0))


def achar_barra(arvore, janela, limite=500):
    """A barra de menus de uma janela (busca em largura, com limite de nós), ou None."""
    fila, vistos = [janela], 0
    while fila and vistos < limite:
        no = fila.pop(0)
        vistos += 1
        if arvore.papel(no) == PAPEL_BARRA:
            return no
        if arvore.papel(no) in PAPEIS_ITEM or arvore.papel(no) in (PAPEL_MENU, PAPEL_POPUP):
            continue                                          # não procura barras dentro de menus
        fila.extend(arvore.filhos(no, 200))
    return None


def conteudo_do_menu(arvore, no):
    """O nó cujos filhos são os itens de um menu. GTK: o próprio menu. Qt: o "popup menu" que fica
    dentro do item. None se não houver itens (o menu ainda não foi montado pelo aplicativo)."""
    papel = arvore.papel(no)
    if papel in (PAPEL_MENU, PAPEL_POPUP):
        return no
    filhos = arvore.filhos(no, 4)
    if len(filhos) == 1 and arvore.papel(filhos[0]) in (PAPEL_MENU, PAPEL_POPUP):
        return filhos[0]
    return None


def titulos(arvore, barra):
    """Os menus da barra → [(nó, rótulo)], só os que têm itens (o Firefox, por exemplo, deixa os menus
    vazios até a pessoa abri-los na janela: aí vale o menu da janela)."""
    menus = []
    for no in arvore.filhos(barra, 40):
        nome = rotulo(arvore.nome(no))
        conteudo = conteudo_do_menu(arvore, no)
        if nome and conteudo is not None and arvore.quantos_filhos(conteudo) > 0:
            menus.append((no, nome))
    return menus


def ler_itens(arvore, menu, registrar, filtrar_invisiveis, nivel=0, conta=None):
    """Itens de um menu → lista de dicionários para a Barra:
    {id, rotulo, tipo: item|marcavel|separador|submenu, ativo, marcado, atalho, itens}.
    registrar(nó) devolve o número que identifica o nó para acioná-lo depois.
    filtrar_invisiveis: no GTK, itens escondidos não têm o estado VISIBLE (no Qt, nenhum item de
    menu fechado tem; lá o item escondido aparece desativado, o que é aceitável)."""
    conta = conta if conta is not None else [0]
    conteudo = conteudo_do_menu(arvore, menu)
    if conteudo is None or nivel > 4:
        return []
    itens = []
    for no in arvore.filhos(conteudo, 200):
        conta[0] += 1
        if conta[0] > 800:
            break
        papel = arvore.papel(no)
        estados = arvore.estados(no)
        if filtrar_invisiveis and "VISIBLE" not in estados:
            continue
        if papel == PAPEL_SEPARADOR:
            if itens and itens[-1]["tipo"] != "separador":
                itens.append({"id": -1, "rotulo": "", "tipo": "separador", "ativo": False, "marcado": False,
                              "atalho": "", "itens": []})
            continue
        if papel not in PAPEIS_ITEM and papel not in (PAPEL_MENU, PAPEL_POPUP):
            continue
        nome = rotulo(arvore.nome(no))
        if not nome or papel == "tearoff menu item":
            continue
        ativo = "ENABLED" in estados or "SENSITIVE" in estados
        sub = conteudo_do_menu(arvore, no) if papel != PAPEL_POPUP else None
        if papel == PAPEL_MENU or sub is not None:
            filhos = ler_itens(arvore, no, registrar, filtrar_invisiveis, nivel + 1, conta)
            itens.append({"id": registrar(no), "rotulo": nome, "tipo": "submenu", "ativo": ativo and bool(filhos),
                          "marcado": False, "atalho": "", "itens": filhos})
            continue
        marcavel = papel in ("check menu item", "radio menu item") or "CHECKABLE" in estados
        itens.append({"id": registrar(no), "rotulo": nome, "tipo": "marcavel" if marcavel else "item", "ativo": ativo,
                      "marcado": "CHECKED" in estados, "atalho": atalho(arvore.tecla(no)), "itens": []})
    while itens and itens[-1]["tipo"] == "separador":
        itens.pop()
    return itens


# ------------------------------------------------------------------ menu do botão ☰ (GNOME; ADR 061)

PAPEIS_DO_POPOVER = {"push button", "check box", "radio button", "toggle button", "menu item", "check menu item",
                     "radio menu item"}
# Nomes do botão ☰ (GTK em português e em inglês); sem nenhum deles, vale o último botão de alternar sem descrição
NOMES_DO_BOTAO = {"menu", "menu principal", "menu do aplicativo", "menu de aplicativo", "main menu", "primary menu",
                  "application menu", "opções", "options"}


class MenuDoBotao:
    """Pseudo-menu da Barra: o popover do botão ☰ (painel) e o botão que o abre (para mostrar na janela)."""

    def __init__(self, painel, botao):
        self.painel, self.botao = painel, botao


def _descendentes(arvore, no, profundidade=7, limite=400):
    pilha, vistos = [(no, 0)], 0
    while pilha and vistos < limite:
        atual, nivel = pilha.pop()
        vistos += 1
        yield atual, nivel
        if nivel < profundidade:
            pilha.extend((f, nivel + 1) for f in reversed(arvore.filhos(atual, 80)))


def itens_do_popover(arvore, painel):
    """[(nó, papel, nome, estados)] dos itens e separadores do popover, na ordem em que aparecem."""
    saida = []
    for no, nivel in _descendentes(arvore, painel):
        if nivel == 0:
            continue
        papel = arvore.papel(no)
        if papel == PAPEL_SEPARADOR:
            saida.append((no, papel, "", set()))
        elif papel in PAPEIS_DO_POPOVER and rotulo(arvore.nome(no)):
            saida.append((no, papel, rotulo(arvore.nome(no)), arvore.estados(no)))
    return saida


def achar_menu_do_botao(arvore, janela, limite=600):
    """O popover do botão ☰ de uma janela sem barra de menus, ou None. É o painel escondido com mais
    itens (pelo menos 3), sem campo de texto (os de busca não são menus); o botão é o de alternar
    visível com um dos nomes de menu (ou o último de alternar sem descrição)."""
    candidatos, botoes = [], []
    for no, _nivel in _descendentes(arvore, janela, profundidade=12, limite=limite):
        papel = arvore.papel(no)
        if papel == "toggle button" and "SHOWING" in arvore.estados(no):
            botoes.append(no)
        if papel == "panel" and "SHOWING" not in arvore.estados(no):
            itens = itens_do_popover(arvore, no)
            if any(arvore.papel(n) == "text" for n, _ in _descendentes(arvore, no, 4, 80)):
                continue
            quantos = sum(1 for i in itens if i[1] != PAPEL_SEPARADOR)
            if quantos >= 3:
                candidatos.append((quantos, no))
    if not candidatos:
        return None
    painel = max(candidatos, key=lambda c: c[0])[1]     # empate: o primeiro (o GTK repete o da tela cheia)
    pelo_nome = [b for b in botoes if arvore.nome(b).strip().lower() in NOMES_DO_BOTAO and not _descricao(arvore, b)]
    sem_descricao = [b for b in botoes if not _descricao(arvore, b)]
    botao = (pelo_nome or sem_descricao or [None])[-1]
    return MenuDoBotao(painel, botao)


def _descricao(arvore, no):
    try:
        return arvore.descricao(no)
    except AttributeError:
        return ""


def ler_itens_do_popover(arvore, menu, registrar, aprendidos):
    """Itens do popover no formato de ler_itens. aprendidos: {nome do item: [nomes]} das páginas internas
    já vistas, que viram submenus (o número de cada subitem leva o item que abre a página)."""
    itens = []
    for no, papel, nome, estados in itens_do_popover(arvore, menu.painel):
        if papel == PAPEL_SEPARADOR:
            if itens and itens[-1]["tipo"] != "separador":
                itens.append({"id": -1, "rotulo": "", "tipo": "separador", "ativo": False, "marcado": False,
                              "atalho": "", "itens": []})
            continue
        if "VISIBLE" not in estados:
            continue
        ativo = "ENABLED" in estados or "SENSITIVE" in estados
        if nome in aprendidos:
            filhos = [{"id": registrar(("pagina", no, sub)), "rotulo": sub, "tipo": "item", "ativo": True, "marcado": False,
                       "atalho": "", "itens": []} for sub in aprendidos[nome]]
            itens.append({"id": registrar(no), "rotulo": nome, "tipo": "submenu", "ativo": ativo and bool(filhos),
                          "marcado": False, "atalho": "", "itens": filhos})
            continue
        marcavel = papel in ("check box", "radio button", "check menu item", "radio menu item") or "CHECKABLE" in estados
        itens.append({"id": registrar(no), "rotulo": nome, "tipo": "marcavel" if marcavel else "item", "ativo": ativo,
                      "marcado": "CHECKED" in estados, "atalho": atalho(arvore.tecla(no)), "itens": []})
    while itens and itens[-1]["tipo"] == "separador":
        itens.pop()
    return itens


# ------------------------------------------------------------------ leitor

# Camadas do próprio DuiaOS (não são aplicativos com menus; ficam "ativas" quando a Barra, a Ilha ou a
# Central de Aplicativos recebem o teclado)
CAMADAS_DO_DUIAOS = {"duiaos-barra-de-recursos", "duiaos-ilha-de-aplicativos", "duiaos-area-de-trabalho",
                     "duiaos-notificacoes", "duiaos-bloqueio", "duiaos-descanso", "duiaos-menu-de-energia"}


def menu_da_janela(nome_do_aplicativo, itens_do_aplicativo=()):
    """O que todo aplicativo tem no menu com o nome dele, com ou sem barra de menus própria. itens_do_aplicativo:
    os do menu do próprio aplicativo com o mesmo nome (vêm antes das ações da janela, num menu só)."""
    def item(acao, texto, atalho_texto=""):
        return {"id": "janela:" + acao, "rotulo": texto, "tipo": "item", "ativo": True, "marcado": False,
                "atalho": atalho_texto, "itens": []}
    separador = {"id": -1, "rotulo": "", "tipo": "separador", "ativo": False, "marcado": False, "atalho": "", "itens": []}
    proprios = list(itens_do_aplicativo)
    # O "Fechar"/"Sair" do aplicativo e o "Encerrar" do DuiaOS fazem o mesmo: fica o do DuiaOS, no fim
    proprios = [i for i in proprios if not (i.get("tipo") == "item" and str(i.get("rotulo", "")).strip() in ("Fechar", "Sair"))]
    while proprios and proprios[-1].get("tipo") == "separador":
        proprios.pop()
    janela = [item("minimizar", "Minimizar", "Super+M"), item("expandir", "Expandir"), separador,
              item("fechar", "Fechar janela"), item("encerrar", f"Encerrar {nome_do_aplicativo or 'o aplicativo'}", "Ctrl+Q")]
    return proprios + ([separador] if proprios else []) + janela


class LeitorDeMenus:
    """Linha de execução que conversa com o AT-SPI. Pedidos entram numa fila; respostas saem por
    funções de retorno (a Barra as liga a sinais do Qt, que levam o resultado à linha principal).

    ao_menus(app_id, titulos)   titulos: [str] (vazio = sem barra de menus pelo AT-SPI)
    ao_itens(indice, itens)     itens de um menu, no formato de ler_itens
    """

    def __init__(self, ao_menus, ao_itens, ao_acionar=None, atspi=None):
        self._ao_menus, self._ao_itens = ao_menus, ao_itens
        self._ao_acionar = ao_acionar or (lambda _id: None)
        self._fila = queue.Queue()
        self._atspi = atspi
        self._janela = None                 # janela (nó) cujos menus estão na Barra
        self._toolkit = ""
        self._menus = []                    # [(nó, rótulo)]
        self._nos = {}                      # número → nó, para acionar (o número leva o menu: menu × 10000 + item)
        self._geracao = 0                   # muda com a janela: números de uma janela anterior não valem mais
        self._ultimo = None                 # (app_id, títulos) enviado por último
        self._app = ""                      # app_id da janela em foco
        self._aprendidos = {}               # (app_id, item do ☰) → [itens da página interna que ele abre]
        self._proxima_varredura = 0.0
        self.pausa = 0.2                    # espera para o GTK trocar a página do ☰ depois de um clique
        self._linha = threading.Thread(target=self._rodar, name="menus-do-aplicativo", daemon=True)
        self._linha.start()

    # Pedidos (chamados da linha principal)
    def foco(self, app_id, titulo=""):
        self._fila.put(("foco", (app_id, titulo)))

    def itens(self, indice):
        self._fila.put(("itens", indice))

    def acionar(self, numero, antes=None):
        self._fila.put(("acionar", (numero, antes)))

    def parar(self):
        self._fila.put(("parar", None))

    # Linha do AT-SPI
    def _rodar(self):
        try:
            if self._atspi is None:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi
                Atspi.init()
                Atspi.set_timeout(800, 3000)    # aplicativo travado: desiste em 0,8 s
                self._atspi = Atspi
            self._arvore = Arvore(self._atspi)
        except Exception as erro:               # noqa: BLE001 — sem AT-SPI, só o menu da janela
            print("Menus dos aplicativos: sem AT-SPI:", erro, flush=True)
            self._arvore = None
        while True:
            pedido, valor = self._fila.get()
            # Vários pedidos de foco em sequência: só o último importa
            while pedido == "foco" and not self._fila.empty():
                proximo = self._fila.queue[0]
                if proximo[0] != "foco":
                    break
                pedido, valor = self._fila.get()
            if pedido == "parar":
                return
            try:
                if pedido == "foco":
                    self._ler_foco(*valor)
                elif pedido == "itens":
                    self._ler_itens(valor)
                elif pedido == "acionar":
                    self._acionar(*valor)
            except Exception as erro:           # noqa: BLE001 — um aplicativo estranho não derruba a Barra
                print("Menus dos aplicativos:", pedido, erro, flush=True)
                if pedido == "itens":
                    self._ao_itens(valor, [])

    def _janela_ativa(self, app_id, titulo=""):
        """A janela com o estado ACTIVE entre os aplicativos que se descrevem pelo AT-SPI. Os que
        têm o nome parecido com o app_id do labwc são vistos primeiro. Se nenhuma estiver ACTIVE
        (alguns aplicativos não marcam a janela ativa no Wayland), vale a janela com o mesmo título
        que o labwc diz estar em foco."""
        A, arvore = self._atspi, self._arvore
        mesa = A.get_desktop(0)
        aplicativos = [mesa.get_child_at_index(i) for i in range(min(mesa.get_child_count(), 80))]
        proprios = {os.getpid(), os.getppid()}      # este serviço e a Barra que o iniciou
        chave = (app_id or "").lower().split(".")[-1]

        def ordem(app):
            try:
                nome = (app.get_name() or "").lower()
            except Exception:                   # noqa: BLE001
                return 2
            return 0 if chave and (chave in nome or nome in chave) else 1
        pelo_titulo = None
        for app in sorted((a for a in aplicativos if a is not None), key=ordem):
            try:
                if app.get_process_id() in proprios or (app.get_name() or "") in CAMADAS_DO_DUIAOS:
                    continue
                for janela in arvore.filhos(app, 30):
                    if "ACTIVE" in arvore.estados(janela):
                        return janela, (app.get_toolkit_name() or "")
                    if titulo and pelo_titulo is None and arvore.nome(janela) == titulo:
                        pelo_titulo = (janela, app.get_toolkit_name() or "")
            except Exception:                   # noqa: BLE001 — aplicativo que fechou no meio
                continue
        return pelo_titulo or (None, "")

    def _ler_foco(self, app_id, titulo=""):
        if self._arvore is None:
            self._enviar_menus(app_id, [], "sem AT-SPI")
            return
        janela, toolkit = None, ""
        if self._janela is not None:            # a mesma janela continua ativa? (uma chamada, sem varrer tudo)
            try:
                if "ACTIVE" in self._arvore.estados(self._janela) or (titulo and self._arvore.nome(self._janela) == titulo):
                    janela, toolkit = self._janela, self._toolkit
            except Exception:                   # noqa: BLE001 — a janela fechou
                pass
        if janela is None:
            janela, toolkit = self._janela_ativa(app_id, titulo)
        if janela is None:
            self._janela, self._menus = None, []
            self._enviar_menus(app_id, [], "o aplicativo não se descreve pela acessibilidade")
            return
        if janela == self._janela and self._menus and isinstance(self._menus[0][0], MenuDoBotao):
            menus, barra = self._menus, None    # a mesma janela com o ☰ já achado: não varre de novo
        elif janela == self._janela and not self._menus and time.monotonic() < self._proxima_varredura:
            return                              # a mesma janela sem menus: procura de novo a cada 5 s, não a cada 1 s
        else:
            barra = achar_barra(self._arvore, janela)
            menus = titulos(self._arvore, barra) if barra is not None else []
            if barra is None:
                botao = achar_menu_do_botao(self._arvore, janela)
                if botao is not None:
                    menus = [(botao, "Menu")]
        if janela != self._janela:
            self._nos = {}
            self._geracao += 1
        self._janela, self._toolkit, self._menus, self._app = janela, toolkit, menus, app_id
        self._proxima_varredura = time.monotonic() + 5
        motivo = "" if menus else ("a janela não tem barra de menus nem o botão ☰" if barra is None else "os menus estão vazios até serem abertos")
        self._enviar_menus(app_id, [nome for _no, nome in menus], motivo)

    def _enviar_menus(self, app_id, nomes, motivo=""):
        if (app_id, nomes) != self._ultimo:
            self._ultimo = (app_id, nomes)
            self.motivo = motivo
            self._ao_menus(app_id, nomes)

    def _registrador(self, indice):
        """Função que numera os nós de um menu. O número leva a janela e o menu, para um clique num menu
        lido antes (ou noutra janela) nunca acionar o item de outro."""
        base = ((self._geracao % 1000) * 100 + indice + 1) * 10000
        for numero in [n for n in self._nos if base <= n < base + 10000]:
            del self._nos[numero]
        contador = [0]

        def registrar(no):
            contador[0] += 1
            numero = base + contador[0]
            self._nos[numero] = no
            return numero
        return registrar

    def _ler_itens(self, indice):
        if self._arvore is None or not 0 <= indice < len(self._menus):
            self._ao_itens(indice, [])
            return
        no, _nome = self._menus[indice]
        if isinstance(no, MenuDoBotao):
            aprendidos = {nome: subs for (app, nome), subs in self._aprendidos.items() if app == self._app}
            self._ao_itens(indice, ler_itens_do_popover(self._arvore, no, self._registrador(indice), aprendidos))
            return
        filtrar = self._toolkit.lower().startswith("gtk")
        self._ao_itens(indice, ler_itens(self._arvore, no, self._registrador(indice), filtrar))

    def _acionar(self, numero, antes):
        no = self._nos.get(numero)
        if no is None:
            return
        if antes:
            antes()                             # devolve o foco à janela do aplicativo
        menu = self._menus[0][0] if self._menus else None
        if isinstance(menu, MenuDoBotao):
            ok = self._acionar_no_popover(menu, no)
        else:
            ok = self._arvore.acionar(no)
        self._ao_acionar(numero if ok else 0)

    def _nomes_do_popover(self, menu):
        return [nome for _n, papel, nome, _e in itens_do_popover(self._arvore, menu.painel) if papel != PAPEL_SEPARADOR]

    def _acionar_no_popover(self, menu, no):
        """Item do ☰. Se ele abriu uma página interna (o popover passou a mostrar outros itens, com o nome
        dele no alto), guarda os itens da página e abre o ☰ na janela, já nessela, para a pessoa escolher."""
        arvore = self._arvore
        if isinstance(no, tuple):               # subitem de uma página já aprendida: abre a página e aciona
            _tipo, abridor, nome_sub = no
            arvore.acionar(abridor)
            time.sleep(self.pausa)
            alvo = next((n for n, papel, nome, _e in itens_do_popover(arvore, menu.painel) if nome == nome_sub), None)
            ok = bool(alvo is not None and arvore.acionar(alvo))
            time.sleep(self.pausa)
            nomes = self._nomes_do_popover(menu)
            if nomes and nomes[0] == rotulo(arvore.nome(abridor)):   # ainda na página: volta para a principal
                primeiro = next(n for n, papel, _nome, _e in itens_do_popover(arvore, menu.painel) if papel != PAPEL_SEPARADOR)
                arvore.acionar(primeiro)
            return ok
        antes = self._nomes_do_popover(menu)
        nome = rotulo(arvore.nome(no))
        ok = arvore.acionar(no)
        time.sleep(self.pausa)
        depois = self._nomes_do_popover(menu)
        if ok and depois != antes and depois and depois[0] == nome:
            self._aprendidos[(self._app, nome)] = depois[1:]
            if menu.botao is not None:
                arvore.acionar(menu.botao)      # mostra o ☰ do aplicativo, aberto na página
        return ok


# ------------------------------------------------------------------ processo à parte

def barramento_de_acessibilidade():
    """True se o barramento de acessibilidade responde (sem ele, o Atspi.init() encerra o processo)."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        conexao = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        resposta = conexao.call_sync("org.a11y.Bus", "/org/a11y/bus", "org.a11y.Bus", "GetAddress", None,
                                     GLib.VariantType.new("(s)"), Gio.DBusCallFlags.NONE, 3000, None)
        return bool(resposta.unpack()[0])
    except Exception:                           # noqa: BLE001
        return False


def servico(entrada=sys.stdin, saida=sys.stdout):
    """O processo do leitor: pedidos em linhas JSON na entrada, respostas em linhas JSON na saída.
    Pedidos: {"pedido": "foco", "app_id"} · {"pedido": "itens", "indice"} · {"pedido": "acionar", "numero"}.
    Respostas: {"evento": "menus", "app_id", "titulos"} · {"evento": "itens", "indice", "itens"} ·
    {"evento": "acionado", "numero"} (0 se não deu)."""
    if not barramento_de_acessibilidade():
        print(json.dumps({"evento": "sem_atspi"}), file=saida, flush=True)
        return 3
    trava = threading.Lock()

    def enviar(dados):
        with trava:
            print(json.dumps(dados, ensure_ascii=False), file=saida, flush=True)
    leitor = LeitorDeMenus(lambda app, nomes: enviar({"evento": "menus", "app_id": app, "titulos": nomes,
                                                      "motivo": getattr(leitor, "motivo", "")}),
                           lambda indice, itens: enviar({"evento": "itens", "indice": indice, "itens": itens}),
                           lambda numero: enviar({"evento": "acionado", "numero": numero}))
    for linha in entrada:
        try:
            pedido = json.loads(linha)
        except ValueError:
            continue
        tipo = pedido.get("pedido")
        if tipo == "foco":
            leitor.foco(str(pedido.get("app_id", "")), str(pedido.get("titulo", "")))
        elif tipo == "itens" and isinstance(pedido.get("indice"), int):
            leitor.itens(pedido["indice"])
        elif tipo == "acionar" and isinstance(pedido.get("numero"), int):
            leitor.acionar(pedido["numero"])
    leitor.parar()
    return 0


class ProcessoDeMenus:
    """O lado da Barra: inicia o serviço, manda pedidos e entrega as respostas pelas funções de retorno
    (chamadas de outra linha de execução: a Barra as liga a sinais do Qt). Se o serviço cair, volta
    em 3 segundos; sem o barramento de acessibilidade, tenta de novo a cada 30 segundos (até lá, só
    o menu da janela)."""

    def __init__(self, ao_menus, ao_itens, comando=None, ao_registro=None):
        self._ao_menus, self._ao_itens = ao_menus, ao_itens
        self._registrar = ao_registro or (lambda _nivel, _texto, **_dados: None)
        self._comando = comando or [sys.executable, os.path.abspath(__file__), "--servico"]
        self._processo = None
        self._trava = threading.Lock()
        self._parado = False
        self._ultimo_foco = ""
        self.motivos = {}                   # app_id → por que ficou sem menus (para os relatórios)
        threading.Thread(target=self._manter, name="processo-de-menus", daemon=True).start()

    def _manter(self):
        while not self._parado:
            try:
                processo = subprocess.Popen(self._comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
            except OSError:
                time.sleep(30)
                continue
            with self._trava:
                self._processo = processo
            if self._ultimo_foco:
                self._mandar({"pedido": "foco", "app_id": self._ultimo_foco})
            sem_atspi = False
            for linha in processo.stdout:
                try:
                    dados = json.loads(linha)
                except ValueError:
                    continue
                evento = dados.get("evento")
                if evento == "menus":
                    if dados.get("app_id") and not dados.get("titulos") and dados.get("motivo"):
                        self.motivos[dados["app_id"]] = dados["motivo"]
                    self._ao_menus(dados.get("app_id", ""), dados.get("titulos", []))
                elif evento == "itens":
                    self._ao_itens(dados.get("indice", -9), dados.get("itens", []))
                elif evento == "sem_atspi":
                    sem_atspi = True
            codigo = processo.wait()
            if sem_atspi:
                self._registrar("aviso", "Menus dos aplicativos: sem o barramento de acessibilidade (AT-SPI)")
            elif not self._parado:
                self._registrar("aviso", "Menus dos aplicativos: o leitor parou", codigo=codigo)
            with self._trava:
                self._processo = None
            self._ao_menus("", [])                  # sem leitor: só o menu da janela
            time.sleep(30 if sem_atspi else 3)

    def _mandar(self, dados):
        with self._trava:
            processo = self._processo
        if processo is None or processo.stdin is None:
            return False
        try:
            processo.stdin.write(json.dumps(dados) + "\n")
            processo.stdin.flush()
            return True
        except (OSError, ValueError):
            return False

    def foco(self, app_id, titulo=""):
        self._ultimo_foco = app_id
        self._mandar({"pedido": "foco", "app_id": app_id, "titulo": titulo})

    def itens(self, indice):
        if not self._mandar({"pedido": "itens", "indice": indice}):
            self._ao_itens(indice, [])

    def acionar(self, numero):
        self._mandar({"pedido": "acionar", "numero": numero})

    def parar(self):
        self._parado = True
        with self._trava:
            processo = self._processo
        if processo:
            processo.terminate()


if __name__ == "__main__" and "--servico" in sys.argv:
    sys.exit(servico())
