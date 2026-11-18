"""DuiaOS — Mail Box: descobre os servidores de uma conta a partir do endereço de e-mail.

Cascata (para no primeiro acerto):
  1. catálogo próprio (provedores.py), pelo domínio do endereço
  2. registros MX do domínio (domínios próprios no Google Workspace, Microsoft 365, Zoho...)
  3. ISPDB do Thunderbird (autoconfig.thunderbird.net; dados MPL-2.0, só consultados)
  4. autoconfig do próprio domínio (autoconfig.DOMINIO e /.well-known/autoconfig)
  5. registros SRV (RFC 6186: _imaps, _imap, _submissions, _submission, _pop3s)
  6. tentativa nos nomes comuns (imap.DOMINIO, mail.DOMINIO) e portas comuns
Sem resultado: o wizard abre a configuração manual.

Rede com tempo curto: cada consulta desiste em poucos segundos.
"""
import socket
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import quote

import provedores

TEMPO = 6
ISPDB = "https://autoconfig.thunderbird.net/v1.1/"


def _baixar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "DuiaOS-MailBox/0.1"})
    with urllib.request.urlopen(pedido, timeout=TEMPO) as resposta:          # noqa: S310 — só https fixos
        return resposta.read(512 * 1024)


def _consultar_dns(nome, tipo):
    try:
        import dns.resolver
    except ImportError:
        return []
    try:
        respostas = dns.resolver.resolve(nome, tipo, lifetime=TEMPO)
    except Exception:  # noqa: BLE001 — NXDOMAIN, sem resposta, tempo esgotado: tudo é "não achou"
        return []
    return list(respostas)


def mx(dominio):
    return [str(r.exchange).rstrip(".") for r in sorted(_consultar_dns(dominio, "MX"), key=lambda r: r.preference)]


def ler_xml_autoconfig(conteudo, email):
    """Lê o formato clientConfig (ISPDB e autoconfig dos domínios)."""
    raiz = ET.fromstring(conteudo)
    provedor = raiz.find("emailProvider")
    if provedor is None:
        return None
    local, _, dominio = email.partition("@")

    def trocar(texto):
        return (texto or "").replace("%EMAILADDRESS%", email).replace("%EMAILLOCALPART%", local) \
            .replace("%EMAILDOMAIN%", dominio)

    def servidor(no):
        tipo = no.get("type")
        socket_tipo = (no.findtext("socketType") or "").upper()
        seguranca = {"SSL": "ssl", "STARTTLS": "starttls", "PLAIN": "nenhuma"}.get(socket_tipo, "ssl")
        autenticacao = [a.text for a in no.findall("authentication")]
        return {"tipo": tipo, "host": trocar(no.findtext("hostname")), "porta": int(no.findtext("port") or 0),
                "seguranca": seguranca, "usuario": trocar(no.findtext("username")) or email,
                "oauth": "OAuth2" in autenticacao}

    def melhor(nos):
        # SSL > STARTTLS > sem criptografia (nunca escolhida se houver outra)
        ordem = {"ssl": 0, "starttls": 1, "nenhuma": 9}
        candidatos = sorted((servidor(n) for n in nos), key=lambda s: ordem[s["seguranca"]])
        return candidatos[0] if candidatos else None

    entrada = melhor([n for n in provedor.findall("incomingServer") if n.get("type") == "imap"]) or \
        melhor([n for n in provedor.findall("incomingServer") if n.get("type") == "pop3"])
    saida = melhor(provedor.findall("outgoingServer"))
    if not entrada or not saida or not entrada["host"] or not saida["host"]:
        return None
    oauth = entrada.pop("oauth") and saida.pop("oauth", False)
    saida.pop("oauth", None)
    return {"provedor": "", "nome_provedor": provedor.findtext("displayName") or dominio,
            "entrada": entrada, "saida": saida, "autenticacao": "senha", "oauth": "oauth" if oauth else "",
            "salva_enviados": False, "pastas": {}, "ajuda": "", "link_ajuda": "", "verificar_certificado": True}


def ispdb(dominio, email):
    try:
        return ler_xml_autoconfig(_baixar(ISPDB + quote(dominio)), email)
    except Exception:  # noqa: BLE001 — sem rede ou domínio desconhecido
        return None


def autoconfig_do_dominio(dominio, email):
    for url in (f"https://autoconfig.{dominio}/mail/config-v1.1.xml?emailaddress={quote(email)}",
                f"https://{dominio}/.well-known/autoconfig/mail/config-v1.1.xml?emailaddress={quote(email)}"):
        try:
            config = ler_xml_autoconfig(_baixar(url), email)
        except Exception:  # noqa: BLE001
            continue
        if config:
            return config
    return None


def srv(dominio, email):
    """RFC 6186: os registros SRV dizem os servidores de IMAP e de envio."""
    def primeiro(*nomes):
        for nome, seguranca in nomes:
            registros = sorted(_consultar_dns(f"{nome}._tcp.{dominio}", "SRV"), key=lambda r: (r.priority, -r.weight))
            for r in registros:
                host = str(r.target).rstrip(".")
                if host and host != ".":
                    return {"host": host, "porta": int(r.port), "seguranca": seguranca, "usuario": email}
        return None

    entrada = primeiro(("_imaps", "ssl"), ("_imap", "starttls"))
    tipo = "imap"
    if not entrada:
        entrada, tipo = primeiro(("_pop3s", "ssl"), ("_pop3", "starttls")), "pop3"
    saida = primeiro(("_submissions", "ssl"), ("_submission", "starttls"))
    if not entrada or not saida:
        return None
    entrada["tipo"], saida["tipo"] = tipo, "smtp"
    return {"provedor": "", "nome_provedor": dominio, "entrada": entrada, "saida": saida, "autenticacao": "senha",
            "oauth": "", "salva_enviados": False, "pastas": {}, "ajuda": "", "link_ajuda": "", "verificar_certificado": True}


def porta_aberta(host, porta, tempo=3):
    try:
        with socket.create_connection((host, porta), timeout=tempo):
            return True
    except OSError:
        return False


def adivinhar(dominio, email, testar=porta_aberta):
    entrada = saida = None
    for host in (f"imap.{dominio}", f"mail.{dominio}", dominio):
        for porta, seguranca in ((993, "ssl"), (143, "starttls")):
            if testar(host, porta):
                entrada = {"tipo": "imap", "host": host, "porta": porta, "seguranca": seguranca, "usuario": email}
                break
        if entrada:
            break
    for host in (f"smtp.{dominio}", f"mail.{dominio}", dominio):
        for porta, seguranca in ((465, "ssl"), (587, "starttls")):
            if testar(host, porta):
                saida = {"tipo": "smtp", "host": host, "porta": porta, "seguranca": seguranca, "usuario": email}
                break
        if saida:
            break
    if not entrada or not saida:
        return None
    return {"provedor": "", "nome_provedor": dominio, "entrada": entrada, "saida": saida, "autenticacao": "senha",
            "oauth": "", "salva_enviados": False, "pastas": {}, "ajuda": "", "link_ajuda": "", "verificar_certificado": True}


def descobrir(email, etapas=None):
    """Configuração para o endereço e de onde ela veio. Devolve (config, origem) ou (None, "")."""
    email = email.strip()
    if "@" not in email:
        return None, ""
    dominio = email.rsplit("@", 1)[1].lower()
    chave = provedores.por_dominio(dominio)
    if chave:
        return provedores.configuracao(chave, email), "catalogo"
    etapas = etapas or {"mx": mx, "ispdb": ispdb, "dominio": autoconfig_do_dominio, "srv": srv, "adivinhar": adivinhar}
    hosts_mx = etapas["mx"](dominio)
    chave = provedores.por_mx(hosts_mx)
    if chave:
        return provedores.configuracao(chave, email), "mx"
    for nome in ("ispdb", "dominio", "srv", "adivinhar"):
        config = etapas[nome](dominio, email)
        if config:
            return config, nome
    # O MX pode apontar para um domínio com configuração conhecida (hospedagem de terceiros)
    for host in hosts_mx[:1]:
        base = ".".join(host.split(".")[-2:])
        if base != dominio:
            config = etapas["ispdb"](base, email)
            if config:
                return config, "ispdb"
    return None, ""
