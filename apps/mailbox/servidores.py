"""DuiaOS — Mail Box: conversa com os servidores (IMAP, POP3 e SMTP).

IMAP: entrar (senha ou XOAUTH2), listar pastas com o papel de cada uma (SPECIAL-USE, RFC 6154, ou pelo
nome), sincronizar por UID (UIDVALIDITY e o último UID visto), marcar lida/sinalizada, mover (MOVE ou
COPY + \\Deleted + EXPUNGE), guardar no servidor (APPEND).
POP3: baixar para a Entrada local, sem repetir (UIDL), deixando ou não no servidor.
SMTP: enviar pela porta de envio (465 com TLS ou 587 com STARTTLS), com senha ou XOAUTH2.

Sempre criptografado, a não ser que a conta peça "nenhuma" explicitamente; o certificado é conferido.
"""
import base64
import imaplib
import poplib
import re
import smtplib
import socket
import ssl

TEMPO = 30
LOTE = 50                       # mensagens por FETCH
TAMANHO_PARA_BAIXAR = 2_000_000  # mensagens maiores só são baixadas ao abrir

NOMES_POR_PAPEL = {
    "enviados": ("sent", "sent items", "sent mail", "sent messages", "enviados", "enviadas", "itens enviados",
                 "mensagens enviadas", "e-mails enviados"),
    "rascunhos": ("drafts", "draft", "rascunhos", "rascunho"),
    "lixeira": ("trash", "deleted", "deleted items", "deleted messages", "lixeira", "lixo", "itens excluídos", "itens excluidos"),
    "spam": ("spam", "junk", "junk e-mail", "junk email", "bulk mail", "lixo eletrônico", "lixo eletronico"),
    "arquivo": ("archive", "archives", "arquivo", "arquivados", "all mail", "todos os e-mails"),
}
USO_ESPECIAL = {"\\sent": "enviados", "\\drafts": "rascunhos", "\\trash": "lixeira", "\\junk": "spam", "\\archive": "arquivo",
                "\\all": "arquivo"}


class ErroDeConta(Exception):
    """Erro para mostrar à pessoa (em português simples)."""


# ------------------------------------------------------------------------------- nomes de pastas IMAP
def utf7_imap_para_texto(nome):
    """Nomes de pastas IMAP vêm em UTF-7 modificado (RFC 3501 5.1.3): "Itens Exclu&AO0-dos"."""
    def trocar(m):
        trecho = m.group(1)
        if trecho == "":
            return "&"
        dados = trecho.replace(",", "/")
        dados += "=" * (-len(dados) % 4)
        return base64.b64decode(dados).decode("utf-16-be")
    return re.sub(r"&([^-]*)-", trocar, nome)


def texto_para_utf7_imap(texto):
    saida, pendente = [], []

    def descarregar():
        if pendente:
            codificado = base64.b64encode("".join(pendente).encode("utf-16-be")).decode().rstrip("=").replace("/", ",")
            saida.append("&" + codificado + "-")
            pendente.clear()
    for c in texto:
        if 0x20 <= ord(c) <= 0x7E:
            descarregar()
            saida.append("&-" if c == "&" else c)
        else:
            pendente.append(c)
    descarregar()
    return "".join(saida)


def _aspas(nome):
    return '"' + nome.replace("\\", "\\\\").replace('"', '\\"') + '"'


_LINHA_LIST = re.compile(r'^\((?P<flags>[^)]*)\)\s+(?P<sep>"(?:[^"\\]|\\.)*"|NIL)\s+(?P<nome>.+)$')


def ler_linha_list(linha):
    if isinstance(linha, tuple):           # nome em literal {n}
        cabeca, nome = linha
        linha = cabeca.decode(errors="replace").rsplit("{", 1)[0] + _aspas(nome.decode(errors="replace"))
    elif isinstance(linha, bytes):
        linha = linha.decode(errors="replace")
    m = _LINHA_LIST.match(linha.strip())
    if not m:
        return None
    flags = m.group("flags").lower().split()
    sep = m.group("sep")
    sep = "" if sep == "NIL" else sep[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    nome = m.group("nome").strip()
    if nome.startswith('"'):
        nome = nome[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return {"caminho": nome, "flags": flags, "separador": sep or "/"}


def papel_da_pasta(caminho, flags, separador="/"):
    if caminho.upper() == "INBOX":
        return "entrada"
    for f in flags:
        if f in USO_ESPECIAL:
            return USO_ESPECIAL[f]
    final = utf7_imap_para_texto(caminho).split(separador)[-1].strip().lower()
    for papel, nomes in NOMES_POR_PAPEL.items():
        if final in nomes:
            return papel
    return ""


def nome_visivel(caminho, separador, papel):
    from caixa_postal import NOMES_PAPEIS
    if papel in NOMES_PAPEIS:
        return NOMES_PAPEIS[papel]
    texto = utf7_imap_para_texto(caminho)
    return texto.replace(separador, " › ") if separador else texto


# ------------------------------------------------------------------------------- IMAP
def _contexto(verificar):
    contexto = ssl.create_default_context()
    if not verificar:
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
    return contexto


def _traduzir_erro(erro):
    texto = str(erro)
    baixo = texto.lower()
    if isinstance(erro, (socket.gaierror,)):
        return "O servidor não foi encontrado. Confira o endereço do servidor e a internet."
    if isinstance(erro, (socket.timeout, TimeoutError)):
        return "O servidor demorou demais para responder."
    if isinstance(erro, ConnectionRefusedError):
        return "O servidor recusou a conexão nessa porta."
    if isinstance(erro, ssl.SSLCertVerificationError):
        return "O certificado de segurança do servidor não é válido."
    if isinstance(erro, ssl.SSLError):
        return "Não foi possível estabelecer uma conexão segura. Confira a porta e o tipo de segurança."
    if "application-specific password" in baixo or "app password" in baixo or "web login required" in baixo:
        return "O provedor pede uma senha de app em vez da senha normal da conta."
    if "authenticationfailed" in baixo or "authentication failed" in baixo or "invalid credentials" in baixo \
            or "login failed" in baixo or "535" in baixo or "auth" in baixo and "fail" in baixo:
        return "Usuário ou senha incorretos."
    if "basicauthblocked" in baixo or "logondenied" in baixo:
        return "O provedor bloqueou o login com senha. Esta conta precisa do login seguro (OAuth)."
    return f"O servidor respondeu com um erro: {texto[:160]}"


def xoauth2(usuario, token):
    return f"user={usuario}\x01auth=Bearer {token}\x01\x01".encode()


class Imap:
    def __init__(self, servidor, segredo, verificar=True, oauth=False):
        self.servidor, self.segredo, self.verificar, self.oauth = servidor, segredo, verificar, oauth
        self.con = None
        self.capacidades = set()

    def conectar(self):
        s = self.servidor
        try:
            if s["seguranca"] == "ssl":
                self.con = imaplib.IMAP4_SSL(s["host"], int(s["porta"]), ssl_context=_contexto(self.verificar), timeout=TEMPO)
            else:
                self.con = imaplib.IMAP4(s["host"], int(s["porta"]), timeout=TEMPO)
                if s["seguranca"] == "starttls":
                    self.con.starttls(ssl_context=_contexto(self.verificar))
            if self.oauth:
                self.con.authenticate("XOAUTH2", lambda _: xoauth2(s["usuario"], self.segredo))
            else:
                self.con.login(s["usuario"], self.segredo)
            self.capacidades = {c.upper() for c in self.con.capabilities}
            if "ENABLE" in self.capacidades and "UTF8=ACCEPT" in self.capacidades:
                try:
                    self.con._simple_command("ENABLE", "UTF8=ACCEPT")
                except imaplib.IMAP4.error:
                    pass
        except (imaplib.IMAP4.error, OSError, ssl.SSLError) as erro:
            self.fechar()
            raise ErroDeConta(_traduzir_erro(erro)) from erro
        return self

    def fechar(self):
        if self.con is not None:
            try:
                self.con.logout()
            except Exception:  # noqa: BLE001 — conexão já caída
                pass
        self.con = None

    def _ok(self, resposta, acao):
        tipo, dados = resposta
        if tipo != "OK":
            raise ErroDeConta(f"O servidor não aceitou {acao}: {(dados[0] or b'').decode(errors='replace')[:120] if dados else ''}")
        return dados

    def pastas(self):
        dados = self._ok(self.con.list(), "listar as pastas")
        saida = []
        for linha in dados:
            if linha is None:
                continue
            item = ler_linha_list(linha)
            if not item or "\\noselect" in item["flags"] or "\\nonexistent" in item["flags"]:
                continue
            item["papel"] = papel_da_pasta(item["caminho"], item["flags"], item["separador"])
            item["nome"] = nome_visivel(item["caminho"], item["separador"], item["papel"])
            saida.append(item)
        return saida

    def selecionar(self, caminho, somente_leitura=False):
        tipo, dados = self.con.select(_aspas(caminho), readonly=somente_leitura)
        if tipo != "OK":
            raise ErroDeConta(f"Não foi possível abrir a pasta {utf7_imap_para_texto(caminho)}.")
        uidvalidity = self.con.untagged_responses.get("UIDVALIDITY", [b"0"])[-1]
        return {"existentes": int(dados[0] or 0), "uidvalidity": int(uidvalidity or 0)}

    def buscar_uids(self, criterio="ALL"):
        dados = self._ok(self.con.uid("SEARCH", None, criterio), "buscar mensagens")
        return [int(u) for u in (dados[0] or b"").split()]

    def flags(self, uids):
        saida = {}
        for i in range(0, len(uids), 500):
            parte = ",".join(str(u) for u in uids[i:i + 500])
            dados = self._ok(self.con.uid("FETCH", parte, "(UID FLAGS)"), "ler as marcações")
            for item in dados:
                texto = item.decode(errors="replace") if isinstance(item, bytes) else ""
                m_uid, m_flags = re.search(r"UID (\d+)", texto), re.search(r"FLAGS \(([^)]*)\)", texto)
                if m_uid and m_flags:
                    saida[int(m_uid.group(1))] = set(m_flags.group(1).split())
        return saida

    def baixar(self, uids, completo=True):
        """Gera (uid, bruto, flags, tamanho) para cada UID. Sem `completo`, só os cabeçalhos."""
        parte_pedida = "BODY.PEEK[]" if completo else "BODY.PEEK[HEADER]"
        for i in range(0, len(uids), LOTE):
            lote = ",".join(str(u) for u in uids[i:i + LOTE])
            dados = self._ok(self.con.uid("FETCH", lote, f"(UID FLAGS RFC822.SIZE {parte_pedida})"), "baixar mensagens")
            for item in dados:
                if not isinstance(item, tuple):
                    continue
                cabeca = item[0].decode(errors="replace")
                m_uid = re.search(r"UID (\d+)", cabeca)
                if not m_uid:
                    continue
                m_flags = re.search(r"FLAGS \(([^)]*)\)", cabeca)
                m_tam = re.search(r"RFC822\.SIZE (\d+)", cabeca)
                yield (int(m_uid.group(1)), item[1], set(m_flags.group(1).split()) if m_flags else set(),
                       int(m_tam.group(1)) if m_tam else len(item[1]))

    def tamanhos(self, uids):
        saida = {}
        for i in range(0, len(uids), 500):
            parte = ",".join(str(u) for u in uids[i:i + 500])
            for item in self._ok(self.con.uid("FETCH", parte, "(UID RFC822.SIZE)"), "ler os tamanhos"):
                texto = item.decode(errors="replace") if isinstance(item, bytes) else ""
                m_uid, m_tam = re.search(r"UID (\d+)", texto), re.search(r"RFC822\.SIZE (\d+)", texto)
                if m_uid and m_tam:
                    saida[int(m_uid.group(1))] = int(m_tam.group(1))
        return saida

    def marcar(self, uid, flag, ligar):
        self._ok(self.con.uid("STORE", str(uid), "+FLAGS.SILENT" if ligar else "-FLAGS.SILENT", f"({flag})"), "marcar")

    def mover(self, uid, destino):
        if "MOVE" in self.capacidades:
            self._ok(self.con.uid("MOVE", str(uid), _aspas(destino)), "mover a mensagem")
            return
        self._ok(self.con.uid("COPY", str(uid), _aspas(destino)), "copiar a mensagem")
        self.apagar(uid)

    def apagar(self, uid):
        self._ok(self.con.uid("STORE", str(uid), "+FLAGS.SILENT", "(\\Deleted)"), "apagar a mensagem")
        if "UIDPLUS" in self.capacidades:
            self._ok(self.con.uid("EXPUNGE", str(uid)), "apagar a mensagem")
        else:
            self.con.expunge()

    def guardar(self, caminho, bruto, flags="(\\Seen)"):
        self._ok(self.con.append(_aspas(caminho), flags, imaplib.Time2Internaldate(__import__("time").time()), bruto),
                 "guardar a mensagem")

    def criar_pasta(self, caminho):
        self._ok(self.con.create(_aspas(caminho)), "criar a pasta")


# ------------------------------------------------------------------------------- POP3
class Pop3:
    def __init__(self, servidor, segredo, verificar=True):
        self.servidor, self.segredo, self.verificar = servidor, segredo, verificar
        self.con = None

    def conectar(self):
        s = self.servidor
        try:
            if s["seguranca"] == "ssl":
                self.con = poplib.POP3_SSL(s["host"], int(s["porta"]), context=_contexto(self.verificar), timeout=TEMPO)
            else:
                self.con = poplib.POP3(s["host"], int(s["porta"]), timeout=TEMPO)
                if s["seguranca"] == "starttls":
                    self.con.stls(context=_contexto(self.verificar))
            self.con.user(s["usuario"])
            self.con.pass_(self.segredo)
        except (poplib.error_proto, OSError, ssl.SSLError) as erro:
            self.fechar()
            raise ErroDeConta(_traduzir_erro(erro)) from erro
        return self

    def fechar(self):
        if self.con is not None:
            try:
                self.con.quit()
            except Exception:  # noqa: BLE001
                pass
        self.con = None

    def identificadores(self):
        """{número: uidl}."""
        _, linhas, _ = self.con.uidl()
        saida = {}
        for linha in linhas:
            numero, uidl = linha.decode(errors="replace").split(" ", 1)
            saida[int(numero)] = uidl.strip()
        return saida

    def baixar(self, numero):
        _, linhas, _ = self.con.retr(numero)
        return b"\r\n".join(linhas) + b"\r\n"

    def apagar(self, numero):
        self.con.dele(numero)


# ------------------------------------------------------------------------------- SMTP
def enviar(servidor, segredo, mensagem, destinatarios, verificar=True, oauth=False):
    s = servidor
    try:
        if s["seguranca"] == "ssl":
            con = smtplib.SMTP_SSL(s["host"], int(s["porta"]), context=_contexto(verificar), timeout=TEMPO)
        else:
            con = smtplib.SMTP(s["host"], int(s["porta"]), timeout=TEMPO)
            con.ehlo()
            if s["seguranca"] == "starttls":
                con.starttls(context=_contexto(verificar))
                con.ehlo()
        with con:
            if oauth:
                con.auth("XOAUTH2", lambda _=None: xoauth2(s["usuario"], segredo).decode(), initial_response_ok=True)
            elif segredo or s.get("usuario"):
                if con.has_extn("auth"):
                    con.login(s["usuario"], segredo)
            recusados = con.send_message(mensagem, to_addrs=destinatarios)
    except smtplib.SMTPRecipientsRefused:
        raise ErroDeConta("O servidor recusou todos os destinatários. Confira os endereços.") from None
    except (smtplib.SMTPException, OSError, ssl.SSLError) as erro:
        raise ErroDeConta(_traduzir_erro(erro)) from erro
    return recusados


def testar_entrada(conta, segredo):
    classe = Imap if conta["entrada"]["tipo"] == "imap" else Pop3
    cliente = classe(conta["entrada"], segredo, conta.get("verificar_certificado", True))
    cliente.conectar()
    cliente.fechar()


def testar_saida(conta, segredo):
    s = conta["saida"]
    verificar = conta.get("verificar_certificado", True)
    try:
        if s["seguranca"] == "ssl":
            con = smtplib.SMTP_SSL(s["host"], int(s["porta"]), context=_contexto(verificar), timeout=TEMPO)
        else:
            con = smtplib.SMTP(s["host"], int(s["porta"]), timeout=TEMPO)
            con.ehlo()
            if s["seguranca"] == "starttls":
                con.starttls(context=_contexto(verificar))
                con.ehlo()
        with con:
            if con.has_extn("auth"):
                con.login(s["usuario"], segredo)
    except (smtplib.SMTPException, OSError, ssl.SSLError) as erro:
        raise ErroDeConta(_traduzir_erro(erro)) from erro
