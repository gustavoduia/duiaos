# Instalar o DuiaOS ao lado do Windows (dual boot)

Este guia instala o DuiaOS num espaço livre do disco, mantendo o Windows,
os arquivos e o PIN do Windows Hello.

## Por que o BitLocker pode pedir a chave de recuperação

O BitLocker (criptografia do Windows) e o PIN do Windows Hello usam o chip
de segurança do computador (TPM). O TPM registra **como** o computador
iniciou: o estado do Secure Boot e os programas de boot usados. Se isso
muda, o Windows desconfia e pede a chave de recuperação; em alguns casos o
PIN deixa de funcionar e precisa ser refeito.

Três coisas causam essa mudança numa instalação de dual boot:

1. **Desligar o Secure Boot** na BIOS.
2. **Iniciar o Windows pelo menu do DuiaOS** (GRUB): o Windows passa a ser
   carregado por outro programa de boot.
3. **Mudar a ordem de boot** no firmware.

O DuiaOS evita as duas primeiras: a ISO e o sistema instalado funcionam com
o **Secure Boot ligado**, e o DuiaOS oferece o **Reiniciar no Windows**, que
inicia o Windows pelo próprio firmware.

## Antes de instalar (no Windows)

1. **Guarde a chave de recuperação do BitLocker** (Prompt de Comando como
   administrador):

   ```
   manage-bde -status C:
   manage-bde -protectors -get C:
   ```

   Anote a "Senha Numérica" (48 dígitos). Ela também fica em
   https://aka.ms/myrecoverykey.

2. **Suspenda a proteção do BitLocker por 3 reinicializações** — o Windows a
   religa sozinho depois:

   ```
   manage-bde -protectors -disable C: -RebootCount 3
   ```

3. **Desligue a Inicialização Rápida**: Painel de Controle → Opções de
   Energia → Escolher a função dos botões de energia → desmarque "Ligar
   inicialização rápida".

4. **Relógio em horário universal** (evita a hora errada ao trocar de
   sistema):

   ```
   reg add "HKLM\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
   ```

5. **Deixe espaço "Não alocado"** no Gerenciamento de Disco (mínimo 30 GB;
   recomendado 50 GB ou mais).

6. **Não desligue o Secure Boot.**

## Instalar

1. Inicie pelo pendrive (Dell: **F12**) e escolha **Instalar o DuiaOS**.
2. Particionamento: **Assistido – usar o maior espaço livre contínuo**.
   **Nunca** escolha "usar o disco inteiro".
3. Confira o resumo: só partições novas no espaço livre; a partição EFI do
   Windows é reaproveitada, sem formatar.

## Depois de instalar

- O menu do DuiaOS mostra o DuiaOS e o **Windows Boot Manager**.
- **Para ir ao Windows sem pedido de chave**, use no DuiaOS:

  ```
  sudo /usr/lib/duiaos/reiniciar-no-windows
  ```

  (Na Fase 4 isso vira o botão "Reiniciar no Windows" no menu de energia.)

- Se mesmo assim o Windows pedir a chave ao ser escolhido pelo menu do
  DuiaOS, entre com a chave e, já no Windows, **renove o registro do
  BitLocker** para o caminho de boot atual:

  ```
  manage-bde -protectors -disable C:
  manage-bde -protectors -enable C:
  ```

- Se o PIN do Windows Hello parar de funcionar: entre com a senha da conta
  Microsoft e recrie o PIN em Configurações → Contas → Opções de entrada.

## Acesso remoto (SSH)

Como no Windows e no macOS, o acesso remoto vem **desligado**. Para
desenvolver pelo Mac, ligue no DuiaOS:

```
sudo systemctl enable --now ssh
```

Cada instalação tem chaves de identificação próprias. Depois de reinstalar,
o Mac avisa que a identificação mudou — é esperado. Limpe a chave antiga no
Mac com `ssh-keygen -R <nome-ou-ip>` e conecte de novo.
