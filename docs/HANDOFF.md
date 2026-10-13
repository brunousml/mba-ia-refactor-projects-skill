# Handoff: Desafio 4 (skill `refactor-arch`)

Atualizado ao fim de cada etapa. Plano aprovado: `/Users/bruno/.claude/plans/docs-planos-desafio-4-plano-detalhado-m-gentle-dongarra.md` (fora do repositório). Plano do desafio: `../../docs/planos/desafio-4-plano-detalhado.md`.

## Estado atual

**Checkpoint 1 concluído:** linha de base, análise manual e skill v1 escritas. Aguardando revisão antes da Fase 1–2 headless.

| Etapa | Status | Artefato |
| --- | --- | --- |
| 0. Preparação | Feito | `docs/`, `scripts/`, `reports/` |
| 1. Linha de base | Feito (P1, P2, P3) | [`docs/baseline/`](baseline/) |
| 2. Análise manual | Feito | [`docs/analise-manual.md`](analise-manual.md) |
| 3. Skill v1 | Feito (rascunho para revisão) | [`code-smells-project/.claude/skills/refactor-arch/`](../code-smells-project/.claude/skills/refactor-arch/) |
| 4. Projeto 1 (Fases 1–2 headless) | Pendente | — |
| 5. Projeto 2 | Pendente | — |
| 6. Projeto 3 | Pendente | — |
| 7. Fechamento e README | Pendente | — |

## Linha de base

Cada `requests-project-N.json` lista as chamadas; cada `before-project-N.json` guarda status e corpo gravados no código **original**.

| Projeto | Chamadas | Porta | Status observados | Arquivos |
| --- | --- | --- | --- | --- |
| 1 (Flask) | 35 | 5001 | 200, 201, 400, 401, 404, 500 | [requests](baseline/requests-project-1.json), [before](baseline/before-project-1.json), [log](runs/project-1/baseline-server.log) |
| 2 (Express) | 7 | 3000 | 200, 400, 404 | [requests](baseline/requests-project-2.json), [before](baseline/before-project-2.json), [log](runs/project-2/baseline-server.log) |
| 3 (Flask + ORM) | 44 | 5001 | 200, 201, 400, 401, 404, 409 | [requests](baseline/requests-project-3.json), [before](baseline/before-project-3.json), [log](runs/project-3/baseline-server.log) |

Ferramentas: [`scripts/smoke.py`](../scripts/smoke.py) (executa as chamadas) e [`scripts/compare.py`](../scripts/compare.py) (compara status e formato do corpo; valores voláteis ficam de fora).

## Decisões e desvios

- **Porta 5000 ocupada no macOS (ControlCenter/AirPlay).** A primeira linha de base do projeto 3 subiu na 5000 e recebeu 403 em todas as chamadas. Descartada; refeita na 5001 com `flask --app app run -p 5001`. Projeto 2 subiu direto na 3000. A skill precisa tratar porta ocupada (já está em `project-analysis.md`, seção 6).
- **Contagem de rotas corrigida:** o projeto 3 tem 20 rotas em `routes/*.py` + `/` e `/health` = 22 no total. O plano dizia 22 só nos blueprints.
- **`overdue` duplicado em 6 lugares** no projeto 3 (o plano dizia 5). `Query.get` aparece em 16 pontos (não 7).
- **Comportamento original preservado no baseline, mesmo onde é ruim.** Exemplos que a Fase 3 vai mudar de propósito e que aparecerão no `compare.py`:
  - `POST /produtos` sem corpo devolve **500** (projeto 1).
  - Checkout cria o usuário **antes** de validar o pagamento; o caso "recusado" deixa a conta criada (projeto 2).
  - `GET /users` e `/login` devolvem o hash da senha (projeto 3).
- **Node 26.7:** o `sqlite3@5.1.6` compilou e carregou sem plano B.
- **`CLAUDE.md` da raiz do fork** continua não versionado. Vai para `CLAUDE.md.off` nas execuções headless (plano, etapa 0).
- **Nomes de framework nas references:** a regra do `CLAUDE.md` pede que o `SKILL.md` e as references não citem frameworks dos 3 projetos. Conferido com `grep`: nenhum achado. Exemplos usam stacks de referência (Django, Pydantic, pino).

## Próximo passo

1. Revisar a análise manual, a skill v1 e a linha de base.
2. Se aprovado: rodar `claude -p "/refactor-arch ../reports/audit-project-1.md"` no projeto 1 (Fases 1–2) e parar no checkpoint seguinte.

## Checklist de entrega (enunciado)

- [ ] Fork público de `mba-ia-refactor-projects-skill`
- [ ] `.claude/skills/refactor-arch/` idêntica nos 3 projetos, com `SKILL.md` e as 5 áreas de conhecimento
- [ ] Catálogo com ≥ 8 anti-patterns (incluindo APIs deprecated) e playbook com ≥ 8 transformações
- [ ] Código refatorado dos 3 projetos commitado
- [ ] `reports/audit-project-1.md`, `-2.md` e `-3.md` na raiz
- [ ] Nos 3 projetos: stack detectada, ≥ 5 findings, ≥ 1 CRITICAL ou HIGH, aplicação no ar e endpoints respondendo
- [ ] README com Análise Manual, Construção da Skill, Resultados e Como Executar
- [ ] URL do fork enviada na área de entrega da plataforma
