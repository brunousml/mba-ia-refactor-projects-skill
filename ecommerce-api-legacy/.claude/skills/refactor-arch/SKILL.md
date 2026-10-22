---
name: refactor-arch
description: Audita e refatora um projeto de backend para a arquitetura MVC em três fases (análise da stack, auditoria com confirmação, refatoração com validação). Use quando o usuário pedir para auditar um projeto, revisar a arquitetura, achar anti-patterns ou code smells, refatorar para MVC ou validar um projeto legado. Funciona em qualquer linguagem ou framework de backend.
argument-hint: "[caminho do relatório]"
allowed-tools: Read Grep Glob Write Edit Bash Agent Skill
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
- Fase 3: `references/mvc-guidelines.md`, `references/testing-guidelines.md` e `references/refactoring-playbook.md`

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

### 3.2 Testes antes de refatorar (TDD)

Os testes são a garantia de que a refatoração foi feita certo. Escreva-os **antes** de mudar qualquer linha do código de produção. Siga `references/testing-guidelines.md`.

1. Use o framework de teste padrão da stack (veja `testing-guidelines.md`). Os testes ficam em `tests/` na raiz do projeto.
2. **Use subagentes** (ferramenta Agent), em paralelo, um por domínio do inventário de rotas. Passe a cada um: a stack, o comando de boot, as rotas do domínio, os findings do relatório que tocam esse domínio e `testing-guidelines.md`. Cada subagente escreve e roda só os testes do seu domínio, sem alterar código de produção. Declare no chat quantos subagentes usou e para quais domínios. Só escreva os testes você mesmo se a ferramenta Agent não estiver disponível nesta sessão, e diga isso no chat.
3. Escreva dois tipos de teste:
   - **caracterização** (verdes no original): todas as rotas pela interface HTTP (cliente de teste do framework), com caso válido, de erro e de não encontrado, e as regras de negócio observáveis (cálculos, descontos, estoque, contagens). Esses testes só usam a interface HTTP e o banco, para continuarem válidos depois que o código mudar de lugar.
   - **comportamento novo** (vermelhos no original): um teste por correção de segurança ou validação que muda o contrato (403 com a flag desligada, 401 sem token, campo sensível removido, 400 no lugar de 500, senha com hash). São a especificação da Fase 3.
4. Rode a suíte no código original. Toda caracterização precisa passar; todo teste de comportamento novo precisa falhar pelo motivo esperado. Grave em `<diretório de trabalho>/suite-original.txt` o comando, a saída, a contagem (verdes e vermelhos) e a lista dos vermelhos.
5. Um teste de caracterização só pode mudar depois se o comportamento que ele cobre estiver em "Intentional changes"; nesse caso, ele vira teste de comportamento novo. Nunca apague ou afrouxe um teste para fazê-lo passar.

### 3.3 Plano de estrutura

Defina a estrutura alvo seguindo `mvc-guidelines.md` e adapte ao ponto de partida. Um monolito é dividido por domínio. Um projeto que já tem camadas recebe só o que falta. Liste no chat os arquivos que serão criados, movidos ou alterados antes de mexer.

### 3.4 Refatoração

Siga a **ordem de aplicação** do final de `refactoring-playbook.md`:
1. estrutura sem mudar lógica;
2. segurança;
3. regra e erros;
4. desempenho e limpeza.

Dentro de cada grupo, trate os findings do relatório. Ao criar uma camada nova (serviço, model), escreva primeiro o teste unitário dela (vermelho) e depois o código (verde). Depois de cada grupo, suba a aplicação e **rode a suíte inteira**, gravando a saída em `<diretório de trabalho>/suite-grupo-<n>.txt` (n = 1 a 4). Não comece o grupo seguinte com teste de caracterização vermelho. Aplicar os quatro grupos de uma vez não é permitido, mesmo em projeto pequeno; sem os quatro arquivos, a Fase 3 não fecha. Adicione dependências só se forem indispensáveis, e registre no manifesto. Se a troca de hash invalidar senhas do seed, refaça o seed mantendo as mesmas senhas de exemplo.

### 3.5 Validação

1. Restaure o estado inicial do banco (como no passo 5 da 3.1) e suba a aplicação refatorada. O boot precisa terminar sem erro.
2. Chame as mesmas rotas, com os mesmos dados e na mesma ordem do snapshot.
3. Compare status e estrutura do corpo (chaves e tipos), ignorando ids e timestamps.
4. Rotas protegidas por flag (T08): valide com as flags desligadas (403 esperado) e com `ENABLE_ADMIN_ROUTES`, `ENABLE_SENSITIVE_READS`, `ENABLE_WRITE_ROUTES` ligadas e `X-Admin-Token` (comportamento original).
5. Corrija toda divergência não intencional. Liste as intencionais.
6. Rode a suíte inteira: todos os testes precisam passar, inclusive os de comportamento novo. Registre a contagem final.
7. Confira de novo os findings do relatório no código novo.

### 3.6 Pendências (obrigatório)

1. Monte a lista de pendências: findings CRITICAL ou HIGH do relatório ainda presentes no código novo, sinais do catálogo encontrados no código novo (com a severidade do catálogo, mesmo que o relatório não os tenha registrado), divergências não intencionais, testes vermelhos e itens ✗ do checklist MVC.
2. Se a lista tiver qualquer CRITICAL ou HIGH, volte ao playbook, aplique a transformação e repita a 3.5. Se nenhuma transformação resolver sem quebrar o contrato, **pare** e peça a decisão ao usuário, mostrando a lista. Nunca feche a Fase 3 com CRITICAL ou HIGH pendente. Se o usuário aceitar o risco explicitamente, registre em "Intentional changes" com a frase dele, e o box marca ✗ em "Zero CRITICAL/HIGH remaining"; um CRITICAL/HIGH nunca entra em "Anti-patterns remaining".
3. Rode a skill `validate-refactor` com a ferramenta Skill (`validate-refactor <relatório> <diretório de trabalho>`). Aplicar as checagens à mão não vale como PASSED: se a skill não puder ser chamada, pare e informe o usuário. Cole no chat o box devolvido, sem editar. Só siga para a saída com `VALIDATION PASSED`. Com `VALIDATION FAILED`, trate cada pendência listada e repita este passo.

### 3.7 Saída

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Validation
  ✓|✗ Application boots without errors
  ✓|✗ All endpoints respond correctly (<N>/<total> iguais ao snapshot, <K> mudanças intencionais)
  ✓|✗ Tests written before refactor: <N> (<C> caracterização, <B> comportamento novo); antes <V> verdes / <R> vermelhos; depois <N>/<N> verdes
  ✓|✗ Zero CRITICAL/HIGH remaining (validate-refactor: PASSED)

## MVC checklist
  ✓|✗ Configuração extraída para módulo de config (sem hardcoded)
  ✓|✗ Models abstraem o acesso a dados
  ✓|✗ Views/Routes só fazem roteamento
  ✓|✗ Controllers concentram o fluxo da aplicação
  ✓|✗ Error handling centralizado
  ✓|✗ Entry point claro (só compõe a aplicação)

## Intentional changes
- <cada mudança de comportamento, com o motivo; inclua também o comportamento arriscado que foi preservado de propósito (ex.: rota que segue executando SQL atrás do guard). Nada disso fica só em notas fora do box>

## Anti-patterns remaining
- <só MEDIUM ou LOW, com o motivo, ou "nenhum">
================================
```
