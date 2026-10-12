# Interface do DuiaOS (shell)

Qt6/QML + Python (PySide6) sobre o compositor labwc (ADRs 002 e 003).
Esta pasta vira o pacote `duiaos-shell` (veja `pacotes/README.md`): fica em
`/usr/share/duiaos/shell` e os arquivos de `sessao/` vão para `/etc/xdg/labwc`.

| Pasta | Componente |
| --- | --- |
| `entrada/` | **Tela de Entrada**: iniciar uma sessão (greetd + cage) |
| `bloqueio/` | **Tela de Bloqueio**: desbloquear uma sessão aberta |
| `comum/` | Visual único das duas telas (`TelaDeAcesso.qml`), menu de energia, símbolo, cores e funções comuns |
| `menu-de-energia/` | **Menu de Energia** da sessão |
| `barra-de-recursos/` | **Barra de Recursos** (relógio, Wi-Fi, som, bateria); o símbolo abre o Menu de Energia |
| `ilha-de-aplicativos/` | **Ilha de Aplicativos** e **Central de Aplicativos** |
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
| Super + W | Abre e fecha o Wise |
| Super + L | Bloqueia a tela |
| Ctrl + Alt + Delete | Menu de Energia |
| Clique no símbolo da Barra | Menu de Energia |

A tela também bloqueia sozinha após 10 minutos sem uso e antes de suspender
(swayidle, em `sessao/autostart`).

## Wise

O Wise fica no repositório privado `duiaos-wise` (pacote `duiaos-wise`). A
interface só conhece o contrato: o comando `/usr/bin/duiaos-wise` existe
quando ele está instalado, e `duiaos-wise --alternar` abre ou fecha a janela.
Com ele instalado aparecem o botão "Wise" na Barra de Recursos, o Wise como
primeiro item fixo da Ilha de Aplicativos (`duiaos-wise.desktop`) e o atalho
Super+W. Sem ele, nada disso aparece.

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
