---
title: Instalar o DuiaOS ao lado do Windows
description: Instale o DuiaOS num espaço livre do disco e continue usando o Windows, seus arquivos e o PIN.
sidebar:
  order: 1
---

Neste guia você instala o DuiaOS ao lado do Windows. Ao terminar, o computador mostra um menu para escolher
o sistema ao ligar, e o Windows continua com os seus arquivos e o PIN do Windows Hello.

**Você vai precisar de:** um pendrive de 8 GB ou mais com a imagem do DuiaOS
([baixe aqui](/baixar/)), pelo menos 30 GB livres no disco (recomendado 50 GB) e cerca de 30 minutos.

## 1. Prepare o Windows

1. **Guarde a chave de recuperação do BitLocker.** Abra o Prompt de Comando como administrador e digite:

   ```
   manage-bde -protectors -get C:
   ```

   Anote a "Senha Numérica" (48 dígitos). Ela também fica em [aka.ms/myrecoverykey](https://aka.ms/myrecoverykey).

2. **Suspenda o BitLocker por 3 reinicializações** (o Windows liga de novo sozinho):

   ```
   manage-bde -protectors -disable C: -RebootCount 3
   ```

3. **Desligue a Inicialização Rápida**: Painel de Controle › Opções de Energia › Escolher a função dos botões
   de energia › desmarque "Ligar inicialização rápida".

4. **Deixe o relógio em horário universal** (evita a hora errada ao trocar de sistema):

   ```
   reg add "HKLM\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
   ```

5. **Libere espaço**: no Gerenciamento de Disco, diminua a partição do Windows e deixe o espaço como
   "Não alocado".

:::caution[Não desligue o Secure Boot]
O DuiaOS funciona com o Secure Boot ligado. Desligá-lo faz o Windows pedir a chave do BitLocker.
:::

## 2. Instale

1. Ligue o computador pelo pendrive (nos Dell, aperte <kbd>F12</kbd> ao ligar) e escolha **Instalar o DuiaOS**.
2. No particionamento, escolha **Assistido – usar o maior espaço livre contínuo**.
   Nunca escolha "usar o disco inteiro": isso apaga o Windows.
3. Confira o resumo antes de confirmar: só partições novas no espaço livre.

## 3. Depois de instalar

- Ao ligar, o menu mostra o **DuiaOS** e o **Windows Boot Manager**.
- Para ir ao Windows sem pedido de chave, use **Reiniciar no Windows** no [Menu de Energia](/documentacao/como-fazer/reiniciar-no-windows/).

Pronto. Agora [conheça a área de trabalho](/documentacao/comecar/conhecer-a-area-de-trabalho/).
