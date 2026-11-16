"""Andamento, travamentos, registros e idempotência do duiaos-agente (ADR 047), sem D-Bus e sem mexer no sistema.

Rodar: python3 -m unittest discover -s agente/testes -t .   (precisa do python3-gi)
"""
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA))
import plano as pl  # noqa: E402

try:
    import importlib.util
    _espec = importlib.util.spec_from_file_location("agente_servico", PASTA / "agente.py")
    ag = importlib.util.module_from_spec(_espec)
    _espec.loader.exec_module(ag)
    TEM_GI = True
except (ImportError, ValueError):
    TEM_GI = False


class TestePlano(unittest.TestCase):
    def test_estimativa(self):
        rapido = pl.estimar_segundos({"atualizar": [{"pacote": "vim"}]}, 3_000_000)
        lento = pl.estimar_segundos({"atualizar": [{"pacote": "linux-image-6.12.117-amd64"}, {"pacote": "vim"}]}, 3_000_000)
        self.assertLess(rapido, 60)
        self.assertGreater(lento, rapido + 170)

    def test_etapas_e_motivos(self):
        self.assertIn("initramfs", pl.descrever_processo("/bin/sh /usr/sbin/update-initramfs -c -k 6.12.117-amd64"))
        self.assertIn("Windows", pl.descrever_processo("/bin/sh /usr/bin/os-prober"))
        self.assertEqual(pl.descrever_processo("bash"), "")
        self.assertIn("Outro programa", pl.explicar_erro("E: Could not get lock /var/lib/dpkg/lock-frontend"))
        self.assertIn("espaço", pl.explicar_erro("dpkg: error: No space left on device"))
        self.assertIn("do pacote linux-image-6.12.117-amd64",
                      pl.explicar_erro("Errors were encountered while processing:\n linux-image-6.12.117-amd64\n"))
        self.assertIn("registro", pl.explicar_erro("algo estranho"))


class AptParado(ag.AptDeMentira if TEM_GI else object):
    """Um apt cujo filho (um 'update-initramfs' de mentira) fica parado sem escrever nada."""

    def executar(self, comando, ao_progresso, ao_processo, ao_linha=lambda _l: None):
        ao_progresso(0.6, "Installed linux-image-6.12.117-amd64 (amd64)")
        ao_linha("Installed linux-image-6.12.117-amd64 (amd64)")
        processo = subprocess.Popen(["bash", "-c", "bash -c 'exec -a update-initramfs sleep 120'; exit 1"])
        pai = type("P", (), {"pid": processo.pid, "poll": processo.poll, "send_signal": processo.send_signal})()
        ao_processo(pai)
        codigo = processo.wait()
        return codigo, "Errors were encountered while processing:\n linux-image-6.12.117-amd64\n"


@unittest.skipUnless(TEM_GI, "sem python3-gi")
class TesteAgente(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.registro = Path(self._pasta.name) / "acoes.jsonl"

    def tearDown(self):
        self._pasta.cleanup()

    def esperar(self, agente, segundos=20):
        fim = time.time() + segundos
        while agente.tarefa is not None and time.time() < fim:
            time.sleep(0.05)
        self.assertIsNone(agente.tarefa, "a tarefa não terminou")
        return agente.ultima

    def test_registro_estimativa_e_plano_uma_vez_so(self):
        agente = ag.Agente(ag.AptDeMentira(), usar_polkit=False, registro=self.registro)
        plano = agente.preparar("atualizar_sistema", {}, 1000)
        self.assertGreater(plano["estimativa_s"], 0)
        agente.executar(plano["id"], 1000, lambda _a: True)
        self.assertTrue(agente.tarefa["registro"].endswith(plano["id"] + ".log"))
        ultima = self.esperar(agente)
        self.assertEqual(ultima["resultado"], "ok")
        texto = agente.ler_registro(ultima["registro"])
        self.assertIn("Passo 10 de 10", texto)
        self.assertEqual(agente.registros()[0]["nome"], ultima["registro"])
        with self.assertRaises(pl.Recusa):                      # o mesmo plano não roda de novo
            agente.executar(plano["id"], 1000, lambda _a: True)
        with self.assertRaises(pl.Recusa):
            agente.ler_registro("../../etc/shadow")

    def test_nada_a_fazer_nao_roda_o_apt(self):
        class AptEmDia(ag.AptDeMentira):
            vezes = 0

            def simular(self, comando):
                AptEmDia.vezes += 1
                return "Inst exemplo [1.0-1] (1.1-1 DuiaOS:teste [all])\n" if AptEmDia.vezes == 1 else ""

            def executar(self, *a, **k):
                raise AssertionError("não devia rodar o apt")
        agente = ag.Agente(AptEmDia(), usar_polkit=False, registro=self.registro)
        plano = agente.preparar("atualizar_sistema", {}, 1000)
        agente.executar(plano["id"], 1000, lambda _a: True)
        ultima = self.esperar(agente)
        self.assertEqual(ultima["resultado"], "ok")
        self.assertIn("já estava tudo instalado", ultima["mensagem"].lower())

    def test_conclui_instalacao_pela_metade_antes(self):
        class AptPelaMetade(ag.AptDeMentira):
            reparos = 0

            def auditar(self):
                return "" if AptPelaMetade.reparos else "linux-image-6.12.117-amd64 está meio configurado"

            def reparar(self, ao_linha):
                AptPelaMetade.reparos += 1
                return True
        agente = ag.Agente(AptPelaMetade(), usar_polkit=False, registro=self.registro)
        plano = agente.preparar("atualizar_sistema", {}, 1000)
        agente.executar(plano["id"], 1000, lambda _a: True)
        self.assertEqual(self.esperar(agente)["resultado"], "ok")
        self.assertEqual(AptPelaMetade.reparos, 1)

    def test_etapa_parada_e_interrompida_com_motivo(self):
        aviso, limite = ag.AVISO_PARADO, ag.LIMITE_PARADO
        ag.AVISO_PARADO, ag.LIMITE_PARADO = 1, 4
        original = ag.time.sleep
        try:
            ag.time.sleep = lambda s: original(min(s, 0.2))
            agente = ag.Agente(AptParado(), usar_polkit=False, registro=self.registro)
            plano = agente.preparar("atualizar_sistema", {}, 1000)
            agente.executar(plano["id"], 1000, lambda _a: True)
            visto = ""
            fim = time.time() + 30
            while agente.tarefa is not None and time.time() < fim:
                visto = visto or agente.tarefa.get("alerta", "")
                if agente.tarefa.get("etapa", "").startswith("Preparando"):
                    etapa = agente.tarefa["etapa"]
                original(0.05)
            ultima = self.esperar(agente, 1)
        finally:
            ag.AVISO_PARADO, ag.LIMITE_PARADO = aviso, limite
            ag.time.sleep = original
        self.assertIn("Está demorando", visto)
        self.assertIn("initramfs", etapa)
        self.assertEqual(ultima["resultado"], "erro")
        self.assertIn("ficou parada", ultima["mensagem"])
        self.assertIn("[vigia]", agente.ler_registro(ultima["registro"]))

    def test_tarefa_interrompida_aparece_depois(self):
        estado = Path(self._pasta.name) / "estado.json"
        estado.write_text(json.dumps({"tarefa": {"id": "abc", "acao": "atualizar_sistema", "argumentos": {},
                                                 "registro": "20261114-184900-0123456789abcdef.log"}, "ultima": None}))
        agente = ag.Agente(ag.AptDeMentira(), usar_polkit=False, registro=self.registro)
        self.assertEqual(agente.ultima["resultado"], "interrompida")
        self.assertIsNone(json.loads(estado.read_text())["tarefa"])


if __name__ == "__main__":
    unittest.main()


class TesteAutoAtualizacao(unittest.TestCase):
    """14/11/2026: o pacote duiaos-agente reiniciava o próprio serviço no meio da atualização feita por ele; com
    PrivateTmp, o /tmp do apt sumia e o gatilho do ca-certificates falhava ("mktemp: No such file")."""

    RAIZ_PACOTE = PASTA.parent / "pacotes" / "duiaos-agente"

    def test_servico_sem_isolamento_que_quebra_o_apt(self):
        unidade = (self.RAIZ_PACOTE / "raiz/usr/lib/systemd/system/duiaos-agente.service").read_text()
        linhas = [l.split("=")[0] for l in unidade.splitlines() if "=" in l and not l.startswith("#")]
        for proibido in ("PrivateTmp", "ProtectHome", "ProtectKernelTunables", "ProtectControlGroups", "ProtectSystem"):
            self.assertNotIn(proibido, linhas)
        self.assertIn("KillMode=process", unidade)

    def test_pacote_nao_reinicia_o_proprio_agente(self):
        for script in ("postinst", "prerm"):
            texto = (self.RAIZ_PACOTE / "DEBIAN" / script).read_text()
            comandos = [l for l in texto.splitlines() if not l.strip().startswith("#")]
            for comando in comandos:
                if "duiaos-agente.service" in comando and script == "postinst":
                    self.fail(f"{script} mexe no serviço em execução: {comando.strip()}")


@unittest.skipUnless(TEM_GI, "sem python3-gi")
class TesteProcurarForcado(unittest.TestCase):
    """O botão Procurar consulta os repositórios sempre; a busca automática respeita o intervalo de 5 min."""

    def _agente(self):
        chamadas = []

        class AptConta(ag.AptDeMentira):
            def atualizar_listas(self, forcar=False):
                chamadas.append(forcar)

        servico = ag.Agente.__new__(ag.Agente)
        servico.apt = AptConta()
        servico._ultimo_update = time.monotonic()      # acabou de consultar
        return servico, chamadas

    def test_sem_forcar_respeita_o_intervalo(self):
        servico, chamadas = self._agente()
        servico._simular("atualizar_sistema", {})
        self.assertEqual(chamadas, [])

    def test_forcar_consulta_mesmo_dentro_do_intervalo(self):
        servico, chamadas = self._agente()
        servico._simular("atualizar_sistema", {"forcar": True})
        self.assertEqual(chamadas, [True])
