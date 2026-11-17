"""DuiaOS — motores de IA na nuvem (Configurações › Inteligência Artificial; ADR 063).

A IA local é do sistema (duiaos-ia, ADR 029). Os motores na nuvem (Google Gemini, OpenAI) são da pessoa:
cada um tem uma chave, que fica no cofre do sistema (Secret Service), e só é usado depois de ativado
aqui — ativar é o consentimento para os pedidos saírem do computador.

Contrato com os programas que usam a IA (hoje, o Wise):
  ~/.config/duiaos/ia.conf      uma seção por motor: ativado = sim|nao, modelos = a, b, c (os que a chave
                                enxerga, conferidos aqui), modelo = o preferido
  cofre do sistema              a chave: atributos {"aplicativo": "duiaos-ia", "motor": NOME}

Nenhuma chave vai para arquivo, registro ou tela (a tela só sabe se há chave).
"""
import configparser
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ARQUIVO = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "duiaos" / "ia.conf"
ATRIBUTOS = {"aplicativo": "duiaos-ia"}
MOTORES = {
    "gemini": {
        "titulo": "Google Gemini", "empresa": "Google",
        "chave_em": "https://aistudio.google.com/apikey",
        "aviso": "Os pedidos e os resultados das consultas vão para os servidores do Google. Na camada gratuita, "
                 "o Google pode usar esse conteúdo para melhorar os produtos dele.",
    },
    "openai": {
        "titulo": "OpenAI", "empresa": "OpenAI",
        "chave_em": "https://platform.openai.com/api-keys",
        "aviso": "Os pedidos e os resultados das consultas vão para os servidores da OpenAI. O uso é cobrado "
                 "pela OpenAI na conta da chave.",
    },
}
_MODELO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,80}$")
# Modelos que não conversam (voz, imagem, busca, incorporação…) ficam fora das listas
_FORA = ("embedding", "tts", "audio", "image", "imagen", "veo", "realtime", "transcribe", "moderation", "whisper",
         "dall-e", "search", "instruct", "aqa", "live", "robotics", "computer-use", "sora", "lyria")


class Erro(Exception):
    pass


# ------------------------------------------------------------------ arquivo

def _ler(arquivo=None):
    dados = configparser.ConfigParser(interpolation=None)
    try:
        dados.read(arquivo or ARQUIVO, encoding="utf-8")
    except (configparser.Error, OSError):
        pass
    return dados


def _gravar(dados, arquivo=None):
    arquivo = Path(arquivo or ARQUIVO)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(".tmp")
    with open(temporario, "w", encoding="utf-8") as saida:
        saida.write("# DuiaOS — motores de IA na nuvem (Configurações › Inteligência Artificial). As chaves ficam no cofre.\n")
        dados.write(saida)
    os.replace(temporario, arquivo)


def definir(motor, arquivo=None, **campos):
    """Muda campos de um motor: ativado (bool), modelo (str), modelos (lista)."""
    if motor not in MOTORES:
        raise Erro("motor desconhecido")
    dados = _ler(arquivo)
    if not dados.has_section(motor):
        dados.add_section(motor)
    for chave, valor in campos.items():
        if chave == "ativado":
            dados.set(motor, chave, "sim" if valor else "nao")
        elif chave == "modelo" and (valor == "" or _MODELO.match(str(valor))):
            dados.set(motor, chave, str(valor))
        elif chave == "modelos":
            dados.set(motor, chave, ", ".join(m for m in valor if _MODELO.match(m))[:4000])
    _gravar(dados, arquivo)


def situacao(arquivo=None, tem_chave=None):
    """Para a tela: [{id, titulo, empresa, chave_em, aviso, ativado, tem_chave, modelos, modelo}]."""
    dados = _ler(arquivo)
    tem_chave = tem_chave or (lambda motor: bool(_ler_chave_sem_erro(motor)))
    lista = []
    for motor, info in MOTORES.items():
        secao = dados[motor] if dados.has_section(motor) else {}
        modelos = [m.strip() for m in secao.get("modelos", "").split(",") if _MODELO.match(m.strip())]
        modelo = secao.get("modelo", "").strip()
        lista.append({"id": motor, **info, "ativado": secao.get("ativado", "nao").strip().lower() == "sim",
                      "tem_chave": tem_chave(motor), "modelos": modelos,
                      "modelo": modelo if modelo in modelos else (modelos[0] if modelos else "")})
    return lista


# ------------------------------------------------------------------ cofre

def _colecao():
    try:
        import secretstorage
    except ImportError as erro:
        raise Erro("o cofre do sistema não está instalado (python3-secretstorage)") from erro
    try:
        conexao = secretstorage.dbus_init()
        colecao = secretstorage.get_default_collection(conexao)
        if colecao.is_locked():
            colecao.unlock()
        return colecao
    except Exception as erro:  # noqa: BLE001 — o secretstorage levanta tipos variados
        raise Erro(f"o cofre do sistema não respondeu ({erro})"[:200]) from erro


def ler_chave(motor):
    for item in _colecao().search_items({**ATRIBUTOS, "motor": motor}):
        return item.get_secret().decode("utf-8")
    if motor == "gemini":                      # chave guardada pelo Wise antes da ADR 063
        for item in _colecao().search_items({"aplicativo": "duiaos-wise", "nome": "gemini"}):
            return item.get_secret().decode("utf-8")
    return None


def _ler_chave_sem_erro(motor):
    try:
        return ler_chave(motor)
    except Erro:
        return None


def gravar_chave(motor, chave):
    if motor not in MOTORES:
        raise Erro("motor desconhecido")
    chave = chave.strip()
    if not 8 <= len(chave) <= 400 or any(c.isspace() for c in chave):
        raise Erro("Essa chave não parece válida: confira se copiou inteira, sem espaços.")
    _colecao().create_item(f"DuiaOS — chave de {MOTORES[motor]['titulo']}", {**ATRIBUTOS, "motor": motor},
                           chave.encode("utf-8"), replace=True)


def apagar_chave(motor):
    colecao = _colecao()
    for item in list(colecao.search_items({**ATRIBUTOS, "motor": motor})):
        item.delete()
    if motor == "gemini":
        for item in list(colecao.search_items({"aplicativo": "duiaos-wise", "nome": "gemini"})):
            item.delete()


# ------------------------------------------------------------------ conferir a chave e listar os modelos

def _get(url, cabecalhos, tempo=20):
    pedido = urllib.request.Request(url, headers=cabecalhos)
    try:
        with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        if erro.code in (400, 401, 403):
            raise Erro("A chave não foi aceita. Confira se copiou a chave inteira e se ela está ativa.") from erro
        if erro.code == 429:
            raise Erro("O serviço recusou por excesso de pedidos ou falta de crédito na conta. Tente mais tarde.") from erro
        raise Erro(f"O serviço respondeu com o erro {erro.code}.") from erro
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as erro:
        raise Erro("Não consegui falar com o serviço. Confira a internet e tente de novo.") from erro


def filtrar_modelos(motor, dados):
    """Resposta da lista de modelos do serviço → nomes dos modelos de conversa, os mais novos primeiro."""
    nomes = []
    if motor == "gemini":
        for m in dados.get("models") or []:
            nome = str(m.get("name", "")).removeprefix("models/")
            if "generateContent" in (m.get("supportedGenerationMethods") or []) and nome.startswith("gemini-"):
                nomes.append((nome, 0))
        nomes.sort(key=lambda par: par[0], reverse=True)
    else:
        for m in dados.get("data") or []:
            nome = str(m.get("id", ""))
            if nome.startswith(("gpt-", "o1", "o3", "o4", "o5", "chatgpt-")):
                nomes.append((nome, int(m.get("created") or 0)))
        nomes.sort(key=lambda par: (par[1], par[0]), reverse=True)
    return [n for n, _ in nomes if _MODELO.match(n) and not any(f in n for f in _FORA)][:40]


def conferir(motor, chave=None, pedir=_get, arquivo=None):
    """Confere a chave no serviço e guarda a lista de modelos que ela enxerga. Devolve a lista."""
    if motor not in MOTORES:
        raise Erro("motor desconhecido")
    chave = chave or ler_chave(motor)
    if not chave:
        raise Erro("Cole a chave primeiro.")
    if motor == "gemini":
        dados = pedir("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", {"x-goog-api-key": chave})
    else:
        dados = pedir("https://api.openai.com/v1/models", {"Authorization": "Bearer " + chave})
    modelos = filtrar_modelos(motor, dados if isinstance(dados, dict) else {})
    if not modelos:
        raise Erro("A chave foi aceita, mas o serviço não listou nenhum modelo de conversa.")
    atual = next((m["modelo"] for m in situacao(arquivo, tem_chave=lambda _m: True) if m["id"] == motor), "")
    definir(motor, arquivo, modelos=modelos, modelo=atual if atual in modelos else modelos[0])
    return modelos
