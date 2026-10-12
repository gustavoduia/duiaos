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

    def carregar(self, nome, manter):
        """Carrega o modelo na memória sem gerar nada. manter: -1 (sempre) ou
        tempo sem uso até descarregar (ex.: "30m"). Leva de segundos a um minuto."""
        try:
            with self._pedir("POST", "/api/generate", {"model": nome, "keep_alive": manter}, tempo=300):
                pass
        except OSError as erro:
            raise ErroOllama(f"Não consegui carregar {nome} na memória.") from erro

    def descarregar(self, nome):
        """Tira o modelo da memória (libera a RAM para o próximo)."""
        try:
            with self._pedir("POST", "/api/generate", {"model": nome, "keep_alive": 0}, tempo=30):
                pass
        except OSError:
            pass
