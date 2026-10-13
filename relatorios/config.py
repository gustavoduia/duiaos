"""Configuração de "Ajude a melhorar o DuiaOS" (ADR 040).

/etc/duiaos/relatorios.conf (0644; nada secreto):
    [relatorios]
    nivel = nao_escolhido | desligado | erros | erros_e_uso | desenvolvimento
    transporte = https | git                 (padrão https; git só nos computadores de teste)
    repositorio = git@github.com:gustavoduia/duiaos-diagnosticos.git     (transporte git)
    endereco = https://…/api/relatorios                                   (transporte https; padrão: o site)
    maquina = dell                                                        (só no nível desenvolvimento)

Sem o arquivo, o nível é "nao_escolhido": nada é coletado nem enviado até a pessoa escolher.
A chave do transporte git fica em /etc/duiaos/relatorios/chave_git (0600, root).
"""
import configparser
import os
import uuid
from pathlib import Path

ARQUIVO = Path(os.environ.get("DUIAOS_RELATORIOS_CONFIG", "/etc/duiaos/relatorios.conf"))
PASTA_ESTADO = Path(os.environ.get("DUIAOS_RELATORIOS_ESTADO", "/var/lib/duiaos-relatorios"))
CHAVE_GIT = Path(os.environ.get("DUIAOS_RELATORIOS_CHAVE", "/etc/duiaos/relatorios/chave_git"))
HOSTS_GITHUB = Path(os.environ.get("DUIAOS_RELATORIOS_HOSTS", "/usr/share/duiaos/relatorios/known_hosts"))

NIVEIS = ("nao_escolhido", "desligado", "erros", "erros_e_uso", "desenvolvimento")
TRANSPORTES = ("https", "git")
# Site do DuiaOS (duiaos-websites, site/worker/relatorios.js): recebe sem credencial e grava em lotes no
# repositório privado. Trocar aqui quando o domínio duiaos.com.br estiver no ar.
ENDERECO_PADRAO = "https://duiaos.gustavoduia.workers.dev/api/relatorios"
NOMES_NIVEIS = {
    "nao_escolhido": "Ainda não escolhido (nada é enviado)",
    "desligado": "Desligado (nada é enviado)",
    "erros": "Erros e informações do computador",
    "erros_e_uso": "Erros, informações do computador e uso",
    "desenvolvimento": "Desenvolvimento (tudo, inclusive conversas do Wise; só computadores de teste)",
}


class Config:
    def __init__(self, nivel="nao_escolhido", transporte="https", repositorio="", endereco="", maquina=""):
        self.nivel = nivel if nivel in NIVEIS else "nao_escolhido"
        self.transporte = transporte if transporte in TRANSPORTES else "https"
        self.repositorio = repositorio
        self.endereco = endereco
        self.maquina = maquina

    @property
    def coleta(self):
        return self.nivel in ("erros", "erros_e_uso", "desenvolvimento")

    @classmethod
    def carregar(cls, arquivo=None):
        dados = configparser.ConfigParser()
        dados.read(arquivo or ARQUIVO)
        sec = dados["relatorios"] if dados.has_section("relatorios") else {}
        return cls(sec.get("nivel", "nao_escolhido"), sec.get("transporte", "https"), sec.get("repositorio", ""),
                   sec.get("endereco", ""), sec.get("maquina", ""))

    def salvar(self, arquivo=None):
        arquivo = Path(arquivo or ARQUIVO)
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        dados = configparser.ConfigParser()
        dados["relatorios"] = {"nivel": self.nivel, "transporte": self.transporte}
        for chave in ("repositorio", "endereco", "maquina"):
            if getattr(self, chave):
                dados["relatorios"][chave] = getattr(self, chave)
        temporario = arquivo.with_suffix(".tmp")
        with open(temporario, "w", encoding="utf-8") as saida:
            saida.write("# DuiaOS — \"Ajude a melhorar o DuiaOS\". Mude com: sudo duiaos-relatorios nivel NIVEL\n")
            dados.write(saida)
        os.chmod(temporario, 0o644)
        temporario.replace(arquivo)


def identificador(pasta=None, novo=False):
    """Número aleatório desta instalação (não é o machine-id; a pessoa pode trocar a qualquer hora)."""
    arquivo = Path(pasta or PASTA_ESTADO) / "instalacao"
    if not novo:
        try:
            valor = arquivo.read_text().strip()
            if len(valor) == 32:
                return valor
        except OSError:
            pass
    valor = uuid.uuid4().hex
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(valor + "\n")
    return valor
