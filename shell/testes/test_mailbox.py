"""Mail Box, o gerenciador de e-mails do DuiaOS (ADR 072): catálogo de provedores, descoberta dos
servidores, leitura segura do HTML, escrever/responder/encaminhar, nomes de pastas IMAP e o motor contra
servidores de verdade (Dovecot com IMAP, IMAPS e POP3, e um SMTP de teste com login).

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "apps" / "mailbox"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import autoconfig  # noqa: E402
import laboratorio_email as lab  # noqa: E402
import mensagem  # noqa: E402
import provedores  # noqa: E402
import servidores  # noqa: E402

try:
    from PySide6 import QtWebEngineQuick  # noqa: F401
    TEM_MOTOR = True
except ImportError:
    TEM_MOTOR = False

ISPDB_XML = b"""<?xml version="1.0"?>
<clientConfig version="1.1">
  <emailProvider id="exemplo.com.br">
    <domain>exemplo.com.br</domain>
    <displayName>Exemplo Hospedagem</displayName>
    <incomingServer type="pop3"><hostname>pop.exemplo.com.br</hostname><port>995</port><socketType>SSL</socketType>
      <username>%EMAILADDRESS%</username><authentication>password-cleartext</authentication></incomingServer>
    <incomingServer type="imap"><hostname>imap.exemplo.com.br</hostname><port>143</port><socketType>STARTTLS</socketType>
      <username>%EMAILLOCALPART%</username><authentication>password-cleartext</authentication></incomingServer>
    <incomingServer type="imap"><hostname>imap.exemplo.com.br</hostname><port>993</port><socketType>SSL</socketType>
      <username>%EMAILLOCALPART%</username><authentication>password-cleartext</authentication></incomingServer>
    <outgoingServer type="smtp"><hostname>smtp.%EMAILDOMAIN%</hostname><port>587</port><socketType>STARTTLS</socketType>
      <username>%EMAILADDRESS%</username><authentication>password-cleartext</authentication></outgoingServer>
  </emailProvider>
</clientConfig>"""


class TestProvedores(unittest.TestCase):
    def test_catalogo_por_dominio(self):
        self.assertEqual(provedores.por_dominio("gmail.com"), "gmail")
        self.assertEqual(provedores.por_dominio("HOTMAIL.COM"), "outlook")
        self.assertEqual(provedores.por_dominio("icloud.com"), "icloud")
        self.assertEqual(provedores.por_dominio("uol.com.br"), "uol")
        self.assertIsNone(provedores.por_dominio("minhaempresa.com.br"))

    def test_mx_identifica_dominios_proprios(self):
        self.assertEqual(provedores.por_mx(["aspmx.l.google.com."]), "gmail")
        self.assertEqual(provedores.por_mx(["empresa-com-br.mail.protection.outlook.com"]), "microsoft365")
        self.assertEqual(provedores.por_mx(["mx1.hostinger.com"]), "hostinger")
        self.assertIsNone(provedores.por_mx(["mx.servidor-desconhecido.net"]))

    def test_configuracao_do_icloud_usa_a_parte_local(self):
        c = provedores.configuracao("icloud", "ana@icloud.com")
        self.assertEqual(c["entrada"]["usuario"], "ana")
        self.assertEqual(c["autenticacao"], "senha_de_app")
        self.assertTrue(c["link_ajuda"].startswith("https://"))

    def test_todos_os_provedores_tem_servidores_criptografados(self):
        for chave in provedores.PROVEDORES:
            c = provedores.configuracao(chave, "pessoa@exemplo.com")
            self.assertIn(c["entrada"]["seguranca"], ("ssl", "starttls"), chave)
            self.assertIn(c["saida"]["seguranca"], ("ssl", "starttls"), chave)
            self.assertNotIn("{dominio}", c["entrada"]["host"], chave)


class TestDescoberta(unittest.TestCase):
    def test_xml_do_ispdb_prefere_ssl_e_imap(self):
        c = autoconfig.ler_xml_autoconfig(ISPDB_XML, "ana@exemplo.com.br")
        self.assertEqual(c["entrada"], {"tipo": "imap", "host": "imap.exemplo.com.br", "porta": 993, "seguranca": "ssl",
                                        "usuario": "ana"})
        self.assertEqual(c["saida"]["host"], "smtp.exemplo.com.br")
        self.assertEqual(c["saida"]["usuario"], "ana@exemplo.com.br")
        self.assertEqual(c["nome_provedor"], "Exemplo Hospedagem")

    def test_cascata(self):
        nada = lambda *a: None  # noqa: E731
        etapas = {"mx": lambda d: ["mx.provedor.invalid"], "ispdb": nada, "dominio": nada, "srv": nada,
                  "adivinhar": lambda d, e: {"entrada": {"host": "mail." + d}, "saida": {}}}
        config, origem = autoconfig.descobrir("ana@empresa.invalid", etapas)
        self.assertEqual((config["entrada"]["host"], origem), ("mail.empresa.invalid", "adivinhar"))
        # catálogo vem antes da rede
        config, origem = autoconfig.descobrir("ana@gmail.com", {"mx": None})
        self.assertEqual((config["provedor"], origem), ("gmail", "catalogo"))
        # MX do Google num domínio próprio
        etapas["mx"] = lambda d: ["alt1.aspmx.l.google.com"]
        config, origem = autoconfig.descobrir("ana@empresa.invalid", etapas)
        self.assertEqual((config["provedor"], origem), ("gmail", "mx"))
        self.assertEqual(autoconfig.descobrir("sem-arroba"), (None, ""))

    def test_adivinhar_pelas_portas(self):
        abertas = {("imap.empresa.invalid", 993), ("mail.empresa.invalid", 587)}
        c = autoconfig.adivinhar("empresa.invalid", "ana@empresa.invalid", lambda h, p: (h, p) in abertas)
        self.assertEqual((c["entrada"]["host"], c["entrada"]["seguranca"]), ("imap.empresa.invalid", "ssl"))
        self.assertEqual((c["saida"]["host"], c["saida"]["porta"], c["saida"]["seguranca"]), ("mail.empresa.invalid", 587, "starttls"))


class TestLeituraSegura(unittest.TestCase):
    def html(self, conteudo, permitir=False):
        bruto = lab.mensagem_de_teste("x", html=conteudo)
        return mensagem.html_para_leitura(mensagem.ler(bruto), permitir)

    def test_tira_scripts_eventos_e_formularios(self):
        saida, _ = self.html("<p onclick='roubar()'>Oi</p><script>alert(1)</script><a href='javascript:x()'>link</a>"
                             "<iframe src='https://mal.invalid'></iframe><form action='https://mal.invalid'><input></form>"
                             "<img src=x onerror=alert(1)>")
        corpo = saida.split("<body>", 1)[1]
        for proibido in ("onclick", "<script", "alert(1)", "javascript:", "<iframe", "<form", "onerror"):
            self.assertNotIn(proibido, corpo)
        self.assertIn("<p>Oi</p>", corpo)
        self.assertIn("Content-Security-Policy", saida)

    def test_imagens_remotas_bloqueadas_ate_liberar(self):
        conteudo = ("<img src='https://rastreio.invalid/p.gif'><div style='background:url(https://rastreio.invalid/f.png)'></div>"
                    "<style>@import url('https://rastreio.invalid/a.css'); b{background:url(//rastreio.invalid/b.png)}</style>")
        saida, bloqueadas = self.html(conteudo)
        self.assertNotIn("rastreio.invalid", saida.split("<body>", 1)[1])
        self.assertGreaterEqual(bloqueadas, 3)
        saida, bloqueadas = self.html(conteudo, permitir=True)
        self.assertIn("https://rastreio.invalid/p.gif", saida)
        self.assertEqual(bloqueadas, 0)

    def test_imagem_embutida_vira_data(self):
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = "a@x.invalid", "b@x.invalid", "cid"
        msg.set_content("texto")
        msg.add_alternative("<p><img src='cid:logo123'></p>", subtype="html")
        msg.get_payload()[1].add_related(b"\x89PNG\r\n\x1a\nfalso", maintype="image", subtype="png", cid="<logo123>")
        saida, bloqueadas = mensagem.html_para_leitura(mensagem.ler(msg.as_bytes()))
        self.assertIn("data:image/png;base64,", saida)
        self.assertEqual(bloqueadas, 0)

    def test_texto_simples_com_links_e_citacao(self):
        saida, _ = mensagem.html_para_leitura(mensagem.ler(lab.mensagem_de_teste("x", corpo="Veja https://duiaos.com.br\n> citado <b>")))
        self.assertIn('<a href="https://duiaos.com.br"', saida)
        self.assertIn("citacao", saida)
        self.assertIn("&lt;b&gt;", saida)


class TestEscrever(unittest.TestCase):
    def test_resumo_anexos_e_previa(self):
        bruto = lab.mensagem_de_teste("=?utf-8?q?Relat=C3=B3rio?=", corpo="Segue o relatório.\n> antigo", anexo=("r.pdf", b"%PDF"))
        r = mensagem.resumo(bruto, 7, {"\\Seen", "\\Flagged"})
        self.assertEqual((r["uid"], r["assunto"], r["de_nome"], r["lida"], r["sinalizada"], r["tem_anexo"]),
                         (7, "Relatório", "Bruno Lima", True, True, True))
        self.assertEqual(r["previa"], "Segue o relatório.")
        self.assertEqual(mensagem.anexos(mensagem.ler(bruto))[0]["nome"], "r.pdf")

    def test_responder_a_todos_sem_mim_e_sem_repetir(self):
        bruto = lab.mensagem_de_teste("Reunião", de="Bruno <bruno@x.invalid>",
                                      para="ana@lab.invalid, Carla <carla@x.invalid>, bruno@x.invalid")
        campos = mensagem.rascunho_de_resposta(mensagem.ler(bruto), "ana@lab.invalid", todos=True)
        self.assertEqual(campos["para"], "Bruno <bruno@x.invalid>")
        self.assertEqual(campos["cc"], "Carla <carla@x.invalid>")
        self.assertEqual(campos["assunto"], "Re: Reunião")
        self.assertIn("> Olá, Ana!", campos["corpo"])
        self.assertTrue(campos["em_resposta_a"].startswith("<"))

    def test_assunto_sem_prefixos_repetidos(self):
        self.assertEqual(mensagem.assunto_resposta("RE: Res: Fwd: Oi"), "Re: Oi")
        self.assertEqual(mensagem.assunto_resposta("Oi", "Enc:"), "Enc: Oi")

    def test_montar_com_anexo_e_destinatarios(self):
        pasta = Path(tempfile.mkdtemp())
        arquivo = pasta / "foto.png"
        arquivo.write_bytes(b"\x89PNG")
        msg, destinos = mensagem.montar("Ana", "ana@lab.invalid", "Bruno <b@x.invalid>, c@x.invalid", "Oi", "Corpo",
                                        cc="d@x.invalid", cco="e@x.invalid", anexos_caminhos=[arquivo],
                                        em_resposta_a="<1@x>", referencias="<0@x>", assinatura="Ana")
        self.assertEqual(destinos, ["b@x.invalid", "c@x.invalid", "d@x.invalid", "e@x.invalid"])
        self.assertNotIn("e@x.invalid", msg.as_string().split("\n\n", 1)[0])     # Cco nunca vai no cabeçalho
        self.assertEqual(msg["References"], "<0@x> <1@x>")
        self.assertIn("foto.png", [p.get_filename() for p in msg.iter_attachments()])
        self.assertIn("-- \nAna", msg.get_body(("plain",)).get_content())
        shutil.rmtree(pasta)


class TestPastasImap(unittest.TestCase):
    def test_utf7_modificado(self):
        self.assertEqual(servidores.utf7_imap_para_texto("Itens Exclu&AO0-dos"), "Itens Excluídos")
        self.assertEqual(servidores.utf7_imap_para_texto("A &- B"), "A & B")
        for texto in ("Lixo Eletrônico", "Ações & Notas", "日本語"):
            self.assertEqual(servidores.utf7_imap_para_texto(servidores.texto_para_utf7_imap(texto)), texto)

    def test_linha_list_e_papel(self):
        item = servidores.ler_linha_list(b'(\\HasNoChildren \\Sent) "/" "[Gmail]/E-mails enviados"')
        self.assertEqual(item["caminho"], "[Gmail]/E-mails enviados")
        self.assertEqual(servidores.papel_da_pasta(item["caminho"], item["flags"], item["separador"]), "enviados")
        self.assertEqual(servidores.papel_da_pasta("INBOX", []), "entrada")
        self.assertEqual(servidores.papel_da_pasta("INBOX.Itens Exclu&AO0-dos", [], "."), "lixeira")
        self.assertEqual(servidores.papel_da_pasta("Projetos", []), "")
        literal = servidores.ler_linha_list((b'(\\HasNoChildren) "." {9}', b"Rascunhos"))
        self.assertEqual(literal["caminho"], "Rascunhos")


@unittest.skipUnless(lab.disponivel(), "precisa do dovecot, do openssl e do aiosmtpd")
class TestMotorContraServidoresReais(unittest.TestCase):
    """O motor do Mail Box falando com um Dovecot e um SMTP de verdade."""

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        os.environ["DUIAOS_MAILBOX_COFRE"] = "memoria"
        import caixa_postal
        import cofre
        self.caixa_postal = caixa_postal
        self.contas = caixa_postal.Contas(self.temp / "contas.json")
        self.banco = caixa_postal.Banco(self.temp / "dados" / "mailbox.db")
        self.cofre = cofre.abrir()
        self.eventos = []

    def tearDown(self):
        self.banco.fechar()
        shutil.rmtree(self.temp, ignore_errors=True)

    def motor(self, config):
        import sincronizador
        conta = self.contas.adicionar("Ana", lab.USUARIO, config)
        self.cofre.guardar(conta["id"], "entrada", lab.SENHA)
        motor = sincronizador.Motor(self.contas, self.banco, self.cofre, lambda e, d: self.eventos.append((e, d)))
        motor.iniciar()
        return motor, conta

    def esperar(self, condicao, tempo=15):
        limite = time.time() + tempo
        while time.time() < limite:
            if condicao():
                return True
            time.sleep(0.1)
        return False

    def erros(self):
        return [d for e, d in self.eventos if e in ("erro", "falha_envio")]

    def test_imap_sincroniza_marca_move_apaga_e_envia(self):
        with lab.Laboratorio() as servidor:
            servidor.entregar(lab.mensagem_de_teste("Primeira"), lida=True)
            servidor.entregar(lab.mensagem_de_teste("Com anexo", anexo=("r.pdf", b"%PDF-1.4")))
            servidor.entregar(lab.mensagem_de_teste("Terceira"))
            servidor.entregar(lab.mensagem_de_teste("Arquivo antigo"), pasta="Itens Arquivados")
            motor, conta = self.motor(servidor.conta_imap)
            try:
                motor.sincronizar_todas()
                self.assertTrue(self.esperar(lambda: any(e == "mensagens" for e, _ in self.eventos) and
                                             (self.banco.pasta_por_papel(conta["id"], "entrada") or {}).get("total") == 3), self.erros())
                papeis = {p["papel"]: p for p in self.banco.pastas(conta["id"])}
                self.assertEqual(set(papeis), {"entrada", "enviados", "rascunhos", "lixeira", "spam", "arquivo"})
                entrada = papeis["entrada"]
                self.assertEqual(self.banco.pasta(entrada["id"])["nao_lidas"], 2)
                msgs = {m["assunto"]: m for m in self.banco.mensagens(entrada["id"])}
                self.assertTrue(msgs["Com anexo"]["tem_anexo"])
                self.assertIsNotNone(self.banco.ler_corpo(conta["id"], entrada["id"], msgs["Terceira"]["uid"]))

                # marcar como lida chega ao servidor: um novo cliente vê a marcação
                motor.pedir(conta["id"], "marcar", id_mensagem=msgs["Terceira"]["id"], campo="lida", valor=True)
                motor.pedir(conta["id"], "apagar", id_mensagem=msgs["Primeira"]["id"])
                self.assertTrue(self.esperar(lambda: self.banco.pasta(papeis["lixeira"]["id"])["total"] == 1), self.erros())
                cliente = servidores.Imap(servidor.conta_imap["entrada"], lab.SENHA, verificar=False).conectar()
                cliente.selecionar("INBOX")
                flags = cliente.flags(cliente.buscar_uids("ALL"))
                cliente.fechar()
                self.assertEqual(len(flags), 2)
                self.assertTrue(all("\\Seen" in f for f in flags.values()) is False)       # "Com anexo" segue não lida
                self.assertEqual(sum("\\Seen" in f for f in flags.values()), 1)

                # apagar na Lixeira apaga de vez
                na_lixeira = self.banco.mensagens(papeis["lixeira"]["id"])[0]
                motor.pedir(conta["id"], "apagar", id_mensagem=na_lixeira["id"])
                self.assertTrue(self.esperar(lambda: self.banco.pasta(papeis["lixeira"]["id"])["total"] == 0), self.erros())

                # enviar: SMTP com login e cópia em Enviados (o Dovecot não guarda sozinho)
                motor.pedir(conta["id"], "enviar", de_nome="Ana", para="Carlos <carlos@exemplo.invalid>", assunto="Olá",
                            corpo="Teste de envio", cco="oculto@exemplo.invalid", id_respondida=msgs["Com anexo"]["id"])
                self.assertTrue(self.esperar(lambda: self.banco.pasta(papeis["enviados"]["id"])["total"] == 1), self.erros())
                self.assertEqual(len(servidor.smtp_recebidas), 1)
                self.assertEqual(sorted(servidor.smtp_recebidas[0]["para"]), ["carlos@exemplo.invalid", "oculto@exemplo.invalid"])
                self.assertNotIn(b"oculto@", servidor.smtp_recebidas[0]["bruto"])
                self.assertTrue(self.esperar(lambda: self.banco.mensagem(msgs["Com anexo"]["id"])["respondida"] == 1))

                # mensagem nova no servidor aparece na próxima sincronização, e vira aviso de "novas"
                servidor.entregar(lab.mensagem_de_teste("Chegou agora"))
                motor.sincronizar_todas()
                self.assertTrue(self.esperar(lambda: any(e == "novas" for e, _ in self.eventos)), self.erros())
                novas = next(d for e, d in self.eventos if e == "novas")["lista"]
                self.assertEqual([m["assunto"] for m in novas], ["Chegou agora"])
                self.assertEqual(self.erros(), [])
            finally:
                motor.encerrar()

    def test_starttls_e_senha_errada(self):
        with lab.Laboratorio() as servidor:
            servidores.testar_entrada(servidor.conta_starttls, lab.SENHA)
            servidores.testar_saida(servidor.conta_imap, lab.SENHA)
            with self.assertRaises(servidores.ErroDeConta) as erro:
                servidores.testar_entrada(servidor.conta_imap, "errada")
            self.assertEqual(str(erro.exception), "Usuário ou senha incorretos.")
            with self.assertRaises(servidores.ErroDeConta):
                servidores.testar_saida(servidor.conta_imap, "errada")
            # certificado autoassinado é recusado quando a conferência está ligada
            with self.assertRaises(servidores.ErroDeConta) as erro:
                servidores.testar_entrada(dict(servidor.conta_imap, verificar_certificado=True), lab.SENHA)
            self.assertIn("certificado", str(erro.exception))

    def test_pop3_baixa_sem_repetir(self):
        with lab.Laboratorio() as servidor:
            servidor.entregar(lab.mensagem_de_teste("Pelo POP 1"))
            servidor.entregar(lab.mensagem_de_teste("Pelo POP 2"))
            motor, conta = self.motor(servidor.conta_pop)
            try:
                motor.sincronizar_todas()
                self.assertTrue(self.esperar(lambda: (self.banco.pasta_por_papel(conta["id"], "entrada") or {}).get("total") == 2),
                                self.erros())
                motor.sincronizar_todas()
                time.sleep(1.5)
                entrada = self.banco.pasta_por_papel(conta["id"], "entrada")
                self.assertEqual(self.banco.pasta(entrada["id"])["total"], 2)          # nada repetido
                m = self.banco.mensagens(entrada["id"])[0]
                motor.pedir(conta["id"], "apagar", id_mensagem=m["id"])                 # vai para a Lixeira local
                self.assertTrue(self.esperar(lambda: self.banco.pasta(self.banco.pasta_por_papel(conta["id"], "lixeira")["id"])["total"] == 1))
                self.assertEqual(self.erros(), [])
            finally:
                motor.encerrar()


@unittest.skipUnless(TEM_MOTOR and shutil.which("xvfb-run"), "precisa do PySide6 com o Qt WebEngine e do xvfb-run")
class TestTelasDoMailBox(unittest.TestCase):
    def test_telas(self):
        for pagina in ("caixa", "wizard", "escrever"):
            with self.subTest(pagina=pagina):
                destino = Path(tempfile.mkdtemp()) / f"mailbox-{pagina}.png"
                ambiente = dict(os.environ, QTWEBENGINE_DISABLE_SANDBOX="1" if os.getuid() == 0 else "")
                r = subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1400x900x24", sys.executable,
                                    str(RAIZ / "apps/mailbox/main.py"), "--demonstracao", "--pagina", pagina,
                                    "--captura", str(destino)], capture_output=True, text=True, timeout=120, env=ambiente)
                self.assertEqual([l for l in r.stderr.splitlines() if ".qml:" in l], [], r.stderr[-2000:])
                self.assertEqual(r.returncode, 0, r.stderr[-1500:])
                self.assertTrue(destino.exists() and destino.stat().st_size > 20000)


if __name__ == "__main__":
    unittest.main()
