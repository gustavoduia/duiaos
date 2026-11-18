"""Duia App Store (ADR 049): catálogo do Debian (DEP-11) e do Flathub (AppStream), vitrine, busca,
o que está instalado, andamento do flatpak e as telas em modo de demonstração. Dados inventados.

Rodar: python3 -m unittest discover -s shell/testes -t .
"""
import gzip
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "apps" / "loja"))

import catalogo  # noqa: E402

try:
    import yaml  # noqa: F401
    TEM_YAML = True
except ImportError:
    TEM_YAML = False
try:
    import PySide6  # noqa: F401
    TEM_QT = True
except ImportError:
    TEM_QT = False

DEP11 = """---
File: DEP-11
Version: '1.0'
Origin: exemplo-main
MediaBaseUrl: https://midia.exemplo.invalid/media
---
Type: desktop-application
ID: org.exemplo.Pintor
Package: pintor
Name:
  C: Pintor
  pt_BR: Pintor Traduzido
Summary:
  C: Paint things
  pt_BR: Pinte coisas
Description:
  C: <p>Paint <em>everything</em>.</p><ul><li>Brushes</li><li>Layers</li></ul>
ProjectLicense: GPL-3.0-or-later
Categories:
- Graphics
- RasterGraphics
Icon:
  cached:
  - name: pintor_org.exemplo.Pintor.png
    width: 64
    height: 64
  remote:
  - url: org/exemplo/Pintor/abc/icons/64x64/pintor.png
    width: 64
    height: 64
Launchable:
  desktop-id:
  - org.exemplo.Pintor.desktop
Url:
  homepage: https://pintor.exemplo.invalid
Screenshots:
- default: true
  source-image:
    url: org/exemplo/Pintor/abc/screenshots/image-1_orig.png
    width: 1920
    height: 1080
  thumbnails:
  - url: org/exemplo/Pintor/abc/screenshots/image-1_752x423.png
    width: 752
    height: 423
---
Type: font
ID: org.exemplo.Fonte
Package: fonts-exemplo
Name:
  C: Fonte
---
Type: desktop-application
ID: org.exemplo.Jogo
Package: jogo-exemplo
Name:
  C: Jogo
Summary:
  C: A game
ProjectLicense: LicenseRef-proprietary
Categories:
- Game
Icon:
  stock: jogo-exemplo
"""

APPSTREAM = """<?xml version="1.0" encoding="UTF-8"?>
<components version="0.8" origin="flathub">
  <component type="desktop-application">
    <id>org.exemplo.Pintor</id>
    <name>Pintor</name>
    <name xml:lang="pt_BR">Pintor Traduzido</name>
    <summary>Paint things</summary>
    <summary xml:lang="pt_BR">Pinte coisas</summary>
    <description><p>Paint
      everything.</p><ul><li>Brushes</li></ul><p xml:lang="pt_BR">Pinte tudo.</p></description>
    <developer id="exemplo"><name>Equipe Exemplo</name></developer>
    <project_license>MPL-2.0</project_license>
    <categories><category>Graphics</category><category>Office</category></categories>
    <icon type="remote" width="128" height="128">https://midia.exemplo.invalid/pintor.png</icon>
    <icon type="cached" width="128" height="128">org.exemplo.Pintor.png</icon>
    <url type="homepage">https://pintor.exemplo.invalid</url>
    <launchable type="desktop-id">org.exemplo.Pintor.desktop</launchable>
    <bundle type="flatpak">app/org.exemplo.Pintor/x86_64/stable</bundle>
    <screenshots><screenshot type="default"><image type="source">https://midia.exemplo.invalid/c1.png</image></screenshot></screenshots>
    <releases><release version="2.1" timestamp="1700000000"/></releases>
    <custom><value key="flathub::verification::verified">true</value></custom>
  </component>
  <component type="runtime"><id>org.exemplo.Base</id><name>Base</name></component>
  <component type="desktop-application">
    <id>org.exemplo.Chat</id>
    <name>Chat</name>
    <summary>Talk</summary>
    <project_license>LicenseRef-proprietary=https://exemplo.invalid</project_license>
    <categories><category>Network</category></categories>
    <bundle type="flatpak">app/org.exemplo.Chat/x86_64/stable</bundle>
  </component>
</components>
"""


class TesteTexto(unittest.TestCase):
    def test_traducao_e_descricao(self):
        self.assertEqual(catalogo.traduzido({"C": "Paint", "pt_BR": "Pinte"}), "Pinte")
        self.assertEqual(catalogo.traduzido({"C": "Pintor", "pt_BR": "Outro"}, catalogo.IDIOMAS_NOME), "Pintor")
        self.assertEqual(catalogo.traduzido({}), "")
        self.assertEqual(catalogo.html_para_texto("<p>Um &amp; dois.</p><ul><li>A</li><li>B</li></ul>"),
                         "Um & dois.\n\n• A\n• B")

    def test_licencas(self):
        self.assertTrue(catalogo.eh_livre("GPL-3.0-or-later"))
        self.assertTrue(catalogo.eh_livre("GPL-3.0+ AND LGPL-3.0+"))
        self.assertTrue(catalogo.eh_livre("GPL-2.0-or-later WITH Classpath-exception-2.0"))
        self.assertFalse(catalogo.eh_livre("LicenseRef-proprietary"))
        self.assertFalse(catalogo.eh_livre(""))
        self.assertEqual(catalogo.nome_da_licenca("LicenseRef-proprietary=https://x"), "Proprietária")
        self.assertEqual(catalogo.nome_da_licenca("MIT OR Apache-2.0"), "MIT ou Apache-2.0")

    def test_categorias(self):
        self.assertEqual(catalogo.categorias_principais(["Audio", "Video", "GTK", "Game"]), ["AudioVideo", "Game"])


@unittest.skipUnless(TEM_YAML, "PyYAML não instalado")
class TesteDebian(unittest.TestCase):
    def test_le_so_aplicativos(self):
        with tempfile.TemporaryDirectory() as pasta:
            icones = Path(pasta) / "icons"
            (icones / "exemplo-main" / "64x64").mkdir(parents=True)
            (icones / "exemplo-main" / "64x64" / "pintor_org.exemplo.Pintor.png").write_bytes(b"png")
            apps = catalogo.ler_dep11(DEP11, (icones,))
        self.assertEqual([a["pacote"] for a in apps], ["pintor", "jogo-exemplo"])
        pintor, jogo = apps
        self.assertEqual(pintor["id"], "debian:pintor")
        self.assertEqual(pintor["nome"], "Pintor")                    # a marca, não a tradução
        self.assertEqual(pintor["resumo"], "Pinte coisas")
        self.assertIn("• Layers", pintor["descricao"])
        self.assertTrue(pintor["icone"].endswith("pintor_org.exemplo.Pintor.png"))
        self.assertEqual(pintor["categorias"], ["Graphics"])
        self.assertEqual(pintor["capturas"], ["https://midia.exemplo.invalid/media/org/exemplo/Pintor/abc/screenshots/image-1_752x423.png"])
        self.assertEqual(pintor["lancador"], "org.exemplo.Pintor.desktop")
        self.assertTrue(pintor["livre"])
        self.assertEqual(jogo["icone"], "jogo-exemplo")              # ícone do tema
        self.assertEqual(jogo["licenca"], "Proprietária")

    def test_icone_remoto_sem_arquivo(self):
        apps = catalogo.ler_dep11(DEP11, ())
        self.assertEqual(apps[0]["icone"], "https://midia.exemplo.invalid/media/org/exemplo/Pintor/abc/icons/64x64/pintor.png")
        self.assertEqual(apps[0]["iconeReserva"], "org.exemplo.Pintor")

    def test_arquivos_da_lista_do_apt(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "exemplo_dists_main_dep11_Components-amd64.yml.gz"
            arquivo.write_bytes(gzip.compress(DEP11.encode()))
            (Path(pasta) / "exemplo_dists_main_binary-amd64_Packages").write_text("")
            self.assertEqual(catalogo.arquivos_dep11((Path(pasta),)), [arquivo.resolve()])
            self.assertEqual(len(catalogo.catalogo_debian((Path(pasta),), ())), 2)


class TesteFlathub(unittest.TestCase):
    def test_appstream(self):
        with tempfile.TemporaryDirectory() as pasta:
            (Path(pasta) / "128x128").mkdir()
            (Path(pasta) / "128x128" / "org.exemplo.Pintor.png").write_bytes(b"png")
            apps = catalogo.ler_appstream_xml(APPSTREAM.encode(), pasta)
            pintor, chat = apps
            self.assertTrue(pintor["icone"].endswith("org.exemplo.Pintor.png"))   # o arquivo local antes da internet
        self.assertEqual(len(apps), 2)                                        # o runtime não entra
        self.assertEqual(pintor["id"], "flathub:org.exemplo.Pintor")
        self.assertEqual(pintor["nome"], "Pintor")
        self.assertEqual(pintor["resumo"], "Pinte coisas")
        self.assertEqual(pintor["descricao"], "Pinte tudo.")
        self.assertEqual(pintor["desenvolvedor"], "Equipe Exemplo")
        self.assertEqual(pintor["versao"], "2.1")
        self.assertTrue(pintor["verificado"])
        self.assertEqual(pintor["categorias"], ["Graphics", "Office"])
        self.assertEqual(pintor["capturas"], ["https://midia.exemplo.invalid/c1.png"])
        self.assertEqual(chat["licenca"], "Proprietária")
        self.assertFalse(chat["livre"])
        self.assertFalse(chat["verificado"])

    def test_descricao_sem_traducao(self):
        xml = APPSTREAM.replace('<p xml:lang="pt_BR">Pinte tudo.</p>', "")
        pintor = catalogo.ler_appstream_xml(xml.encode())[0]
        self.assertEqual(pintor["descricao"], "Paint everything.\n\n• Brushes")
        self.assertEqual(pintor["icone"], "https://midia.exemplo.invalid/pintor.png")


class TesteVitrineEBusca(unittest.TestCase):
    def setUp(self):
        self.flathub = catalogo.ler_appstream_xml(APPSTREAM.encode())
        self.debian = [catalogo.montar("debian", "org.exemplo.Pintor", "pintor", "Pintor", "Pinte"),
                       catalogo.montar("debian", "org.exemplo.Editor", "editor-exemplo", "Editor", "Edite textos",
                                       categorias=["TextEditor"])]

    def test_juntar_com_alternativa(self):
        juntos = catalogo.juntar(self.debian, self.flathub)
        self.assertEqual([a["id"] for a in juntos], ["flathub:org.exemplo.Chat", "debian:editor-exemplo",
                                                    "flathub:org.exemplo.Pintor"])
        self.assertEqual(juntos[2]["alternativa"], {"id": "debian:pintor", "fonte": "debian"})
        preferindo_debian = catalogo.juntar(self.debian, self.flathub, preferir="debian")
        self.assertIn("debian:pintor", [a["id"] for a in preferindo_debian])

    def test_vitrine_usa_a_primeira_opcao_e_nao_repete(self):
        juntos = catalogo.juntar(self.debian, self.flathub)
        destaques = {"destaques": [{"app": "org.nao.Existe|org.exemplo.Pintor", "titulo": "T"},
                                   {"app": "org.nao.Existe"}],
                     "colecoes": [{"titulo": "C", "apps": ["org.exemplo.Pintor|pintor", "org.exemplo.Pintor",
                                                           "editor-exemplo", "nada"]},
                                  {"titulo": "Vazia", "apps": ["nada"]}]}
        vitrine = catalogo.vitrine(juntos, destaques)
        self.assertEqual([d["app"]["id"] for d in vitrine["destaques"]], ["flathub:org.exemplo.Pintor"])
        self.assertEqual([c["titulo"] for c in vitrine["colecoes"]], ["C"])
        self.assertEqual([a["id"] for a in vitrine["colecoes"][0]["apps"]], ["flathub:org.exemplo.Pintor",
                                                                            "debian:editor-exemplo"])

    def test_destaques_do_repositorio(self):
        destaques = catalogo.ler_destaques(RAIZ / "apps" / "loja" / "destaques.json")
        self.assertGreaterEqual(len(destaques["destaques"]), 3)
        self.assertTrue(all(c["apps"] for c in destaques["colecoes"]))

    def test_busca_sem_acento_e_nome_primeiro(self):
        apps = [catalogo.montar("flathub", "a.B", "a.B", "Vídeo Fácil", "Edite"),
                catalogo.montar("flathub", "c.D", "c.D", "Outro", "Um editor de vídeo"),
                catalogo.montar("flathub", "e.F", "e.F", "Música", "Toque")]
        self.assertEqual([a["nome"] for a in catalogo.buscar(apps, "video")], ["Vídeo Fácil", "Outro"])
        self.assertEqual(catalogo.buscar(apps, "   "), [])


class TesteInstalados(unittest.TestCase):
    def test_dpkg(self):
        saida = "pintor\tii \t1.0-1\nvelho\trc \t0.9\nlib:amd64\tii \t2.0\n"
        self.assertEqual(catalogo.interpretar_dpkg(saida), {"pintor": "1.0-1", "lib": "2.0"})

    def test_flatpak(self):
        saida = "org.exemplo.Pintor\t2.1\tuser\norg.exemplo.Chat\t\tsystem\n\n"
        self.assertEqual(catalogo.interpretar_flatpak_lista(saida),
                         {"org.exemplo.Pintor": {"versao": "2.1", "instalacao": "user"},
                          "org.exemplo.Chat": {"versao": "", "instalacao": "system"}})


class TesteAndamentoFlatpak(unittest.TestCase):
    def test_linhas(self):
        ler = catalogo.ler_linha_flatpak
        self.assertEqual(ler("Looking for matches…", "instalar"), (None, "Conferindo o que precisa"))
        self.assertEqual(ler("Installing… \x1b[2m██ \x1b[22m   10%\x1b[6n", "instalar"),
                         (0.1, "Instalando — 10%"))
        fracao, mensagem = ler("Installing 2/4… ███  50%  1.2 MB/s", "instalar")
        self.assertAlmostEqual(fracao, 0.375)
        self.assertEqual(mensagem, "Instalando (parte 2 de 4) — 50%")
        self.assertEqual(ler("Uninstalling…", "remover"), (None, "Removendo"))
        self.assertEqual(ler("\x1b[?25l\x1b[6n", "instalar"), (None, ""))
        self.assertEqual(ler("error: No remote refs found", "instalar"), (None, "error: No remote refs found"))


class TesteCache(unittest.TestCase):
    def test_refaz_so_quando_as_origens_mudam(self):
        chamadas = []

        def gerar():
            chamadas.append(1)
            return [{"id": "flathub:x"}]
        with tempfile.TemporaryDirectory() as pasta:
            # pasta_appstream_flathub procura em $XDG_DATA_HOME/flatpak/appstream/flathub/ARQ/active
            origem = Path(pasta) / "flatpak" / "appstream" / catalogo.FLATHUB / "x86_64" / "active"
            origem.mkdir(parents=True)
            (origem / "appstream.xml.gz").write_bytes(gzip.compress(b"<components/>"))
            antes = os.environ.get("XDG_DATA_HOME")
            os.environ["XDG_DATA_HOME"] = pasta
            try:
                cache = Path(pasta) / "cache"
                self.assertEqual(catalogo.carregar("flathub", gerar, cache), [{"id": "flathub:x"}])
                self.assertEqual(catalogo.carregar("flathub", gerar, cache), [{"id": "flathub:x"}])
                self.assertEqual(len(chamadas), 1)                    # a segunda veio do cache
                (origem / "appstream.xml.gz").write_bytes(gzip.compress(b"<components> </components>"))
                catalogo.carregar("flathub", gerar, cache)
                self.assertEqual(len(chamadas), 2)                    # o catálogo mudou: refeito
            finally:
                if antes is None:
                    os.environ.pop("XDG_DATA_HOME", None)
                else:
                    os.environ["XDG_DATA_HOME"] = antes


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteIlha(unittest.TestCase):
    """Quem já tinha a Ilha configurada ganha a Duia App Store uma vez, ao lado das Configurações."""

    def test_migracao(self):
        sys.path.insert(0, str(RAIZ / "shell" / "ilha-de-aplicativos"))
        import importlib.util
        especificacao = importlib.util.spec_from_file_location("ilha_main", RAIZ / "shell" / "ilha-de-aplicativos" / "main.py")
        ilha = importlib.util.module_from_spec(especificacao)
        from unittest import mock
        with mock.patch.dict(os.environ):              # o módulo da Ilha escolhe a plataforma do Qt ao ser lido
            especificacao.loader.exec_module(ilha)
        with tempfile.TemporaryDirectory() as pasta:
            ilha.PASTA_CONFIG, ilha.ARQUIVO_CONFIG = Path(pasta), Path(pasta) / "ilha.conf"
            ilha.ARQUIVO_CONFIG.write_text("[ilha]\nversao = 2\nfixados = duiaos-configuracoes.desktop;foot.desktop\n")
            novos = ["duiaos-configuracoes.desktop", "duiaos-loja.desktop", "duiaos-ora.desktop", "duiaos-mailbox.desktop"]
            self.assertEqual(ilha.ler_fixados(), novos + ["foot.desktop"])
            ilha.gravar_fixados(["foot.desktop"])                  # depois, a pessoa tirou: não volta
            self.assertEqual(ilha.ler_fixados(), ["foot.desktop"])
            ilha.ARQUIVO_CONFIG.write_text("[ilha]\nfixados = foot.desktop\n")     # versão 1
            self.assertEqual(ilha.ler_fixados(), novos + ["foot.desktop"])
            # versão 3 com o Firefox fixado: o lugar dele vai para o Ora, e o Mail Box entra logo depois (ADR 073)
            ilha.ARQUIVO_CONFIG.write_text("[ilha]\nversao = 3\nfixados = duiaos-configuracoes.desktop;duiaos-loja.desktop;"
                                           "foot.desktop;firefox-esr.desktop\n")
            self.assertEqual(ilha.ler_fixados(), ["duiaos-configuracoes.desktop", "duiaos-loja.desktop", "foot.desktop",
                                                  "duiaos-ora.desktop", "duiaos-mailbox.desktop"])


@unittest.skipUnless(TEM_QT, "PySide6 não instalado")
class TesteTelasDaLoja(unittest.TestCase):
    def test_telas(self):
        capturas = Path(os.environ.get("DUIAOS_CAPTURAS") or tempfile.mkdtemp(prefix="duiaos-capturas-"))
        capturas.mkdir(parents=True, exist_ok=True)
        casos = [("descobrir", []), ("instalados", []), ("atualizacoes", []), ("categoria:Graphics", []),
                 ("busca:editor", []), ("app:flathub:org.gimp.GIMP", []),
                 ("app:debian:stellarium", ["--confirmar", "debian:stellarium"])]
        with tempfile.TemporaryDirectory() as inicio:
            for pagina, extra in casos:
                with self.subTest(pagina=pagina):
                    arquivo = capturas / ("loja-" + pagina.replace(":", "-") + ".png")
                    ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": inicio,
                                "XDG_CONFIG_HOME": inicio + "/.config", "XDG_RUNTIME_DIR": inicio}
                    resultado = subprocess.run([sys.executable, "apps/loja/main.py", "--demonstracao", "--pagina", pagina,
                                                *extra, "--captura", str(arquivo)], capture_output=True, text=True,
                                               timeout=60, env=ambiente, cwd=RAIZ)
                    erros = [linha for linha in resultado.stderr.splitlines()
                             if any(e in linha for e in ("TypeError", "ReferenceError", "SyntaxError", "is not a type",
                                                         "Cannot assign", "is not defined", "non-existent property"))]
                    self.assertEqual(erros, [])
                    self.assertTrue(arquivo.is_file(), resultado.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()


class TesteTamanho(unittest.TestCase):
    """Tamanho do download e do aplicativo instalado (ADR 059)."""

    APT = ("Reading package lists...\n"
           "'http://deb.debian.org/debian/pool/main/g/gimp/gimp_3.0_amd64.deb' gimp_3.0_amd64.deb 4680180 MD5Sum:e1\n"
           "'http://deb.debian.org/debian/pool/main/b/babl/libbabl_0.1_amd64.deb' libbabl_0.1_amd64.deb 319820 MD5Sum:aa\n"
           "0 upgraded, 2 newly installed, 0 to remove and 0 not upgraded.\nNeed to get 5000 kB of archives.\n"
           "After this operation, 21.5 MB of additional disk space will be used.\n")
    FLATPAK = ("        ID: org.gimp.GIMP\n  Download: 102.5 MB\n Installed: 268.6 MB\n   Runtime: org.gnome.Platform/x86_64/51\n")
    RUNTIME = "  Download: 432.8 MB\n Installed: 1.1 GB\n"

    def test_apt(self):
        self.assertEqual(catalogo.tamanho_apt(self.APT), {"baixar": 5000000, "instalar": 21500000, "pacotes": 2})
        self.assertIsNone(catalogo.tamanho_apt("E: Unable to locate package nada\n"))

    def test_flatpak(self):
        self.assertEqual(catalogo.tamanho_flatpak(self.FLATPAK),
                         {"baixar": 102500000, "instalar": 268600000, "runtime": "org.gnome.Platform/x86_64/51"})
        self.assertIsNone(catalogo.tamanho_flatpak("error: No remote refs found"))

    def test_soma_o_ambiente_quando_falta(self):
        def rodar(comando, falta=True):
            texto = " ".join(comando)
            if "remote-info" in texto and "runtime/" in texto:
                return self.RUNTIME
            if "remote-info" in texto:
                return self.FLATPAK
            return "" if falta else "Ref: runtime/org.gnome.Platform/x86_64/51"
        app = {"fonte": "flathub", "pacote": "org.gimp.GIMP"}
        com_ambiente = catalogo.tamanho_do_app(app, rodar)
        self.assertEqual((com_ambiente["baixar"], com_ambiente["instalar"]), (535300000, 1368600000))
        self.assertIn("ambiente", com_ambiente["detalhe"])
        sem = catalogo.tamanho_do_app(app, lambda c: rodar(c, falta=False))
        self.assertEqual((sem["baixar"], sem["detalhe"]), (102500000, ""))
        debian = catalogo.tamanho_do_app({"fonte": "debian", "pacote": "gimp"}, lambda c: self.APT)
        self.assertEqual((debian["baixar"], debian["detalhe"]), (5000000, "Com 1 pacote de que ele precisa"))

    def test_instalado(self):
        self.assertEqual(catalogo.tamanho_instalado({"fonte": "debian", "pacote": "gimp"}, lambda c: "20480\n"), 20480 * 1024)
        self.assertEqual(catalogo.tamanho_instalado({"fonte": "flathub", "pacote": "x"}, lambda c: self.FLATPAK), 268600000)
