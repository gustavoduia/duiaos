-- DuiaOS — site: pedidos de suporte.
CREATE TABLE IF NOT EXISTS chamados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  protocolo TEXT NOT NULL UNIQUE,
  criado_em TEXT NOT NULL,
  nome TEXT NOT NULL,
  email TEXT NOT NULL,
  assunto TEXT NOT NULL,
  mensagem TEXT NOT NULL,
  situacao TEXT NOT NULL DEFAULT 'novo'   -- novo | respondido | fechado
);
CREATE INDEX IF NOT EXISTS chamados_situacao ON chamados (situacao, criado_em);
