"""DuiaOS — Mail Box: senhas e tokens das contas no cofre do sistema (Secret Service: gnome-keyring).

Nada de senha em arquivo. Sem cofre na sessão, a senha fica só na memória enquanto o Mail Box estiver
aberto, e a janela avisa. DUIAOS_MAILBOX_COFRE=memoria força o cofre em memória (testes).
"""
import os
import threading

ATRIBUTO_APP = "duiaos-mailbox"


class CofreIndisponivel(Exception):
    pass


class CofreMemoria:
    persistente = False

    def __init__(self):
        self._dados = {}
        self._trava = threading.Lock()

    def guardar(self, conta, servico, segredo):
        with self._trava:
            self._dados[(conta, servico)] = segredo

    def ler(self, conta, servico):
        with self._trava:
            return self._dados.get((conta, servico))

    def apagar(self, conta):
        with self._trava:
            for chave in [k for k in self._dados if k[0] == conta]:
                del self._dados[chave]


class CofreSistema:
    """Secret Service pelo python3-secretstorage (o mesmo cofre das chaves de IA das Configurações)."""
    persistente = True

    def __init__(self):
        import secretstorage
        self._ss = secretstorage
        try:
            self._conexao = secretstorage.dbus_init()
            self._colecao = secretstorage.get_default_collection(self._conexao)
            if self._colecao.is_locked():
                self._colecao.unlock()
        except Exception as erro:  # noqa: BLE001 — sem D-Bus, sem gnome-keyring, coleção trancada
            raise CofreIndisponivel(str(erro)) from erro
        self._trava = threading.Lock()

    def _atributos(self, conta, servico):
        return {"application": ATRIBUTO_APP, "conta": conta, "servico": servico}

    def guardar(self, conta, servico, segredo):
        with self._trava:
            self._colecao.create_item(f"Mail Box — {conta} ({servico})", self._atributos(conta, servico),
                                      segredo.encode(), replace=True)

    def ler(self, conta, servico):
        with self._trava:
            for item in self._colecao.search_items(self._atributos(conta, servico)):
                return item.get_secret().decode()
        return None

    def apagar(self, conta):
        with self._trava:
            for item in self._colecao.search_items({"application": ATRIBUTO_APP, "conta": conta}):
                item.delete()


def abrir():
    if os.environ.get("DUIAOS_MAILBOX_COFRE") == "memoria":
        return CofreMemoria()
    try:
        return CofreSistema()
    except (ImportError, CofreIndisponivel):
        return CofreMemoria()
