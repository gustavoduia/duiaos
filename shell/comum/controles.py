"""DuiaOS — controles do sistema: Wi-Fi, Bluetooth, som, brilho, bateria, energia,
luz noturna, modo avião, teclado e captura de tela.

Um só lugar para ler e mudar o estado do computador, usado pela Barra de
Recursos (ícones, balões e Central de Controle) e pelas Configurações.

Ferramentas do Debian por trás de cada controle:
  Wi-Fi e modo avião   nmcli (NetworkManager)
  Bluetooth            bluetoothctl (BlueZ)
  Som e microfone      wpctl (PipeWire/WirePlumber)
  Brilho               brightnessctl (pelo logind, sem senha para quem está no computador)
  Bateria              /sys/class/power_supply
  Modo de energia      powerprofilesctl (power-profiles-daemon)
  Luz noturna          wlsunset
  Captura de tela      grim

As funções de leitura (ler_*/interpretar_*) são puras e testadas em
shell/testes. A classe Controles roda os comandos fora da linha da interface e
avisa o QML quando algo muda.

Uso direto (sessao/autostart):
  controles.py --aplicar-luz-noturna   liga o wlsunset conforme as preferências
"""
import datetime
import glob
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pastas  # noqa: E402

TEMPO_LIMITE = 4


def executar(*comando, entrada=None, tempo=TEMPO_LIMITE):
    """Roda um comando e devolve (código, saída). Código 127 se o programa não existe."""
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=tempo,
                                   input=entrada, check=False)
        return resultado.returncode, resultado.stdout.strip()
    except FileNotFoundError:
        return 127, ""
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def separar_nmcli(linha):
    """Divide uma linha de 'nmcli -t' nos ':' que não estão escapados."""
    campos, atual, escapado = [], [], False
    for c in linha:
        if escapado:
            atual.append(c)
            escapado = False
        elif c == "\\":
            escapado = True
        elif c == ":":
            campos.append("".join(atual))
            atual = []
        else:
            atual.append(c)
    campos.append("".join(atual))
    return campos


# --------------------------------------------------------------------- Wi-Fi

def interpretar_redes(saida):
    """'nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list' → redes únicas, melhor sinal primeiro."""
    redes = {}
    for linha in saida.splitlines():
        campos = separar_nmcli(linha)
        if len(campos) < 4:
            continue
        em_uso, ssid, sinal, seguranca = campos[0], campos[1], campos[2], campos[3]
        if not ssid:
            continue                      # rede oculta
        try:
            sinal = int(sinal)
        except ValueError:
            sinal = 0
        atual = redes.get(ssid)
        conectada = em_uso.strip() == "*"
        if atual is None or sinal > atual["sinal"] or conectada:
            redes[ssid] = {
                "ssid": ssid,
                "sinal": max(sinal, atual["sinal"]) if atual else sinal,
                "segura": seguranca.strip() not in ("", "--"),
                "conectada": conectada or bool(atual and atual["conectada"]),
            }
    lista = list(redes.values())
    lista.sort(key=lambda r: (not r["conectada"], -r["sinal"], r["ssid"].casefold()))
    return lista


def nivel_wifi(sinal):
    """Sinal de 0–100 → 1 a 3 arcos."""
    if sinal >= 67:
        return 3
    if sinal >= 34:
        return 2
    return 1


def ler_redes_salvas(saida):
    """'nmcli -t -f NAME,TYPE connection show' → nomes das redes Wi-Fi salvas."""
    salvas = []
    for linha in saida.splitlines():
        campos = separar_nmcli(linha)
        if len(campos) >= 2 and campos[1] in ("802-11-wireless", "wifi"):
            salvas.append(campos[0])
    return salvas


def ler_ethernet(saida):
    """'nmcli -t -f TYPE,STATE device' → True se há cabo conectado."""
    for linha in saida.splitlines():
        campos = separar_nmcli(linha)
        if len(campos) >= 2 and campos[0] == "ethernet" and campos[1] == "connected":
            return True
    return False


# ----------------------------------------------------------------- Bluetooth

def interpretar_bluetooth_show(saida):
    """'bluetoothctl show' → (existe adaptador, ligado)."""
    if not saida or "No default controller" in saida:
        return False, False
    return True, bool(re.search(r"^\s*Powered:\s*yes", saida, re.M))


def interpretar_dispositivos(saida):
    """'bluetoothctl devices [Filtro]' → [{'endereco', 'nome'}]."""
    dispositivos = []
    for linha in saida.splitlines():
        achado = re.match(r"^\s*Device\s+([0-9A-F:]{17})\s+(.*)$", linha.strip(), re.I)
        if achado:
            dispositivos.append({"endereco": achado.group(1).upper(), "nome": achado.group(2).strip()})
    return dispositivos


# ---------------------------------------------------------------------- som

def interpretar_volume(saida):
    """'wpctl get-volume' → (volume 0–100 ou -1, mudo)."""
    if not saida.startswith("Volume:"):
        return -1, False
    try:
        volume = round(float(saida.split()[1]) * 100)
    except (IndexError, ValueError):
        return -1, False
    return volume, "MUTED" in saida


def interpretar_saidas(saida, secao="Sinks"):
    """Lista de saídas (Sinks) ou entradas (Sources) de áudio do 'wpctl status'."""
    dispositivos, na_audio, na_secao = [], False, False
    for linha in saida.splitlines():
        limpa = linha.replace("│", " ").replace("├", " ").replace("└", " ").replace("─", " ").rstrip()
        texto = limpa.strip()
        if not texto:
            continue
        if texto in ("Audio", "Video", "Settings"):
            na_audio = texto == "Audio"
            na_secao = False
            continue
        if texto.endswith(":"):
            na_secao = na_audio and texto[:-1] == secao
            continue
        if not na_secao:
            continue
        achado = re.match(r"^(\*)?\s*(\d+)\.\s+(.*?)(\s+\[vol:.*\])?$", texto)
        if achado:
            dispositivos.append({"id": int(achado.group(2)), "nome": achado.group(3).strip(),
                                 "padrao": bool(achado.group(1))})
    return dispositivos


# ------------------------------------------------------------------- brilho

def interpretar_brilho(saida):
    """'brightnessctl -m' → porcentagem (-1 sem tela com brilho ajustável)."""
    for linha in saida.splitlines():
        campos = linha.split(",")
        if len(campos) >= 4 and campos[1] == "backlight":
            try:
                return int(campos[3].rstrip("%"))
            except ValueError:
                return -1
    return -1


# ------------------------------------------------------------------ bateria

def ler_bateria(raiz="/sys/class/power_supply"):
    """Bateria: {'nivel', 'carregando', 'ligada_na_tomada', 'minutos'}; nivel -1 sem bateria."""
    estado = {"nivel": -1, "carregando": False, "ligada_na_tomada": False, "minutos": -1}
    for pasta in sorted(glob.glob(os.path.join(raiz, "*"))):
        tipo = _ler(pasta, "type")
        if tipo == "Mains" and _ler(pasta, "online") == "1":
            estado["ligada_na_tomada"] = True
    for pasta in sorted(glob.glob(os.path.join(raiz, "BAT*"))):
        try:
            estado["nivel"] = int(_ler(pasta, "capacity"))
        except ValueError:
            continue
        situacao = _ler(pasta, "status")
        estado["carregando"] = situacao == "Charging"
        if situacao == "Full":
            estado["ligada_na_tomada"] = True
        estado["minutos"] = _minutos_restantes(pasta, situacao)
        break
    return estado


def _ler(pasta, nome):
    try:
        return Path(pasta, nome).read_text().strip()
    except OSError:
        return ""


def _minutos_restantes(pasta, situacao):
    """Tempo até acabar (descarregando) ou encher (carregando), pela energia ou carga."""
    for agora, cheio, taxa in (("energy_now", "energy_full", "power_now"), ("charge_now", "charge_full", "current_now")):
        try:
            atual, total, consumo = (int(_ler(pasta, n)) for n in (agora, cheio, taxa))
        except ValueError:
            continue
        if consumo <= 0:
            return -1
        if situacao == "Discharging":
            return int(atual / consumo * 60)
        if situacao == "Charging":
            return int((total - atual) / consumo * 60)
        return -1
    return -1


def descrever_tempo(minutos):
    if minutos < 0:
        return ""
    horas, resto = divmod(minutos, 60)
    if horas and resto:
        return f"{horas} h {resto} min"
    if horas:
        return f"{horas} h"
    return f"{resto} min"


# ----------------------------------------------------------- modo de energia

PERFIS = {"power-saver": "Economia", "balanced": "Equilibrado", "performance": "Desempenho"}


def interpretar_perfis(saida):
    """'powerprofilesctl list' → (perfis disponíveis na ordem de PERFIS)."""
    achados = re.findall(r"^\s*\*?\s*(power-saver|balanced|performance):", saida, re.M)
    return [p for p in PERFIS if p in achados]


# ------------------------------------------------------------- luz noturna

def luz_noturna_comando(modo, inicio="19:00", fim="06:30", temperatura=4000, agora=None):
    """Comando do wlsunset para o modo ('ligada' = agora até o fim; 'programada'), ou [] se desligada."""
    if modo not in ("ligada", "programada"):
        return []
    duracao = "600"
    if modo == "ligada":
        # Ligada agora e sem hora para apagar: a "noite" começa há 2 minutos e o
        # "dia" dura 1 minuto, daqui a quase 24 horas (a sessão seguinte refaz a conta).
        agora = agora or datetime.datetime.now()
        inicio = (agora - datetime.timedelta(minutes=2)).strftime("%H:%M")
        fim = (agora - datetime.timedelta(minutes=3)).strftime("%H:%M")
        duracao = "30"
    return ["wlsunset", "-t", str(int(temperatura)), "-T", "6500", "-s", inicio, "-S", fim, "-d", duracao]


def aplicar_luz_noturna(modo=None):
    """Para o wlsunset da sessão e, se for o caso, inicia de novo conforme as preferências."""
    modo = modo or pastas.ler_preferencia("luz-noturna", "modo", "desligada")
    inicio = pastas.ler_preferencia("luz-noturna", "inicio", "19:00")
    fim = pastas.ler_preferencia("luz-noturna", "fim", "06:30")
    temperatura = pastas.ler_preferencia("luz-noturna", "temperatura", "4000")
    executar("pkill", "-u", str(os.getuid()), "-x", "wlsunset")
    comando = luz_noturna_comando(modo, inicio, fim, int(temperatura) if temperatura.isdigit() else 4000)
    if comando:
        try:
            subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError:
            return False
    return True


# ------------------------------------------------------------------- teclado

LAYOUTS = {
    "br": "Português (Brasil, ABNT2)",
    "us": "Inglês (EUA)",
    "us:intl": "Inglês (EUA, internacional com acentos)",
    "pt": "Português (Portugal)",
    "es": "Espanhol",
    "latam": "Espanhol (América Latina)",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
    "gb": "Inglês (Reino Unido)",
}


def interpretar_localectl(saida):
    """'localectl status' → 'br', 'us:intl' etc."""
    layout = re.search(r"X11 Layout:\s*(\S+)", saida)
    variante = re.search(r"X11 Variant:\s*(\S+)", saida)
    if not layout:
        return "br"
    return layout.group(1) + (":" + variante.group(1) if variante else "")


# ===================================================================== Qt

def _criar_classe():
    from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

    class Controles(QObject):
        """Estado do sistema para o QML, lido em segundo plano a cada 3 segundos."""

        mudou = Signal()
        redesMudaram = Signal()
        bluetoothMudou = Signal()
        aviso = Signal(str)
        _chegou = Signal(str, object)

        def __init__(self, demonstracao=False):
            super().__init__()
            self._demo = demonstracao
            self._e = {
                "wifiExiste": True, "wifiLigado": False, "wifiRede": "", "wifiSinal": 0, "ethernet": False,
                "btExiste": False, "btLigado": False, "btConectados": [],
                "volume": -1, "mudo": False, "microfone": -1, "microfoneMudo": False,
                "saidas": [], "entradas": [],
                "brilho": -1, "bateria": -1, "carregando": False, "tomada": False, "minutos": -1,
                "perfil": "", "perfis": [], "luzNoturna": pastas.ler_preferencia("luz-noturna", "modo", "desligada"),
                "teclado": "br",
            }
            self._redes, self._salvas, self._buscando = [], [], False
            self._bt_pareados, self._bt_proximos, self._bt_buscando = [], [], False
            self._ocupado = False
            self._ajustes = {}              # valor arrastado na interface → aplicado sem atraso
            self._chegou.connect(self._ao_chegar)
            if demonstracao:
                self._preencher_demonstracao()
            else:
                self._timer = QTimer(self, interval=3000, timeout=self.atualizar)
                self._timer.start()
                self.atualizar()

        # --------------------------------------------------------- execução
        def _fundo(self, nome, funcao, *args):
            def tarefa():
                try:
                    resultado = funcao(*args)
                except Exception as erro:          # nunca derrubar a interface
                    resultado = erro
                self._chegou.emit(nome, resultado)
            threading.Thread(target=tarefa, daemon=True).start()

        def _ao_chegar(self, nome, resultado):
            if isinstance(resultado, Exception):
                return
            if nome == "estado":
                self._ocupado = False
                for chave, valor in self._ajustes.items():
                    if time.monotonic() - valor[1] < 2.5:
                        resultado[chave] = valor[0]       # não "pula" o controle enquanto a pessoa arrasta
                self._e.update(resultado)
                self.mudou.emit()
            elif nome == "redes":
                self._redes, self._salvas = resultado
                self._buscando = False
                self.redesMudaram.emit()
            elif nome == "bt":
                self._bt_pareados, self._bt_proximos = resultado
                self._bt_buscando = False
                self.bluetoothMudou.emit()
            elif nome == "aviso" and resultado:
                self.aviso.emit(resultado)
                self.atualizar()
                self.buscarRedes(False)

        @Slot()
        def atualizar(self):
            if self._demo or self._ocupado:
                return
            self._ocupado = True
            self._fundo("estado", ler_estado)

        # ------------------------------------------------------------ Wi-Fi
        @Slot(bool)
        def buscarRedes(self, varrer=True):
            if self._demo:
                return
            self._buscando = True
            self.redesMudaram.emit()
            self._fundo("redes", ler_redes, varrer)

        @Slot(bool)
        def ligarWifi(self, ligar):
            self._e["wifiLigado"] = ligar
            self.mudou.emit()
            if not self._demo:
                self._fundo("aviso", lambda: executar("nmcli", "radio", "wifi", "on" if ligar else "off") and "")

        @Slot(str, str)
        def conectarWifi(self, ssid, senha):
            if self._demo:
                return
            def conectar():
                if senha:
                    codigo, _ = executar("nmcli", "-a", "device", "wifi", "connect", ssid,
                                         entrada=senha + "\n", tempo=40)
                else:
                    codigo, _ = executar("nmcli", "device", "wifi", "connect", ssid, tempo=40)
                return f"Conectado a {ssid}." if codigo == 0 else f"Não foi possível conectar a {ssid}. Confira a senha."
            self._fundo("aviso", conectar)

        @Slot(str)
        def desconectarWifi(self, ssid):
            if not self._demo:
                self._fundo("aviso", lambda: executar("nmcli", "connection", "down", "id", ssid) and f"Desconectado de {ssid}.")

        @Slot(str)
        def esquecerWifi(self, ssid):
            if not self._demo:
                self._fundo("aviso", lambda: executar("nmcli", "connection", "delete", "id", ssid) and f"A rede {ssid} foi esquecida.")

        @Slot(str, result=bool)
        def redeSalva(self, ssid):
            return ssid in self._salvas

        # -------------------------------------------------------- Bluetooth
        @Slot(bool)
        def ligarBluetooth(self, ligar):
            self._e["btLigado"] = ligar
            self.mudou.emit()
            if not self._demo:
                self._fundo("aviso", lambda: executar("bluetoothctl", "power", "on" if ligar else "off") and "")

        @Slot(bool)
        def buscarBluetooth(self, varrer=True):
            if self._demo:
                return
            self._bt_buscando = True
            self.bluetoothMudou.emit()
            self._fundo("bt", ler_bluetooth, varrer)

        @Slot(str)
        def conectarBluetooth(self, endereco):
            if self._demo:
                return
            def conectar():
                executar("bluetoothctl", "pair", endereco, tempo=25)
                executar("bluetoothctl", "trust", endereco)
                codigo, _ = executar("bluetoothctl", "connect", endereco, tempo=25)
                return "Dispositivo conectado." if codigo == 0 else "Não foi possível conectar o dispositivo."
            self._fundo("aviso", conectar)

        @Slot(str)
        def desconectarBluetooth(self, endereco):
            if not self._demo:
                self._fundo("aviso", lambda: executar("bluetoothctl", "disconnect", endereco) and "Dispositivo desconectado.")

        @Slot(str)
        def esquecerBluetooth(self, endereco):
            if not self._demo:
                self._fundo("aviso", lambda: executar("bluetoothctl", "remove", endereco) and "Dispositivo removido.")

        # -------------------------------------------------------- modo avião
        @Slot(bool)
        def modoAviao(self, ligar):
            self._e["wifiLigado"] = not ligar
            self._e["btLigado"] = not ligar if self._e["btExiste"] else False
            self.mudou.emit()
            if not self._demo:
                def aplicar():
                    executar("nmcli", "radio", "all", "off" if ligar else "on")
                    executar("bluetoothctl", "power", "off" if ligar else "on")
                    return ""
                self._fundo("aviso", aplicar)

        # ---------------------------------------------------------------- som
        def _ajuste(self, chave, valor):
            self._ajustes[chave] = (valor, time.monotonic())
            self._e[chave] = valor
            self.mudou.emit()

        @Slot(int)
        def definirVolume(self, valor):
            valor = max(0, min(100, int(valor)))
            self._ajuste("volume", valor)
            if not self._demo:
                self._fundo("x", executar, "wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{valor / 100:.2f}")
                if self._e["mudo"] and valor > 0:
                    self.alternarMudo()

        @Slot()
        def alternarMudo(self):
            self._ajuste("mudo", not self._e["mudo"])
            if not self._demo:
                self._fundo("x", executar, "wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")

        @Slot(int)
        def definirMicrofone(self, valor):
            valor = max(0, min(100, int(valor)))
            self._ajuste("microfone", valor)
            if not self._demo:
                self._fundo("x", executar, "wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SOURCE@", f"{valor / 100:.2f}")

        @Slot()
        def alternarMicrofoneMudo(self):
            self._ajuste("microfoneMudo", not self._e["microfoneMudo"])
            if not self._demo:
                self._fundo("x", executar, "wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle")

        @Slot(int)
        def escolherDispositivoDeSom(self, identificador):
            if not self._demo:
                self._fundo("aviso", lambda: executar("wpctl", "set-default", str(identificador)) and "")

        # ------------------------------------------------------------ brilho
        @Slot(int)
        def definirBrilho(self, valor):
            valor = max(5, min(100, int(valor)))     # nunca apaga a tela de vez
            self._ajuste("brilho", valor)
            if not self._demo:
                self._fundo("x", executar, "brightnessctl", "-q", "set", f"{valor}%")

        # ---------------------------------------------------- modo de energia
        @Slot(str)
        def definirPerfil(self, perfil):
            if perfil not in PERFIS:
                return
            self._ajuste("perfil", perfil)
            if not self._demo:
                self._fundo("x", executar, "powerprofilesctl", "set", perfil)

        # ------------------------------------------------------- luz noturna
        @Slot(str)
        def definirLuzNoturna(self, modo):
            if modo not in ("desligada", "ligada", "programada"):
                return
            pastas.gravar_preferencia("luz-noturna", "modo", modo)
            self._e["luzNoturna"] = modo
            self.mudou.emit()
            if not self._demo:
                self._fundo("x", aplicar_luz_noturna, modo)

        @Slot(str, str)
        def definirHorarioLuzNoturna(self, inicio, fim):
            for valor in (inicio, fim):
                if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", valor):
                    self.aviso.emit("Use horários no formato 19:00.")
                    return
            pastas.gravar_preferencia("luz-noturna", "inicio", inicio)
            pastas.gravar_preferencia("luz-noturna", "fim", fim)
            if not self._demo and self._e["luzNoturna"] != "desligada":
                self._fundo("x", aplicar_luz_noturna, None)

        # ---------------------------------------------------- captura de tela
        @Slot()
        def capturarTela(self):
            if self._demo:
                return
            def capturar():
                time.sleep(0.6)                      # o balão some antes da foto
                destino = pastas.pasta("PICTURES") / "Capturas de tela"
                destino.mkdir(parents=True, exist_ok=True)
                nome = destino / datetime.datetime.now().strftime("Captura de tela %Y-%m-%d às %H.%M.%S.png")
                codigo, _ = executar("grim", str(nome))
                return f"Captura salva em Imagens › Capturas de tela." if codigo == 0 else "Não foi possível capturar a tela."
            self._fundo("aviso", capturar)

        # ------------------------------------------------------- propriedades
        def _p(chave, tipo, sinal=mudou):
            return Property(tipo, lambda self: self._e[chave], notify=sinal)

        wifiExiste = _p("wifiExiste", bool)
        wifiLigado = _p("wifiLigado", bool)
        wifiRede = _p("wifiRede", str)
        wifiSinal = _p("wifiSinal", int)
        ethernet = _p("ethernet", bool)
        bluetoothExiste = _p("btExiste", bool)
        bluetoothLigado = _p("btLigado", bool)
        bluetoothConectados = _p("btConectados", "QVariantList")
        volume = _p("volume", int)
        mudo = _p("mudo", bool)
        microfone = _p("microfone", int)
        microfoneMudo = _p("microfoneMudo", bool)
        saidas = _p("saidas", "QVariantList")
        entradas = _p("entradas", "QVariantList")
        brilho = _p("brilho", int)
        bateria = _p("bateria", int)
        carregando = _p("carregando", bool)
        tomada = _p("tomada", bool)
        perfil = _p("perfil", str)
        perfis = _p("perfis", "QVariantList")
        luzNoturna = _p("luzNoturna", str)
        teclado = _p("teclado", str)

        tempoBateria = Property(str, lambda self: descrever_tempo(self._e["minutos"]), notify=mudou)
        nivelWifi = Property(int, lambda self: nivel_wifi(self._e["wifiSinal"]) if self._e["wifiRede"] else 0, notify=mudou)
        modoAviaoLigado = Property(bool, lambda self: self._e["wifiExiste"] and not self._e["wifiLigado"]
                                   and not self._e["btLigado"], notify=mudou)
        redes = Property("QVariantList", lambda self: self._redes, notify=redesMudaram)
        buscandoRedes = Property(bool, lambda self: self._buscando, notify=redesMudaram)
        bluetoothPareados = Property("QVariantList", lambda self: self._bt_pareados, notify=bluetoothMudou)
        bluetoothProximos = Property("QVariantList", lambda self: self._bt_proximos, notify=bluetoothMudou)
        buscandoBluetooth = Property(bool, lambda self: self._bt_buscando, notify=bluetoothMudou)
        nomesPerfis = Property("QVariantMap", lambda self: dict(PERFIS), constant=True)
        layouts = Property("QVariantMap", lambda self: dict(LAYOUTS), constant=True)

        # ------------------------------------------------------ demonstração
        def _preencher_demonstracao(self):
            self._e.update({
                "wifiLigado": True, "wifiRede": "Casa Duia 5G", "wifiSinal": 82,
                "btExiste": True, "btLigado": True,
                "btConectados": [{"endereco": "AA:BB:CC:DD:EE:01", "nome": "Fone Duia"}],
                "volume": 62, "microfone": 70,
                "saidas": [{"id": 46, "nome": "Alto-falantes internos", "padrao": True},
                           {"id": 51, "nome": "Fone Duia", "padrao": False}],
                "entradas": [{"id": 47, "nome": "Microfone interno", "padrao": True}],
                "brilho": 75, "bateria": 84, "minutos": 312,
                "perfil": "balanced", "perfis": ["power-saver", "balanced", "performance"],
            })
            self._redes = [
                {"ssid": "Casa Duia 5G", "sinal": 82, "segura": True, "conectada": True},
                {"ssid": "Casa Duia", "sinal": 64, "segura": True, "conectada": False},
                {"ssid": "Vizinho", "sinal": 31, "segura": True, "conectada": False},
                {"ssid": "Café Aberto", "sinal": 22, "segura": False, "conectada": False},
            ]
            self._salvas = ["Casa Duia 5G", "Casa Duia"]
            self._bt_pareados = [{"endereco": "AA:BB:CC:DD:EE:01", "nome": "Fone Duia", "conectado": True},
                                 {"endereco": "AA:BB:CC:DD:EE:02", "nome": "Teclado sem fio", "conectado": False}]

    return Controles


def ler_estado():
    """Lê tudo o que a Barra mostra (roda fora da linha da interface)."""
    e = {}
    codigo, radio = executar("nmcli", "-t", "-f", "WIFI", "radio")
    e["wifiExiste"] = codigo != 127
    e["wifiLigado"] = radio.strip() == "enabled"
    _, dispositivos = executar("nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device")
    e["ethernet"] = ler_ethernet(dispositivos)
    rede, sinal = "", 0
    if e["wifiLigado"]:
        _, lista = executar("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "no")
        conectada = next((r for r in interpretar_redes(lista) if r["conectada"]), None)
        if conectada:
            rede, sinal = conectada["ssid"], conectada["sinal"]
    e["wifiRede"], e["wifiSinal"] = rede, sinal

    _, show = executar("bluetoothctl", "show", tempo=2)
    e["btExiste"], e["btLigado"] = interpretar_bluetooth_show(show)
    e["btConectados"] = []
    if e["btLigado"]:
        _, conectados = executar("bluetoothctl", "devices", "Connected", tempo=2)
        e["btConectados"] = interpretar_dispositivos(conectados)

    e["volume"], e["mudo"] = interpretar_volume(executar("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")[1])
    e["microfone"], e["microfoneMudo"] = interpretar_volume(executar("wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@")[1])
    _, status = executar("wpctl", "status")
    e["saidas"] = interpretar_saidas(status, "Sinks")
    e["entradas"] = interpretar_saidas(status, "Sources")

    e["brilho"] = interpretar_brilho(executar("brightnessctl", "-m", "-c", "backlight")[1])

    bateria = ler_bateria()
    e["bateria"], e["carregando"] = bateria["nivel"], bateria["carregando"]
    e["tomada"], e["minutos"] = bateria["ligada_na_tomada"], bateria["minutos"]

    codigo, perfil = executar("powerprofilesctl", "get", tempo=2)
    e["perfil"] = perfil if codigo == 0 else ""
    e["perfis"] = interpretar_perfis(executar("powerprofilesctl", "list", tempo=2)[1]) if codigo == 0 else []

    e["luzNoturna"] = pastas.ler_preferencia("luz-noturna", "modo", "desligada")
    e["teclado"] = interpretar_localectl(executar("localectl", "status", tempo=2)[1])
    return e


def ler_redes(varrer):
    _, lista = executar("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list",
                        "--rescan", "yes" if varrer else "no", tempo=15)
    _, salvas = executar("nmcli", "-t", "-f", "NAME,TYPE", "connection", "show")
    return interpretar_redes(lista), ler_redes_salvas(salvas)


def ler_bluetooth(varrer):
    if varrer:
        executar("bluetoothctl", "--timeout", "8", "scan", "on", tempo=12)
    _, pareados = executar("bluetoothctl", "devices", "Paired")
    _, conectados = executar("bluetoothctl", "devices", "Connected")
    _, todos = executar("bluetoothctl", "devices")
    ids_conectados = {d["endereco"] for d in interpretar_dispositivos(conectados)}
    lista_pareados = [{**d, "conectado": d["endereco"] in ids_conectados} for d in interpretar_dispositivos(pareados)]
    ids_pareados = {d["endereco"] for d in lista_pareados}
    proximos = [{**d, "conectado": False} for d in interpretar_dispositivos(todos)
                if d["endereco"] not in ids_pareados and not re.match(r"^([0-9A-F]{2}-){5}", d["nome"])]
    return lista_pareados, proximos


_CLASSE = None


def Controles(demonstracao=False):  # noqa: N802 — cria a classe Qt só quando usada
    global _CLASSE
    if _CLASSE is None:
        _CLASSE = _criar_classe()
    return _CLASSE(demonstracao)


if __name__ == "__main__":
    if "--aplicar-luz-noturna" in sys.argv:
        sys.exit(0 if aplicar_luz_noturna() else 1)
    print(__doc__)
