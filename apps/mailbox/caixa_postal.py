"""DuiaOS — Mail Box: contas, pastas e mensagens guardadas no computador.

Contas em ~/.config/duiaos/mailbox/contas.json (sem senhas: elas ficam no cofre). Pastas e mensagens em
~/.local/share/duiaos/mailbox/mailbox.db (SQLite, busca pelo FTS5); o conteúdo de cada mensagem em
corpos/<conta>/<pasta>/<uid>.eml. Tudo com permissão só da pessoa (0600/0700).

Sem Qt: testável sozinho.
"""
import json
import os
import shutil
import sqlite3
import threading
import time
import uuid
from pathlib import Path

PASTA_DADOS = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "duiaos" / "mailbox"
ARQUIVO_CONTAS = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "duiaos" / "mailbox" / "contas.json"

PAPEIS = ("entrada", "enviados", "rascunhos", "lixeira", "spam", "arquivo")
ORDEM_PAPEIS = {p: i for i, p in enumerate(PAPEIS)}
NOMES_PAPEIS = {"entrada": "Entrada", "enviados": "Enviados", "rascunhos": "Rascunhos", "lixeira": "Lixeira",
                "spam": "Spam", "arquivo": "Arquivo"}

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pastas (
    id INTEGER PRIMARY KEY, conta TEXT NOT NULL, caminho TEXT NOT NULL, nome TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT '', separador TEXT NOT NULL DEFAULT '/', uidvalidity INTEGER NOT NULL DEFAULT 0,
    ultimo_uid INTEGER NOT NULL DEFAULT 0, nao_lidas INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0,
    UNIQUE (conta, caminho));
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY, conta TEXT NOT NULL, pasta INTEGER NOT NULL REFERENCES pastas(id) ON DELETE CASCADE,
    uid INTEGER NOT NULL, message_id TEXT NOT NULL DEFAULT '', assunto TEXT NOT NULL DEFAULT '',
    de_nome TEXT NOT NULL DEFAULT '', de_email TEXT NOT NULL DEFAULT '', para TEXT NOT NULL DEFAULT '',
    cc TEXT NOT NULL DEFAULT '', data REAL NOT NULL DEFAULT 0, lida INTEGER NOT NULL DEFAULT 0,
    sinalizada INTEGER NOT NULL DEFAULT 0, respondida INTEGER NOT NULL DEFAULT 0, tem_anexo INTEGER NOT NULL DEFAULT 0,
    previa TEXT NOT NULL DEFAULT '', tamanho INTEGER NOT NULL DEFAULT 0, baixada INTEGER NOT NULL DEFAULT 0,
    referencias TEXT NOT NULL DEFAULT '', em_resposta_a TEXT NOT NULL DEFAULT '',
    UNIQUE (pasta, uid));
CREATE TABLE IF NOT EXISTS pop_vistos (conta TEXT NOT NULL, uidl TEXT NOT NULL, PRIMARY KEY (conta, uidl));
CREATE INDEX IF NOT EXISTS mensagens_pasta_data ON mensagens (pasta, data DESC);
CREATE VIRTUAL TABLE IF NOT EXISTS mensagens_busca USING fts5 (
    assunto, de_nome, de_email, para, previa, content='mensagens', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS mensagens_ai AFTER INSERT ON mensagens BEGIN
    INSERT INTO mensagens_busca (rowid, assunto, de_nome, de_email, para, previa)
    VALUES (new.id, new.assunto, new.de_nome, new.de_email, new.para, new.previa); END;
CREATE TRIGGER IF NOT EXISTS mensagens_ad AFTER DELETE ON mensagens BEGIN
    INSERT INTO mensagens_busca (mensagens_busca, rowid, assunto, de_nome, de_email, para, previa)
    VALUES ('delete', old.id, old.assunto, old.de_nome, old.de_email, old.para, old.previa); END;
CREATE TRIGGER IF NOT EXISTS mensagens_au AFTER UPDATE OF assunto, de_nome, de_email, para, previa ON mensagens BEGIN
    INSERT INTO mensagens_busca (mensagens_busca, rowid, assunto, de_nome, de_email, para, previa)
    VALUES ('delete', old.id, old.assunto, old.de_nome, old.de_email, old.para, old.previa);
    INSERT INTO mensagens_busca (rowid, assunto, de_nome, de_email, para, previa)
    VALUES (new.id, new.assunto, new.de_nome, new.de_email, new.para, new.previa); END;
"""

CAMPOS_RESUMO = ("uid", "message_id", "assunto", "de_nome", "de_email", "para", "cc", "data", "lida", "sinalizada",
                 "respondida", "tem_anexo", "previa", "tamanho", "referencias", "em_resposta_a")


# ------------------------------------------------------------------------------------------- contas
class Contas:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else ARQUIVO_CONTAS
        try:
            self.lista = json.loads(self.caminho.read_text())
        except (OSError, ValueError):
            self.lista = []

    def salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.caminho.parent, 0o700)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(json.dumps(self.lista, ensure_ascii=False, indent=2))
        os.chmod(temporario, 0o600)
        temporario.replace(self.caminho)

    def adicionar(self, nome, email, config):
        conta = {"id": uuid.uuid4().hex[:12], "nome": nome, "email": email, "provedor": config.get("provedor", ""),
                 "nome_provedor": config.get("nome_provedor", ""), "entrada": config["entrada"], "saida": config["saida"],
                 "autenticacao": config.get("autenticacao", "senha"), "salva_enviados": config.get("salva_enviados", False),
                 "pastas": config.get("pastas", {}), "verificar_certificado": config.get("verificar_certificado", True),
                 "assinatura": "", "dias_offline": 60, "manter_no_servidor": True, "criada": time.time()}
        self.lista.append(conta)
        self.salvar()
        return conta

    def obter(self, id_conta):
        return next((c for c in self.lista if c["id"] == id_conta), None)

    def atualizar(self, id_conta, **campos):
        conta = self.obter(id_conta)
        if conta:
            conta.update(campos)
            self.salvar()
        return conta

    def remover(self, id_conta):
        self.lista = [c for c in self.lista if c["id"] != id_conta]
        self.salvar()


# ------------------------------------------------------------------------------------------- banco
class Banco:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else PASTA_DADOS / "mailbox.db"
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.caminho.parent, 0o700)
        self._trava = threading.RLock()
        self._con = sqlite3.connect(self.caminho, check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA foreign_keys=ON")
        self._con.executescript(ESQUEMA)
        os.chmod(self.caminho, 0o600)
        self.pasta_corpos = self.caminho.parent / "corpos"

    def _exec(self, sql, parametros=()):
        with self._trava, self._con:
            return self._con.execute(sql, parametros)

    def _todos(self, sql, parametros=()):
        with self._trava:
            return [dict(l) for l in self._con.execute(sql, parametros).fetchall()]

    def _um(self, sql, parametros=()):
        linhas = self._todos(sql, parametros)
        return linhas[0] if linhas else None

    # ---------------------------------------------------------------- pastas
    def gravar_pasta(self, conta, caminho, nome, papel="", separador="/"):
        self._exec("INSERT INTO pastas (conta, caminho, nome, papel, separador) VALUES (?, ?, ?, ?, ?) "
                   "ON CONFLICT (conta, caminho) DO UPDATE SET nome = excluded.nome, papel = excluded.papel, "
                   "separador = excluded.separador", (conta, caminho, nome, papel, separador))
        return self._um("SELECT * FROM pastas WHERE conta = ? AND caminho = ?", (conta, caminho))

    def pastas(self, conta=None):
        sql, par = ("SELECT * FROM pastas WHERE conta = ?", (conta,)) if conta else ("SELECT * FROM pastas", ())
        lista = self._todos(sql, par)
        return sorted(lista, key=lambda p: (p["conta"], ORDEM_PAPEIS.get(p["papel"], 99), p["caminho"].lower()))

    def pasta(self, id_pasta):
        return self._um("SELECT * FROM pastas WHERE id = ?", (id_pasta,))

    def pasta_por_papel(self, conta, papel):
        return self._um("SELECT * FROM pastas WHERE conta = ? AND papel = ? ORDER BY id LIMIT 1", (conta, papel))

    def remover_pastas_ausentes(self, conta, caminhos):
        for p in self.pastas(conta):
            if p["caminho"] not in caminhos:
                self._apagar_corpos(conta, p["id"])
                self._exec("DELETE FROM pastas WHERE id = ?", (p["id"],))

    def estado_pasta(self, id_pasta, **campos):
        if campos:
            definicoes = ", ".join(f"{k} = ?" for k in campos)
            self._exec(f"UPDATE pastas SET {definicoes} WHERE id = ?", (*campos.values(), id_pasta))

    def recontar(self, id_pasta):
        conta = self._um("SELECT COUNT(*) AS total, SUM(CASE WHEN lida = 0 THEN 1 ELSE 0 END) AS nao_lidas "
                         "FROM mensagens WHERE pasta = ?", (id_pasta,))
        self.estado_pasta(id_pasta, total=conta["total"] or 0, nao_lidas=conta["nao_lidas"] or 0)

    def esvaziar_pasta(self, id_pasta):
        pasta = self.pasta(id_pasta)
        if pasta:
            self._apagar_corpos(pasta["conta"], id_pasta)
        self._exec("DELETE FROM mensagens WHERE pasta = ?", (id_pasta,))

    # ---------------------------------------------------------------- mensagens
    def caminho_corpo(self, conta, id_pasta, uid):
        return self.pasta_corpos / conta / str(id_pasta) / f"{uid}.eml"

    def gravar_mensagem(self, conta, id_pasta, resumo, bruto=None):
        valores = [resumo.get(c, "") if c not in ("lida", "sinalizada", "respondida", "tem_anexo") else int(bool(resumo.get(c)))
                   for c in CAMPOS_RESUMO]
        baixada = 1 if bruto is not None else 0
        self._exec(f"INSERT INTO mensagens (conta, pasta, {', '.join(CAMPOS_RESUMO)}, baixada) "
                   f"VALUES (?, ?, {', '.join('?' for _ in CAMPOS_RESUMO)}, ?) "
                   "ON CONFLICT (pasta, uid) DO UPDATE SET lida = excluded.lida, sinalizada = excluded.sinalizada, "
                   "respondida = excluded.respondida, baixada = MAX(baixada, excluded.baixada)",
                   (conta, id_pasta, *valores, baixada))
        if bruto is not None:
            self.gravar_corpo(conta, id_pasta, resumo["uid"], bruto)

    def gravar_corpo(self, conta, id_pasta, uid, bruto):
        destino = self.caminho_corpo(conta, id_pasta, uid)
        destino.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.pasta_corpos, 0o700)
        temporario = destino.with_suffix(".tmp")
        temporario.write_bytes(bruto)
        os.chmod(temporario, 0o600)
        temporario.replace(destino)
        self._exec("UPDATE mensagens SET baixada = 1 WHERE pasta = ? AND uid = ?", (id_pasta, uid))

    def ler_corpo(self, conta, id_pasta, uid):
        caminho = self.caminho_corpo(conta, id_pasta, uid)
        return caminho.read_bytes() if caminho.exists() else None

    def mensagem(self, id_mensagem):
        return self._um("SELECT * FROM mensagens WHERE id = ?", (id_mensagem,))

    def mensagens(self, id_pasta=None, busca="", limite=400, papel=None):
        """Mensagens de uma pasta (ou de todas as pastas com um papel, como "entrada": a caixa unificada)."""
        filtro, parametros = [], []
        if id_pasta is not None:
            filtro.append("m.pasta = ?")
            parametros.append(id_pasta)
        if papel:
            filtro.append("p.papel = ?")
            parametros.append(papel)
        juncao = "JOIN pastas p ON p.id = m.pasta"
        if busca.strip():
            juncao += " JOIN mensagens_busca b ON b.rowid = m.id"
            filtro.append("mensagens_busca MATCH ?")
            parametros.append(" ".join(f'"{p.replace(chr(34), "")}"*' for p in busca.split()))
        onde = ("WHERE " + " AND ".join(filtro)) if filtro else ""
        return self._todos(f"SELECT m.*, p.papel AS papel FROM mensagens m {juncao} {onde} "
                           f"ORDER BY m.data DESC LIMIT ?", (*parametros, limite))

    def uids(self, id_pasta):
        return {l["uid"] for l in self._todos("SELECT uid FROM mensagens WHERE pasta = ?", (id_pasta,))}

    def marcar(self, id_mensagem, **campos):
        definicoes = ", ".join(f"{k} = ?" for k in campos)
        self._exec(f"UPDATE mensagens SET {definicoes} WHERE id = ?", (*[int(v) for v in campos.values()], id_mensagem))

    def atualizar_flags(self, id_pasta, flags_por_uid):
        with self._trava, self._con:
            for uid, flags in flags_por_uid.items():
                self._con.execute("UPDATE mensagens SET lida = ?, sinalizada = ?, respondida = ? WHERE pasta = ? AND uid = ?",
                                  (int("\\Seen" in flags), int("\\Flagged" in flags), int("\\Answered" in flags), id_pasta, uid))

    def remover_mensagens(self, id_pasta, uids):
        pasta = self.pasta(id_pasta)
        for uid in uids:
            if pasta:
                caminho = self.caminho_corpo(pasta["conta"], id_pasta, uid)
                caminho.unlink(missing_ok=True)
            self._exec("DELETE FROM mensagens WHERE pasta = ? AND uid = ?", (id_pasta, uid))

    def nao_baixadas(self, id_pasta, limite_tamanho, limite=200):
        return self._todos("SELECT uid FROM mensagens WHERE pasta = ? AND baixada = 0 AND tamanho <= ? "
                           "ORDER BY data DESC LIMIT ?", (id_pasta, limite_tamanho, limite))

    def pop_visto(self, conta, uidl):
        return bool(self._um("SELECT 1 AS s FROM pop_vistos WHERE conta = ? AND uidl = ?", (conta, uidl)))

    def marcar_pop_visto(self, conta, uidl):
        self._exec("INSERT OR IGNORE INTO pop_vistos (conta, uidl) VALUES (?, ?)", (conta, uidl))

    def proximo_uid(self, id_pasta):
        linha = self._um("SELECT MAX(uid) AS m FROM mensagens WHERE pasta = ?", (id_pasta,))
        return (linha["m"] or 0) + 1

    def remover_conta(self, conta):
        self._exec("DELETE FROM pop_vistos WHERE conta = ?", (conta,))
        self._exec("DELETE FROM mensagens WHERE conta = ?", (conta,))
        self._exec("DELETE FROM pastas WHERE conta = ?", (conta,))
        shutil.rmtree(self.pasta_corpos / conta, ignore_errors=True)

    def _apagar_corpos(self, conta, id_pasta):
        shutil.rmtree(self.pasta_corpos / conta / str(id_pasta), ignore_errors=True)

    def fechar(self):
        self._con.close()
