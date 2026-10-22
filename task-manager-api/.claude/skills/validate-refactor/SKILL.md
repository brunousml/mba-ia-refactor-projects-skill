---
name: validate-refactor
description: Valida, sem alterar código, se a refatoração tem testes escritos antes da mudança e todos verdes, da Fase 3 da refactor-arch fechou todos os findings CRITICAL e HIGH do relatório de auditoria, se toda rota sem autenticação passou por um guard do T08 e se as únicas divergências do snapshot são as intencionais. Use ao final da Fase 3, antes do box de saída, ou quando o usuário pedir para validar, conferir ou checar pendências de uma refatoração.
argument-hint: "[caminho do relatório de auditoria]"
allowed-tools: Read Grep Glob Bash
---

# validate-refactor

Confira a refatoração do projeto do diretório atual. **Não edite nenhum arquivo.** O resultado é uma lista de pendências; quem corrige é a refactor-arch (ou o usuário).

Referências (da refactor-arch): `../refactor-arch/references/anti-patterns-catalog.md` e `../refactor-arch/references/refactoring-playbook.md`.

## Entradas

- Relatório de auditoria: `$ARGUMENTS`; se vazio, `reports/audit-report.md`.
- Snapshot da 3.1 e chamadas gravadas no diretório de trabalho da Fase 3, se existirem.
- Lista de "Intentional changes" que a refactor-arch montou nesta execução.

## Checagens

Para cada uma, registre ✓ ou ✗ e, quando ✗, `arquivo:linha` e o finding.

### C1. Findings CRITICAL e HIGH
Para cada finding CRITICAL ou HIGH do relatório, procure no código novo os **sinais** do anti-pattern no catálogo (não só nos arquivos citados no relatório; o código pode ter mudado de lugar). Pendente se ao menos um sinal continua presente sem a transformação indicada.

### C2. Rotas sem autenticação (AP-07)
Liste todas as rotas registradas (método, caminho, `arquivo:linha`). Classifique cada uma:
- administração (reset, SQL/comando, exclusão em massa, relatório/exportação) → precisa do guard `ENABLE_ADMIN_ROUTES`;
- leitura de dados pessoais, financeiros ou de pagamento → guard `ENABLE_SENSITIVE_READS`;
- POST, PUT, PATCH ou DELETE → guard `ENABLE_WRITE_ROUTES` (ou o de administração, se for o caso);
- saúde, login e leituras públicas → sem guard.

Pendente: rota que precisava de guard e não tem; guard que não devolve 403 com a flag desligada; guard que não exige `X-Admin-Token` em tempo constante com a flag ligada. Um "login" cujo token nenhuma rota verifica só fica resolvido se as rotas que deveriam depender dele estiverem guardadas.

### C3. Comportamento
Se houver snapshot, suba a aplicação refatorada a partir do mesmo estado inicial do banco e repita as chamadas duas vezes:
1. flags desligadas: toda divergência precisa estar em "Intentional changes" (403 de rota guardada, campo sensível removido, 500 → 400);
2. flags ligadas e `X-Admin-Token`: as rotas guardadas voltam ao comportamento original; só sobram as divergências que não dependem de flag.

Compare status e estrutura do corpo (chaves e tipos), ignorando ids e timestamps. Pare a aplicação no fim. Sem snapshot, marque C3 como "não executada" e trate como pendência.

### C4. Testes (TDD)
- Existe suíte em `tests/` cobrindo todas as rotas do inventário (caracterização) e cada correção que muda o contrato (comportamento novo).
- A Fase 3 registrou a execução da suíte no código original **antes** da refatoração (caracterização verde, comportamento novo vermelho).
- Rode a suíte agora: todos verdes. Pendente: rota sem teste, correção sem teste, teste vermelho, teste apagado ou afrouxado (`skip`, assert removido) sem registro em "Intentional changes".

### C5. Box de saída
- "Anti-patterns remaining" só pode ter MEDIUM ou LOW, cada um com motivo.
- Os ✓ do box precisam bater com C1–C4.

## Saída

```
================================
VALIDATION PASSED | VALIDATION FAILED
================================
C1 CRITICAL/HIGH resolvidos   ✓|✗
C2 Rotas protegidas (T08)      ✓|✗  (<N> rotas, <K> guardadas)
C3 Comportamento               ✓|✗  (off: <D> divergências, <I> intencionais; on: <D2>)
C4 Testes                      ✓|✗  (<N> testes, <V> verdes; rotas cobertas <R>/<T>)
C5 Box coerente                ✓|✗

## Pendências
- [SEVERIDADE] <finding> — <arquivo:linha> — <o que falta>
(ou "nenhuma")
================================
```

`VALIDATION PASSED` só com C1–C5 em ✓. Qualquer pendência CRITICAL ou HIGH resulta em `VALIDATION FAILED`.
