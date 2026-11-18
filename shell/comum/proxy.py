"""DuiaOS — proxy da internet (Configurações › Rede e Internet › Proxy; ADR 070).

Três modos, como no GNOME, no macOS e no Windows: Desligado, Manual (HTTP, HTTPS e SOCKS, com exceções) e
Automático (endereço de configuração PAC). Gravado onde cada tipo de programa lê:
- as chaves org.gnome.system.proxy (gsettings): Firefox e Chrome com "proxy do sistema", programas GTK e
  o Flatpak — valem na hora;
- as variáveis http_proxy, https_proxy, all_proxy e no_proxy (terminal, Python, git, curl): num arquivo do
  DuiaOS que o abridor de programas (aplicativos.iniciar) acrescenta a cada programa aberto pela Ilha, pela
  Central e pelo Explorador, e em ~/.config/environment.d (serviços do usuário);
- o apt do sistema, pelo duiaos-agente (ConfigurarProxy, com autorização): só o modo Manual com HTTP.

O modo Automático (PAC) não tem variável equivalente: só os programas que leem as chaves do sistema o usam.
"""
import ipaddress
import os
import re
import subprocess
from pathlib import Path

ESQUEMA = "org.gnome.system.proxy"
EXCECOES_PADRAO = ["localhost", "127.0.0.0/8", "::1"]


def _config():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def arquivo_ambiente():
    return _config() / "duiaos" / "proxy.env"


def _rodar(comando):
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=5, check=False)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def _gsettings_valor(texto):
    """Saída do 'gsettings get' → valor Python: 'manual' → manual, 8080 → 8080, ['a', 'b'] → lista."""
    texto = texto.strip()
    if texto.startswith("@as "):
        texto = texto[4:]
    if texto.startswith("["):
        return re.findall(r"'((?:[^'\\]|\\.)*)'", texto)
    if texto.startswith("'") and texto.endswith("'"):
        return texto[1:-1]
    try:
        return int(texto)
    except ValueError:
        return texto


def ler(rodar=None):
    rodar = rodar or _rodar

    def obter(esquema, chave, padrao):
        codigo, saida = rodar(["gsettings", "get", esquema, chave])
        return _gsettings_valor(saida) if codigo == 0 and saida else padrao
    modo = obter(ESQUEMA, "mode", "none")
    config = {"modo": {"none": "desligado", "manual": "manual", "auto": "automatico"}.get(modo, "desligado"),
              "pac": obter(ESQUEMA, "autoconfig-url", ""), "excecoes": obter(ESQUEMA, "ignore-hosts", EXCECOES_PADRAO)}
    for tipo in ("http", "https", "socks"):
        config[tipo] = {"servidor": obter(f"{ESQUEMA}.{tipo}", "host", ""), "porta": obter(f"{ESQUEMA}.{tipo}", "port", 0)}
    return config


def validar(config):
    erros = []
    if config.get("modo") == "automatico":
        if not re.match(r"^(https?|file)://\S+$", config.get("pac", "") or ""):
            erros.append("Endereço de configuração automática inválido (ex.: http://proxy.empresa/proxy.pac).")
    if config.get("modo") == "manual":
        algum = False
        for tipo, nome in (("http", "HTTP"), ("https", "HTTPS"), ("socks", "SOCKS")):
            servidor = (config.get(tipo, {}).get("servidor") or "").strip()
            if not servidor:
                continue
            algum = True
            if not re.match(r"^[A-Za-z0-9.\-\[\]:]+$", servidor):
                erros.append(f"Servidor {nome} inválido: {servidor}.")
            try:
                porta = int(config.get(tipo, {}).get("porta") or 0)
            except (TypeError, ValueError):
                porta = 0
            if not 0 < porta < 65536:
                erros.append(f"Porta do proxy {nome} precisa ser um número de 1 a 65535.")
        if not algum:
            erros.append("Preencha pelo menos um servidor de proxy (ex.: HTTP).")
    return erros


def ambiente(config):
    """Variáveis de ambiente do modo Manual (vazias nos outros modos)."""
    if config.get("modo") != "manual":
        return {}
    variaveis = {}

    def url(tipo, esquema):
        dados = config.get(tipo, {})
        servidor = (dados.get("servidor") or "").strip()
        return f"{esquema}://{servidor}:{int(dados.get('porta') or 0)}/" if servidor else ""
    http, https, socks = url("http", "http"), url("https", "http"), url("socks", "socks5")
    if http:
        variaveis["http_proxy"] = http
    if https or http:
        variaveis["https_proxy"] = https or http
    if socks:
        variaveis["all_proxy"] = socks
    excecoes = ",".join(config.get("excecoes") or EXCECOES_PADRAO)
    if variaveis:
        variaveis["no_proxy"] = excecoes
        variaveis.update({k.upper(): v for k, v in list(variaveis.items())})
    return variaveis


def gravar(config, rodar=None):
    """Grava nas chaves do sistema e nos arquivos de ambiente. ValueError com a mensagem se algo estiver errado."""
    erros = validar(config)
    if erros:
        raise ValueError(" ".join(erros))
    rodar = rodar or _rodar
    modo = {"desligado": "none", "manual": "manual", "automatico": "auto"}[config.get("modo", "desligado")]
    comandos = [["gsettings", "set", ESQUEMA, "mode", modo]]
    if modo == "auto":
        comandos.append(["gsettings", "set", ESQUEMA, "autoconfig-url", config.get("pac", "")])
    if modo == "manual":
        for tipo in ("http", "https", "socks"):
            dados = config.get(tipo, {})
            comandos.append(["gsettings", "set", f"{ESQUEMA}.{tipo}", "host", (dados.get("servidor") or "").strip()])
            comandos.append(["gsettings", "set", f"{ESQUEMA}.{tipo}", "port", str(int(dados.get("porta") or 0))])
        excecoes = config.get("excecoes") or EXCECOES_PADRAO
        comandos.append(["gsettings", "set", ESQUEMA, "ignore-hosts", "[" + ", ".join(f"'{e}'" for e in excecoes) + "]"])
    for comando in comandos:
        rodar(comando)
    variaveis = ambiente(config)
    texto = "".join(f"{k}={v}\n" for k, v in sorted(variaveis.items()))
    for destino in (arquivo_ambiente(), _config() / "environment.d" / "90-duiaos-proxy.conf"):
        destino.parent.mkdir(parents=True, exist_ok=True)
        if texto:
            destino.write_text("# DuiaOS — proxy (Configurações › Rede e Internet). Não edite: é refeito pela tela.\n" + texto)
        else:
            destino.unlink(missing_ok=True)
    return variaveis


def ambiente_salvo(arquivo=None):
    """Variáveis gravadas pela tela (para o abridor de programas). {} se o proxy está desligado."""
    arquivo = Path(arquivo or arquivo_ambiente())
    variaveis = {}
    try:
        for linha in arquivo.read_text().splitlines():
            if "=" in linha and not linha.startswith("#"):
                chave, valor = linha.split("=", 1)
                if re.match(r"^(https?|all|no|HTTPS?|ALL|NO)_(proxy|PROXY)$", chave):
                    variaveis[chave] = valor
    except OSError:
        pass
    return variaveis


def configuracao_apt(config):
    """Texto do /etc/apt/apt.conf.d/95duiaos-proxy (só o proxy HTTP do modo Manual), ou "" para tirar."""
    if config.get("modo") != "manual":
        return ""
    http = config.get("http", {})
    servidor = (http.get("servidor") or "").strip()
    if not servidor:
        return ""
    try:
        porta = int(http.get("porta") or 0)
    except (TypeError, ValueError):
        return ""
    if not re.match(r"^[A-Za-z0-9.\-]+$", servidor) and not _eh_ip(servidor):
        return ""
    return (f'Acquire::http::Proxy "http://{servidor}:{porta}/";\n'
            f'Acquire::https::Proxy "http://{servidor}:{porta}/";\n')


def _eh_ip(texto):
    try:
        ipaddress.ip_address(texto.strip("[]"))
        return True
    except ValueError:
        return False
