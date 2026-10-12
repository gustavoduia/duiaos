# IA do sistema (duiaos-ia)

A IA é um recurso do DuiaOS, não de um programa (ADR 029). Esta pasta é o
serviço que guarda **o modelo de IA local ativo, um só para o sistema
inteiro** (ADR 030), e cuida do catálogo de modelos. Vai para o pacote
`duiaos-ia`, junto com a Central de IA (`apps/central-de-ia/`).

| Arquivo | O que faz |
| --- | --- |
| `catalogo.json` | Modelos oferecidos: Qwen3.5, Qwen3, Gemma 4, Llama 3 a 3.3 e Phi-3 a 4, com tamanho, licença e o padrão (`qwen3.5:4b`) |
| `catalogo.py` | Regras sem rede: memória necessária, o que cabe neste computador, catálogo montado para as telas |
| `motor_ollama.py` | Conversa com o Ollama local (listar, baixar com progresso, remover) |
| `servico.py` | Serviço do sistema `duiaos-ia.service`, D-Bus `org.duiaos.IA1` |
| `cliente.py` | Comando `duiaos-ia` |
| `testes/` | Testes (o do serviço sobe um D-Bus e um Ollama de mentira) |

## Contrato para outros programas

- **Ler** (sem D-Bus): `/var/lib/duiaos-ia/estado.json`, legível por todos.
  `ativo` é o modelo a usar (nome do Ollama, ex.: `qwen3.5:4b`), `endereco`
  é a API do Ollama (`http://127.0.0.1:11434`), `tarefa` traz o download em
  andamento (`modelo`, `fracao`, `concluido`, `total`, `automatico`) e
  `ultima`, o resultado do último download.
- **Mudar** (D-Bus do sistema, `org.duiaos.IA1` em `/org/duiaos/IA1`):
  `Estado() → s` (JSON com o catálogo), `Baixar(s)`, `Ativar(s)`,
  `Remover(s)`, `Cancelar()`, `GarantirPadrao()`; sinal `Mudou(s)` com o
  estado público. Mudanças exigem a autorização `org.duiaos.ia.gerenciar` do
  polkit: a pessoa sentada no computador tem; pela sessão SSH, só com `sudo`.
- Só modelos do catálogo são aceitos. O modelo ativo não pode ser removido
  (ative outro antes). Modelos que não cabem na memória são recusados.

## 1º login

O `autostart` da sessão chama `duiaos-ia garantir-padrao`. Sem modelo ativo,
o serviço ativa o padrão se ele já estiver baixado; se não, começa a baixá-lo
(ou um menor da mesma família, se a memória não der) e o ativa ao terminar.
Se a pessoa já escolheu outro modelo, nada muda.

## Testar

```bash
python3 -m unittest discover -s ia/testes -t ia          # precisa de python3-gi e dbus-daemon
python3 apps/central-de-ia/main.py --demonstracao        # visual da Central, sem o serviço
```
