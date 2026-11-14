# Interface do DuiaOS (shell)

Qt6/QML + Python (PySide6) sobre o compositor labwc (ADRs 002 e 003).
Esta pasta vira o pacote `duiaos-shell` (veja `pacotes/README.md`): fica em
`/usr/share/duiaos/shell` e os arquivos de `sessao/` vão para `/etc/xdg/labwc`.

| Pasta | Componente |
| --- | --- |
| `entrada/` | **Tela de Entrada**: iniciar uma sessão (greetd + cage) |
| `bloqueio/` | **Tela de Bloqueio**: desbloquear uma sessão aberta |
| `comum/` | Visual único das duas telas (`TelaDeAcesso.qml`), menu de energia, símbolo e funções comuns; `qml/DuiaOS/` (biblioteca QML `import DuiaOS`: tema, botões, interruptores, deslizantes, ícones), `icones.py` (ícones próprios em SVG), `controles.py` (Wi-Fi, Bluetooth, som, brilho, bateria, energia, luz noturna), `pastas.py` (pastas do usuário e preferências), `aplicativos.py`, `tipos.py`, `sessao.py` (aplica as preferências ao entrar) |
| `menu-de-energia/` | **Menu de Energia** da sessão (Ctrl+Alt+Delete) |
| `barra-de-recursos/` | **Barra de Recursos**: Menu do DuiaOS, botão Wise, aplicativo em uso, ícones de controle (até 4 + balão da seta), **Central de Controle** e relógio (calendário) |
| `ilha-de-aplicativos/` | **Ilha de Aplicativos** (com pasta Aplicativos, pilha de Downloads e Lixeira) e **Central de Aplicativos** em tela cheia |
| `testes/` | Testes da lógica e das telas (`python3 -m unittest discover -s shell/testes -t .`) |

Os aplicativos **Explorador de Arquivos** e **Configurações** ficam em `../apps/` e
entram no mesmo pacote `duiaos-shell` (ADR 044).

## Ver as telas sem a sessão do DuiaOS

Cada parte abre numa janela comum, com dados de exemplo, e pode salvar a imagem:

```sh
python3 shell/barra-de-recursos/main.py --demonstracao --painel central   # menu, central, wifi, som, bateria…
python3 shell/ilha-de-aplicativos/main.py --demonstracao --downloads       # ou --central
python3 apps/explorador-de-arquivos/main.py ~/Documentos
python3 apps/configuracoes/main.py --demonstracao --secao tela
# + --captura arquivo.png para salvar a imagem e sair
```
| `sessao/` | Início da sessão e configuração do labwc |
| `pacotes.list` | Pacotes do Debian usados pela interface (entram na ISO) |

## Do boot à área de trabalho

1. **Animação de boot** (Plymouth, tema `duiaos`): o símbolo Órbita com o ponto
   balançando na abertura do "D". Também aparece ao desligar.
2. **Tela de Entrada**: o greetd abre `entrada/iniciar` como o usuário
   `_greetd`; o cage mostra a tela em tela cheia. Depois da senha correta, o
   greetd inicia `sessao/iniciar-sessao`. No modo live, a sessão abre direto,
   sem senha (`/usr/lib/duiaos/preparar-entrada`).
3. **Sessão**: labwc + papel de parede + Barra de Recursos + Ilha de
   Aplicativos. O Wise só existe a partir daqui.

A Tela de Entrada e a Tela de Bloqueio são **a mesma tela**, com o mesmo
visual (`comum/TelaDeAcesso.qml`); muda só o texto que descreve o momento:
"Digite a senha para iniciar a sessão" ou "Sessão bloqueada. Digite a senha
para desbloquear".

## Atalhos

| Atalho | Ação |
| --- | --- |
| Super + Espaço | Abre e fecha a Central de Aplicativos |
| Super + E | Abre o Explorador de Arquivos |
| Super + W | Abre e fecha o Wise |
| Super + L | Bloqueia a tela |
| Ctrl + Alt + Delete | Menu de Energia |
| Clique no símbolo da Barra | Menu do DuiaOS (Configurações, Repousar, Reiniciar, Desligar, Encerrar sessão…) |

A tela também bloqueia sozinha após 10 minutos sem uso (muda em Configurações ›
Bateria e energia) e antes de repousar (swayidle, iniciado por `comum/sessao.py`).

## Wise

O Wise fica no repositório privado `duiaos-wise` (pacote `duiaos-wise`). A
interface só conhece o contrato:

| Contrato | Uso |
| --- | --- |
| `/usr/bin/duiaos-wise` | Existe quando o Wise está instalado |
| `duiaos-wise --alternar` | Abre ou fecha a janela (botão da Barra, Ilha, Super+W, ícone perto da bateria) |
| `duiaos-wise --fundo` | Chamado ao abrir a sessão (`sessao/autostart`), que o reabre se ele fechar; o Wise começa descansando e cumprimenta a pessoa |
| `$XDG_RUNTIME_DIR/duiaos-wise.estado` | JSON `{"pid", "estado"}` com `aberto`, `descansando` ou `pensando`, enquanto ele roda |
| `duiaos-wise.desktop` e o ícone `duiaos-wise` | Wise como primeiro item fixo da Ilha; ícone na Barra |

Com ele instalado aparecem o botão "Wise" na Barra de Recursos, o ícone do
Wise perto da bateria (mais apagado quando ele descansa), o Wise como
primeiro item fixo da Ilha de Aplicativos e o atalho Super+W. O botão
flutuante com a carinha, no canto inferior direito, é do próprio Wise. Sem
ele instalado, nada disso aparece.

## Menu de Energia

Bloquear · Encerrar sessão · Suspender · Reiniciar · **Reiniciar no Windows**
(só aparece com dual boot) · Desligar. Na Tela de Entrada e na Tela de
Bloqueio, o botão **Energia** mostra Suspender, Reiniciar, Reiniciar no
Windows e Desligar. "Reiniciar no Windows" usa o serviço
`duiaos-reiniciar-no-windows.service`, liberado pelo polkit só para quem está
no computador.

## Testar o visual sem reiniciar

```bash
python3 shell/entrada/main.py --demonstracao    # senha "duia" entra
python3 shell/bloqueio/main.py --demonstracao   # senha "duia" desbloqueia
```

Para a sessão usar o código do repositório em vez do instalado, copie
`/etc/xdg/labwc/environment` para `~/.config/labwc/environment` e descomente
a linha `DUIAOS_SHELL=...`. Depois, encerre a sessão e entre de novo.

## Limitação conhecida da Tela de Bloqueio

A Tela de Bloqueio usa uma camada "overlay" do Wayland com teclado exclusivo,
e não o protocolo próprio de bloqueio (`ext-session-lock`), que o Qt 6.8 do
Debian 13 não oferece. Para compensar: se ela for encerrada sem a senha, o
script `bloqueio/bloquear` a abre de novo na hora e, se falhar repetidamente,
usa o swaylock (que usa o protocolo). A troca para o protocolo próprio está
prevista antes da 1.0 (ADR 026).
