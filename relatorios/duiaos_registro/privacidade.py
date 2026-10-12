"""Privacidade dos registros (ADR 040).

limpar_segredos(valor): sempre, em todo registro — senhas, chaves, tokens e credenciais em endereços viram
"[oculto]". Vale para textos, dicionários e listas.

anonimizar(texto, ...): antes de um relatório sair do computador nos níveis "erros" e "erros_e_uso" — tira
nomes de usuário e de computador, pastas pessoais, e-mails, endereços IP e MAC. No nível "desenvolvimento"
(só computadores de teste do DuiaOS) os textos vão como estão, sem os segredos.
"""
import re

OCULTO = "[oculto]"
LIMITE_TEXTO = 16000

# Nome do campo inteiro ou uma parte entre "_" ("tokens_por_segundo" não é segredo; "access_token" é)
CAMPOS_SECRETOS = re.compile(r"(^|_)(senha|password|passwd|token|segredo|secret|chave|api_?key|authorization|"
                             r"cookie)($|_)", re.I)
TEXTOS_SECRETOS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),                              # Google (Gemini)
    re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[0-9A-Za-z_]{20,}"),     # GitHub
    re.compile(r"\bsk-[0-9A-Za-z_\-]{20,}"),
    re.compile(r"\bya29\.[0-9A-Za-z_\-\.]{20,}"),                        # token de acesso do Google
    re.compile(r"\beyJ[0-9A-Za-z_\-]{10,}\.[0-9A-Za-z_\-]{10,}\.[0-9A-Za-z_\-]{10,}"),   # JWT
    re.compile(r"(?i)\b(bearer|basic)\s+[0-9A-Za-z_\-\.=+/]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)\b((?:senha|password|passwd|token|secret)\s*[=:]\s*)\S+"),
    re.compile(r"(?i)(\w+://[^/\s:@]+:)[^@\s/]+@"),                     # usuario:senha@ em endereços
]

EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Completo (8 grupos) ou abreviado com "::" — "12:34:56" (hora) não é endereço
IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
                  r"|(?<![0-9A-Za-z:])(?:[0-9a-fA-F]{1,4}:){1,6}:(?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){0,5})?")
MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
PASTA_PESSOAL = re.compile(r"/home/[^/\s\"']+")


def limpar_segredos(valor, _profundidade=0):
    if _profundidade > 12:
        return "…"
    if isinstance(valor, dict):
        return {str(k): (OCULTO if CAMPOS_SECRETOS.search(str(k)) and v not in (None, "", False)
                         else limpar_segredos(v, _profundidade + 1)) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [limpar_segredos(v, _profundidade + 1) for v in valor]
    if isinstance(valor, str):
        texto = valor
        for padrao in TEXTOS_SECRETOS:
            texto = padrao.sub(lambda m: (m.group(1) if padrao.groups else "") + OCULTO, texto)
        return texto if len(texto) <= LIMITE_TEXTO else texto[:LIMITE_TEXTO] + "…"
    if isinstance(valor, (int, float, bool)) or valor is None:
        return valor
    return limpar_segredos(str(valor), _profundidade + 1)


def anonimizar(valor, nomes=(), _profundidade=0):
    """Tira o que identifica a pessoa ou o computador. `nomes`: nomes de usuário e do computador a trocar."""
    if _profundidade > 12:
        return "…"
    if isinstance(valor, dict):
        return {k: anonimizar(v, nomes, _profundidade + 1) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [anonimizar(v, nomes, _profundidade + 1) for v in valor]
    if not isinstance(valor, str):
        return valor
    texto = limpar_segredos(valor)
    texto = PASTA_PESSOAL.sub("/home/[usuario]", texto)
    texto = EMAIL.sub("[email]", texto)
    texto = MAC.sub("[mac]", texto)
    texto = IPV6.sub("[ip]", texto)
    texto = IPV4.sub(lambda m: m.group(0) if m.group(0).startswith(("0.", "127.")) else "[ip]", texto)
    for nome in sorted({n for n in nomes if n and len(n) >= 3}, key=len, reverse=True):
        texto = re.sub(rf"\b{re.escape(nome)}\b", "[nome]", texto)
    return texto
