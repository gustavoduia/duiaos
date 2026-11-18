"""DuiaOS — Mail Box: ler, mostrar com segurança e escrever mensagens (MIME).

Ler:     resumo dos cabeçalhos, prévia do texto, anexos, corpo em HTML para a leitura.
Mostrar: HTML limpo — sem scripts, sem formulários que enviam, sem eventos; imagens externas bloqueadas
         até a pessoa liberar (evita o rastreamento por pixel); imagens embutidas (cid:) viram data:.
Escrever: nova mensagem, resposta (Re:, In-Reply-To, References, citação) e encaminhamento, com anexos.

Sem Qt: testável sozinho (shell/testes/test_mailbox.py).
"""
import base64
import email
import email.policy
import html
import mimetypes
import re
import time
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import formataddr, getaddresses, make_msgid, parsedate_to_datetime, formatdate
from html.parser import HTMLParser
from pathlib import Path


def decodificar(valor):
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(str(valor))))
    except Exception:  # noqa: BLE001 — cabeçalho mal codificado: mostra como veio
        return str(valor)


def ler(bruto):
    return email.message_from_bytes(bruto, policy=email.policy.default)


def enderecos(valor):
    return [{"nome": decodificar(n), "email": e} for n, e in getaddresses([decodificar(valor)]) if e]


def data_de(msg, reserva=0):
    try:
        return parsedate_to_datetime(msg["Date"]).timestamp()
    except Exception:  # noqa: BLE001
        return reserva or time.time()


def _texto_da_parte(parte):
    try:
        return parte.get_content()
    except Exception:  # noqa: BLE001 — conjunto de caracteres desconhecido
        carga = parte.get_payload(decode=True) or b""
        return carga.decode("utf-8", errors="replace")


def corpos(msg):
    """(texto, html) da mensagem — a melhor parte de cada tipo."""
    texto = html_ = ""
    for parte in msg.walk():
        if parte.is_multipart() or parte.get_content_disposition() == "attachment":
            continue
        tipo = parte.get_content_type()
        if tipo == "text/plain" and not texto:
            texto = _texto_da_parte(parte)
        elif tipo == "text/html" and not html_:
            html_ = _texto_da_parte(parte)
    return texto, html_


def anexos(msg):
    saida = []
    for i, parte in enumerate(msg.walk()):
        if parte.is_multipart():
            continue
        disposicao = parte.get_content_disposition()
        nome = parte.get_filename()
        if disposicao == "attachment" or (nome and disposicao != "inline" and not parte.get_content_type().startswith("text/")):
            carga = parte.get_payload(decode=True) or b""
            saida.append({"indice": i, "nome": decodificar(nome) or f"anexo-{i}", "tipo": parte.get_content_type(),
                          "tamanho": len(carga)})
    return saida


def conteudo_do_anexo(msg, indice):
    for i, parte in enumerate(msg.walk()):
        if i == indice:
            return parte.get_payload(decode=True) or b""
    return None


def previa(msg, limite=180):
    texto, html_ = corpos(msg)
    if not texto and html_:
        texto = html_para_texto(html_)
    texto = re.sub(r"(?m)^>.*$", "", texto)
    return re.sub(r"\s+", " ", texto).strip()[:limite]


def html_para_texto(conteudo):
    conteudo = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", conteudo)
    conteudo = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", conteudo)
    return html.unescape(re.sub(r"<[^>]+>", " ", conteudo))


def resumo(bruto, uid=0, flags=()):
    """Cabeçalhos e prévia de uma mensagem, para a lista."""
    msg = ler(bruto)
    remetente = (enderecos(msg["From"]) or [{"nome": "", "email": ""}])[0]
    return {"uid": uid, "message_id": (msg["Message-ID"] or "").strip(), "assunto": decodificar(msg["Subject"]),
            "de_nome": remetente["nome"], "de_email": remetente["email"],
            "para": ", ".join(e["email"] for e in enderecos(msg["To"])),
            "cc": ", ".join(e["email"] for e in enderecos(msg["Cc"])),
            "data": data_de(msg), "lida": "\\Seen" in flags, "sinalizada": "\\Flagged" in flags,
            "respondida": "\\Answered" in flags, "tem_anexo": bool(anexos(msg)), "previa": previa(msg),
            "tamanho": len(bruto), "referencias": (msg["References"] or "").strip(),
            "em_resposta_a": (msg["In-Reply-To"] or "").strip()}


# ------------------------------------------------------------------------------------------- mostrar
_PROIBIDAS = {"script", "iframe", "frame", "frameset", "object", "embed", "applet", "form", "base", "meta", "link",
              "noscript", "template", "portal"}
_VAZIAS = {"br", "hr", "img", "input", "col", "area", "wbr", "source", "track"}
_URL_PERIGOSA = re.compile(r"^\s*(javascript|vbscript|data:text/html)", re.IGNORECASE)
_URL_REMOTA_CSS = re.compile(r"url\(\s*['\"]?\s*(https?:)?//[^)]*\)", re.IGNORECASE)


class _Limpador(HTMLParser):
    def __init__(self, permitir_remoto, imagens_cid):
        super().__init__(convert_charrefs=False)
        self.saida = []
        self.pular = 0
        self.permitir_remoto = permitir_remoto
        self.cid = imagens_cid
        self.bloqueadas = 0

    def _atributos(self, tag, attrs):
        limpos = []
        for nome, valor in attrs:
            nome = nome.lower()
            valor = valor or ""
            if nome.startswith("on") or nome in ("srcdoc", "formaction", "ping"):
                continue
            if nome in ("href", "src", "action", "background", "poster", "xlink:href") and _URL_PERIGOSA.match(valor):
                continue
            if nome == "src" and tag == "img" or nome == "background":
                if valor.lower().startswith("cid:"):
                    valor = self.cid.get(valor[4:].strip("<>"), "")
                elif re.match(r"^\s*(https?:)?//", valor, re.IGNORECASE) and not self.permitir_remoto:
                    self.bloqueadas += 1
                    continue
            if nome == "srcset" and not self.permitir_remoto:
                continue
            if nome == "style" and not self.permitir_remoto and _URL_REMOTA_CSS.search(valor):
                self.bloqueadas += 1
                valor = _URL_REMOTA_CSS.sub("none", valor)
            limpos.append(f' {nome}="{html.escape(valor, quote=True)}"')
        if tag == "a":
            limpos.append(' target="_blank" rel="noopener noreferrer"')
        return "".join(limpos)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _PROIBIDAS:
            if tag not in _VAZIAS and tag not in ("meta", "link", "base"):
                self.pular += 1
            return
        if self.pular:
            return
        self.saida.append(f"<{tag}{self._atributos(tag, attrs)}>")

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if tag in _PROIBIDAS or self.pular:
            return
        self.saida.append(f"<{tag}{self._atributos(tag, attrs)}/>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _PROIBIDAS:
            if tag not in ("meta", "link", "base"):
                self.pular = max(0, self.pular - 1)
            return
        if not self.pular and tag not in _VAZIAS:
            self.saida.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.pular:
            self.saida.append(data)

    def handle_entityref(self, nome):
        if not self.pular:
            self.saida.append(f"&{nome};")

    def handle_charref(self, nome):
        if not self.pular:
            self.saida.append(f"&#{nome};")

    def handle_comment(self, data):
        pass


def _bloquear_css_remoto(conteudo, permitir_remoto):
    """Dentro de <style>: tira @import e url() remotos."""
    if permitir_remoto:
        return conteudo, 0
    def trocar_estilo(m):
        css = m.group(2)
        n = len(_URL_REMOTA_CSS.findall(css)) + len(re.findall(r"@import", css, re.IGNORECASE))
        css = re.sub(r"@import[^;]*;", "", css, flags=re.IGNORECASE)
        css = _URL_REMOTA_CSS.sub("none", css)
        trocar_estilo.total += n
        return m.group(1) + css + m.group(3)
    trocar_estilo.total = 0
    conteudo = re.sub(r"(?is)(<style[^>]*>)(.*?)(</style>)", trocar_estilo, conteudo)
    return conteudo, trocar_estilo.total


def imagens_embutidas(msg):
    mapa = {}
    for parte in msg.walk():
        cid = (parte.get("Content-ID") or "").strip("<> ")
        if cid and parte.get_content_maintype() == "image":
            carga = parte.get_payload(decode=True) or b""
            mapa[cid] = f"data:{parte.get_content_type()};base64,{base64.b64encode(carga).decode()}"
    return mapa


def texto_para_html(texto):
    seguro = html.escape(texto)
    seguro = re.sub(r"(https?://[^\s<>&\"]+)", r'<a href="\1">\1</a>', seguro)
    linhas = []
    for linha in seguro.split("\n"):
        nivel = len(re.match(r"^((&gt;\s?)*)", linha).group(1).replace(" ", "")) // 4
        conteudo = re.sub(r"^((&gt;\s?)*)", "", linha) if nivel else linha
        linhas.append(f'<div class="citacao" style="margin-left:{nivel * 12}px">{conteudo or "&nbsp;"}</div>' if nivel
                      else (conteudo or "<br>"))
    return "<div class=\"texto-simples\">" + "\n".join(l if l.startswith("<div") else l + "<br>" for l in linhas) + "</div>"


def html_para_leitura(msg, permitir_remoto=False, escuro=False):
    """HTML pronto para o WebEngineView sem JavaScript. Devolve (html, imagens_bloqueadas)."""
    texto, html_ = corpos(msg)
    bloqueadas = 0
    if html_:
        html_, n_css = _bloquear_css_remoto(html_, permitir_remoto)
        limpador = _Limpador(permitir_remoto, imagens_embutidas(msg))
        limpador.feed(html_)
        limpador.close()
        corpo = "".join(limpador.saida)
        bloqueadas = limpador.bloqueadas + n_css
        fundo, cor = "#ffffff", "#1f2933"              # e-mails em HTML foram feitos para fundo claro
    else:
        corpo = texto_para_html(texto)
        fundo, cor = ("#131A30", "#E6EAF0") if escuro else ("#ffffff", "#1f2933")
    estilo = (f"<style>html,body{{margin:0;padding:0;background:{fundo};color:{cor};}}"
              "body{padding:20px 24px;font-family:Inter,system-ui,sans-serif;font-size:14px;line-height:1.55;"
              "word-wrap:break-word;overflow-wrap:anywhere}"
              ".texto-simples{white-space:normal}.citacao{border-left:3px solid #8a94a3;padding-left:10px;color:#5b6675}"
              "img{max-width:100%;height:auto}a{color:#2E6BE6}"
              "blockquote{border-left:3px solid #c9d2de;margin:0 0 0 4px;padding-left:12px;color:#5b6675}</style>")
    politica = ("<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; img-src data: "
                + ("https: http:" if permitir_remoto else "") + "; style-src 'unsafe-inline'"
                + (" https: http:" if permitir_remoto else "") + "; font-src data:"
                + (" https: http:" if permitir_remoto else "") + "\">")
    return f"<!DOCTYPE html><html><head><meta charset=\"utf-8\">{politica}{estilo}</head><body>{corpo}</body></html>", bloqueadas


# ------------------------------------------------------------------------------------------- escrever
def _lista(texto):
    return [formataddr((n, e)) if n else e for n, e in getaddresses([texto or ""]) if e]


def montar(de_nome, de_email, para, assunto, corpo, cc="", cco="", anexos_caminhos=(), em_resposta_a="",
           referencias="", assinatura=""):
    msg = EmailMessage()
    msg["From"] = formataddr((de_nome, de_email)) if de_nome else de_email
    if _lista(para):
        msg["To"] = ", ".join(_lista(para))
    if _lista(cc):
        msg["Cc"] = ", ".join(_lista(cc))
    msg["Subject"] = assunto
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=de_email.rpartition("@")[2] or None)
    msg["User-Agent"] = "Mail Box 0.1 (DuiaOS)"
    if em_resposta_a:
        msg["In-Reply-To"] = em_resposta_a
        msg["References"] = (referencias + " " + em_resposta_a).strip()
    texto = corpo + (f"\n\n-- \n{assinatura}" if assinatura else "")
    msg.set_content(texto)
    for caminho in anexos_caminhos:
        caminho = Path(caminho)
        tipo, _ = mimetypes.guess_type(caminho.name)
        principal, sub = (tipo or "application/octet-stream").split("/", 1)
        msg.add_attachment(caminho.read_bytes(), maintype=principal, subtype=sub, filename=caminho.name)
    destinatarios = [e for campo in (para, cc, cco) if campo for _, e in getaddresses([campo]) if e]
    return msg, destinatarios


def assunto_resposta(assunto, prefixo="Re:"):
    base = re.sub(r"^\s*((re|res|enc|fwd?|tr)\s*:\s*)+", "", assunto or "", flags=re.IGNORECASE)
    return f"{prefixo} {base}".strip()


def citacao(msg):
    texto, html_ = corpos(msg)
    if not texto and html_:
        texto = html_para_texto(html_)
    texto = re.sub(r"\n{3,}", "\n\n", texto.strip())
    remetente = (enderecos(msg["From"]) or [{"nome": "", "email": ""}])[0]
    quem = remetente["nome"] or remetente["email"]
    try:
        quando = parsedate_to_datetime(msg["Date"]).strftime("%d/%m/%Y, às %H:%M")
    except Exception:  # noqa: BLE001
        quando = ""
    cabecalho = f"Em {quando}, {quem} escreveu:" if quando else f"{quem} escreveu:"
    return cabecalho + "\n" + "\n".join("> " + l for l in texto.split("\n"))


def rascunho_de_resposta(msg, meu_email, todos=False):
    """Campos iniciais da janela Escrever para responder."""
    responder_para = msg["Reply-To"] or msg["From"]
    para = [e for e in enderecos(responder_para)]
    cc = []
    if todos:
        outros = enderecos(msg["To"]) + enderecos(msg["Cc"])
        vistos = {p["email"].lower() for p in para} | {meu_email.lower()}
        for e in outros:
            if e["email"].lower() not in vistos:
                vistos.add(e["email"].lower())
                cc.append(e)
    formatar = lambda lista: ", ".join(formataddr((e["nome"], e["email"])) if e["nome"] else e["email"] for e in lista)  # noqa: E731
    return {"para": formatar(para), "cc": formatar(cc), "assunto": assunto_resposta(decodificar(msg["Subject"])),
            "corpo": "\n\n" + citacao(msg), "em_resposta_a": (msg["Message-ID"] or "").strip(),
            "referencias": (msg["References"] or "").strip()}


def rascunho_de_encaminhamento(msg):
    texto, html_ = corpos(msg)
    if not texto and html_:
        texto = html_para_texto(html_)
    cabecalho = ("\n\n---------- Mensagem encaminhada ----------\n"
                 f"De: {decodificar(msg['From'])}\nData: {msg['Date'] or ''}\nAssunto: {decodificar(msg['Subject'])}\n"
                 f"Para: {decodificar(msg['To'])}\n\n")
    return {"para": "", "cc": "", "assunto": assunto_resposta(decodificar(msg["Subject"]), "Enc:"),
            "corpo": cabecalho + texto.strip(), "em_resposta_a": "", "referencias": ""}
