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
# Firewall (ADR 071): o tipo de rede escolhido pela pessoa → zona do firewalld (arquivos do duiaos-agente)
ZONAS = {"privada": "duiaos-privada", "publica": "duiaos-publica", "": ""}
TIPO_DA_ZONA = {"duiaos-privada": "privada", "duiaos-publica": "publica", "home": "privada", "work": "privada",
                "trusted": "privada", "internal": "privada", "public": "publica", "external": "publica", "drop": "publica",
                "block": "publica", "dmz": "publica"}
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
        "zona": TIPO_DA_ZONA.get(c.get("connection.zone", ""), ""),
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
    if "zona" in config:
        args += ["connection.zone", ZONAS.get(config["zona"], "")]
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


# ------------------------------------------------------------------ VPN (Fase 2, ADR 070)

def _nome_de_interface(nome):
    """Nome de placa válido (até 15 letras, sem espaço) a partir do nome da conexão: 'Trabalho SP' → 'wg-trabalho-sp'."""
    import unicodedata
    base = "".join(c for c in unicodedata.normalize("NFD", nome.lower()) if not unicodedata.combining(c))
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "vpn"
    return ("wg-" + base)[:15].rstrip("-")


def importar_vpn(caminho, rodar=None):
    """Importa o arquivo que o provedor entrega: .conf (WireGuard) ou .ovpn (OpenVPN). Devolve o nome da conexão."""
    import os
    import shutil
    import tempfile
    caminho = str(caminho)
    extensao = os.path.splitext(caminho)[1].lower()
    if extensao == ".ovpn":
        tipo, arquivo = "openvpn", caminho
    elif extensao == ".conf":
        # O NetworkManager usa o nome do arquivo como nome da placa (até 15 letras, sem espaços)
        tipo = "wireguard"
        pasta = tempfile.mkdtemp(prefix="duiaos-vpn-")
        arquivo = os.path.join(pasta, _nome_de_interface(os.path.splitext(os.path.basename(caminho))[0]) + ".conf")
        shutil.copyfile(caminho, arquivo)
    else:
        raise ErroDeRede("Escolha um arquivo .conf (WireGuard) ou .ovpn (OpenVPN).")
    codigo, saida, erro = nmcli("connection", "import", "type", tipo, "file", arquivo, rodar=rodar)
    if codigo != 0:
        if tipo == "openvpn" and "unknown VPN plugin" in (erro or "") + (saida or ""):
            raise ErroDeRede("Falta o suporte a OpenVPN (pacote network-manager-openvpn).")
        raise ErroDeRede(_erro(erro, "O arquivo de VPN não foi aceito."))
    m = re.search(r"Connection '(.+)' \(([0-9a-f-]{36})\)", saida)
    return m.group(1) if m else os.path.splitext(os.path.basename(arquivo))[0]


def gerar_chaves_wireguard():
    """Par de chaves do WireGuard (X25519, em base64): (privada, pública)."""
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    privada = X25519PrivateKey.generate()
    bruta = privada.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    publica = privada.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(bruta).decode(), base64.b64encode(publica).decode()


def _chave_wireguard(texto, nome):
    import base64
    try:
        if len(base64.b64decode(texto.strip(), validate=True)) == 32:
            return texto.strip()
    except ValueError:
        pass
    raise ErroDeRede(f"{nome} do WireGuard inválida (são 44 letras terminando em =).")


def configuracao_wireguard(endereco, chave_privada, chave_servidor, servidor, permitidos="0.0.0.0/0, ::/0", dns="",
                           chave_compartilhada=""):
    """Texto do arquivo .conf do WireGuard (o formato que os provedores entregam), conferido."""
    erros = []
    for item in _lista(endereco):
        try:
            ipaddress.ip_interface(item)
        except ValueError:
            erros.append(f"Endereço da VPN inválido: {item} (ex.: 10.0.0.2/32).")
    if not _lista(endereco):
        erros.append("Falta o endereço da VPN (ex.: 10.0.0.2/32).")
    if not re.match(r"^[\w.\-\[\]:]+:\d{1,5}$", (servidor or "").strip()):
        erros.append("Servidor no formato endereço:porta (ex.: vpn.exemplo.com:51820).")
    for item in _lista(dns):
        try:
            ipaddress.ip_address(item)
        except ValueError:
            erros.append(f"Servidor DNS inválido: {item}.")
    if erros:
        raise ErroDeRede(" ".join(erros))
    linhas = ["[Interface]", f"PrivateKey = {_chave_wireguard(chave_privada, 'Chave privada')}", f"Address = {', '.join(_lista(endereco))}"]
    if _lista(dns):
        linhas.append(f"DNS = {', '.join(_lista(dns))}")
    linhas += ["", "[Peer]", f"PublicKey = {_chave_wireguard(chave_servidor, 'Chave do servidor')}", f"Endpoint = {servidor.strip()}",
               f"AllowedIPs = {', '.join(_lista(permitidos)) or '0.0.0.0/0, ::/0'}", "PersistentKeepalive = 25"]
    if chave_compartilhada.strip():
        linhas.append(f"PresharedKey = {_chave_wireguard(chave_compartilhada, 'Chave compartilhada')}")
    return "\n".join(linhas) + "\n"


def nova_wireguard(nome, configuracao_texto, rodar=None):
    """Cria a VPN WireGuard a partir do texto do .conf (configuracao_wireguard). Devolve o nome."""
    import os
    import tempfile
    pasta = tempfile.mkdtemp(prefix="duiaos-vpn-")
    arquivo = os.path.join(pasta, _nome_de_interface(nome) + ".conf")
    with open(arquivo, "w", encoding="utf-8") as saida:
        saida.write(configuracao_texto)
    os.chmod(arquivo, 0o600)
    try:
        importado = importar_vpn(arquivo, rodar=rodar)
        if nome and importado != nome:
            nmcli("connection", "modify", importado, "connection.id", nome, rodar=rodar)
        return nome or importado
    finally:
        os.unlink(arquivo)
        os.rmdir(pasta)


PROTOCOLOS_OPENCONNECT = {"anyconnect": "Cisco AnyConnect", "gp": "Palo Alto GlobalProtect", "fortinet": "Fortinet",
                          "nc": "Juniper / Pulse Secure", "pulse": "Ivanti Connect Secure"}


def nova_openconnect(nome, servidor, protocolo="anyconnect", rodar=None):
    """VPN de empresa pelo OpenConnect: o login (usuário e senha) é pedido ao conectar."""
    if not (nome or "").strip() or not (servidor or "").strip():
        raise ErroDeRede("Dê um nome e o endereço do servidor da VPN.")
    if protocolo not in PROTOCOLOS_OPENCONNECT:
        raise ErroDeRede("Escolha o tipo de VPN da empresa.")
    codigo, _, erro = nmcli("connection", "add", "type", "vpn", "con-name", nome.strip(), "vpn-type", "openconnect",
                            "vpn.data", f"gateway={servidor.strip()},protocol={protocolo},cookie-flags=2,gateway-flags=2,gwcert-flags=2",
                            "connection.autoconnect", "no", rodar=rodar)
    if codigo != 0:
        if "openconnect" in (erro or "").lower() and "plugin" in (erro or "").lower():
            raise ErroDeRede("Falta o suporte a VPN de empresa (pacote network-manager-openconnect).")
        raise ErroDeRede(_erro(erro, "Não foi possível criar a VPN."))


# ------------------------------------------------------------------ Wi-Fi corporativo (802.1X)

METODOS_EAP = {"peap": "PEAP", "ttls": "TTLS", "tls": "TLS (certificado)"}


def conectar_empresa(ssid, metodo="peap", usuario="", senha="", interna="mschapv2", identidade_anonima="",
                     certificado_ca="", dominio="", certificado="", chave="", senha_chave="", sem_verificar=False, rodar=None):
    """Wi-Fi corporativo ou da faculdade (WPA2/WPA3-Enterprise, ex.: eduroam). Cria a conexão e conecta."""
    if not ssid or metodo not in METODOS_EAP:
        raise ErroDeRede("Escolha a rede e o método de autenticação.")
    if not usuario:
        raise ErroDeRede("Falta o usuário (ex.: nome@faculdade.edu.br).")
    if metodo != "tls" and not senha:
        raise ErroDeRede("Falta a senha.")
    if metodo == "tls" and not (certificado and chave):
        raise ErroDeRede("Escolha o seu certificado e a chave.")
    if not certificado_ca and not sem_verificar:
        raise ErroDeRede("Escolha o certificado da instituição (CA) ou marque que não quer verificar.")
    args = ["connection", "add", "type", "wifi", "con-name", ssid, "ssid", ssid, "wifi-sec.key-mgmt", "wpa-eap",
            "802-1x.eap", metodo, "802-1x.identity", usuario]
    if metodo in ("peap", "ttls"):
        args += ["802-1x.phase2-auth", interna or "mschapv2", "802-1x.password", senha]
    if identidade_anonima:
        args += ["802-1x.anonymous-identity", identidade_anonima]
    if certificado_ca:
        args += ["802-1x.ca-cert", certificado_ca]
    if dominio:
        args += ["802-1x.domain-suffix-match", dominio]
    if metodo == "tls":
        args += ["802-1x.client-cert", certificado, "802-1x.private-key", chave, "802-1x.private-key-password", senha_chave]
    codigo, saida, erro = nmcli(*args, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a conexão."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    if m:
        ativar(m.group(1), rodar=rodar, tempo=60)


# ------------------------------------------------------------------ compartilhar a internet

NOME_PONTO_DE_ACESSO = "Ponto de acesso do DuiaOS"


def ligar_ponto_de_acesso(dispositivo, nome, senha, rodar=None):
    """Transforma a Wi-Fi do computador numa rede para outros aparelhos (o NetworkManager faz o roteamento)."""
    if not (nome or "").strip():
        raise ErroDeRede("Dê um nome à rede.")
    if len(senha or "") < 8:
        raise ErroDeRede("A senha precisa ter pelo menos 8 letras ou números.")
    args = ["device", "wifi", "hotspot", "con-name", NOME_PONTO_DE_ACESSO, "ssid", nome.strip(), "password", senha]
    if dispositivo:
        args[3:3] = ["ifname", dispositivo]
    codigo, _, erro = nmcli(*args, rodar=rodar, tempo=30)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível ligar o ponto de acesso (a placa Wi-Fi precisa aceitar esse modo)."))


def desligar_ponto_de_acesso(rodar=None):
    nmcli("connection", "down", NOME_PONTO_DE_ACESSO, rodar=rodar, tempo=20)


def texto_qr_wifi(ssid, senha, seguranca="WPA"):
    """O texto do QR code de Wi-Fi que os celulares entendem: WIFI:T:WPA;S:nome;P:senha;;"""
    def escapar(t):
        return re.sub(r'([\;,:"])', r"\\\1", t or "")
    tipo = "nopass" if not senha else ("WEP" if seguranca == "none" else "WPA")
    return f"WIFI:T:{tipo};S:{escapar(ssid)};" + (f"P:{escapar(senha)};" if senha else "") + ";"


def gerar_qr(texto, destino, rodar=None):
    """Imagem PNG do QR code (pelo qrencode). Devolve o caminho."""
    rodar = rodar or (lambda c: subprocess.run(c, capture_output=True, timeout=10, check=False))
    try:
        r = rodar(["qrencode", "-t", "PNG", "-s", "8", "-m", "2", "-o", str(destino), texto])
    except FileNotFoundError:
        raise ErroDeRede("Falta o qrencode para gerar o código.")
    if getattr(r, "returncode", 1) != 0:
        raise ErroDeRede("Não foi possível gerar o código.")
    return str(destino)


# ================================================================== Fase 3 (ADR 071)

# ------------------------------------------------------------------ firewall e tipo de rede

FIREWALL_CMD = ["firewall-cmd"]


def interpretar_firewall(estado, padrao, ssh):
    """Saídas do firewall-cmd (--state, --get-default-zone, --query-service=ssh) → o que a página mostra."""
    return {"instalado": estado != "ausente", "ligado": estado.strip() == "running",
            "padrao": padrao.strip(), "ssh": ssh.strip() == "yes"}


def ler_firewall(rodar=None):
    """Estado do firewall lido como a pessoa (o firewalld libera a leitura sem senha)."""
    rodar = rodar or _rodar

    def cmd(*args):
        codigo, saida, _ = rodar([*FIREWALL_CMD, *args], tempo=5)
        return codigo, saida
    codigo, estado = cmd("--state")
    if codigo == 127:
        return interpretar_firewall("ausente", "", "")
    if estado.strip() != "running":
        return interpretar_firewall("not running", "", "")
    _, padrao = cmd("--get-default-zone")
    _, ssh = cmd("--permanent", f"--zone={ZONAS['privada']}", "--query-service=ssh")
    return interpretar_firewall(estado, padrao, ssh)


def definir_tipo_de_rede(uuid, tipo, rodar=None):
    """Privada (casa, trabalho: o computador aparece para os outros e aceita o acesso remoto, se ligado) ou
    pública (café, aeroporto: não aceita nenhuma conexão de fora). Vale na hora, sem derrubar a conexão."""
    if tipo not in ("privada", "publica"):
        raise ErroDeRede("Escolha rede privada ou pública.")
    codigo, _, erro = nmcli("connection", "modify", uuid, "connection.zone", ZONAS[tipo], rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível mudar o tipo de rede."))
    dispositivo = next((c["dispositivo"] for c in ler_conexoes(rodar=rodar) if c["uuid"] == uuid and c["ativa"]), "")
    if dispositivo:
        codigo, _, _ = nmcli("device", "reapply", dispositivo, rodar=rodar, tempo=20)
        if codigo != 0:                        # algumas placas não aceitam reaplicar: reativa
            ativar(uuid, rodar=rodar)


def sem_tipo_de_rede(conexoes, zonas):
    """Conexões ativas de cabo, Wi-Fi ou celular sem tipo de rede escolhido (para a pergunta da Barra)."""
    return [c for c in conexoes if c["ativa"] and c["tipo"] in ("cabo", "wifi", "celular", "bluetooth")
            and not zonas.get(c["uuid"])]


def ler_zonas(conexoes, rodar=None):
    """{uuid: tipo de rede} das conexões ativas."""
    zonas = {}
    for c in conexoes:
        if c["ativa"]:
            codigo, saida, _ = nmcli("-t", "-g", "connection.zone", "connection", "show", c["uuid"], rodar=rodar)
            zonas[c["uuid"]] = TIPO_DA_ZONA.get(saida.strip(), "") if codigo == 0 else ""
    return zonas


# ------------------------------------------------------------------ celular (USB, Bluetooth, modem)

DRIVERS_DE_CELULAR = {"rndis_host": "Android", "cdc_ncm": "Android", "cdc_ether": "Celular", "ipheth": "iPhone"}


def celular_por_usb(dispositivo, pasta="/sys/class/net"):
    """'Android'/'iPhone'/'Celular' se a placa é um celular compartilhando a internet pelo cabo USB, senão ''."""
    import os
    try:
        driver = os.path.basename(os.readlink(f"{pasta}/{dispositivo}/device/driver"))
    except OSError:
        return ""
    return DRIVERS_DE_CELULAR.get(driver, "")


def conectar_celular_bluetooth(endereco, nome="", rodar=None):
    """Internet do celular pelo Bluetooth (PAN: o 'Ponto de acesso Bluetooth' do Android/iPhone). O celular
    precisa estar pareado (Configurações › Bluetooth). Devolve o UUID."""
    if not re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", endereco or ""):
        raise ErroDeRede("Endereço Bluetooth inválido.")
    codigo, saida, erro = nmcli("connection", "add", "type", "bluetooth", "con-name", (nome or "Celular") + " (Bluetooth)",
                                "bluetooth.bdaddr", endereco.upper(), "bluetooth.type", "panu", rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a conexão pelo Bluetooth."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    uuid = m.group(1) if m else ""
    if uuid:
        ativar(uuid, rodar=rodar)
    return uuid


# APN das operadoras do Brasil (usuário e senha quando a operadora pede)
OPERADORAS = {
    "Vivo": {"apn": "zap.vivo.com.br", "usuario": "vivo", "senha": "vivo"},
    "Claro": {"apn": "claro.com.br", "usuario": "claro", "senha": "claro"},
    "TIM": {"apn": "timbrasil.br", "usuario": "tim", "senha": "tim"},
    "Oi": {"apn": "gprs.oi.com.br", "usuario": "oi", "senha": "oi"},
}


def nova_celular(nome, apn, usuario="", senha="", pin="", rodar=None):
    """Modem 4G/5G (pelo ModemManager): cria a conexão com o APN da operadora e conecta. Devolve o UUID."""
    apn = (apn or "").strip()
    if not apn or not re.match(r"^[A-Za-z0-9.\-]{1,100}$", apn):
        raise ErroDeRede("Informe o APN da operadora (ex.: zap.vivo.com.br).")
    if pin and not re.match(r"^\d{4,8}$", pin):
        raise ErroDeRede("O PIN tem de 4 a 8 números.")
    args = ["connection", "add", "type", "gsm", "ifname", "*", "con-name", (nome or "Rede celular").strip(), "gsm.apn", apn]
    if usuario:
        args += ["gsm.username", usuario]
    if senha:
        args += ["gsm.password", senha]
    if pin:
        args += ["gsm.pin", pin]
    codigo, saida, erro = nmcli(*args, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a conexão celular."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    return m.group(1) if m else ""


def interpretar_modem(texto):
    """'mmcli -m N -K' → {operadora, sinal, tecnologia, estado} (só o que a página mostra)."""
    c = {}
    for linha in texto.splitlines():
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            c[chave.strip()] = valor.strip()
    try:
        sinal = int(c.get("modem.generic.signal-quality.value", "0"))
    except ValueError:
        sinal = 0
    tecnologia = c.get("modem.generic.access-technologies.value[1]", "") or c.get("modem.generic.access-technologies.value", "")
    return {"operadora": c.get("modem.3gpp.operator-name", "--").replace("--", ""), "sinal": sinal,
            "tecnologia": {"lte": "4G", "5gnr": "5G", "umts": "3G", "hsdpa": "3G", "hspa": "3G", "edge": "2G", "gsm": "2G"}.get(tecnologia, tecnologia.upper()),
            "estado": c.get("modem.generic.state", ""), "bloqueado": c.get("modem.generic.unlock-required", "--") not in ("--", "sim-pin2", "")}


def ler_modens(rodar=None):
    """Modens do ModemManager (mmcli), com operadora e sinal. Sem ModemManager, lista vazia."""
    rodar = rodar or _rodar
    codigo, saida, _ = rodar(["mmcli", "-L", "-K"], tempo=5)
    if codigo != 0:
        return []
    modens = []
    for caminho in re.findall(r"/org/freedesktop/ModemManager1/Modem/(\d+)", saida):
        c2, info, _ = rodar(["mmcli", "-m", caminho, "-K"], tempo=5)
        if c2 == 0:
            modens.append({"numero": caminho, **interpretar_modem(info)})
    return modens


# ------------------------------------------------------------------ avançado: VLAN, ponte, agregação

MODOS_DE_AGREGACAO = {"active-backup": "Reserva (uma placa por vez)", "802.3ad": "LACP (802.3ad, precisa do switch)",
                      "balance-rr": "Alternar (todas juntas)", "balance-alb": "Equilibrar (sem configurar o switch)"}


def _nome_de_placa(nome, padrao):
    limpo = re.sub(r"[^a-z0-9]", "", (nome or "").lower())[:12]
    return limpo or padrao


def nova_vlan(placa, numero, nome="", rodar=None):
    """VLAN (rede virtual com etiqueta 802.1Q) sobre uma placa. Devolve o UUID."""
    try:
        numero = int(numero)
    except (TypeError, ValueError):
        numero = 0
    if not 1 <= numero <= 4094:
        raise ErroDeRede("O número da VLAN vai de 1 a 4094.")
    if not placa:
        raise ErroDeRede("Escolha a placa da VLAN.")
    interface = f"{placa[:10]}.{numero}"[:15]
    codigo, saida, erro = nmcli("connection", "add", "type", "vlan", "con-name", nome or f"VLAN {numero}", "ifname", interface,
                                "vlan.parent", placa, "vlan.id", str(numero), rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a VLAN."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    return m.group(1) if m else ""


def _nova_com_membros(tipo, nome, placas, extras, rodar):
    if not placas:
        raise ErroDeRede("Escolha ao menos uma placa.")
    interface = _nome_de_placa(nome, "br0" if tipo == "bridge" else "bond0")
    codigo, saida, erro = nmcli("connection", "add", "type", tipo, "con-name", nome, "ifname", interface, *extras, rodar=rodar)
    if codigo != 0:
        raise ErroDeRede(_erro(erro, "Não foi possível criar a conexão."))
    m = re.search(r"\(([0-9a-f-]{36})\)", saida)
    uuid = m.group(1) if m else ""
    porta = "bridge" if tipo == "bridge" else "bond"
    for placa in placas:
        codigo, _, erro = nmcli("connection", "add", "type", "ethernet", "con-name", f"{nome} · {placa}", "ifname", placa,
                                "connection.port-type", porta, "connection.controller", interface, rodar=rodar)
        if codigo != 0:
            raise ErroDeRede(_erro(erro, f"Não foi possível pôr {placa} em {nome}."))
    return uuid


def nova_ponte(nome, placas, rodar=None):
    """Ponte (bridge): junta placas numa só rede, como um switch (máquinas virtuais na rede da casa). Devolve o UUID."""
    if not (nome or "").strip():
        raise ErroDeRede("Dê um nome à ponte.")
    return _nova_com_membros("bridge", nome.strip(), list(placas), ["bridge.stp", "no"], rodar)


def nova_agregacao(nome, placas, modo="active-backup", rodar=None):
    """Agregação (bond): duas ou mais placas como uma (reserva ou mais velocidade). Devolve o UUID."""
    if not (nome or "").strip():
        raise ErroDeRede("Dê um nome à agregação.")
    if modo not in MODOS_DE_AGREGACAO:
        raise ErroDeRede("Modo de agregação desconhecido.")
    return _nova_com_membros("bond", nome.strip(), list(placas), ["bond.options", f"mode={modo},miimon=100"], rodar)


def apagar_com_membros(uuid, rodar=None):
    """Apaga uma ponte ou agregação e as placas que estavam nela (que voltam ao normal)."""
    codigo, saida, _ = nmcli("-t", "-g", "connection.interface-name", "connection", "show", uuid, rodar=rodar)
    interface = saida.strip() if codigo == 0 else ""
    if interface:
        codigo, lista, _ = nmcli("-t", "-f", "UUID", "connection", "show", rodar=rodar)
        for outro in lista.split():
            c2, controlador, _ = nmcli("-t", "-g", "connection.controller", "connection", "show", outro, rodar=rodar)
            if c2 == 0 and controlador.strip() == interface:
                nmcli("connection", "delete", outro, rodar=rodar)
    esquecer(uuid, rodar=rodar)


# ------------------------------------------------------------------ diagnóstico

def _passo(nome, ok, explicacao, dica=""):
    return {"nome": nome, "ok": bool(ok), "explicacao": explicacao, "dica": "" if ok else dica}


def diagnosticar(rodar=None, resolver=None, pingar=None):
    """Confere a rede do começo ao fim e explica em português onde parou: placa, endereço, roteador, nomes
    (DNS) e internet. Para no primeiro passo que falhar (os seguintes dependem dele)."""
    import socket
    rodar = rodar or _rodar
    resolver = resolver or (lambda nome: socket.getaddrinfo(nome, 443, proto=socket.IPPROTO_TCP))
    pingar = pingar or (lambda ip: rodar(["ping", "-c", "1", "-W", "2", ip], tempo=5)[0] == 0)
    passos = []
    dispositivos = ler_dispositivos(rodar=rodar)
    conectados = [d for d in dispositivos if d["estado"] == "conectado" and d["tipo"] != "vpn"]
    if not dispositivos:
        passos.append(_passo("Placa de rede", False, "Nenhuma placa de rede foi encontrada.",
                             "Numa máquina virtual, confira se ela tem uma placa de rede; num computador, se o Wi-Fi não está desligado por uma tecla."))
        return passos
    if not conectados:
        cabo_solto = any(d["tipo"] == "cabo" and d["estado"] == "indisponivel" for d in dispositivos)
        passos.append(_passo("Conexão", False, "O computador não está conectado a nenhuma rede.",
                             "Confira se o cabo está bem encaixado nas duas pontas." if cabo_solto else "Escolha uma Wi-Fi ou ligue o cabo de rede."))
        return passos
    principal = conectados[0]
    passos.append(_passo("Conexão", True, f"Conectado: {principal['conexao']} ({NOMES_TIPO.get(principal['tipo'], principal['tipo'])})."))
    detalhes = ler_detalhes(principal["dispositivo"], rodar=rodar)
    ipv4 = [e for e in detalhes.get("ipv4", []) if not e.startswith("169.254.")]
    if not ipv4 and not detalhes.get("ipv6"):
        passos.append(_passo("Endereço", False, "O roteador não deu um endereço (IP) ao computador.",
                             "Desligue e ligue o roteador, ou ponha um endereço fixo em Detalhes › Endereço."))
        return passos
    passos.append(_passo("Endereço", True, "O computador tem o endereço " + (ipv4[0].split("/")[0] if ipv4 else detalhes["ipv6"][0].split("/")[0]) + "."))
    gateway = detalhes.get("gateway4") or detalhes.get("gateway6") or ""
    if not gateway:
        passos.append(_passo("Roteador", False, "A rede não informou o roteador (gateway), então não há caminho para a internet.",
                             "Se o endereço é fixo, preencha o gateway em Detalhes › Endereço."))
        return passos
    if pingar(gateway):
        passos.append(_passo("Roteador", True, f"O roteador ({gateway}) responde."))
    else:
        passos.append(_passo("Roteador", True, f"O roteador ({gateway}) não respondeu ao teste, mas muitos roteadores ignoram esse teste; seguindo."))
    try:
        resolver("deb.debian.org")
        passos.append(_passo("Nomes (DNS)", True, "Os nomes de sites são traduzidos em endereços."))
    except OSError:
        passos.append(_passo("Nomes (DNS)", False, "Os nomes de sites não estão sendo traduzidos (o DNS não responde).",
                             "Em Detalhes › DNS, escolha Cloudflare ou Google e salve."))
        return passos
    conectividade = verificar_conectividade(rodar=rodar)
    if conectividade == "full":
        passos.append(_passo("Internet", True, "A internet está funcionando."))
    elif conectividade == "portal":
        passos.append(_passo("Internet", False, "Esta rede pede login numa página antes de liberar a internet.",
                             "Use o botão Fazer login na rede, no topo da página."))
    else:
        passos.append(_passo("Internet", False, "A rede local funciona, mas a internet não chega.",
                             "O problema deve estar no roteador ou na operadora: reinicie o roteador e, se continuar, ligue para a operadora."))
    return passos
