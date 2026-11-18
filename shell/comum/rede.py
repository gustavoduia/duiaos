"""DuiaOS — rede: tudo o que a interface sabe e muda sobre conexões, pelo NetworkManager (ADR 069).

Um só lugar para as Configurações › Rede e Internet, a Barra de Recursos e o diagnóstico. Fala com o
NetworkManager pelo nmcli no modo de scripts (-t), a interface estável que o projeto documenta para
programas, e acompanha as mudanças pelo "nmcli monitor" (sem consultar de tempos em tempos).

Por que nmcli e não a libnm pelo GObject: os aplicativos do DuiaOS são Qt (PySide6) e a libnm precisa
do laço do GLib; o nmcli não precisa de nada além do próprio NetworkManager, já era o que a página do
Wi-Fi usava, e roda igual nos testes (shell/testes/test_rede.py com um NetworkManager de verdade, quando
o ambiente permite, e com saídas gravadas).

Permissões: mudar conexões passa pelo polkit do próprio NetworkManager (quem está no computador muda as
próprias conexões; as de todos os usuários pedem administrador). Nada aqui roda como root.

As funções interpretar_* são puras; as outras recebem `rodar` (padrão: subprocess) para os testes.
"""
import ipaddress
import re
import subprocess

NMCLI = "nmcli"
TEMPO = 8

# Tipo do NetworkManager → tipo do DuiaOS (o que a página mostra)
TIPOS = {
    "ethernet": "cabo", "802-3-ethernet": "cabo",
    "wifi": "wifi", "802-11-wireless": "wifi",
    "wireguard": "vpn", "vpn": "vpn",
    "gsm": "celular", "cdma": "celular",
    "bt": "bluetooth", "bluetooth": "bluetooth",
    "bridge": "ponte", "bond": "agregacao", "vlan": "vlan",
}
IGNORAR = {"loopback", "wifi-p2p", "tun", "ifb", "dummy", "veth-peer"}
ESTADOS = {"connected": "conectado", "connecting": "conectando", "disconnected": "desconectado",
           "unavailable": "indisponivel", "unmanaged": "fora", "deactivating": "desconectando", "disconnecting": "desconectando"}
NOMES_TIPO = {"cabo": "Cabo de rede", "wifi": "Wi-Fi", "vpn": "VPN", "celular": "Rede celular",
              "bluetooth": "Celular pelo Bluetooth", "ponte": "Ponte", "agregacao": "Agregação de placas", "vlan": "VLAN"}

DNS_CONHECIDOS = {
    "Cloudflare": ["1.1.1.1", "1.0.0.1"],
    "Google": ["8.8.8.8", "8.8.4.4"],
    "Quad9": ["9.9.9.9", "149.112.112.112"],
}


class ErroDeRede(Exception):
    """Erro com mensagem pronta para a pessoa ler."""


def _rodar(comando, entrada=None, tempo=TEMPO):
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=tempo, input=entrada, check=False)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", "nmcli não encontrado"
    except subprocess.TimeoutExpired:
        return 124, "", "o NetworkManager demorou para responder"
    except OSError as erro:
        return 1, "", str(erro)


def nmcli(*argumentos, rodar=None, entrada=None, tempo=TEMPO):
    return (rodar or _rodar)([NMCLI, *argumentos], entrada=entrada, tempo=tempo)


# ------------------------------------------------------------------ leitura (puras)

def separar(linha):
    """Divide uma linha do 'nmcli -t' nos ':' que não estão escapados (\\: é um ':' de verdade)."""
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


def estado_curto(estado):
    """'connected (externally)' → 'conectado'; 'connecting (getting IP configuration)' → 'conectando'."""
    return ESTADOS.get(estado.split(" ")[0], estado.split(" ")[0])


def interpretar_dispositivos(texto):
    """'nmcli -t -f DEVICE,TYPE,STATE,CONNECTION,CON-UUID device' → placas que a pessoa usa."""
    lista = []
    for linha in texto.splitlines():
        campos = separar(linha)
        if len(campos) < 5:
            continue
        dispositivo, tipo_nm, estado, conexao, uuid = campos[:5]
        if tipo_nm in IGNORAR or tipo_nm not in TIPOS:
            continue
        curto = estado_curto(estado)
        if curto == "fora":
            continue                         # não gerenciadas (ex.: placas de contêineres)
        lista.append({"dispositivo": dispositivo, "tipo": TIPOS[tipo_nm], "tipoNm": tipo_nm, "estado": curto,
                      "conexao": conexao, "uuid": uuid, "externo": "externally" in estado})
    ordem = ["cabo", "wifi", "celular", "bluetooth", "vpn", "ponte", "agregacao", "vlan"]
    return sorted(lista, key=lambda d: (ordem.index(d["tipo"]) if d["tipo"] in ordem else 99, d["dispositivo"]))


def interpretar_campos(texto):
    """Linhas 'CHAVE:valor' do 'nmcli -t' (show) → dicionário; 'IP4.ADDRESS[1]' e '[2]' viram uma lista."""
    campos = {}
    for linha in texto.splitlines():
        if ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.replace("\\:", ":")
        m = re.match(r"^(.*)\[(\d+)\]$", chave)
        if m:
            campos.setdefault(m.group(1), []).append(valor)
        else:
            campos[chave] = valor
    return campos


def _lista(valor):
    if isinstance(valor, list):
        return [v for v in valor if v]
    return [v.strip() for v in re.split(r"[,\s]+", valor or "") if v.strip()]


def interpretar_detalhes(texto):
    """'nmcli -t -f GENERAL,CAPABILITIES,WIRED-PROPERTIES,IP4,IP6 device show X' → o que a página mostra."""
    c = interpretar_campos(texto)
    velocidade = c.get("CAPABILITIES.SPEED", "")
    return {
        "mac": c.get("GENERAL.HWADDR", ""),
        "mtu": c.get("GENERAL.MTU", ""),
        "limitada": c.get("GENERAL.METERED", "").startswith("yes"),
        "velocidade": "" if velocidade in ("", "unknown", "0 Mb/s") else velocidade.replace("Mb/s", "Mbit/s"),
        "cabo": c.get("WIRED-PROPERTIES.CARRIER", "") != "off",
        "ipv4": _lista(c.get("IP4.ADDRESS", [])),
        "gateway4": c.get("IP4.GATEWAY", ""),
        "dns4": _lista(c.get("IP4.DNS", [])),
        "ipv6": [e for e in _lista(c.get("IP6.ADDRESS", [])) if not e.lower().startswith("fe80")],
        "gateway6": c.get("IP6.GATEWAY", ""),
        "dns6": _lista(c.get("IP6.DNS", [])),
    }


def interpretar_conexoes(texto):
    """'nmcli -t -f NAME,UUID,TYPE,DEVICE,AUTOCONNECT,AUTOCONNECT-PRIORITY,ACTIVE connection show'."""
    lista = []
    for linha in texto.splitlines():
        campos = separar(linha)
        if len(campos) < 7:
            continue
        nome, uuid, tipo_nm, dispositivo, automatico, prioridade, ativa = campos[:7]
        if tipo_nm not in TIPOS:
            continue
        try:
            prioridade = int(prioridade)
        except ValueError:
            prioridade = 0
        lista.append({"nome": nome, "uuid": uuid, "tipo": TIPOS[tipo_nm], "dispositivo": dispositivo,
                      "automatico": automatico == "yes", "prioridade": prioridade, "ativa": ativa == "yes"})
    return lista


def _metodo(valor):
    return {"auto": "auto", "manual": "manual", "disabled": "desligado", "ignore": "desligado",
            "shared": "compartilhado", "link-local": "local", "dhcp": "auto"}.get(valor, "auto")


def _enderecos(valor):
    enderecos = []
    for item in _lista(valor):
        endereco, _, prefixo = item.partition("/")
        enderecos.append({"endereco": endereco, "prefixo": prefixo})
    return enderecos


def interpretar_conexao(texto):
    """'nmcli -t connection show UUID' (todas as configurações) → o que o diálogo de Detalhes edita."""
    c = interpretar_campos(texto)
    tipo_nm = c.get("connection.type", "")
    tipo = TIPOS.get(tipo_nm, tipo_nm)
    secao = "802-11-wireless" if tipo == "wifi" else "802-3-ethernet"
    try:
        prioridade = int(c.get("connection.autoconnect-priority", "0"))
    except ValueError:
        prioridade = 0
    return {
        "uuid": c.get("connection.uuid", ""), "nome": c.get("connection.id", ""), "tipo": tipo, "tipoNm": tipo_nm,
        "dispositivo": c.get("connection.interface-name", ""),
        "automatico": c.get("connection.autoconnect", "yes") == "yes", "prioridade": prioridade,
        "limitada": {"yes": "sim", "no": "nao"}.get(c.get("connection.metered", "unknown"), "auto"),
        "todos": c.get("connection.permissions", "") == "",
        "zona": c.get("connection.zone", ""),
        "ipv4": {"metodo": _metodo(c.get("ipv4.method", "auto")), "enderecos": _enderecos(c.get("ipv4.addresses", "")),
                 "gateway": c.get("ipv4.gateway", ""), "dns": _lista(c.get("ipv4.dns", "")),
                 "soDnsManual": c.get("ipv4.ignore-auto-dns", "no") == "yes", "rotas": c.get("ipv4.routes", "")},
        "ipv6": {"metodo": _metodo(c.get("ipv6.method", "auto")), "enderecos": _enderecos(c.get("ipv6.addresses", "")),
                 "gateway": c.get("ipv6.gateway", ""), "dns": _lista(c.get("ipv6.dns", "")),
                 "soDnsManual": c.get("ipv6.ignore-auto-dns", "no") == "yes", "rotas": c.get("ipv6.routes", "")},
        "mac": c.get(secao + ".cloned-mac-address", "") or "",
        "mtu": "" if c.get(secao + ".mtu", "auto") in ("auto", "0") else c.get(secao + ".mtu", ""),
        "ssid": c.get("802-11-wireless.ssid", ""),
        "oculta": c.get("802-11-wireless.hidden", "no") == "yes",
        "seguranca": c.get("802-11-wireless-security.key-mgmt", ""),
        "vpn": c.get("vpn.service-type", "").rsplit(".", 1)[-1] if tipo_nm == "vpn" else ("wireguard" if tipo_nm == "wireguard" else ""),
    }


# ------------------------------------------------------------------ validação (pura)

def prefixo_de(texto, versao=4):
    """'24', '/24' ou '255.255.255.0' → 24. ErroDeRede se não for uma máscara válida."""
    texto = (texto or "").strip().lstrip("/")
    if not texto:
        raise ErroDeRede("Falta a máscara (ex.: 255.255.255.0 ou 24).")
    if texto.isdigit():
        prefixo = int(texto)
        if not (0 < prefixo <= (32 if versao == 4 else 128)):
            raise ErroDeRede(f"Máscara fora do intervalo: /{prefixo}.")
        return prefixo
    if versao == 4:
        try:
            return ipaddress.IPv4Network(f"0.0.0.0/{texto}").prefixlen
        except ValueError:
            pass
    raise ErroDeRede(f"Máscara inválida: {texto} (use 255.255.255.0 ou 24).")


def validar_familia(config, versao):
    """Erros (em português) de uma família (ipv4/ipv6) da configuração; [] se está tudo certo."""
    erros = []
    nome = "IPv4" if versao == 4 else "IPv6"
    classe = ipaddress.IPv4Address if versao == 4 else ipaddress.IPv6Address
    redes = []
    if config.get("metodo") == "manual":
        enderecos = [e for e in config.get("enderecos", []) if (e.get("endereco") or "").strip()]
        if not enderecos:
            erros.append(f"{nome} manual precisa de pelo menos um endereço.")
        for e in enderecos:
            try:
                endereco = classe(e["endereco"].strip())
                prefixo = prefixo_de(str(e.get("prefixo", "")), versao)
                rede = ipaddress.ip_network(f"{endereco}/{prefixo}", strict=False)
                if versao == 4 and (endereco == rede.network_address or endereco == rede.broadcast_address) and prefixo < 31:
                    erros.append(f"{endereco} é o endereço da própria rede ou de difusão: escolha outro.")
                redes.append(rede)
            except ErroDeRede as erro:
                erros.append(str(erro))
            except ValueError:
                erros.append(f"Endereço {nome} inválido: {e['endereco']}.")
        gateway = (config.get("gateway") or "").strip()
        if gateway:
            try:
                g = classe(gateway)
                if redes and not any(g in r for r in redes):
                    erros.append(f"O gateway {g} não está na mesma rede do endereço.")
            except ValueError:
                erros.append(f"Gateway {nome} inválido: {gateway}.")
    for dns in config.get("dns", []):
        dns = dns.strip()
        if dns:
            try:
                ipaddress.ip_address(dns)
            except ValueError:
                erros.append(f"Servidor DNS inválido: {dns}.")
    return erros


def validar(config):
    erros = validar_familia(config.get("ipv4", {}), 4) + validar_familia(config.get("ipv6", {}), 6)
    mtu = str(config.get("mtu", "") or "").strip()
    if mtu and (not mtu.isdigit() or not 576 <= int(mtu) <= 9000):
        erros.append("MTU precisa ser um número entre 576 e 9000 (o comum é 1500).")
    return erros


_METODO_NM = {"auto": "auto", "manual": "manual", "desligado": "disabled", "compartilhado": "shared", "local": "link-local"}


def _argumentos_familia(prefixo, config, versao):
    metodo = config.get("metodo", "auto")
    if versao == 6 and metodo == "desligado":
        nm_metodo = "disabled"
    else:
        nm_metodo = _METODO_NM.get(metodo, "auto")
    enderecos = [e for e in config.get("enderecos", []) if (e.get("endereco") or "").strip()]
    args = []
    if metodo == "manual":
        textos = [f"{e['endereco'].strip()}/{prefixo_de(str(e.get('prefixo', '')), versao)}" for e in enderecos]
        args += [f"{prefixo}.method", "manual", f"{prefixo}.addresses", ", ".join(textos),
                 f"{prefixo}.gateway", (config.get("gateway") or "").strip()]
    else:
        # Primeiro tira os endereços fixos, depois muda o método (o NetworkManager recusa "auto" com endereço
        # sem gateway em algumas versões; e "manual" sem endereço)
        args += [f"{prefixo}.addresses", "", f"{prefixo}.gateway", "", f"{prefixo}.method", nm_metodo]
    dns = [d.strip() for d in config.get("dns", []) if d.strip()]
    args += [f"{prefixo}.dns", ", ".join(dns), f"{prefixo}.ignore-auto-dns", "yes" if dns and config.get("soDnsManual", True) else "no"]
    if "rotas" in config:
        args += [f"{prefixo}.routes", config.get("rotas", "") or ""]
    return args


def argumentos(config):
    """Configuração do diálogo de Detalhes → argumentos do 'nmcli connection modify'."""
    args = []
    if "automatico" in config:
        args += ["connection.autoconnect", "yes" if config["automatico"] else "no"]
    if "prioridade" in config:
        args += ["connection.autoconnect-priority", str(int(config["prioridade"]))]
    if "limitada" in config:
        args += ["connection.metered", {"sim": "yes", "nao": "no"}.get(config["limitada"], "unknown")]
    if "ipv4" in config:
        args += _argumentos_familia("ipv4", config["ipv4"], 4)
    if "ipv6" in config:
        args += _argumentos_familia("ipv6", config["ipv6"], 6)
    secao = "802-11-wireless" if config.get("tipo") == "wifi" else ("802-3-ethernet" if config.get("tipo") == "cabo" else "")
    if secao and "mac" in config:
        args += [f"{secao}.cloned-mac-address", config.get("mac") or ""]
    if secao and "mtu" in config:
        args += [f"{secao}.mtu", str(config.get("mtu") or "auto")]
    if config.get("tipo") == "wifi" and "oculta" in config:
        args += ["802-11-wireless.hidden", "yes" if config["oculta"] else "no"]
    return args


# ------------------------------------------------------------------ estado geral e frases

def interpretar_geral(texto):
    """'nmcli -t -f STATE,CONNECTIVITY,WIFI-HW,WIFI general' → {estado, conectividade, wifiHw, wifi}."""
    campos = separar(texto.strip().splitlines()[0]) if texto.strip() else []
    campos += [""] * (4 - len(campos))
    return {"estado": campos[0], "conectividade": campos[1] or "unknown",
            "wifiHw": campos[2] == "enabled", "wifi": campos[3] == "enabled"}


def resumo(dispositivos, conectividade):
    """Uma frase do estado da rede para o topo da página e para a Barra."""
    conectados = [d for d in dispositivos if d["estado"] == "conectado" and d["tipo"] != "vpn"]
    vpn = [d for d in dispositivos if d["estado"] == "conectado" and d["tipo"] == "vpn"]
    if not dispositivos:
        return "Nenhuma placa de rede encontrada"
    if not conectados:
        if any(d["estado"] == "conectando" for d in dispositivos):
            return "Conectando…"
        if any(d["tipo"] == "cabo" and d["estado"] == "indisponivel" for d in dispositivos) and \
                not any(d["tipo"] == "wifi" for d in dispositivos):
            return "Cabo de rede desconectado"
        return "Sem conexão"
    principal = conectados[0]
    como = {"cabo": "pelo cabo", "wifi": f"à Wi-Fi {principal['conexao']}", "celular": "pela rede celular",
            "bluetooth": "pelo celular (Bluetooth)"}.get(principal["tipo"], f"por {principal['conexao']}")
    internet = {"full": "Internet funcionando", "portal": "Esta rede pede login", "limited": "Sem internet",
                "none": "Sem internet"}.get(conectividade, "")
    frase = f"Conectado {como}" + (f" · {internet}" if internet else "")
    if vpn:
        frase += f" · VPN {vpn[0]['conexao']}"
    return frase


# ------------------------------------------------------------------ comandos

def _erro(saida_erro, padrao):
    texto = (saida_erro or "").strip().splitlines()
    texto = texto[-1] if texto else ""
    texto = re.sub(r"^Error:\s*", "", texto)
    if "Insufficient privileges" in texto or "not authorized" in texto.lower():
        return "Só um administrador deste computador pode mudar esta conexão."
    if "Secrets were required" in texto or "secrets" in texto.lower():
        return "A rede pediu uma senha que não foi dada (ou está errada)."
    if "No network with SSID" in texto:
        return "Rede não encontrada. Confira o nome (as letras maiúsculas contam)."
    return padrao + (f" ({texto})" if texto else "")


def ler_dispositivos(rodar=None):
    codigo, saida, _ = nmcli("-t", "-f", "DEVICE,TYPE,STATE,CONNECTION,CON-UUID", "device", rodar=rodar)
    return interpretar_dispositivos(saida) if codigo == 0 else []


def ler_geral(rodar=None):
    codigo, saida, _ = nmcli("-t", "-f", "STATE,CONNECTIVITY,WIFI-HW,WIFI", "general", rodar=rodar)
    return interpretar_geral(saida) if codigo == 0 else {"estado": "", "conectividade": "unknown", "wifiHw": False, "wifi": False}


def verificar_conectividade(rodar=None):
    """Pede ao NetworkManager para testar a internet agora: full, portal, limited, none ou unknown."""
    codigo, saida, _ = nmcli("networking", "connectivity", "check", rodar=rodar, tempo=15)
    return saida.strip() if codigo == 0 and saida.strip() else "unknown"


def ler_detalhes(dispositivo, rodar=None):
    codigo, saida, _ = nmcli("-t", "-f", "GENERAL.HWADDR,GENERAL.MTU,GENERAL.METERED,CAPABILITIES.SPEED,"
                             "WIRED-PROPERTIES.CARRIER,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,IP6.ADDRESS,IP6.GATEWAY,IP6.DNS",
                             "device", "show", dispositivo, rodar=rodar)
    if codigo != 0:
        # Placas sem cabo (WIRED-PROPERTIES) ou Wi-Fi: alguns campos não existem; pede os gerais
        codigo, saida, _ = nmcli("-t", "-f", "GENERAL,IP4,IP6", "device", "show", dispositivo, rodar=rodar)
    return interpretar_detalhes(saida) if codigo == 0 else {}


def ler_conexoes(rodar=None):
    codigo, saida, _ = nmcli("-t", "-f", "NAME,UUID,TYPE,DEVICE,AUTOCONNECT,AUTOCONNECT-PRIORITY,ACTIVE",
                             "connection", "show", rodar=rodar)
    return interpretar_conexoes(saida) if codigo == 0 else []


def ler_conexao(uuid, rodar=None):
    codigo, saida, erro = nmcli("-t", "connection", "show", uuid, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não encontrei esta conexão."))
    return interpretar_conexao(saida)


def modificar(uuid, args, reativar=True, rodar=None):
    """Grava as mudanças e, se a conexão estiver em uso, reativa para valerem já."""
    if args:
        codigo, _, erro = nmcli("connection", "modify", uuid, *args, rodar=rodar)
        if codigo != 0:
            raise ErroDeRede(_erro(erro, "O NetworkManager não aceitou a configuração."))
    if reativar:
        codigo, _, erro = nmcli("connection", "up", uuid, rodar=rodar, tempo=45)
        if codigo != 0:
            raise ErroDeRede(_erro(erro, "A configuração foi gravada, mas a conexão não subiu."))


def aplicar(uuid, config, rodar=None):
    """Valida, guarda a configuração anterior (para voltar atrás) e aplica. Devolve os argumentos de volta."""
    erros = validar(config)
    if erros:
        raise ErroDeRede(" ".join(erros))
    anterior = ler_conexao(uuid, rodar=rodar)
    volta = argumentos({"tipo": anterior["tipo"], **{k: anterior[k] for k in config if k in anterior and k != "tipo"}})
    ativa = any(c["uuid"] == uuid and c["ativa"] for c in ler_conexoes(rodar=rodar))
    modificar(uuid, argumentos(config), reativar=ativa, rodar=rodar)
    return volta


def voltar(uuid, args_de_volta, rodar=None):
    ativa = any(c["uuid"] == uuid and c["ativa"] for c in ler_conexoes(rodar=rodar))
    modificar(uuid, args_de_volta, reativar=ativa, rodar=rodar)


def conectar_dispositivo(dispositivo, rodar=None):
    codigo, _, erro = nmcli("device", "connect", dispositivo, rodar=rodar, tempo=45)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível conectar."))


def desconectar_dispositivo(dispositivo, rodar=None):
    codigo, _, erro = nmcli("device", "disconnect", dispositivo, rodar=rodar, tempo=20)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível desconectar."))


def ativar(uuid, rodar=None, tempo=45):
    codigo, _, erro = nmcli("connection", "up", uuid, rodar=rodar, tempo=tempo)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível conectar."))


def desativar(uuid, rodar=None):
    codigo, _, erro = nmcli("connection", "down", uuid, rodar=rodar, tempo=20)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível desconectar."))


def esquecer(uuid, rodar=None):
    codigo, _, erro = nmcli("connection", "delete", uuid, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível esquecer esta conexão."))


def nova_conexao_cabo(dispositivo, nome, config=None, rodar=None):
    """Cria um perfil para o cabo (ex.: 'Escritório' com IP fixo) e devolve o UUID."""
    if not (nome or "").strip():
        raise ErroDeRede("Dê um nome à conexão.")
    config = config or {}
    erros = validar(config)
    if erros:
        raise ErroDeRede(" ".join(erros))
    args = ["connection", "add", "type", "ethernet", "con-name", nome.strip()]
    if dispositivo:
        args += ["ifname", dispositivo]
    args += argumentos({**config, "tipo": "cabo"})
    codigo, saida, erro = nmcli(*args, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a conexão."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    return m.group(1) if m else ""


def conectar_oculta(ssid, senha="", rodar=None):
    """Conecta a uma Wi-Fi que não anuncia o nome."""
    if not (ssid or "").strip():
        raise ErroDeRede("Escreva o nome da rede.")
    args = ["device", "wifi", "connect", ssid, "hidden", "yes"]
    entrada = None
    if senha:
        args = ["-a", *args]
        entrada = senha + "\n"
    codigo, _, erro = nmcli(*args, rodar=rodar, entrada=entrada, tempo=45)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, f"Não foi possível conectar a {ssid}."))


def senha_salva(uuid, rodar=None):
    """Senha da Wi-Fi guardada (o NetworkManager pede autorização pelo polkit)."""
    codigo, saida, erro = nmcli("-s", "-g", "802-11-wireless-security.psk", "connection", "show", uuid, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível ler a senha."))
    return saida.strip()


def redes_salvas_wifi(conexoes):
    return [c for c in conexoes if c["tipo"] == "wifi"]


# ------------------------------------------------------------------ vigia (Qt)

def criar_vigia(dono, ao_mudar, atraso_ms=400):
    """Roda o 'nmcli monitor' e chama ao_mudar() (uma vez por rajada de mudanças) na linha da interface.
    Se o monitor cair (NetworkManager reiniciou), tenta de novo em 5 s."""
    from PySide6.QtCore import QProcess, QTimer
    juntar = QTimer(dono, singleShot=True, interval=atraso_ms, timeout=ao_mudar)
    processo = QProcess(dono)
    processo.setProgram(NMCLI)
    processo.setArguments(["monitor"])
    vivo = [True]
    processo.destroyed.connect(lambda *_: vivo.__setitem__(0, False))

    def leu():
        if vivo[0]:
            processo.readAllStandardOutput()
            juntar.start()
    processo.readyReadStandardOutput.connect(leu)
    reiniciar = QTimer(dono, singleShot=True, interval=5000, timeout=lambda: vivo[0] and processo.start())
    processo.finished.connect(lambda *_: vivo[0] and reiniciar.start())
    processo.errorOccurred.connect(lambda *_: None)
    processo.start()
    return processo
