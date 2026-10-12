# DuiaOS — Estado atual

> Atualize este arquivo no FIM de cada bloco de trabalho, no mesmo PR. Ele é o que a próxima sessão (de
> qualquer conta) lê para continuar. Escreva fatos verificáveis: branch, PR, commit, o que está instalado onde.

Atualizado em: 12/10/2026 (19h20) · por: Claude (conta do Gustavo) · sessão session_01LzmCWyGMx1FKt4d1cuh5R8

## 1. O que está na main e o que está pendente
- **duiaos main**: PRs #1–#5 e **#9** (duiaos-ollama, duiaos-ia, Central de IA, duiaos-agente, acessibilidade,
  medição de motores, continuidade; ADRs 030–039), merge em 12/10 (17h30). #6–#8 fechados.
- **duiaos-wise main**: #1, #2 e **#5** (carinha de robô, aprovação, clima, agenda, uso do computador).
  **#7** aberto (diagnóstico W17 + correções W18; substitui o #6, fechado quando a base foi apagada).
- **duiaos-websites main**: #1 e #2 (publicados). **#4** aberto (irmão do Wise #7; substitui o #3).
- **duiaos #10** (`claude/logs-do-sistema`, rascunho): logs do sistema, F1.

## 2. O que está instalado em cada máquina
| Máquina | duiaos | duiaos-wise | Como conferir |
| --- | --- | --- | --- |
| Dell | branch `claude/tres-frentes` (medição); pacotes: a confirmar | a confirmar (carinha antiga ⇒ provavelmente a main) | 🔗 DELL: `dpkg -l 'duiaos*' \| grep ^ii` e `cd ~/Projetos/duiaos-wise && git log --oneline -1` |
| Mac | — | — | — |

## 3. Em andamento (quem / branch / PR rascunho)
- Claude (conta do Gustavo): `claude/logs-do-sistema` (PR #10, rascunho) — logs do sistema F1: biblioteca
  `duiaos-registro`, falhas, perfil, coletor `duiaos-relatorios` com envio ao `duiaos-diagnosticos`.

## 4. Próximos passos
1. Gustavo: testar no Dell as duas branches (instalar-local + reboot) e fazer o merge de duiaos #9 e Wise #5.
2. Depois do merge de #9 e #5: lançar a versão 0.3.0 (ISO + apt) e retirar os avisos "Na próxima versão" da
   documentação. O Wise ainda não entra na ISO (distribuição pública do Wise não decidida — pergunta abaixo).
3. Google/Microsoft na agenda: Gustavo registra os aplicativos (duiaos-wise/docs/contas-de-agenda.md).
4. Logs do sistema, F1 (decisão acima): PR novo a partir da main depois dos merges.
5. Seguir o plano (docs/visao.md): W3 voz, W4 Central de IA completa (gateway da nuvem no duiaos-ia), P4 instalador.

## 5. Decisões recentes (detalhe nos ADRs)
- 12/10 (tarde): **logs do sistema** padronizados como nas distribuições (journald + falhas estilo apport/
  coredump + perfil estilo Ubuntu Insights + uso agregado estilo eos-metrics), centralizados no repositório
  privado `duiaos-diagnosticos` para TODO o sistema (não só o Wise). Consentimento: pergunta na 1ª entrada,
  sem opção marcada (nada sai antes). Usuários enviam ao Worker do site, que grava no repositório em lotes;
  computadores de teste enviam pelo Git (nível "Desenvolvimento"). Nome visível: **"Ajude a melhorar o
  DuiaOS"**. Fases: F1 registro + falhas + perfil + coletor `duiaos-relatorios` (Git) e Wise migrado; F2 uso +
  tela de consentimento; F3 Worker + agrupamento de falhas. Começa depois do merge de #9, Wise #5/#6 e site #2/#3.
- 12/10: motor **Ollama mantido** (ADR 036; medição no Dell). Pente de RAM fica para depois.
- 12/10: agenda local + .ics + CalDAV + Google + Microsoft; clima com cidade escolhida (MET Norway).
- 12/10: o Wise opera qualquer aplicativo como a pessoa, com aprovação nas ações arriscadas.
- 12/10: continuidade no Git (várias contas do Claude); documentação para usuários desde já; site no Cloudflare.

## 6. Perguntas em aberto para o Gustavo
- Titular dos direitos (PF ou CNPJ).
- Nome visível do recurso "Wise usando o computador" (hoje "Usar o computador").
- Domínio do site (ex.: duiaos.com.br / duiaos.com).
- Como o Wise chega a quem baixa a ISO (repositório apt privado, pacote fechado no apt público, só no Dell)?
- Licença da documentação: proprietária (hoje) ou aberta (CC BY-SA, como o Ubuntu)?

## 7. Fila de problemas conhecidos
- `duiaos.local` (mDNS) não resolve a partir do Mac — usar `duiaos` ou o IP.
- BitLocker pede recuperação após o dual boot → instalador próprio deve detectar (P4).
- EULA/oferta de fonte são minutas: revisar com advogado antes da 1.0.
- Tela de Bloqueio sem ext-session-lock (ADR 026). Ponteiro entre monitores: aceito (ADR 027).
- Chave do repositório apt vence em 2036. Distribuição pública do Wise não decidida.
- Placas NVIDIA: sem CUDA no duiaos-ollama. `intel-opencl-icd` não existe no Debian 13.
- Programas de terceiros que não mandam as "opcoes" fazem o Ollama recarregar o modelo.
- Wise com 23 ferramentas: aquecimento após o boot mais longo (estimado ~20 s; medir).
- Risco das ações na tela avaliado por palavras (pode falhar); Flatpak fora do agente.

## 8. Ambiente do Claude (dicas para a próxima sessão)
- `gh` só via REST. Python 3.13 do container sem `gi`: use `python3.12` para D-Bus/AT-SPI.
- Captura QML offscreen: `shiboken6.wrapInstance(..., QQuickWindow)` + `grabWindow()`.
- AT-SPI de verdade: Xvfb + dbus-run-session + `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`.
- CalDAV de teste: Radicale com HTTPS (`SSL_CERT_FILE`, `no_proxy=127.0.0.1`).
- Rede: open-meteo bloqueado; api.met.no, nominatim, huggingface, GitHub, npm e PyPI liberados.
