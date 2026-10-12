---
title: O Windows pede a chave do BitLocker
description: Por que acontece e como evitar nas próximas vezes.
---

O BitLocker pede a chave quando o jeito de ligar o computador muda: Secure Boot desligado, Windows iniciado
pelo menu do DuiaOS ou ordem de boot alterada.

1. Digite a chave de recuperação (48 dígitos, em [aka.ms/myrecoverykey](https://aka.ms/myrecoverykey)).
2. Já no Windows, abra o Prompt de Comando como administrador e renove o registro do BitLocker:

   ```
   manage-bde -protectors -disable C:
   manage-bde -protectors -enable C:
   ```

3. Daqui em diante, vá para o Windows por [Reiniciar no Windows](/documentacao/como-fazer/reiniciar-no-windows/).

Se o PIN do Windows Hello parar de funcionar, entre com a senha da conta Microsoft e recrie o PIN em
Configurações › Contas › Opções de entrada.
