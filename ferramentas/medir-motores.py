#!/usr/bin/env python3
"""DuiaOS — compara motores de IA local com o mesmo modelo e a mesma pergunta.

Onde rodar: 🔗 DELL (sessão SSH). Pede a senha do sudo uma vez: para medir os
outros motores sem disputa, o Ollama e o duiaos-ia ficam parados durante a
medição e voltam sozinhos no fim (mesmo se der erro ou Ctrl+C).

  python3 ferramentas/medir-motores.py                 # tudo (~30–40 min, ~7 GB de downloads)
  python3 ferramentas/medir-motores.py --sem-openvino  # só Ollama e llama.cpp
  python3 ferramentas/medir-motores.py --pequeno       # Qwen3.5 0.8B: confere o script (~5 min)

O que é medido (pedido típico do Wise: lê ~150 pedaços, escreve 100):
  1. Ollama atual, com as opções calibradas pelo duiaos-ia (threads, placa).
  2. llama-server (llama.cpp, MIT) com o MESMO arquivo do modelo do Ollama,
     no processador e na placa de vídeo (Vulkan).
  3. llama-server com o Qwen3.5 4B "MTP" (o modelo traz cabeças que adivinham
     as próximas palavras; o próprio modelo confere): sem e com MTP.
  4. llama-server com rascunho: o Qwen3.5 0.8B adivinha e o 4B confere.
  5. llama-server com rascunho por repetição (ngram), sem modelo extra.
  6. OpenVINO GenAI (Apache-2.0, Intel), Qwen3.5 4B INT4: processador, placa
     de vídeo e placa + MTP.
Temperatura 0 em tudo: com rascunho/MTP a resposta deve sair igual ou quase
igual à sem rascunho (o modelo principal confere cada palavra; contas em lote
podem trocar uma palavra) — a coluna "resposta" mostra o quanto ficou igual.

Resultado: tabela na tela e JSON em ~/.cache/duiaos/motores/resultado-*.json.
Downloads com sha256 conferido; tudo fica em ~/.cache/duiaos/motores (apague
a pasta depois, se quiser o espaço de volta).
"""
import argparse
import difflib
import hashlib
import json
import os
import platform
import shutil
import signal
import statistics
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "duiaos" / "motores"
ESTADO_IA = Path("/var/lib/duiaos-ia/estado.json")
MODELOS_OLLAMA = Path("/usr/share/ollama/.ollama/models")
OLLAMA = "http://127.0.0.1:11434"
PORTA = 9941
PAUSA = float(os.environ.get("DUIAOS_MEDIR_PAUSA", "10"))  # segundos entre medidas: o processador esfria

# llama.cpp oficial (MIT), build b11560. O pacote vulkan também traz o processador.
LLAMA_TAG = "b11560"
LLAMA = {
    "x86_64": ("llama-b11560-bin-ubuntu-vulkan-x64.tar.gz",
               "57a37c454fac239ac03188b87e49f517cba1ca8276572c9f2dd5e4c26aa2dbc3"),
    "aarch64": ("llama-b11560-bin-ubuntu-vulkan-arm64.tar.gz",
                "f38551cf49518c62cb6f4915d289d395d0c416a2ae055311aba387646389fe46"),
}

HF = "https://huggingface.co"
# (repositório, revisão fixa, arquivo, sha256) — todos Apache-2.0 (Qwen3.5)
GGUF = {
    "4b-mtp": ("unsloth/Qwen3.5-4B-MTP-GGUF", "86835bf9949e4d14d6860f7910b1340ad4f271a9",
               "Qwen3.5-4B-Q4_K_M.gguf", "3874209241c9a397e2f62cd3f70f80fd2dfbf0dfccb6838416bdb48a714e8630"),
    "0.8b": ("unsloth/Qwen3.5-0.8B-GGUF", "6ab461498e2023f6e3c1baea90a8f0fe38ab64d0",
             "Qwen3.5-0.8B-Q4_K_M.gguf", "bd258782e35f7f458f8aced1adc053e6e92e89bc735ba3be89d38a06121dc517"),
    "0.8b-mtp": ("unsloth/Qwen3.5-0.8B-MTP-GGUF", "cf8a611f6ed2c2060046219a19f12cd3d5ecd67c",
                 "Qwen3.5-0.8B-Q4_K_M.gguf", "ac7c9d7a1b3e3695bb3bd50f8ceaa97f9c93e99ccc3d3d1a620301b6dd6d3d86"),
}
OPENVINO = {
    "4b": ("OpenVINO/Qwen3.5-4B-int4-ov", "f2377291372c62c0114ee20a094261fa3b193b0b"),
    "0.8b": ("OpenVINO/Qwen3.5-0.8B-int4-ov", "c509b52e248feaa93aaeb51adf4f340b43422aee"),
}
OPENVINO_PIP = ["openvino==2026.4.0", "openvino-tokenizers==2026.4.0.0", "openvino-genai==2026.4.0.0",
                "huggingface_hub"]

# Pergunta igual para todos: formato de conversa do Qwen escrito à mão (sem
# "raciocínio"), para os três motores lerem exatamente os mesmos pedaços.
SISTEMA = ("Você é o Wise, o assistente do DuiaOS, um sistema operacional brasileiro. Fale sempre em "
           "português do Brasil, de forma simples, gentil e direta, para pessoas sem conhecimento técnico. "
           "Use as ferramentas para informações deste computador e nunca invente valores.")
CONSULTA = ('{"memoria":{"total_gb":15.4,"usada_gb":9.8,"livre_gb":5.6},"processador":{"uso":37,'
            '"nucleos":8},"programas":[{"nome":"Firefox","processador":12,"memoria_mb":1430},'
            '{"nome":"Ollama","processador":18,"memoria_mb":3900},{"nome":"Wise","processador":1,'
            '"memoria_mb":180}]}')
PERGUNTA = ("O computador está lento. Com base nesta consulta, explique em três parágrafos o que está "
            "usando mais memória e o que eu posso fazer: " + CONSULTA)
PROMPT = (f"<|im_start|>system\n{SISTEMA}<|im_end|>\n<|im_start|>user\n{PERGUNTA}<|im_end|>\n"
          "<|im_start|>assistant\n<think>\n\n</think>\n\n")
ESCREVER = 100


def dizer(texto):
    print(texto, flush=True)


# ------------------------------------------------------------------ downloads
def baixar(url, destino, sha256):
    destino = Path(destino)
    if destino.exists() and sha_de(destino) == sha256:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    dizer(f"    baixando {url.split('/')[-1]}")
    subprocess.run(["curl", "-fL", "--retry", "3", "-C", "-", "--progress-bar", "-o", str(parcial), url],
                   check=True)
    if sha_de(parcial) != sha256:
        parcial.unlink()
        raise SystemExit(f"O arquivo {destino.name} não confere com o sha256 esperado. Nada foi usado.")
    parcial.rename(destino)
    return destino


def sha_de(arquivo):
    h = hashlib.sha256()
    with open(arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gguf(chave):
    repo, rev, arquivo, sha = GGUF[chave]
    return baixar(f"{HF}/{repo}/resolve/{rev}/{arquivo}", CACHE / "gguf" / repo.replace("/", "_") / arquivo, sha)


def llama_server():
    nome, sha = LLAMA[platform.machine()]
    pacote = baixar(f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_TAG}/{nome}",
                    CACHE / nome, sha)
    pasta = CACHE / f"llama-{LLAMA_TAG}"
    binario = pasta / f"llama-{LLAMA_TAG}" / "llama-server"
    if not binario.exists():
        pasta.mkdir(parents=True, exist_ok=True)
        with tarfile.open(pacote) as tar:
            tar.extractall(pasta, filter="data")
    return binario


# ------------------------------------------------------------------- serviços
class Servicos:
    """Para o Ollama e o duiaos-ia durante a medição e garante a volta."""

    def __init__(self):
        self.parados = False
        # Pede a senha agora e mantém o sudo válido até o fim (a medição passa de
        # 15 min; sem isso, religar os serviços no fim pediria a senha de novo)
        subprocess.run(["sudo", "-v"], check=True)
        def manter():
            while True:
                time.sleep(60)
                subprocess.run(["sudo", "-n", "-v"], capture_output=True, check=False)
        threading.Thread(target=manter, daemon=True).start()

    def parar(self):
        dizer("==> Parando o Ollama e o duiaos-ia durante a medição (voltam no fim)")
        subprocess.run(["sudo", "systemctl", "stop", "duiaos-ia", "ollama"], check=True)
        self.parados = True

    def voltar(self):
        if self.parados:
            dizer("==> Ligando de novo o Ollama e o duiaos-ia")
            subprocess.run(["sudo", "systemctl", "start", "ollama", "duiaos-ia"], check=False)
            self.parados = False


def pedir(url, corpo, tempo=900):
    pedido = urllib.request.Request(url, json.dumps(corpo).encode(), {"Content-Type": "application/json"})
    abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with abridor.open(pedido, timeout=tempo) as resposta:
        return json.load(resposta)


def mediana(valores):
    return round(statistics.median(valores), 2) if valores else None


# ------------------------------------------------------------------- 1. Ollama
def blob_do_ollama(modelo):
    """Arquivo GGUF que o Ollama usa para o modelo (o mesmo peso, para comparar)."""
    nome, _, etiqueta = modelo.partition(":")
    manifesto = MODELOS_OLLAMA / "manifests/registry.ollama.ai/library" / nome / (etiqueta or "latest")
    try:
        dados = json.loads(manifesto.read_text())
    except (OSError, ValueError):
        dados = json.loads(subprocess.run(["sudo", "cat", str(manifesto)], capture_output=True, text=True,
                                          check=True).stdout)
    for camada in dados.get("layers", []):
        if camada.get("mediaType") == "application/vnd.ollama.image.model":
            blob = MODELOS_OLLAMA / "blobs" / camada["digest"].replace(":", "-")
            copia = CACHE / "ollama" / blob.name
            if not copia.exists():
                copia.parent.mkdir(parents=True, exist_ok=True)
                dizer(f"    copiando o modelo do Ollama ({blob.name[:19]}…)")
                subprocess.run(["sudo", "cp", str(blob), str(copia)], check=True)
                subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", str(copia)], check=True)
            return copia
    raise SystemExit(f"Não achei o arquivo do modelo {modelo} no Ollama.")


def medir_ollama(modelo, opcoes, repeticoes):
    corpo = {"model": modelo, "prompt": PROMPT, "raw": True, "stream": False, "keep_alive": -1,
             "options": {**opcoes, "num_predict": ESCREVER, "temperature": 0, "seed": 1}}
    pedir(f"{OLLAMA}/api/generate", {**corpo, "options": {**corpo["options"], "num_predict": 4}})  # aquece
    medidas = []
    for _ in range(repeticoes):
        time.sleep(PAUSA)
        inicio = time.monotonic()
        r = pedir(f"{OLLAMA}/api/generate", corpo)
        total = time.monotonic() - inicio
        medidas.append({"lidos": r["prompt_eval_count"], "ler_s": r["prompt_eval_duration"] / 1e9,
                        "escritos": r["eval_count"], "escrever_s": r["eval_duration"] / 1e9,
                        "total_s": total, "texto": r.get("response", "")})
    return medidas


# ---------------------------------------------------------------- 2–5. llama
def medir_llama(binario, modelo, threads, placa, extra, repeticoes):
    args = [str(binario), "-m", str(modelo), "-t", str(threads), "-c", "8192", "-np", "1",
            "--host", "127.0.0.1", "--port", str(PORTA), "--no-webui", "-ngl", "99" if placa else "0"]
    if not placa:
        args += ["-dev", "none"]
    args += extra
    log = open(CACHE / "llama-server.log", "w")
    processo = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(300):
            if processo.poll() is not None:
                raise RuntimeError("o llama-server fechou (veja ~/.cache/duiaos/motores/llama-server.log)")
            try:
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                        f"http://127.0.0.1:{PORTA}/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        break
            except (OSError, ValueError):
                pass
            time.sleep(1)
        else:
            raise RuntimeError("o llama-server não ficou pronto em 5 minutos")
        corpo = {"prompt": PROMPT, "n_predict": ESCREVER, "temperature": 0, "seed": 1, "cache_prompt": False,
                 "ignore_eos": True}
        pedir(f"http://127.0.0.1:{PORTA}/completion", {**corpo, "n_predict": 4})            # aquece
        medidas = []
        for _ in range(repeticoes):
            time.sleep(PAUSA)
            inicio = time.monotonic()
            r = pedir(f"http://127.0.0.1:{PORTA}/completion", corpo)
            total = time.monotonic() - inicio
            t = r["timings"]
            m = {"lidos": t["prompt_n"], "ler_s": t["prompt_ms"] / 1000, "escritos": t["predicted_n"],
                 "escrever_s": t["predicted_ms"] / 1000, "total_s": total, "texto": r.get("content", "")}
            if t.get("draft_n"):
                m["aceitos"] = round(t.get("draft_n_accepted", 0) / t["draft_n"], 2)
            medidas.append(m)
        return medidas
    finally:
        processo.send_signal(signal.SIGINT)
        try:
            processo.wait(30)
        except subprocess.TimeoutExpired:
            processo.kill()
        log.close()


# ---------------------------------------------------------------- 6. OpenVINO
OV_MEDIR = r'''
import json, sys, time
import openvino_genai as g
caminho, aparelho, mtp, repeticoes, pausa, threads = (sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]),
                                                     float(sys.argv[5]), int(sys.argv[6]))
prompt = sys.stdin.read()
kw = {"INFERENCE_NUM_THREADS": threads} if aparelho == "CPU" else {}
if mtp:
    sc = g.SchedulerConfig(); sc.enable_prefix_caching = False
    kw.update(draft_model=g.draft_model(caminho, aparelho), scheduler_config=sc)
pipe = g.VLMPipeline(caminho, aparelho, **kw)
c = g.GenerationConfig(); c.max_new_tokens = %d; c.do_sample = False; c.apply_chat_template = False
c.ignore_eos = True
if mtp: c.num_assistant_tokens = mtp
c4 = g.GenerationConfig(); c4.max_new_tokens = 4; c4.do_sample = False; c4.apply_chat_template = False
if mtp: c4.num_assistant_tokens = mtp
pipe.generate(prompt, generation_config=c4)
for _ in range(repeticoes):
    time.sleep(pausa)
    inicio = time.monotonic(); r = pipe.generate(prompt, generation_config=c); total = time.monotonic() - inicio
    m = r.perf_metrics
    ler = m.get_ttft().mean / 1000
    print(json.dumps({"lidos": m.get_num_input_tokens(), "ler_s": ler, "escritos": m.get_num_generated_tokens(),
                      "escrever_s": max(total - ler, 1e-6), "total_s": total, "texto": str(r)}), flush=True)
''' % ESCREVER


def preparar_openvino(chave):
    venv = CACHE / "openvino-venv"
    python = venv / "bin" / "python"
    if not python.exists():
        dizer("    criando ambiente Python do OpenVINO (~320 MB)")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        except subprocess.CalledProcessError as erro:
            raise RuntimeError("falta o python3-venv (sudo apt install python3-venv)") from erro
        subprocess.run([str(python), "-m", "pip", "install", "-q", *OPENVINO_PIP], check=True)
        opt = venv / "bin" / "opt_in_out"
        if opt.exists():                       # sem telemetria da Intel
            subprocess.run([str(opt), "--opt_out"], capture_output=True, check=False)
    repo, rev = OPENVINO[chave]
    pasta = CACHE / "openvino" / repo.replace("/", "_")
    if not (pasta / "openvino_language_model.xml").exists():
        dizer(f"    baixando {repo} (~{'3' if chave == '4b' else '0,9'} GB)")
        subprocess.run([str(python), "-I", "-c",
                        "import sys; from huggingface_hub import snapshot_download as s; "
                        "s(sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3])", repo, rev, str(pasta)],
                       check=True, env={**os.environ, "HF_HUB_DISABLE_TELEMETRY": "1"})
    return python, pasta


def tem_placa_openvino():
    return any(Path("/etc/OpenCL/vendors").glob("*intel*")) if Path("/etc/OpenCL/vendors").exists() else False


def medir_openvino(python, pasta, aparelho, mtp, repeticoes, threads):
    ambiente = {**os.environ, "OMP_NUM_THREADS": str(threads)}
    r = subprocess.run([str(python), "-I", "-c", OV_MEDIR, str(pasta), aparelho, str(mtp), str(repeticoes),
                        str(PAUSA), str(threads)], input=PROMPT, capture_output=True, text=True, env=ambiente, timeout=3600)
    medidas = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    if not medidas:
        raise RuntimeError((r.stderr.strip().splitlines() or ["falhou sem mensagem"])[-1][:300])
    return medidas


# ------------------------------------------------------------------- resumo
def resumir(nome, medidas):
    ler = [m["lidos"] / m["ler_s"] for m in medidas if m["ler_s"] > 0]
    escrever = [m["escritos"] / m["escrever_s"] for m in medidas if m["escrever_s"] > 0]
    linha = {"config": nome, "ler_por_s": mediana(ler), "escrever_por_s": mediana(escrever),
             "total_s": mediana([m["total_s"] for m in medidas]), "lidos": medidas[0]["lidos"],
             "escritos": medidas[0]["escritos"], "texto": medidas[0]["texto"], "medidas": medidas}
    if any("aceitos" in m for m in medidas):
        linha["aceitos"] = mediana([m.get("aceitos", 0) for m in medidas])
    return linha


def tabela(linhas, base_texto):
    dizer("")
    dizer(f"{'Configuração':<58} {'ler/s':>7} {'escrever/s':>11} {'total':>7} {'aceitos':>8}  resposta")
    dizer("-" * 112)
    for l in linhas:
        if "erro" in l:
            dizer(f"{l['config']:<58} {'—':>7} {'—':>11} {'—':>7} {'':>8}  falhou: {l['erro'][:60]}")
            continue
        aceitos = f"{l['aceitos'] * 100:.0f}%" if "aceitos" in l else ""
        igual = ""
        if base_texto.get(l.get("grupo")):
            # Rascunho/MTP conferem em lote: contas um pouco diferentes podem trocar
            # uma palavra no meio; a parecença mostra se a resposta é a mesma ideia
            parecida = difflib.SequenceMatcher(None, l["texto"], base_texto[l["grupo"]]).ratio()
            igual = "igual" if parecida == 1 else f"{parecida * 100:.0f}% igual"
        dizer(f"{l['config']:<58} {l['ler_por_s']:>7.1f} {l['escrever_por_s']:>11.2f} {l['total_s']:>6.1f}s"
              f" {aceitos:>8}  {igual}")


def principal():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--repeticoes", type=int, default=3)
    p.add_argument("--sem-openvino", action="store_true")
    p.add_argument("--sem-ollama", action="store_true", help="não mede o Ollama (ex.: fora do DuiaOS)")
    p.add_argument("--pequeno", action="store_true", help="usa o Qwen3.5 0.8B: só para conferir o script")
    a = p.parse_args()
    if platform.machine() not in LLAMA:
        raise SystemExit("Arquitetura não suportada por este script.")
    CACHE.mkdir(parents=True, exist_ok=True)

    estado = {}
    try:
        estado = json.loads(ESTADO_IA.read_text())
    except (OSError, ValueError):
        pass
    modelo = "qwen3.5:0.8b" if a.pequeno else (estado.get("ativo") or "qwen3.5:4b")
    opcoes = estado.get("opcoes") or {}
    threads = opcoes.get("num_thread") or max(1, (os.cpu_count() or 2) // 2)
    na_placa = bool(opcoes.get("num_gpu"))
    dizer(f"==> Modelo: {modelo} · opções calibradas: {opcoes or 'nenhuma'} · threads: {threads}")
    dizer("    Deixe o notebook na tomada e sem outros programas pesados abertos.")

    servicos = Servicos() if not a.sem_ollama else None
    # Downloads primeiro (com o Ollama ainda ligado)
    dizer("==> Preparando (downloads com sha256 conferido)")
    binario = llama_server()
    mtp = gguf("0.8b-mtp" if a.pequeno else "4b-mtp")
    rascunho = None if a.pequeno else gguf("0.8b")
    blob = None if a.sem_ollama else blob_do_ollama(modelo)
    ov = None
    if not a.sem_openvino:
        try:
            ov = preparar_openvino("0.8b" if a.pequeno else "4b")
        except (RuntimeError, subprocess.CalledProcessError) as erro:
            dizer(f"    OpenVINO fica de fora: {erro}")

    linhas = []
    base_texto = {}

    def rodar(nome, grupo, funcao, *args):
        dizer(f"==> {nome}")
        try:
            linha = resumir(nome, funcao(*args))
            linha["grupo"] = grupo
            if grupo and grupo not in base_texto:
                base_texto[grupo] = linha["texto"]
            linhas.append(linha)
            dizer(f"    ler {linha['ler_por_s']}/s · escrever {linha['escrever_por_s']}/s · total {linha['total_s']} s"
                  + (f" · aceitos {linha['aceitos'] * 100:.0f}%" if "aceitos" in linha else ""))
        except Exception as erro:  # um motor que falha não derruba a comparação
            dizer(f"    falhou: {erro}")
            linhas.append({"config": nome, "erro": str(erro)})

    if not a.sem_ollama:
        rodar(f"Ollama (atual, {'placa' if na_placa else 'processador'})", None,
              medir_ollama, modelo, opcoes, a.repeticoes)

    try:
        if servicos:
            servicos.parar()
        if blob:
            rodar("llama-server · arquivo do Ollama · processador", "ollama",
                  medir_llama, binario, blob, threads, False, [], a.repeticoes)
            rodar("llama-server · arquivo do Ollama · placa (Vulkan)", "ollama",
                  medir_llama, binario, blob, threads, True, [], a.repeticoes)
        # Melhor lugar para o resto: o que o llama-server mediu melhor
        placa = na_placa
        medidos = [l for l in linhas if l.get("grupo") == "ollama" and "erro" not in l]
        if len(medidos) == 2:
            placa = medidos[1]["total_s"] < medidos[0]["total_s"]
        onde = "placa" if placa else "processador"
        rodar(f"llama-server · MTP-GGUF sem MTP · {onde}", "mtp",
              medir_llama, binario, mtp, threads, placa, [], a.repeticoes)
        for n in (1, 2, 3):
            rodar(f"llama-server · MTP ({n} por vez) · {onde}", "mtp", medir_llama, binario, mtp, threads, placa,
                  ["--spec-type", "draft-mtp", "--spec-draft-n-max", str(n)], a.repeticoes)
        if rascunho:
            for n in (2, 4):
                rodar(f"llama-server · rascunho 0.8B ({n} por vez) · {onde}", "mtp", medir_llama, binario, mtp,
                      threads, placa, ["--spec-type", "draft-simple", "-md", str(rascunho),
                                       "--spec-draft-n-max", str(n), "-ngld", "99" if placa else "0"],
                      a.repeticoes)
        rodar(f"llama-server · ngram (sem modelo extra) · {onde}", "mtp", medir_llama, binario, mtp, threads,
              placa, ["--spec-type", "ngram-mod"], a.repeticoes)
        if ov:
            python, pasta = ov
            rodar("OpenVINO · INT4 · processador", "openvino",
                  medir_openvino, python, pasta, "CPU", 0, a.repeticoes, threads)
            if tem_placa_openvino():
                rodar("OpenVINO · INT4 · placa (GPU)", "openvino",
                      medir_openvino, python, pasta, "GPU", 0, a.repeticoes, threads)
                for n in (1, 2):
                    rodar(f"OpenVINO · INT4 · placa + MTP ({n} por vez)", "openvino",
                          medir_openvino, python, pasta, "GPU", n, a.repeticoes, threads)
            else:
                dizer("    OpenVINO na placa fica de fora: falta o driver OpenCL da Intel (compute-runtime,"
                      " que não está no Debian 13); medindo no processador.")
                for n in (1, 2):
                    rodar(f"OpenVINO · INT4 · processador + MTP ({n} por vez)", "openvino",
                          medir_openvino, python, pasta, "CPU", n, a.repeticoes, threads)
    finally:
        if servicos:
            servicos.voltar()

    tabela(linhas, base_texto)
    arquivo = CACHE / f"resultado-{time.strftime('%Y%m%d-%H%M')}.json"
    arquivo.write_text(json.dumps({"modelo": modelo, "opcoes": opcoes, "threads": threads,
                                   "processador": platform.processor() or platform.machine(),
                                   "linhas": linhas}, ensure_ascii=False, indent=1))
    dizer(f"\nResultado completo: {arquivo}")
    dizer("Copie a tabela acima e mande para o Claude.")


if __name__ == "__main__":
    try:
        principal()
    except KeyboardInterrupt:
        sys.exit(130)
