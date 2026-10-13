---
name: refactor-arch
description: Audita e refatora um projeto de backend para a arquitetura MVC em três fases (análise da stack, auditoria com confirmação, refatoração com validação). Use quando o usuário pedir para auditar um projeto, revisar a arquitetura, achar anti-patterns ou code smells, refatorar para MVC ou validar um projeto legado. Funciona em qualquer linguagem ou framework de backend.
argument-hint: [caminho do relatório, ex.: ../reports/audit-project-1.md]
---

# refactor-arch

Analise o projeto do diretório atual, audite e, só depois de confirmação explícita, refatore para MVC. Execute as fases nesta ordem e não pule nenhuma.

## Regras que valem em todas as fases

1. **Antes da confirmação da Fase 2, não altere nenhum arquivo de código.** A única escrita permitida nessa fase é o relatório.
2. Todo finding cita arquivo e linha exatos. Leia o trecho antes de escrever a linha.
3. A stack vem dos arquivos do projeto (manifestos, imports, comandos de boot), nunca de suposição.
4. Não invente rotas, tabelas ou findings. Se não encontrou algo, diga isso.
5. Preserve o comportamento externo: mesmo método, caminho, status e formato de resposta. Mudança de comportamento só nas correções de segurança, e cada uma deve ser listada.

Leia as referências apenas na fase que precisa delas:

- Fase 1: `references/project-analysis.md`
- Fase 2: `references/anti-patterns-catalog.md` e `references/audit-report-template.md`
- Fase 3: `references/mvc-guidelines.md` e `references/refactoring-playbook.md`

## Fase 1: Análise

1. Leia os manifestos e identifique linguagem, framework, dependências e banco, seguindo `project-analysis.md`.
2. Liste os arquivos de código do projeto, excluindo dependências, builds, ambientes virtuais e arquivos gerados. Conte.
3. Monte o **inventário de rotas**: método, caminho completo e `arquivo:linha` de cada registro. A Fase 3 usa esta lista para validar.
4. Descreva o domínio da aplicação e a arquitetura atual (monolito, camadas parciais ou MVC).
5. Imprima o resumo neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão>
Framework:     <framework e versão>
Dependencies:  <principais dependências>
Domain:        <domínio em uma frase>
Architecture:  <classificação e motivo em uma frase>
Source files:  <N> files analyzed
DB tables:     <tabelas>
Routes:        <N> (inventário completo abaixo)
================================
```

Em seguida, imprima o inventário de rotas em uma tabela.

## Fase 2: Auditoria

1. Para cada anti-pattern de `anti-patterns-catalog.md`, procure os sinais de detecção no código. Leia o trecho antes de confirmar.
2. Classifique cada finding pela escala de severidade do catálogo.
3. Ordene os findings de CRITICAL a LOW.
4. Escreva o relatório no caminho dado em `$ARGUMENTS` (padrão: `reports/audit-report.md` na raiz do projeto), seguindo `audit-report-template.md`.
5. Imprima o mesmo relatório na saída.
6. Se encontrar menos de 5 findings, releia o catálogo antes de concluir. Não force findings que não existem.
7. Termine com exatamente esta linha e **pare**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Não edite código, não instale dependências e não rode migrações nesta fase.

## Fase 3: Refatoração

Só comece com confirmação explícita ("sim", "y", "prossiga"). Qualquer outra resposta encerra a skill sem alterar nada.

1. **Snapshot do comportamento atual.** Suba a aplicação original (comando e porta em `project-analysis.md`). Chame cada rota do inventário com dados válidos, de erro e de não encontrado. Grave status e corpo de cada resposta em um arquivo temporário. Se a aplicação não subir antes de qualquer mudança, pare e reporte.
2. **Plano de estrutura.** Defina a estrutura alvo seguindo `mvc-guidelines.md`. Adapte ao ponto de partida: um monolito é dividido por domínio; um projeto que já tem camadas recebe apenas o que falta. Liste no chat os arquivos que serão criados, movidos ou alterados antes de mexer.
3. **Refatoração.** Aplique `refactoring-playbook.md`, uma transformação por finding, na ordem do relatório. Mantenha caminhos, métodos e formato de resposta. Adicione dependências somente se forem indispensáveis, e registre-as no manifesto.
4. **Validação.** Suba a aplicação refatorada e confirme que o boot não tem erro. Chame cada rota do inventário com os mesmos dados do snapshot e compare status e formato do corpo. Divergência não intencional deve ser corrigida. Divergência intencional deve ser listada.
5. Se a aplicação usa dados de seed e a troca de hash invalidou senhas antigas, recrie o seed e registre a ação.
6. Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Validation
  ✓ ou ✗ Application boots without errors
  ✓ ou ✗ All endpoints respond as before (<N>/<total> iguais)

## Intentional changes
- <cada mudança de comportamento, com motivo>

## Anti-patterns remaining
- <lista, ou "nenhum">
================================
```
