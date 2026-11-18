"""DuiaOS — laboratório de e-mail para os testes do Mail Box: um Dovecot de verdade (IMAP com STARTTLS,
IMAPS e POP3) e um servidor SMTP de teste (aiosmtpd, com login), numa pasta temporária, só em 127.0.0.1.

    with Laboratorio() as lab:
        lab.entregar("ana@lab.invalid", bruto)       # coloca uma mensagem na Entrada
        lab.conta_imap  /  lab.conta_pop             # configurações prontas para o Mail Box
        lab.smtp_recebidas                           # o que o SMTP de teste recebeu

Precisa de: dovecot (dovecot-imapd, dovecot-pop3d), openssl e o módulo aiosmtpd.
"""
import getpass
import grp
import os
import pwd
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

USUARIO = "ana@lab.invalid"
SENHA = "senha-de-teste"


def disponivel():
    try:
        import aiosmtpd  # noqa: F401
    except ImportError:
        return False
    return bool(shutil.which("dovecot") or Path("/usr/sbin/dovecot").exists()) and bool(shutil.which("openssl"))


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Laboratorio:
    def __enter__(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="lab-email-"))
        os.chmod(self.pasta, 0o755)
        self.portas = {n: _porta_livre() for n in ("imap", "imaps", "pop3", "smtp")}
        self._certificado()
        self._dovecot()
        self._smtp()
        base_imap = {"host": "127.0.0.1", "usuario": USUARIO}
        self.conta_imap = {"provedor": "", "nome_provedor": "Laboratório",
                           "entrada": dict(base_imap, tipo="imap", porta=self.portas["imaps"], seguranca="ssl"),
                           "saida": dict(base_imap, tipo="smtp", porta=self.portas["smtp"], seguranca="nenhuma"),
                           "autenticacao": "senha", "salva_enviados": False, "pastas": {}, "verificar_certificado": False}
        self.conta_starttls = dict(self.conta_imap, entrada=dict(base_imap, tipo="imap", porta=self.portas["imap"],
                                                                  seguranca="starttls"))
        self.conta_pop = dict(self.conta_imap, entrada=dict(base_imap, tipo="pop3", porta=self.portas["pop3"],
                                                             seguranca="starttls"))
        return self

    def __exit__(self, *erro):
        self.controle_smtp.stop()
        subprocess.run([self.binario, "-c", str(self.config), "stop"], stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        time.sleep(0.3)
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _certificado(self):
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
                        "-subj", "/CN=127.0.0.1", "-keyout", str(self.pasta / "chave.pem"),
                        "-out", str(self.pasta / "certificado.pem")], check=True, capture_output=True, timeout=60)

    def _dovecot(self):
        self.binario = shutil.which("dovecot") or "/usr/sbin/dovecot"
        root = os.getuid() == 0
        # Como root (contêineres de teste), o correio fica com o "nobody": o dovecot não aceita o uid 0
        eu = self.dono = pwd.getpwnam("nobody") if root else pwd.getpwuid(os.getuid())
        (self.pasta / "usuarios").write_text(f"{USUARIO}:{{PLAIN}}{SENHA}::::\n")
        (self.pasta / "correio").mkdir()
        if root:
            os.chown(self.pasta / "correio", eu.pw_uid, eu.pw_gid)
        usuario_interno = "dovecot" if root else eu.pw_name
        usuario_login = "dovenull" if root else eu.pw_name
        p = self.pasta
        self.config = p / "dovecot.conf"
        self.config.write_text(f"""
base_dir = {p}/run
state_dir = {p}/estado
log_path = {p}/dovecot.log
info_log_path = {p}/dovecot.log
protocols = imap pop3
listen = 127.0.0.1
ssl = yes
ssl_cert = <{p}/certificado.pem
ssl_key = <{p}/chave.pem
disable_plaintext_auth = no
auth_mechanisms = plain login
default_internal_user = {usuario_interno}
default_internal_group = {grp.getgrgid(pwd.getpwnam(usuario_interno).pw_gid).gr_name}
default_login_user = {usuario_login}
first_valid_uid = 0
mail_location = maildir:~/Maildir
passdb {{
  driver = passwd-file
  args = scheme=PLAIN username_format=%u {p}/usuarios
}}
userdb {{
  driver = static
  args = uid={eu.pw_uid} gid={eu.pw_gid} home={p}/correio/%n
}}
service imap-login {{
  inet_listener imap {{
    port = {self.portas['imap']}
  }}
  inet_listener imaps {{
    port = {self.portas['imaps']}
    ssl = yes
  }}
}}
service pop3-login {{
  inet_listener pop3 {{
    port = {self.portas['pop3']}
  }}
  inet_listener pop3s {{
    port = 0
  }}
}}
service anvil {{
  chroot =
}}
service imap-login {{
  chroot =
}}
service pop3-login {{
  chroot =
}}
pop3_uidl_format = %08Xu%08Xv
namespace inbox {{
  inbox = yes
  separator = /
  mailbox Sent {{
    special_use = \\Sent
    auto = create
  }}
  mailbox Trash {{
    special_use = \\Trash
    auto = create
  }}
  mailbox Drafts {{
    special_use = \\Drafts
    auto = create
  }}
  mailbox Junk {{
    special_use = \\Junk
    auto = create
  }}
  mailbox "Itens Arquivados" {{
    special_use = \\Archive
    auto = create
  }}
}}
""")
        # O dovecot vai para o fundo e herda a saída: sem DEVNULL, o subprocess esperaria por ele para sempre
        with open(p / "inicio.log", "w") as registro:
            resultado = subprocess.run([self.binario, "-c", str(self.config)], stdin=subprocess.DEVNULL,
                                       stdout=registro, stderr=registro, timeout=20)
        if resultado.returncode != 0:
            raise RuntimeError("dovecot não abriu: " + (p / "inicio.log").read_text()[-400:])
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", self.portas["imaps"]), timeout=0.5).close()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("dovecot não respondeu: " + (p / "dovecot.log").read_text()[-400:])

    def _smtp(self):
        from aiosmtpd.controller import Controller
        from aiosmtpd.smtp import AuthResult, LoginPassword

        recebidas = self.smtp_recebidas = []

        class Destino:
            async def handle_DATA(self, server, session, envelope):
                recebidas.append({"de": envelope.mail_from, "para": list(envelope.rcpt_tos), "bruto": envelope.content})
                return "250 OK"

        def autenticar(server, session, envelope, mecanismo, dados):
            ok = isinstance(dados, LoginPassword) and dados.login.decode() == USUARIO and dados.password.decode() == SENHA
            return AuthResult(success=ok)

        self.controle_smtp = Controller(Destino(), hostname="127.0.0.1", port=self.portas["smtp"],
                                        authenticator=autenticar, auth_require_tls=False)
        self.controle_smtp.start()

    def maildir(self, pasta="INBOX"):
        base = self.pasta / "correio" / USUARIO.split("@")[0] / "Maildir"
        return base if pasta == "INBOX" else base / ("." + pasta)

    def entregar(self, bruto, pasta="INBOX", lida=False):
        """Coloca uma mensagem direto no Maildir, como o servidor de entrega faria."""
        destino = self.maildir(pasta)
        for sub in ("cur", "new", "tmp"):
            (destino / sub).mkdir(parents=True, exist_ok=True)
        nome = f"{time.time():.6f}.{os.getpid()}.lab"
        arquivo = destino / ("cur" if lida else "new") / (nome + (":2,S" if lida else ""))
        arquivo.write_bytes(bruto)
        if os.getuid() == 0:
            eu = self.dono
            for caminho in [destino.parents[1], *destino.parents[1].rglob("*")]:
                os.chown(caminho, eu.pw_uid, eu.pw_gid)
        return arquivo


def mensagem_de_teste(assunto, de="Bruno Lima <bruno@exemplo.invalid>", para=USUARIO, corpo="Olá, Ana!", html=None,
                      anexo=None):
    from email.message import EmailMessage
    from email.utils import formatdate, make_msgid
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = de, para, assunto
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="exemplo.invalid")
    msg.set_content(corpo)
    if html:
        msg.add_alternative(html, subtype="html")
    if anexo:
        nome, dados = anexo
        msg.add_attachment(dados, maintype="application", subtype="pdf", filename=nome)
    return msg.as_bytes()


if __name__ == "__main__":
    print("usuário:", getpass.getuser(), "| laboratório disponível:", disponivel())
