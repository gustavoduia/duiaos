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


def _arquivos(pasta, nome):
    return sorted((cfg.PASTA_ESTADO / pasta).glob("*.json")) if (cfg.PASTA_ESTADO / pasta).is_dir() else []


def estado():
    config = cfg.Config.carregar()
    print(f"Ajude a melhorar o DuiaOS: {cfg.NOMES_NIVEIS[config.nivel]}")
    if config.coleta:
        print(f"Envio: {config.transporte}" + (f" ({config.repositorio})" if config.transporte == "git" else ""))
    try:
        dados = json.loads((cfg.PASTA_ESTADO / "estado.json").read_text())
        print("Última coleta:", datetime.fromtimestamp(dados["coletado_ate"]).strftime("%d/%m/%Y %H:%M"))
    except (OSError, ValueError, KeyError):
        print("Última coleta: nenhuma")
    try:
        resultado = json.loads((cfg.PASTA_ESTADO / "ultimo-envio.json").read_text())
        quando = datetime.fromtimestamp(resultado["t"]).strftime("%d/%m/%Y %H:%M")
        print(f"Último envio: {quando} — " + (resultado.get("erro") or f"{resultado.get('enviados', 0)} relatório(s)"))
    except (OSError, ValueError, KeyError):
        print("Último envio: nenhum")
    print(f"Pendentes: {len(_arquivos('pendentes', ''))} · Enviados guardados: {len(_arquivos('enviados', ''))}")
    print(f"Pasta: {cfg.PASTA_ESTADO} (sudo para ler)")
    return 0


def ver(argumentos):
    if argumentos:
        caminho = argumentos[0]
    else:
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
        (cfg.PASTA_ESTADO / "ultimo-envio.json").write_text(json.dumps(resultado, ensure_ascii=False))
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
        print("Relatórios guardados apagados.")
        return 0
    print(__doc__)
    return 0 if comando in ("-h", "--help", "ajuda") else 2
