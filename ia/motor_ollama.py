"""DuiaOS — conversa com o Ollama local (http://127.0.0.1:11434) para listar,
baixar e remover modelos. Só a biblioteca padrão do Python.

O que o Ollama devolve é dado: nomes e números são conferidos antes de usar.
"""
import json
import time
import urllib.error
import urllib.request

ENDERECO = "http://127.0.0.1:11434"


class ErroOllama(Exception):
    """Falha ao falar com o Ollama, com mensagem pronta para a pessoa."""


class Cancelado(Exception):
    pass


class Ollama:
    def __init__(self, endereco=ENDERECO):
        self.endereco = endereco.rstrip("/")
        # Fala só com o Ollama local, nunca por um proxy do sistema
        self._abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _pedir(self, metodo, caminho, dados=None, tempo=5):
        corpo = json.dumps(dados).encode() if dados is not None else None
        pedido = urllib.request.Request(self.endereco + caminho, data=corpo, method=metodo,
                                        headers={"Content-Type": "application/json"})
        return self._abridor.open(pedido, timeout=tempo)

    def versao(self):
        """Versão do Ollama, ou None se ele não está respondendo."""
        try:
            with self._pedir("GET", "/api/version", tempo=2) as resposta:
                return str(json.load(resposta).get("version", ""))[:40] or None
        except (OSError, ValueError):
            return None

    def esperar(self, segundos=30):
        """Espera o Ollama responder (ele pode estar iniciando junto com o sistema)."""
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            if self.versao():
                return True
            time.sleep(1)
        return False

    def instalados(self):
        """Nomes dos modelos baixados, ex.: {"qwen3.5:4b"}."""
        try:
            with self._pedir("GET", "/api/tags", tempo=3) as resposta:
                dados = json.load(resposta)
        except (OSError, ValueError) as erro:
            raise ErroOllama("A IA local (Ollama) não está respondendo.") from erro
        nomes = set()
        for modelo in dados.get("models") or []:
            nome = modelo.get("name") or modelo.get("model")
            if isinstance(nome, str) and len(nome) < 200:
                nomes.add(nome)
        return nomes

    def remover(self, nome):
        try:
            with self._pedir("DELETE", "/api/delete", {"model": nome}, tempo=30):
                pass
        except urllib.error.HTTPError as erro:
            if erro.code != 404:          # já não existia: tudo bem
                raise ErroOllama(f"O Ollama não conseguiu remover {nome} (erro {erro.code}).") from erro
        except OSError as erro:
            raise ErroOllama("A IA local (Ollama) não está respondendo.") from erro

    def baixar(self, nome, ao_progresso, cancelado):
        """Baixa um modelo. ao_progresso(concluido, total, status) é chamado a cada
        parte recebida; cancelado() é consultado no caminho (devolve True para parar).
        O Ollama guarda o que já veio: baixar de novo continua de onde parou."""
        partes = {}          # digest -> (concluido, total)
        try:
            resposta = self._pedir("POST", "/api/pull", {"model": nome, "stream": True}, tempo=60)
        except urllib.error.HTTPError as erro:
            raise ErroOllama(f"O Ollama recusou o download de {nome} (erro {erro.code}).") from erro
        except OSError as erro:
            raise ErroOllama("A IA local (Ollama) não está respondendo.") from erro
        with resposta:
            for linha in resposta:
                if cancelado():
                    raise Cancelado()
                try:
                    item = json.loads(linha)
                except ValueError:
                    continue
                if not isinstance(item, dict):
                    continue
                if item.get("error"):
                    raise ErroOllama(f"Download de {nome} falhou: {str(item['error'])[:200]}")
                status = str(item.get("status", ""))[:80]
                digest = item.get("digest")
                if isinstance(digest, str) and isinstance(item.get("total"), int):
                    concluido = item.get("completed") if isinstance(item.get("completed"), int) else 0
                    partes[digest] = (concluido, item["total"])
                concluido = sum(c for c, _t in partes.values())
                total = sum(t for _c, t in partes.values())
                ao_progresso(concluido, total, status)
                if status == "success":
                    return
        raise ErroOllama(f"O download de {nome} terminou antes da hora. Tente de novo.")

    # ------------------------------------------------------------ memória
    def carregados(self):
        """Modelos carregados na memória agora (prontos para responder na hora)."""
        try:
            with self._pedir("GET", "/api/ps", tempo=3) as resposta:
                dados = json.load(resposta)
        except (OSError, ValueError) as erro:
            raise ErroOllama("A IA local (Ollama) não está respondendo.") from erro
        return {m.get("name") or m.get("model") for m in dados.get("models") or []
                if isinstance(m.get("name") or m.get("model"), str)}

    def carregar(self, nome, manter, opcoes=None):
        """Carrega o modelo na memória sem gerar nada. manter: -1 (sempre) ou
        tempo sem uso até descarregar (ex.: "30m"). opcoes: as mesmas que todos os
        programas usam com este modelo (ex.: num_thread) — outras recarregariam."""
        corpo = {"model": nome, "keep_alive": manter}
        if opcoes:
            corpo["options"] = dict(opcoes)
        try:
            with self._pedir("POST", "/api/generate", corpo, tempo=300):
                pass
        except OSError as erro:
            raise ErroOllama(f"Não consegui carregar {nome} na memória.") from erro

    def medir(self, nome, manter, opcoes, texto, palavras=32):
        """Lê um texto e escreve algumas palavras; devolve os números do Ollama:
        {"carregar_s", "lidos", "ler_s", "escritos", "escrever_s"}."""
        corpo = {"model": nome, "prompt": texto, "stream": False, "keep_alive": manter, "think": False,
                 "options": {**(opcoes or {}), "num_predict": palavras, "temperature": 0, "seed": 1}}
        try:
            with self._pedir("POST", "/api/generate", corpo, tempo=900) as resposta:
                r = json.load(resposta)
        except (OSError, ValueError) as erro:
            raise ErroOllama(f"A medição de {nome} falhou.") from erro
        return {"carregar_s": r.get("load_duration", 0) / 1e9,
                "lidos": r.get("prompt_eval_count", 0), "ler_s": r.get("prompt_eval_duration", 0) / 1e9,
                "escritos": r.get("eval_count", 0), "escrever_s": r.get("eval_duration", 0) / 1e9}

    def memoria_do_carregado(self, nome):
        """(bytes na memória, bytes na placa de vídeo) do modelo carregado, ou None."""
        try:
            with self._pedir("GET", "/api/ps", tempo=3) as resposta:
                dados = json.load(resposta)
        except (OSError, ValueError):
            return None
        for m in dados.get("models") or []:
            if (m.get("name") or m.get("model")) == nome:
                return int(m.get("size") or 0), int(m.get("size_vram") or 0)
        return None

    def descarregar(self, nome):
        """Tira o modelo da memória (libera a RAM para o próximo)."""
        try:
            with self._pedir("POST", "/api/generate", {"model": nome, "keep_alive": 0}, tempo=30):
                pass
        except OSError:
            pass
