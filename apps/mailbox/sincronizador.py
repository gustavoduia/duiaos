"""DuiaOS — Mail Box: o motor. Uma linha de trabalho por conta, com a conexão aberta e uma fila de pedidos.

Pedidos: sincronizar (todas as pastas principais), sincronizar_pasta, baixar (o conteúdo de uma mensagem
grande ao abrir), marcar (lida/sinalizada), mover, apagar (para a Lixeira; na Lixeira, de vez), enviar
(SMTP e uma cópia em Enviados quando o provedor não guarda sozinho).

Avisos para a janela pela função `avisar(evento, dados)`, chamada da linha de trabalho:
  pastas(conta)  mensagens(conta, pasta)  novas(conta, lista)  estado(conta, texto)  erro(conta, texto)
  enviada(conta)  falha_envio(conta, texto)  corpo(id)

Sem Qt: testável contra servidores de verdade (Dovecot e um SMTP de teste em shell/testes/test_mailbox.py).
"""
import queue
import threading
import time

import mensagem
import servidores
from servidores import ErroDeConta

LIMITE_INICIAL = 300            # mensagens mais recentes de cada pasta na primeira sincronização
PAPEIS_AUTOMATICOS = ("entrada", "enviados", "rascunhos", "lixeira", "spam")


class Trabalhador(threading.Thread):
    def __init__(self, conta, banco, cofre, avisar):
        super().__init__(daemon=True, name=f"mailbox-{conta['id']}")
        self.conta = conta
        self.banco = banco
        self.cofre = cofre
        self.avisar = avisar
        self.fila = queue.Queue()
        self.imap = None
        self.parar = False
        self.primeira = True

    # ---------------------------------------------------------------- fila
    def pedir(self, acao, **dados):
        self.fila.put((acao, dados))

    def run(self):
        while not self.parar:
            try:
                acao, dados = self.fila.get(timeout=1)
            except queue.Empty:
                continue
            if acao == "sair":
                break
            for tentativa in (1, 2):
                try:
                    getattr(self, "_" + acao)(**dados)
                    break
                except ErroDeConta as erro:
                    self._fechar()
                    if acao == "enviar":
                        self.avisar("falha_envio", {"conta": self.conta["id"], "texto": str(erro)})
                    else:
                        self.avisar("erro", {"conta": self.conta["id"], "texto": str(erro)})
                    break
                except (OSError, EOFError, servidores.imaplib.IMAP4.abort) as erro:
                    # conexão caiu no meio: reconecta e tenta mais uma vez
                    self._fechar()
                    if tentativa == 2:
                        self.avisar("erro", {"conta": self.conta["id"], "texto": "A conexão com o servidor caiu."})
                except Exception as erro:  # noqa: BLE001 — nunca deixar a linha de trabalho morrer
                    self._fechar()
                    self.avisar("erro", {"conta": self.conta["id"], "texto": f"Erro inesperado: {type(erro).__name__}"})
                    break
            self.avisar("estado", {"conta": self.conta["id"], "texto": ""})
        self._fechar()

    def encerrar(self):
        self.parar = True
        self.fila.put(("sair", {}))

    # ---------------------------------------------------------------- conexão
    def _segredo(self, servico="entrada"):
        segredo = self.cofre.ler(self.conta["id"], servico) or self.cofre.ler(self.conta["id"], "entrada")
        if segredo is None:
            raise ErroDeConta("A senha desta conta não está guardada. Entre de novo na conta.")
        return segredo

    def _cliente(self):
        if self.imap is None:
            self.imap = servidores.Imap(self.conta["entrada"], self._segredo(), self.conta.get("verificar_certificado", True),
                                        oauth=self.conta.get("autenticacao") == "oauth").conectar()
        return self.imap

    def _fechar(self):
        if self.imap is not None:
            self.imap.fechar()
        self.imap = None

    @property
    def eh_pop(self):
        return self.conta["entrada"]["tipo"] == "pop3"

    # ---------------------------------------------------------------- sincronizar
    def _sincronizar(self):
        cid = self.conta["id"]
        self.avisar("estado", {"conta": cid, "texto": "Sincronizando…"})
        if self.eh_pop:
            novas = self._sincronizar_pop()
        else:
            cliente = self._cliente()
            caminhos = set()
            for p in cliente.pastas():
                self.banco.gravar_pasta(cid, p["caminho"], p["nome"], p["papel"], p["separador"])
                caminhos.add(p["caminho"])
            self.banco.remover_pastas_ausentes(cid, caminhos)
            self.avisar("pastas", {"conta": cid})
            novas = []
            for pasta in self.banco.pastas(cid):
                if pasta["papel"] in PAPEIS_AUTOMATICOS or pasta["ultimo_uid"] > 0:
                    resultado = self._sincronizar_imap(cliente, pasta)
                    if pasta["papel"] == "entrada":
                        novas.extend(resultado)
        if novas and not self.primeira:
            self.avisar("novas", {"conta": cid, "lista": [m for m in novas if not m["lida"]]})
        self.primeira = False

    def _sincronizar_pasta(self, id_pasta):
        pasta = self.banco.pasta(id_pasta)
        if pasta and not self.eh_pop and not pasta["caminho"].startswith("local:"):
            self._sincronizar_imap(self._cliente(), pasta)

    def _sincronizar_imap(self, cliente, pasta):
        cid, pid = self.conta["id"], pasta["id"]
        info = cliente.selecionar(pasta["caminho"])
        ultimo = pasta["ultimo_uid"]
        if info["uidvalidity"] != pasta["uidvalidity"]:
            if pasta["uidvalidity"]:
                self.banco.esvaziar_pasta(pid)
            ultimo = 0
            self.banco.estado_pasta(pid, uidvalidity=info["uidvalidity"], ultimo_uid=0)
        no_servidor = cliente.buscar_uids("ALL") if info["existentes"] else []
        conjunto = set(no_servidor)
        locais = self.banco.uids(pid)
        sumiram = locais - conjunto
        if sumiram:
            self.banco.remover_mensagens(pid, sumiram)
        novos = [u for u in no_servidor if u > ultimo and u not in locais]
        if ultimo == 0:
            novos = novos[-LIMITE_INICIAL:]
        resumos = []
        if novos:
            tamanhos = cliente.tamanhos(novos)
            pequenos = [u for u in novos if tamanhos.get(u, 0) <= servidores.TAMANHO_PARA_BAIXAR]
            grandes = [u for u in novos if u not in set(pequenos)]
            for completo, lista in ((True, pequenos), (False, grandes)):
                for uid, bruto, flags, tamanho in cliente.baixar(lista, completo=completo):
                    r = mensagem.resumo(bruto, uid, flags)
                    r["tamanho"] = tamanho
                    if not completo:
                        r["previa"] = ""
                    self.banco.gravar_mensagem(cid, pid, r, bruto if completo else None)
                    resumos.append(r)
        existentes = sorted(locais & conjunto)
        if existentes:
            self.banco.atualizar_flags(pid, cliente.flags(existentes))
        if no_servidor:
            self.banco.estado_pasta(pid, ultimo_uid=max(no_servidor))
        self.banco.recontar(pid)
        self.avisar("mensagens", {"conta": cid, "pasta": pid})
        return resumos

    def _pastas_locais(self):
        cid = self.conta["id"]
        for caminho, papel in (("INBOX", "entrada"), ("local:Enviados", "enviados"), ("local:Lixeira", "lixeira")):
            from caixa_postal import NOMES_PAPEIS
            self.banco.gravar_pasta(cid, caminho, NOMES_PAPEIS[papel], papel)
        self.avisar("pastas", {"conta": cid})

    def _sincronizar_pop(self):
        cid = self.conta["id"]
        self._pastas_locais()
        entrada = self.banco.pasta_por_papel(cid, "entrada")
        cliente = servidores.Pop3(self.conta["entrada"], self._segredo(), self.conta.get("verificar_certificado", True)).conectar()
        resumos = []
        try:
            for numero, uidl in sorted(cliente.identificadores().items()):
                if self.banco.pop_visto(cid, uidl):
                    continue
                bruto = cliente.baixar(numero)
                uid = self.banco.proximo_uid(entrada["id"])
                r = mensagem.resumo(bruto, uid, set())
                self.banco.gravar_mensagem(cid, entrada["id"], r, bruto)
                self.banco.marcar_pop_visto(cid, uidl)
                resumos.append(r)
                if not self.conta.get("manter_no_servidor", True):
                    cliente.apagar(numero)
        finally:
            cliente.fechar()
        self.banco.recontar(entrada["id"])
        self.avisar("mensagens", {"conta": cid, "pasta": entrada["id"]})
        return resumos

    # ---------------------------------------------------------------- uma mensagem
    def _mensagem_e_pasta(self, id_mensagem):
        m = self.banco.mensagem(id_mensagem)
        if not m:
            return None, None
        return m, self.banco.pasta(m["pasta"])

    def _remota(self, pasta):
        return not self.eh_pop and not pasta["caminho"].startswith("local:")

    def _baixar(self, id_mensagem):
        m, pasta = self._mensagem_e_pasta(id_mensagem)
        if not m or self.banco.ler_corpo(m["conta"], m["pasta"], m["uid"]) is not None or not self._remota(pasta):
            self.avisar("corpo", {"id": id_mensagem})
            return
        cliente = self._cliente()
        cliente.selecionar(pasta["caminho"])
        for uid, bruto, _flags, _tam in cliente.baixar([m["uid"]], completo=True):
            self.banco.gravar_corpo(m["conta"], m["pasta"], uid, bruto)
            if not m["previa"]:
                r = mensagem.resumo(bruto, uid)
                self.banco._exec("UPDATE mensagens SET previa = ?, tem_anexo = ? WHERE id = ?",
                                 (r["previa"], int(r["tem_anexo"]), id_mensagem))
        self.avisar("corpo", {"id": id_mensagem})

    def _marcar(self, id_mensagem, campo, valor):
        m, pasta = self._mensagem_e_pasta(id_mensagem)
        if not m:
            return
        self.banco.marcar(id_mensagem, **{campo: valor})
        self.banco.recontar(m["pasta"])
        self.avisar("mensagens", {"conta": m["conta"], "pasta": m["pasta"]})
        if self._remota(pasta):
            cliente = self._cliente()
            cliente.selecionar(pasta["caminho"])
            cliente.marcar(m["uid"], {"lida": "\\Seen", "sinalizada": "\\Flagged", "respondida": "\\Answered"}[campo], valor)

    def _mover(self, id_mensagem, id_destino):
        m, pasta = self._mensagem_e_pasta(id_mensagem)
        destino = self.banco.pasta(id_destino)
        if not m or not destino or destino["id"] == pasta["id"]:
            return
        if self._remota(pasta) and self._remota(destino):
            cliente = self._cliente()
            cliente.selecionar(pasta["caminho"])
            cliente.mover(m["uid"], destino["caminho"])
            self.banco.remover_mensagens(pasta["id"], [m["uid"]])
            self._sincronizar_imap(cliente, destino)
        else:
            bruto = self.banco.ler_corpo(m["conta"], m["pasta"], m["uid"])
            novo = dict(m)
            novo["uid"] = self.banco.proximo_uid(destino["id"])
            self.banco.gravar_mensagem(m["conta"], destino["id"], novo, bruto)
            self.banco.remover_mensagens(pasta["id"], [m["uid"]])
            self.banco.recontar(destino["id"])
        self.banco.recontar(pasta["id"])
        self.avisar("mensagens", {"conta": m["conta"], "pasta": pasta["id"]})
        self.avisar("mensagens", {"conta": m["conta"], "pasta": destino["id"]})

    def _apagar(self, id_mensagem):
        m, pasta = self._mensagem_e_pasta(id_mensagem)
        if not m:
            return
        lixeira = self.banco.pasta_por_papel(m["conta"], "lixeira")
        if lixeira and lixeira["id"] != pasta["id"]:
            self._mover(id_mensagem, lixeira["id"])
            return
        if self._remota(pasta):
            cliente = self._cliente()
            cliente.selecionar(pasta["caminho"])
            cliente.apagar(m["uid"])
        self.banco.remover_mensagens(pasta["id"], [m["uid"]])
        self.banco.recontar(pasta["id"])
        self.avisar("mensagens", {"conta": m["conta"], "pasta": pasta["id"]})

    # ---------------------------------------------------------------- enviar
    def _enviar(self, de_nome, para, assunto, corpo, cc="", cco="", anexos=(), em_resposta_a="", referencias="",
                id_respondida=0):
        cid = self.conta["id"]
        self.avisar("estado", {"conta": cid, "texto": "Enviando…"})
        msg, destinatarios = mensagem.montar(de_nome or self.conta.get("nome", ""), self.conta["email"], para, assunto, corpo,
                                             cc, cco, anexos, em_resposta_a, referencias, self.conta.get("assinatura", ""))
        if not destinatarios:
            raise ErroDeConta("Escreva pelo menos um destinatário.")
        oauth = self.conta.get("autenticacao") == "oauth"
        servidores.enviar(self.conta["saida"], self._segredo("saida"), msg, destinatarios,
                          self.conta.get("verificar_certificado", True), oauth)
        bruto = msg.as_bytes()
        self.avisar("enviada", {"conta": cid})
        # Cópia em Enviados (Gmail e Microsoft guardam sozinhos)
        try:
            if self.eh_pop:
                self._pastas_locais()
                enviados = self.banco.pasta_por_papel(cid, "enviados")
                r = mensagem.resumo(bruto, self.banco.proximo_uid(enviados["id"]), {"\\Seen"})
                self.banco.gravar_mensagem(cid, enviados["id"], r, bruto)
                self.banco.recontar(enviados["id"])
            elif not self.conta.get("salva_enviados"):
                cliente = self._cliente()
                enviados = self.banco.pasta_por_papel(cid, "enviados")
                if not enviados:
                    cliente.criar_pasta("Sent")
                    enviados = self.banco.gravar_pasta(cid, "Sent", "Enviados", "enviados")
                cliente.guardar(enviados["caminho"], bruto)
                self._sincronizar_imap(cliente, self.banco.pasta(enviados["id"]))
        except ErroDeConta as erro:
            self.avisar("erro", {"conta": cid, "texto": "A mensagem foi enviada, mas a cópia em Enviados falhou: " + str(erro)})
        if id_respondida:
            try:
                self._marcar(id_respondida, "respondida", True)
            except ErroDeConta:
                pass


class Motor:
    """Os trabalhadores de todas as contas."""

    def __init__(self, contas, banco, cofre, avisar):
        self.contas, self.banco, self.cofre, self.avisar = contas, banco, cofre, avisar
        self.trabalhadores = {}

    def iniciar(self):
        for conta in self.contas.lista:
            self._trabalhador(conta["id"])

    def _trabalhador(self, id_conta):
        t = self.trabalhadores.get(id_conta)
        if t is None or not t.is_alive():
            conta = self.contas.obter(id_conta)
            if not conta:
                return None
            t = Trabalhador(conta, self.banco, self.cofre, self.avisar)
            t.start()
            self.trabalhadores[id_conta] = t
        return t

    def pedir(self, id_conta, acao, **dados):
        t = self._trabalhador(id_conta)
        if t:
            t.pedir(acao, **dados)

    def sincronizar_todas(self):
        for conta in self.contas.lista:
            self.pedir(conta["id"], "sincronizar")

    def remover(self, id_conta):
        t = self.trabalhadores.pop(id_conta, None)
        if t:
            t.encerrar()

    def encerrar(self):
        for t in self.trabalhadores.values():
            t.encerrar()
        for t in self.trabalhadores.values():
            t.join(timeout=3)
