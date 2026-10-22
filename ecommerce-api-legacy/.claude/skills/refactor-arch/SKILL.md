---
name: refactor-arch
description: Audita e refatora um projeto de backend para a arquitetura MVC em três fases (análise da stack, auditoria com confirmação, refatoração com validação). Use quando o usuário pedir para auditar um projeto, revisar a arquitetura, achar anti-patterns ou code smells, refatorar para MVC ou validar um projeto legado. Funciona em qualquer linguagem ou framework de backend.
argument-hint: "[caminho do relatório]"
allowed-tools: Read Grep Glob Write Edit Bash
---

# refactor-arch

Analise o projeto do diretório atual, audite e, só depois de confirmação explícita, refatore para MVC. Execute as fases nesta ordem, sem pular nenhuma.

## Regras para todas as fases

1. **Fases 1 e 2 são só leitura.** Não edite código, não instale dependências, não suba a aplicação, não rode seed nem migração. A única escrita permitida é o relatório da Fase 2.
2. Todo finding cita arquivo e linha exatos. Leia o trecho antes de escrever o número.
3. A stack vem dos arquivos do projeto (manifestos, imports, comando de boot), nunca de suposição.
4. Não invente rotas, tabelas ou findings. Se algo não existe, diga isso.
5. Preserve o comportamento externo: método, caminho, status, formato da resposta e porta padrão. Mudança de comportamento só nas correções de segurança e de validação, e cada uma é listada.

Leia as referências só na fase que precisa delas:

- Fase 1: `references/project-analysis.md`
- Fase 2: `references/anti-patterns-catalog.md` e `references/audit-report-template.md`
- Fase 3: `references/mvc-guidelines.md` e `references/refactoring-playbook.md`

## Fase 1: Análise

1. Leia os manifestos e identifique linguagem, framework, dependências e banco, seguindo `project-analysis.md`.
2. Liste e conte os arquivos de código do projeto, excluindo dependências, builds, ambientes virtuais e arquivos gerados.
3. Monte o **inventário de rotas**: método, caminho completo e `arquivo:linha` de cada registro. A Fase 3 usa essa lista para validar.
4. Identifique o comando de boot, a porta, o arquivo de banco e o seed, sem executar nada.
5. Descreva o domínio da aplicação e a arquitetura atual (monolito, camadas parciais ou MVC).
6. Imprima o resumo neste formato e, em seguida, o inventário de rotas em tabela:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão>
Framework:     <framework e versão>
Dependencies:  <principais dependências>
Domain:        <domínio em uma frase>
Architecture:  <classificação e o motivo, em uma frase>
Source files:  <N> files analyzed
DB tables:     <tabelas>
Routes:        <N> (inventário abaixo)
================================
```

## Fase 2: Auditoria

1. Para cada anti-pattern de `anti-patterns-catalog.md`, procure os sinais de detecção no código. Leia o trecho antes de confirmar.
2. Classifique cada finding com a severidade definida no catálogo.
3. Ordene os findings de CRITICAL a LOW.
4. Escreva o relatório seguindo `audit-report-template.md`. Use o caminho recebido como argumento: `$ARGUMENTS`. Se o argumento vier vazio, use `reports/audit-report.md` na raiz do projeto.
5. Imprima o mesmo relatório na saída.
6. Se houver menos de 5 findings, releia o catálogo antes de concluir. Não force findings que não existem.
7. Termine com exatamente esta linha e **pare**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Fase 3: Refatoração

Só comece com confirmação explícita ("sim", "y", "prossiga"). Qualquer outra resposta encerra a skill sem alterar nada.

### 3.1 Snapshot do comportamento atual

1. Instale as dependências no ambiente do projeto e prepare a porta, conforme a seção 6 de `project-analysis.md`.
2. Crie um diretório de trabalho **fora do projeto** (`mktemp -d`). Faça backup do arquivo de banco, se houver, e rode o seed, se houver.
3. Suba a aplicação original e confirme que a resposta vem dela. Se não subir antes de qualquer mudança, pare e reporte.
4. Chame cada rota do inventário com caso válido, de erro e de não encontrado. As rotas destrutivas (exclusão, reset, administração) ficam por último. Grave método, caminho, status e corpo no diretório de trabalho.
5. Pare a aplicação e restaure o banco ou rode o seed de novo, para a validação começar do mesmo estado.

### 3.2 Plano de estrutura

Defina a estrutura alvo seguindo `mvc-guidelines.md` e adapte ao ponto de partida. Um monolito é dividido por domínio. Um projeto que já tem camadas recebe só o que falta. Liste no chat os arquivos que serão criados, movidos ou alterados antes de mexer.

### 3.3 Refatoração

Siga a **ordem de aplicação** do final de `refactoring-playbook.md`:
1. estrutura sem mudar lógica;
2. segurança;
3. regra e erros;
4. desempenho e limpeza.

Dentro de cada grupo, trate os findings do relatório. Suba a aplicação depois de cada grupo. Adicione dependências só se forem indispensáveis, e registre no manifesto. Se a troca de hash invalidar senhas do seed, refaça o seed mantendo as mesmas senhas de exemplo.

### 3.4 Validação

1. Restaure o estado inicial do banco (como no passo 5 do snapshot) e suba a aplicação refatorada. O boot precisa terminar sem erro.
2. Chame as mesmas rotas, com os mesmos dados e na mesma ordem do snapshot.
3. Compare status e estrutura do corpo (chaves e tipos), ignorando ids e timestamps.
4. Rotas protegidas por flag (T08): valide com as flags desligadas (403 esperado) e com `ENABLE_ADMIN_ROUTES`, `ENABLE_SENSITIVE_READS`, `ENABLE_WRITE_ROUTES` ligadas e `X-Admin-Token` (comportamento original).
5. Corrija toda divergência não intencional. Liste as intencionais.
6. Confira de novo os findings do relatório no código novo.

### 3.5 Pendências (obrigatório)

1. Monte a lista de pendências: findings CRITICAL ou HIGH do relatório ainda presentes no código novo, divergências não intencionais e itens ✗ do checklist MVC.
2. Se a lista tiver qualquer CRITICAL ou HIGH, volte ao playbook, aplique a transformação e repita a 3.4. Se nenhuma transformação resolver sem quebrar o contrato, **pare** e peça a decisão ao usuário, mostrando a lista. Nunca feche a Fase 3 com CRITICAL ou HIGH pendente.
3. Rode a skill `validate-refactor` (em `.claude/skills/validate-refactor/`) passando o caminho do relatório. Só siga para a saída com `VALIDATION PASSED`. Com `VALIDATION FAILED`, trate cada pendência listada e repita este passo.

### 3.6 Saída

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Validation
  ✓|✗ Application boots without errors
  ✓|✗ All endpoints respond correctly (<N>/<total> iguais ao snapshot, <K> mudanças intencionais)
  ✓|✗ Zero CRITICAL/HIGH remaining (validate-refactor: PASSED)

## MVC checklist
  ✓|✗ Configuração extraída para módulo de config (sem hardcoded)
  ✓|✗ Models abstraem o acesso a dados
  ✓|✗ Views/Routes só fazem roteamento
  ✓|✗ Controllers concentram o fluxo da aplicação
  ✓|✗ Error handling centralizado
  ✓|✗ Entry point claro (só compõe a aplicação)

## Intentional changes
- <cada mudança de comportamento, com o motivo>

## Anti-patterns remaining
- <só MEDIUM ou LOW, com o motivo, ou "nenhum">
================================
```
