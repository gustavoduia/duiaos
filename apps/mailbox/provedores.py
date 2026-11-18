"""DuiaOS — Mail Box: catálogo próprio de provedores de e-mail (primeiro passo do wizard).

Cada provedor diz os servidores, a forma de entrar e, quando o provedor exige senha de app, o passo a
passo e o link da página certa. Os endereços e portas são os publicados pelos provedores.

    servidor: {"tipo": imap|pop3|smtp, "host", "porta", "seguranca": ssl|starttls|nenhuma}
    autenticacao: "senha" (a senha da conta), "senha_de_app" (gerada no site do provedor) ou "oauth"
"""

IMAP_SSL, SMTP_SSL, SMTP_STARTTLS = 993, 465, 587


def _imap(host, porta=IMAP_SSL, seguranca="ssl"):
    return {"tipo": "imap", "host": host, "porta": porta, "seguranca": seguranca}


def _pop(host, porta=995, seguranca="ssl"):
    return {"tipo": "pop3", "host": host, "porta": porta, "seguranca": seguranca}


def _smtp(host, porta=SMTP_SSL, seguranca="ssl"):
    return {"tipo": "smtp", "host": host, "porta": porta, "seguranca": seguranca}


PROVEDORES = {
    "gmail": {
        "nome": "Gmail", "dominios": ["gmail.com", "googlemail.com"],
        "mx": ["google.com", "googlemail.com"],
        "entrada": _imap("imap.gmail.com"), "saida": _smtp("smtp.gmail.com"),
        "autenticacao": "senha_de_app", "oauth": "google", "salva_enviados": True,
        "pastas": {"enviados": "[Gmail]/Sent Mail", "lixeira": "[Gmail]/Trash", "spam": "[Gmail]/Spam",
                   "rascunhos": "[Gmail]/Drafts", "arquivo": "[Gmail]/All Mail"},
        "ajuda": "O Google pede uma senha de app para programas de e-mail. Ative a verificação em duas etapas "
                 "na sua Conta Google, crie uma senha de app com o nome “Mail Box” e cole aqui as 16 letras.",
        "link_ajuda": "https://myaccount.google.com/apppasswords",
    },
    "outlook": {
        "nome": "Outlook.com e Hotmail", "dominios": ["outlook.com", "outlook.com.br", "hotmail.com", "hotmail.com.br",
                                                     "live.com", "msn.com", "passport.com"],
        "mx": ["olc.protection.outlook.com"],
        "entrada": _imap("outlook.office365.com"), "saida": _smtp("smtp-mail.outlook.com", SMTP_STARTTLS, "starttls"),
        "autenticacao": "oauth", "oauth": "microsoft", "salva_enviados": True,
        "ajuda": "A Microsoft só aceita programas de e-mail com login seguro (OAuth). O Mail Box abre a página de "
                 "login da Microsoft para você entrar.",
        "link_ajuda": "https://support.microsoft.com/office/c5a1e7b2-e7a1-4b67-b0e5-4d6f2a0c5e8e",
    },
    "microsoft365": {
        "nome": "Microsoft 365 (trabalho ou escola)", "dominios": [],
        "mx": ["mail.protection.outlook.com"],
        "entrada": _imap("outlook.office365.com"), "saida": _smtp("smtp.office365.com", SMTP_STARTTLS, "starttls"),
        "autenticacao": "oauth", "oauth": "microsoft", "salva_enviados": True,
        "ajuda": "Contas do Microsoft 365 entram com o login da empresa (OAuth). Algumas empresas pedem que o "
                 "administrador libere programas de e-mail.",
        "link_ajuda": "",
    },
    "icloud": {
        "nome": "iCloud Mail", "dominios": ["icloud.com", "me.com", "mac.com"],
        "mx": ["icloud.com"],
        "entrada": _imap("imap.mail.me.com"), "saida": _smtp("smtp.mail.me.com", SMTP_STARTTLS, "starttls"),
        "autenticacao": "senha_de_app", "usuario": "parte_local", "salva_enviados": False,
        "ajuda": "A Apple pede uma senha de app: entre na sua conta Apple, abra “Entrar e segurança” › "
                 "“Senhas de app”, crie uma para o Mail Box e cole aqui.",
        "link_ajuda": "https://account.apple.com/account/manage",
    },
    "yahoo": {
        "nome": "Yahoo Mail", "dominios": ["yahoo.com", "yahoo.com.br", "ymail.com", "rocketmail.com"],
        "mx": ["yahoodns.net"],
        "entrada": _imap("imap.mail.yahoo.com"), "saida": _smtp("smtp.mail.yahoo.com"),
        "autenticacao": "senha_de_app", "salva_enviados": False,
        "ajuda": "O Yahoo pede uma senha de app: abra a Segurança da conta, gere uma senha de app para o Mail Box "
                 "e cole aqui.",
        "link_ajuda": "https://login.yahoo.com/account/security",
    },
    "aol": {
        "nome": "AOL Mail", "dominios": ["aol.com"],
        "mx": ["mx-aol.mail.gm0.yahoodns.net"],
        "entrada": _imap("imap.aol.com"), "saida": _smtp("smtp.aol.com"),
        "autenticacao": "senha_de_app", "salva_enviados": False,
        "ajuda": "A AOL pede uma senha de app, gerada na Segurança da conta.",
        "link_ajuda": "https://login.aol.com/account/security",
    },
    "zoho": {
        "nome": "Zoho Mail", "dominios": ["zoho.com", "zohomail.com"],
        "mx": ["zoho.com", "zohomail.com"],
        "entrada": _imap("imap.zoho.com"), "saida": _smtp("smtp.zoho.com"),
        "autenticacao": "senha", "salva_enviados": False,
        "ajuda": "Com a verificação em duas etapas ligada, o Zoho pede uma senha de app.",
        "link_ajuda": "https://accounts.zoho.com/home#security/app_password",
    },
    "gmx": {
        "nome": "GMX", "dominios": ["gmx.com", "gmx.net", "gmx.de"],
        "mx": ["gmx.net", "gmx.com"],
        "entrada": _imap("imap.gmx.com"), "saida": _smtp("mail.gmx.com"),
        "autenticacao": "senha", "salva_enviados": False,
        "ajuda": "No GMX, o acesso por IMAP precisa estar ligado nas configurações da conta, no site.",
        "link_ajuda": "",
    },
    "fastmail": {
        "nome": "Fastmail", "dominios": ["fastmail.com", "fastmail.fm"],
        "mx": ["messagingengine.com"],
        "entrada": _imap("imap.fastmail.com"), "saida": _smtp("smtp.fastmail.com"),
        "autenticacao": "senha_de_app", "salva_enviados": False,
        "ajuda": "A Fastmail pede uma senha de app, criada em Configurações › Privacidade e segurança.",
        "link_ajuda": "https://app.fastmail.com/settings/security/devicekeys",
    },
    "proton": {
        "nome": "Proton Mail (pelo Bridge)", "dominios": ["proton.me", "protonmail.com", "pm.me"],
        "mx": ["protonmail.ch"],
        "entrada": _imap("127.0.0.1", 1143, "starttls"), "saida": _smtp("127.0.0.1", 1025, "starttls"),
        "autenticacao": "senha", "salva_enviados": True, "certificado_local": True,
        "ajuda": "O Proton Mail funciona em programas de e-mail pelo Proton Mail Bridge (planos pagos). Instale "
                 "e abra o Bridge, e use aqui a senha que ele mostra.",
        "link_ajuda": "https://proton.me/mail/bridge",
    },
    # ---------------------------------------------------------------- Brasil
    "uol": {
        "nome": "UOL", "dominios": ["uol.com.br"],
        "mx": ["uol.com.br"],
        "entrada": _imap("imap.uol.com.br"), "saida": _smtp("smtps.uol.com.br", SMTP_STARTTLS, "starttls"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
    "bol": {
        "nome": "BOL", "dominios": ["bol.com.br"],
        "mx": ["bol.com.br"],
        "entrada": _imap("imap.bol.com.br"), "saida": _smtp("smtps.bol.com.br", SMTP_STARTTLS, "starttls"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
    "terra": {
        "nome": "Terra", "dominios": ["terra.com.br"],
        "mx": ["terra.com.br"],
        "entrada": _imap("imap.terra.com.br"), "saida": _smtp("smtp.terra.com.br", SMTP_STARTTLS, "starttls"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
    "locaweb": {
        "nome": "Locaweb", "dominios": [],
        "mx": ["locaweb.com.br"],
        "entrada": _imap("email-ssl.com.br"), "saida": _smtp("email-ssl.com.br"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
    "kinghost": {
        "nome": "KingHost", "dominios": [],
        "mx": ["kinghost.net"],
        "entrada": _imap("imap.{dominio}"), "saida": _smtp("smtp.{dominio}", SMTP_STARTTLS, "starttls"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
    "hostinger": {
        "nome": "Hostinger", "dominios": [],
        "mx": ["hostinger.com", "hostinger.com.br"],
        "entrada": _imap("imap.hostinger.com"), "saida": _smtp("smtp.hostinger.com"),
        "autenticacao": "senha", "salva_enviados": False, "ajuda": "", "link_ajuda": "",
    },
}

# Atalhos do primeiro passo do wizard (na ordem em que aparecem)
DESTAQUES = ["gmail", "outlook", "icloud", "yahoo", "microsoft365"]


def por_dominio(dominio):
    dominio = (dominio or "").lower().strip(".")
    for chave, p in PROVEDORES.items():
        if dominio in p["dominios"]:
            return chave
    return None


def por_mx(hosts_mx):
    """O provedor pelos servidores MX do domínio (domínios próprios no Google Workspace, Microsoft 365...)."""
    for host in hosts_mx:
        host = host.lower().rstrip(".")
        for chave, p in PROVEDORES.items():
            if any(host == m or host.endswith("." + m) for m in p.get("mx", [])):
                return chave
    return None


def configuracao(chave, email):
    """Configuração pronta de um provedor do catálogo para este endereço."""
    p = PROVEDORES[chave]
    local, _, dominio = email.partition("@")
    usuario = local if p.get("usuario") == "parte_local" else email

    def preencher(servidor):
        s = dict(servidor)
        s["host"] = s["host"].replace("{dominio}", dominio)
        s["usuario"] = usuario
        return s

    return {"provedor": chave, "nome_provedor": p["nome"], "entrada": preencher(p["entrada"]), "saida": preencher(p["saida"]),
            "autenticacao": p["autenticacao"], "oauth": p.get("oauth", ""), "salva_enviados": p.get("salva_enviados", False),
            "pastas": dict(p.get("pastas", {})), "ajuda": p.get("ajuda", ""), "link_ajuda": p.get("link_ajuda", ""),
            "verificar_certificado": not p.get("certificado_local", False)}
