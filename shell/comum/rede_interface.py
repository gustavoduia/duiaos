"""DuiaOS — objeto "rede" do QML (Configurações › Rede e Internet e Barra de Recursos; ADR 069).

Lê o estado pelo shell/comum/rede.py fora da linha da interface e atualiza quando o NetworkManager avisa
(nmcli monitor), sem consultar de tempos em tempos. Mudanças de endereço (IP, DNS, MAC, MTU) pedem
confirmação: se a pessoa não disser "Manter" em 20 segundos (a conexão pode ter caído com um IP errado,
e ela nem consegue clicar), a configuração anterior volta sozinha — como a troca de resolução de tela.
"""
import os
import threading
from pathlib import Path

import proxy
import rede

TEMPO_CONFIRMAR = 20
CHAVES_DE_ENDERECO = ("ipv4", "ipv6", "mac", "mtu")

_CLASSE = None


def Rede(demonstracao=False):            # noqa: N802 — usado como classe
    global _CLASSE
    if _CLASSE is None:
        _CLASSE = _criar_classe()
    return _CLASSE(demonstracao)


def _criar_classe():
    from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

    class _Rede(QObject):
        mudou = Signal()
        conexaoMudou = Signal()
        confirmacaoMudou = Signal()
        aviso = Signal(str)
        senhaLida = Signal(str, str)                  # uuid, senha
        proxyMudou = Signal()
        firewallMudou = Signal()
        diagnosticoMudou = Signal()
        qrPronto = Signal(str, str)                   # uuid, caminho da imagem
        _chegou = Signal(str, object)

        def __init__(self, demonstracao):
            super().__init__()
            self._demo = demonstracao
            self._dispositivos, self._conexoes, self._detalhes = [], [], {}
            self._geral = {"estado": "", "conectividade": "unknown", "wifiHw": False, "wifi": False}
            self._conexao, self._abrindo = {}, ""
            self._confirmar = {"uuid": "", "volta": [], "restam": 0}
            self._lendo = False
            self._de_novo = False
            self._zonas, self._usb, self._modens = {}, {}, []
            self._firewall = {"instalado": False, "ligado": False, "padrao": "", "ssh": False}
            self._diagnostico = []
            self._diagnosticando = False
            self._proxy = {"modo": "desligado", "pac": "", "excecoes": proxy.EXCECOES_PADRAO,
                           "http": {"servidor": "", "porta": 0}, "https": {"servidor": "", "porta": 0}, "socks": {"servidor": "", "porta": 0}}
            self._chegou.connect(self._ao_chegar)
            self._relogio = QTimer(self, interval=1000, timeout=self._contar)
            if demonstracao:
                self._preencher_demonstracao()
                return
            self._vigia = rede.criar_vigia(self, self.atualizar)
            self.atualizar()
            self._fundo("proxy-lido", proxy.ler)

        # ---------------------------------------------------------- fundo
        def _fundo(self, nome, funcao, *args):
            def tarefa():
                try:
                    resultado = funcao(*args)
                except rede.ErroDeRede as erro:
                    resultado = erro
                except Exception as erro:          # noqa: BLE001 — nunca derrubar a janela
                    resultado = rede.ErroDeRede(f"Algo deu errado: {erro}")
                self._chegou.emit(nome, resultado)
            threading.Thread(target=tarefa, daemon=True).start()

        def _ao_chegar(self, nome, resultado):
            if nome == "estado":
                self._lendo = False
                if not isinstance(resultado, Exception):
                    (self._dispositivos, self._conexoes, self._geral, self._detalhes,
                     self._zonas, self._usb, self._modens, fw) = resultado
                    if fw is not None and fw != self._firewall:
                        self._firewall = fw
                        self.firewallMudou.emit()
                    for d in self._dispositivos:       # celular pelo cabo USB aparece como celular, não como cabo
                        if self._usb.get(d["dispositivo"]):
                            d["celularUsb"] = self._usb[d["dispositivo"]]
                    self.mudou.emit()
                if self._de_novo:
                    self._de_novo = False
                    self.atualizar()
                return
            if nome == "conexao":
                if isinstance(resultado, Exception):
                    self.aviso.emit(str(resultado))
                    self._abrindo = ""
                else:
                    self._conexao = resultado
                self.conexaoMudou.emit()
                return
            if nome.startswith("aplicar:"):
                uuid, endereco = nome.split(":")[1], nome.endswith(":endereco")
                if isinstance(resultado, Exception):
                    self.aviso.emit(str(resultado))
                elif endereco:
                    self._confirmar = {"uuid": uuid, "volta": resultado, "restam": TEMPO_CONFIRMAR}
                    self._relogio.start()
                    self.confirmacaoMudou.emit()
                else:
                    self.aviso.emit("Configuração salva.")
                self.abrirConexao(uuid)
                self.atualizar()
                return
            if nome == "voltou":
                self.aviso.emit(str(resultado) if isinstance(resultado, Exception) else "A configuração anterior voltou.")
                if self._abrindo:
                    self.abrirConexao(self._abrindo)
                self.atualizar()
                return
            if nome == "firewall":
                if not isinstance(resultado, Exception):
                    self._firewall = resultado
                    self.firewallMudou.emit()
                return
            if nome == "diagnostico":
                self._diagnosticando = False
                self._diagnostico = [] if isinstance(resultado, Exception) else resultado
                if isinstance(resultado, Exception):
                    self.aviso.emit(str(resultado))
                self.diagnosticoMudou.emit()
                return
            if nome == "proxy-lido":
                if not isinstance(resultado, Exception):
                    self._proxy = resultado
                    self.proxyMudou.emit()
                return
            if nome.startswith("qr:"):
                if isinstance(resultado, Exception):
                    self.aviso.emit(str(resultado))
                else:
                    self.qrPronto.emit(nome[3:], resultado)
                return
            if nome.startswith("senha:"):
                if isinstance(resultado, Exception):
                    self.aviso.emit(str(resultado))
                else:
                    self.senhaLida.emit(nome[6:], resultado)
                return
            if isinstance(resultado, Exception):
                self.aviso.emit(str(resultado))
            elif isinstance(resultado, str) and resultado:
                self.aviso.emit(resultado)
            self.atualizar()

        # ------------------------------------------------------- leitura
        @Slot()
        def atualizar(self):
            if self._demo:
                return
            if self._lendo:
                self._de_novo = True               # chega uma mudança no meio da leitura: lê de novo depois
                return
            self._lendo = True

            def ler():
                dispositivos = rede.ler_dispositivos()
                detalhes = {d["dispositivo"]: rede.ler_detalhes(d["dispositivo"]) for d in dispositivos
                            if d["estado"] in ("conectado", "conectando") and d["tipo"] != "vpn"}
                conexoes = rede.ler_conexoes()
                usb = {d["dispositivo"]: rede.celular_por_usb(d["dispositivo"]) for d in dispositivos if d["tipo"] == "cabo"}
                modens = rede.ler_modens() if any(d["tipo"] == "celular" for d in dispositivos) else []
                zonas = rede.ler_zonas(conexoes)
                # Rede ainda sem tipo: confere o firewall agora (na entrada ele pode ter subido depois da Barra)
                fw = rede.ler_firewall() if rede.sem_tipo_de_rede(conexoes, zonas) else None
                return dispositivos, conexoes, rede.ler_geral(), detalhes, zonas, usb, modens, fw
            self._fundo("estado", ler)

        @Slot(str)
        def abrirConexao(self, uuid):
            """Carrega a conexão no diálogo de Detalhes ("" fecha)."""
            self._abrindo = uuid
            if not uuid:
                self._conexao = {}
                self.conexaoMudou.emit()
                return
            if self._demo:
                self._conexao = dict(_DEMO_CONEXAO, uuid=uuid)
                self.conexaoMudou.emit()
                return
            self._fundo("conexao", rede.ler_conexao, uuid)

        @Slot(str, result="QVariantMap")
        def detalhesDe(self, dispositivo):
            return self._detalhes.get(dispositivo, {})

        @Slot("QVariantMap", result="QVariantList")
        def validar(self, config):
            return rede.validar(config)

        # -------------------------------------------------------- mudanças
        @Slot("QVariantMap")
        def aplicarConexao(self, config):
            uuid = config.get("uuid") or self._abrindo
            erros = rede.validar(config)
            if erros:
                self.aviso.emit(erros[0])
                return
            if self._demo:
                self.aviso.emit("Demonstração: nada foi mudado.")
                return
            endereco = any(chave in config for chave in CHAVES_DE_ENDERECO) and self._mudou_endereco(config)
            self._fundo(f"aplicar:{uuid}:{'endereco' if endereco else 'simples'}", rede.aplicar, uuid, config)

        def _mudou_endereco(self, config):
            atual = self._conexao or {}
            return any(chave in config and config[chave] != atual.get(chave) for chave in CHAVES_DE_ENDERECO)

        def _contar(self):
            self._confirmar["restam"] -= 1
            self.confirmacaoMudou.emit()
            if self._confirmar["restam"] <= 0:
                self.desfazer()

        @Slot()
        def manter(self):
            self._relogio.stop()
            self._confirmar = {"uuid": "", "volta": [], "restam": 0}
            self.confirmacaoMudou.emit()
            self.aviso.emit("Configuração mantida.")

        @Slot()
        def desfazer(self):
            self._relogio.stop()
            uuid, volta = self._confirmar["uuid"], self._confirmar["volta"]
            self._confirmar = {"uuid": "", "volta": [], "restam": 0}
            self.confirmacaoMudou.emit()
            if uuid:
                self._fundo("voltou", rede.voltar, uuid, volta)

        def _acao(self, funcao, *args, mensagem=""):
            if self._demo:
                return
            def fazer():
                funcao(*args)
                return mensagem
            self._fundo("acao", fazer)

        @Slot(str)
        def conectarDispositivo(self, dispositivo):
            self._acao(rede.conectar_dispositivo, dispositivo)

        @Slot(str)
        def desconectarDispositivo(self, dispositivo):
            self._acao(rede.desconectar_dispositivo, dispositivo)

        @Slot(str)
        def ativar(self, uuid):
            self._acao(rede.ativar, uuid)

        @Slot(str)
        def desativar(self, uuid):
            self._acao(rede.desativar, uuid)

        @Slot(str)
        def esquecer(self, uuid):
            self._acao(rede.esquecer, uuid, mensagem="Conexão esquecida.")
            if uuid == self._abrindo:
                self.abrirConexao("")

        @Slot(str, str, "QVariantMap")
        def novaConexaoCabo(self, dispositivo, nome, config):
            if self._demo:
                return
            def criar():
                uuid = rede.nova_conexao_cabo(dispositivo, nome, config)
                if uuid:
                    rede.ativar(uuid)
                return f"Conexão “{nome}” criada."
            self._fundo("acao", criar)

        @Slot(str, str)
        def conectarOculta(self, ssid, senha):
            self._acao(rede.conectar_oculta, ssid, senha, mensagem=f"Conectado a {ssid}.")

        @Slot(str)
        def lerSenha(self, uuid):
            if self._demo:
                self.senhaLida.emit(uuid, "senha-de-exemplo")
                return
            self._fundo("senha:" + uuid, rede.senha_salva, uuid)

        # ------------------------------------------------- Fase 2 (ADR 070)
        @Slot(str)
        def importarVpn(self, endereco):
            caminho = endereco[7:] if endereco.startswith("file://") else endereco
            from urllib.parse import unquote
            caminho = unquote(caminho)
            if self._demo:
                return
            self._fundo("acao", lambda: f"VPN “{rede.importar_vpn(caminho)}” adicionada. Ligue-a na lista de VPNs.")

        @Slot(result="QVariantMap")
        def gerarChavesWireguard(self):
            try:
                privada, publica = rede.gerar_chaves_wireguard()
            except ImportError:
                self.aviso.emit("Falta o python3-cryptography para gerar as chaves.")
                return {}
            return {"privada": privada, "publica": publica}

        @Slot("QVariantMap")
        def novaWireguard(self, dados):
            try:
                texto = rede.configuracao_wireguard(dados.get("endereco", ""), dados.get("privada", ""), dados.get("chaveServidor", ""),
                                                    dados.get("servidor", ""), dados.get("permitidos", "") or "0.0.0.0/0, ::/0",
                                                    dados.get("dns", ""), dados.get("compartilhada", ""))
            except rede.ErroDeRede as erro:
                self.aviso.emit(str(erro))
                return
            if not self._demo:
                self._fundo("acao", lambda: f"VPN “{rede.nova_wireguard(dados.get('nome', '') or 'WireGuard', texto)}” adicionada.")

        @Slot(str, str, str)
        def novaOpenConnect(self, nome, servidor, protocolo):
            if not self._demo:
                self._acao(rede.nova_openconnect, nome, servidor, protocolo, mensagem=f"VPN “{nome}” adicionada.")

        @Slot("QVariantMap")
        def conectarEmpresa(self, d):
            if self._demo:
                return
            self._acao(rede.conectar_empresa, d.get("ssid", ""), d.get("metodo", "peap"), d.get("usuario", ""), d.get("senha", ""),
                       d.get("interna", "mschapv2"), d.get("anonima", ""), d.get("ca", "").replace("file://", ""), d.get("dominio", ""),
                       d.get("certificado", "").replace("file://", ""), d.get("chave", "").replace("file://", ""), d.get("senhaChave", ""),
                       bool(d.get("semVerificar")), mensagem=f"Conectado a {d.get('ssid', '')}.")

        @Slot("QVariantMap")
        def gravarProxy(self, config):
            config = {k: (dict(v) if hasattr(v, "keys") else v) for k, v in dict(config).items()}
            erros = proxy.validar(config)
            if erros:
                self.aviso.emit(erros[0])
                return
            if self._demo:
                self.aviso.emit("Demonstração: nada foi mudado.")
                return
            proxy.gravar(config)
            self._proxy = config
            self.proxyMudou.emit()
            # O apt do sistema (atualizações) usa o mesmo proxy HTTP: pelo duiaos-agente, com autorização
            import json
            import interface
            http = config.get("http", {}) if config.get("modo") == "manual" else {}
            pedido = {"servidor": http.get("servidor", ""), "porta": int(http.get("porta") or 0)} if http.get("servidor") else {}
            interface.chamar_agente(self, "ConfigurarProxy", [json.dumps(pedido)],
                                    lambda _r: self.aviso.emit("Proxy salvo. Programas abertos agora já usam; os que estavam abertos, ao reabrir."),
                                    lambda m: self.aviso.emit("Proxy salvo para os programas, mas não para as atualizações do sistema: " + m))

        @Slot(str, str)
        def ligarPontoDeAcesso(self, nome, senha):
            wifi = next((d["dispositivo"] for d in self._dispositivos if d["tipo"] == "wifi"), "")
            self._acao(rede.ligar_ponto_de_acesso, wifi, nome, senha, mensagem=f"Ponto de acesso “{nome}” ligado.")

        @Slot()
        def desligarPontoDeAcesso(self):
            self._acao(rede.desligar_ponto_de_acesso, mensagem="Ponto de acesso desligado.")

        @Slot(str, str, str)
        def qrWifi(self, uuid, ssid, seguranca):
            destino = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / f"duiaos-qr-{uuid[:8]}.png"
            if self._demo:
                return

            def gerar():
                senha = rede.senha_salva(uuid) if seguranca else ""
                return rede.gerar_qr(rede.texto_qr_wifi(ssid, senha, seguranca), destino)
            self._fundo("qr:" + uuid, gerar)

        # ------------------------------------------------- Fase 3 (ADR 071)
        @Slot()
        def lerFirewall(self):
            if not self._demo:
                self._fundo("firewall", rede.ler_firewall)

        @Slot(bool, bool)
        def configurarFirewall(self, ligado, ssh):
            if self._demo:
                self._firewall = dict(self._firewall, ligado=ligado, ssh=ssh)
                self.firewallMudou.emit()
                return
            import json
            import interface
            interface.chamar_agente(self, "ConfigurarFirewall", [json.dumps({"ligado": bool(ligado), "ssh": bool(ssh)})],
                                    lambda _r: (self.aviso.emit("Firewall " + ("ligado." if ligado else "desligado.")), self.lerFirewall()),
                                    lambda m: (self.aviso.emit(m), self.lerFirewall()))

        @Slot(str, str)
        def definirTipoDeRede(self, uuid, tipo):
            if self._demo:
                self._zonas[uuid] = tipo
                self.mudou.emit()
                return
            self._acao(rede.definir_tipo_de_rede, uuid, tipo,
                       mensagem="Rede marcada como " + ("privada." if tipo == "privada" else "pública."))

        @Slot()
        def diagnosticar(self):
            if self._diagnosticando:
                return
            self._diagnosticando = True
            self._diagnostico = []
            self.diagnosticoMudou.emit()
            if self._demo:
                self._diagnostico = [rede._passo("Conexão", True, "Conectado: Conexão cabeada 1 (Cabo de rede)."),
                                     rede._passo("Endereço", True, "O computador tem o endereço 192.168.0.23."),
                                     rede._passo("Roteador", True, "O roteador (192.168.0.1) responde."),
                                     rede._passo("Nomes (DNS)", False, "Os nomes de sites não estão sendo traduzidos (o DNS não responde).",
                                                 "Em Detalhes › DNS, escolha Cloudflare ou Google e salve.")]
                self._diagnosticando = False
                self.diagnosticoMudou.emit()
                return
            self._fundo("diagnostico", rede.diagnosticar)

        @Slot(str, str)
        def conectarCelularBluetooth(self, endereco, nome):
            self._acao(rede.conectar_celular_bluetooth, endereco, nome, mensagem=f"Usando a internet de {nome or 'celular'} pelo Bluetooth.")

        @Slot("QVariantMap")
        def novaCelular(self, d):
            self._acao(rede.nova_celular, d.get("nome", ""), d.get("apn", ""), d.get("usuario", ""), d.get("senha", ""), d.get("pin", ""),
                       mensagem="Conexão celular criada.")

        @Slot("QVariantMap")
        def novaAvancada(self, d):
            tipo, nome, placas = d.get("tipo", ""), d.get("nome", ""), list(d.get("placas", []) or [])
            if tipo == "vlan":
                self._acao(rede.nova_vlan, d.get("placa", ""), d.get("numero", 0), nome, mensagem="VLAN criada.")
            elif tipo == "ponte":
                self._acao(rede.nova_ponte, nome, placas, mensagem=f"Ponte “{nome}” criada.")
            elif tipo == "agregacao":
                self._acao(rede.nova_agregacao, nome, placas, d.get("modo", "active-backup"), mensagem=f"Agregação “{nome}” criada.")

        @Slot(str)
        def apagarComMembros(self, uuid):
            self._acao(rede.apagar_com_membros, uuid, mensagem="Conexão apagada.")
            self.abrirConexao("")

        # ---------------------------------------------------- propriedades
        def _resumo(self):
            return rede.resumo(self._dispositivos, self._geral["conectividade"])

        def _icone(self):
            """Ícone da Barra: o tipo da conexão principal e o estado da internet."""
            conectados = [d for d in self._dispositivos if d["estado"] == "conectado" and d["tipo"] != "vpn"]
            if not self._dispositivos:
                return ""
            if not conectados:
                return "rede-desligada" if not any(d["tipo"] == "wifi" for d in self._dispositivos) else "wifi-0"
            principal = conectados[0]
            sem_internet = self._geral["conectividade"] in ("none", "limited", "portal")
            if principal["tipo"] == "wifi":
                return "wifi-alerta" if sem_internet else ""     # "" = a Barra usa o sinal da Wi-Fi
            return "rede-alerta" if sem_internet else "rede"

        dispositivos = Property("QVariantList", lambda self: self._dispositivos, notify=mudou)
        conexoes = Property("QVariantList", lambda self: self._conexoes, notify=mudou)
        resumo = Property(str, _resumo, notify=mudou)
        conectividade = Property(str, lambda self: self._geral["conectividade"], notify=mudou)
        temPlaca = Property(bool, lambda self: bool(self._dispositivos), notify=mudou)
        temWifi = Property(bool, lambda self: any(d["tipo"] == "wifi" for d in self._dispositivos), notify=mudou)
        temCabo = Property(bool, lambda self: any(d["tipo"] == "cabo" for d in self._dispositivos), notify=mudou)
        vpnAtiva = Property(str, lambda self: next((d["conexao"] for d in self._dispositivos
                                                    if d["tipo"] == "vpn" and d["estado"] == "conectado"), ""), notify=mudou)
        icone = Property(str, _icone, notify=mudou)
        conexao = Property("QVariantMap", lambda self: self._conexao, notify=conexaoMudou)
        conexaoAberta = Property(str, lambda self: self._abrindo, notify=conexaoMudou)
        confirmando = Property(int, lambda self: self._confirmar["restam"], notify=confirmacaoMudou)
        dnsConhecidos = Property("QVariantMap", lambda self: rede.DNS_CONHECIDOS, constant=True)
        protocolosOpenconnect = Property("QVariantMap", lambda self: rede.PROTOCOLOS_OPENCONNECT, constant=True)
        metodosEap = Property("QVariantMap", lambda self: rede.METODOS_EAP, constant=True)
        proxyAtual = Property("QVariantMap", lambda self: self._proxy, notify=proxyMudou)
        firewall = Property("QVariantMap", lambda self: self._firewall, notify=firewallMudou)
        zonas = Property("QVariantMap", lambda self: self._zonas, notify=mudou)
        semTipo = Property("QVariantList", lambda self: rede.sem_tipo_de_rede(self._conexoes, self._zonas), notify=mudou)
        modens = Property("QVariantList", lambda self: self._modens, notify=mudou)
        diagnostico = Property("QVariantList", lambda self: self._diagnostico, notify=diagnosticoMudou)
        diagnosticando = Property(bool, lambda self: self._diagnosticando, notify=diagnosticoMudou)
        operadoras = Property("QVariantMap", lambda self: rede.OPERADORAS, constant=True)
        modosDeAgregacao = Property("QVariantMap", lambda self: rede.MODOS_DE_AGREGACAO, constant=True)
        pontoDeAcesso = Property(bool, lambda self: any(c["nome"] == rede.NOME_PONTO_DE_ACESSO and c["ativa"] for c in self._conexoes), notify=mudou)

        def _preencher_demonstracao(self):
            self._dispositivos = [
                {"dispositivo": "enp3s0", "tipo": "cabo", "tipoNm": "ethernet", "estado": "conectado", "conexao": "Conexão cabeada 1",
                 "uuid": "11111111-1111-1111-1111-111111111111", "externo": False},
                {"dispositivo": "wlp2s0", "tipo": "wifi", "tipoNm": "wifi", "estado": "conectado", "conexao": "Casa Duia 5G",
                 "uuid": "22222222-2222-2222-2222-222222222222", "externo": False},
                {"dispositivo": "wg0", "tipo": "vpn", "tipoNm": "wireguard", "estado": "conectado", "conexao": "Trabalho",
                 "uuid": "33333333-3333-3333-3333-333333333333", "externo": False}]
            self._conexoes = [
                {"nome": "Conexão cabeada 1", "uuid": "11111111-1111-1111-1111-111111111111", "tipo": "cabo", "dispositivo": "enp3s0",
                 "automatico": True, "prioridade": 0, "ativa": True},
                {"nome": "Escritório (IP fixo)", "uuid": "44444444-4444-4444-4444-444444444444", "tipo": "cabo", "dispositivo": "",
                 "automatico": False, "prioridade": 0, "ativa": False},
                {"nome": "Casa Duia 5G", "uuid": "22222222-2222-2222-2222-222222222222", "tipo": "wifi", "dispositivo": "wlp2s0",
                 "automatico": True, "prioridade": 0, "ativa": True},
                {"nome": "Trabalho", "uuid": "33333333-3333-3333-3333-333333333333", "tipo": "vpn", "dispositivo": "wg0",
                 "automatico": False, "prioridade": 0, "ativa": True}]
            self._geral = {"estado": "connected", "conectividade": "full", "wifiHw": True, "wifi": True}
            self._detalhes = {
                "enp3s0": {"mac": "3C:52:82:AA:BB:CC", "mtu": "1500", "limitada": False, "velocidade": "1000 Mbit/s", "cabo": True,
                           "ipv4": ["192.168.0.23/24"], "gateway4": "192.168.0.1", "dns4": ["192.168.0.1"], "ipv6": [], "gateway6": "", "dns6": []},
                "wlp2s0": {"mac": "A4:C3:F0:11:22:33", "mtu": "1500", "limitada": False, "velocidade": "", "cabo": True,
                           "ipv4": ["192.168.0.41/24"], "gateway4": "192.168.0.1", "dns4": ["192.168.0.1"], "ipv6": [], "gateway6": "", "dns6": []}}
            # A Wi-Fi ainda sem tipo de rede (mostra a pergunta "privada ou pública?")
            self._zonas = {"11111111-1111-1111-1111-111111111111": "privada", "22222222-2222-2222-2222-222222222222": ""}
            self._firewall = {"instalado": True, "ligado": True, "padrao": "duiaos-publica", "ssh": True}

    return _Rede


_DEMO_CONEXAO = {
    "nome": "Conexão cabeada 1", "tipo": "cabo", "tipoNm": "802-3-ethernet", "dispositivo": "enp3s0",
    "automatico": True, "prioridade": 0, "limitada": "auto", "todos": True, "zona": "",
    "ipv4": {"metodo": "manual", "enderecos": [{"endereco": "192.168.0.23", "prefixo": "24"}], "gateway": "192.168.0.1",
             "dns": ["1.1.1.1", "1.0.0.1"], "soDnsManual": True, "rotas": ""},
    "ipv6": {"metodo": "auto", "enderecos": [], "gateway": "", "dns": [], "soDnsManual": False, "rotas": ""},
    "mac": "stable", "mtu": "", "ssid": "", "oculta": False, "seguranca": "", "vpn": "",
}
