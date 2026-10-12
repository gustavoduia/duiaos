"""duiaos-relatorios — "Ajude a melhorar o DuiaOS" pelo terminal (ADR 040).

  duiaos-relatorios estado                  nível, último envio, relatórios pendentes e enviados
  duiaos-relatorios ver [ARQUIVO]           mostra o último relatório (pendente ou enviado), como vai/foi enviado
  duiaos-relatorios enviar                  coleta e envia agora (pede ao serviço; não precisa de sudo)
  sudo duiaos-relatorios nivel NIVEL        desligado | erros | erros_e_uso | desenvolvimento
  sudo duiaos-relatorios novo-identificador troca o número aleatório desta instalação
  sudo duiaos-relatorios apagar             apaga os relatórios guardados neste computador
  duiaos-relatorios coletar                 (usado pelo serviço) coleta e envia
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

from . import config as cfg

ID_ENVIADO = "91f4f6d28d1b4bb5a2e734752a3a5805"         # catálogo: relatórios enviados
ID_NIVEL = "3d4c21837a954343884b8922b6e95950"           # catálogo: nível mudou

try:
    import duiaos_registro as registro
except ImportError:                                    # testes fora do sistema
    registro = None


def _arquivos(pasta, nome=""):
    """Relatórios guardados (a pasta é só do root: sem sudo, a lista vem vazia)."""
    try:
        caminho = cfg.PASTA_ESTADO / pasta
        return sorted(caminho.glob("*.json")) if caminho.is_dir() else []
    except PermissionError:
        return []


def _data(t):
    return datetime.fromtimestamp(t).strftime("%d/%m/%Y %H:%M")


def estado():
    """Funciona sem sudo: lê situacao.json (0644), que o serviço publica a cada coleta."""
    config = cfg.Config.carregar()
    print(f"Ajude a melhorar o DuiaOS: {cfg.NOMES_NIVEIS[config.nivel]}")
    if config.coleta:
        print(f"Envio: {config.transporte}" + (f" ({config.repositorio})" if config.transporte == "git" else ""))
    try:
        situacao = json.loads((cfg.PASTA_ESTADO / "situacao.json").read_text())
    except (OSError, ValueError):
        situacao = {}
    print("Última coleta:", _data(situacao["coleta"]) if situacao.get("coleta") else "nenhuma")
    envio = situacao.get("envio") or {}
    if envio.get("t"):
        print(f"Último envio: {_data(envio['t'])} — " + (envio.get("erro") or f"{envio.get('enviados', 0)} relatório(s)"))
    else:
        print("Último envio: nenhum")
    print(f"Pendentes: {situacao.get('pendentes', 0)} · Enviados guardados: {situacao.get('enviados', 0)}")
    print(f"Relatórios em {cfg.PASTA_ESTADO} (para ler: sudo duiaos-relatorios ver)")
    return 0


def ver(argumentos):
    if argumentos:
        caminho = argumentos[0]
    else:
        if not os.access(cfg.PASTA_ESTADO / "pendentes", os.R_OK | os.X_OK) and \
                (cfg.PASTA_ESTADO / "pendentes").exists():
            print("Os relatórios só podem ser lidos pelo administrador: sudo duiaos-relatorios ver", file=sys.stderr)
            return 1
        todos = sorted(_arquivos("pendentes", "") + _arquivos("enviados", ""), key=lambda c: c.name)
        if not todos:
            print("Nenhum relatório guardado.")
            return 0
        caminho = todos[-1]
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            print(json.dumps(json.load(arquivo), ensure_ascii=False, indent=2))
    except PermissionError:
        print("Sem permissão: use sudo duiaos-relatorios ver", file=sys.stderr)
        return 1
    return 0


def _exigir_root():
    if os.geteuid() != 0:
        print("Precisa de administrador: use sudo.", file=sys.stderr)
        sys.exit(1)


def nivel(argumentos):
    if not argumentos or argumentos[0] not in cfg.NIVEIS[1:]:
        print("Uso: sudo duiaos-relatorios nivel " + " | ".join(cfg.NIVEIS[1:]), file=sys.stderr)
        return 2
    _exigir_root()
    config = cfg.Config.carregar()
    anterior, config.nivel = config.nivel, argumentos[0]
    config.salvar()
    if registro:
        registro.registrar(registro.NOTA, "relatorios.nivel", f"Ajude a melhorar o DuiaOS: {anterior} → {config.nivel}",
                           componente="duiaos-relatorios", message_id=ID_NIVEL, anterior=anterior,
                           nivel=config.nivel)
    print(f"Ajude a melhorar o DuiaOS: {cfg.NOMES_NIVEIS[config.nivel]}")
    return 0


def coletar_e_enviar():
    from . import coleta, envio
    config = cfg.Config.carregar()
    try:
        caminho = coleta.coletar(config)
    except Exception:  # noqa: BLE001 — falha do coletor também vira relatório (na próxima)
        if registro:
            registro.falha("na coleta", componente="duiaos-relatorios")
        raise
    resultado = envio.enviar_pendentes(config)
    resultado["t"] = time.time()
    if config.coleta:
        coleta.publicar_situacao(coleta=time.time(), envio=resultado)
    if registro and resultado.get("erro"):
        registro.aviso("relatorios.envio_falhou", f"Envio dos relatórios falhou: {resultado['erro']}",
                       componente="duiaos-relatorios")
    elif registro and resultado.get("enviados"):
        registro.registrar(registro.INFO, "relatorios.enviado", f"{resultado['enviados']} relatório(s) enviado(s)",
                           componente="duiaos-relatorios", message_id=ID_ENVIADO)
    print(f"Coleta: {caminho or 'nada novo'} · Envio: {resultado}")
    return 0 if not resultado.get("erro") else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    comando = argv[0] if argv else "estado"
    if registro:
        registro.instalar_ganchos("duiaos-relatorios")
    if comando == "estado":
        return estado()
    if comando == "ver":
        return ver(argv[1:])
    if comando == "nivel":
        return nivel(argv[1:])
    if comando == "coletar":
        _exigir_root()
        return coletar_e_enviar()
    if comando == "enviar":
        # O serviço roda como root com proteções; a regra do polkit deixa quem está no computador pedir
        return subprocess.call(["systemctl", "start", "duiaos-relatorios.service"])
    if comando == "novo-identificador":
        _exigir_root()
        print("Novo identificador:", cfg.identificador(novo=True))
        return 0
    if comando == "apagar":
        _exigir_root()
        for pasta in ("pendentes", "enviados"):
            for caminho in _arquivos(pasta, ""):
                caminho.unlink(missing_ok=True)
        from . import coleta
        coleta.publicar_situacao()
        print("Relatórios guardados apagados.")
        return 0
    print(__doc__)
    return 0 if comando in ("-h", "--help", "ajuda") else 2
