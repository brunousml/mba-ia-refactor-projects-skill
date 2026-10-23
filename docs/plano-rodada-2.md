# Plano da rodada 2: ajustes pedidos na revisão

## Contexto

A revisão da entrega apontou que a Fase 3 do P1 e do P3 terminava com AP-07 parcial. Leituras sensíveis e escritas comuns continuavam sem autenticação, e o box marcava ✗ em "Zero anti-patterns remaining". O objetivo é que a skill não aceite fechar a Fase 3 com CRITICAL ou HIGH pendente e que o T08 tenha guards para esses casos, sem criar um sistema de autenticação completo, que quebraria o contrato de todos os clientes.

Durante a execução, o usuário acrescentou quatro pedidos, que já estão incorporados abaixo: TDD com testes escritos antes da refatoração, subagentes para escrever e revisar, Sonnet nos subagentes de tarefa direta (Opus só onde há raciocínio pesado) e o humanizer em todo texto em prosa.

O andamento detalhado fica no [HANDOFF](HANDOFF.md).

## 1. Skill

A skill é a mesma nos 3 projetos. Edito uma cópia, sincronizo as outras e confiro com `diff -r`.

- `SKILL.md`, Fase 3:
  - 3.2: testes antes de refatorar. Subagentes Sonnet, um por domínio, escrevem testes de caracterização (verdes no original) e de comportamento novo (vermelhos no original). A refatoração só começa quando todos terminam e o `suite-original.txt` está gravado.
  - 3.4: a suíte roda depois de cada grupo de transformações, com a saída em `suite-grupo-<n>.txt`. Aplicar os 4 grupos de uma vez não é permitido.
  - 3.6: pendências. Com CRITICAL ou HIGH na lista, a skill volta ao playbook ou para e pede decisão ao usuário. A lista inclui os sinais do catálogo achados no código novo, mesmo os que o relatório não registrou.
  - 3.7: "Anti-patterns remaining" só aceita MEDIUM e LOW. O box ganha a linha de testes.
- `refactoring-playbook.md`, T08: guards de acesso por flag (`ENABLE_ADMIN_ROUTES`, `ENABLE_SENSITIVE_READS`, `ENABLE_WRITE_ROUTES`), gerados por uma única fábrica. Desligada, a rota responde 403; ligada, exige `X-Admin-Token` em tempo constante. Quando a rota reaproveita uma conta existente pelo corpo, confere a senha.
- `anti-patterns-catalog.md`, AP-07: a correção indica qual guard usar, e a conta existente identificada pelo corpo sem credencial entra como HIGH.
- `testing-guidelines.md` (nova): framework por stack, isolamento do banco, o que cobrir (inclusive token errado por flag).
- `validate-refactor` (skill nova, somente leitura): checagens C1 a C5 (CRITICAL/HIGH resolvidos, guards por rota, comportamento com flags off e on, evidência dos testes, coerência do box). A refactor-arch a chama pela ferramenta Skill, e checagem feita à mão não vale como PASSED.

## 2. Reexecução dos 3 projetos

Cada projeto volta ao código original (preservando `.claude/`) e roda as Fases 1 a 3 em modo headless, desacoplado da sessão, com `scripts/run-skill.sh`. P1 e P3 usam a porta 5001 e por isso rodam um depois do outro; o P2 usa a 3000 e pode rodar em paralelo.

Depois de cada execução, antes de passar ao próximo projeto:

1. Rodar a suíte do projeto.
2. Rodar `scripts/smoke.py` e `scripts/compare.py` contra `docs/baseline/before-project-N.json` com as flags desligadas (as novas divergências 403 são intencionais) e com as flags ligadas e o token (só podem sobrar as divergências já documentadas). `scripts/with-token.py` gera as chamadas com o token.
3. Listar as pendências: CRITICAL ou HIGH não resolvidos, divergências fora de "Intentional changes", testes vermelhos, ✗ no checklist. Só seguir com a lista vazia ou com aceite explícito do usuário.
4. Gravar os diffs em `docs/runs/project-N/` (`diff.md` e `diff-flags-on.md`) e commitar só os caminhos do projeto.

## 3. Revisão por subagentes

- Um revisor por projeto, procurando CRITICAL ou HIGH que sobrou, guard faltando, divergência não documentada, teste fraco e incoerência entre relatório, box e código. Revisão de segurança usa Opus.
- Um revisor para a skill, procurando brechas que deixem a Fase 3 fechar com CRITICAL ou HIGH.
- Achado de código é corrigido em TDD: teste vermelho primeiro, depois o código. Achado que revela falha da skill vira regra na skill.

## 4. Documentação e commits

- `reports/audit-project-{1,2,3}.md` gerados de novo pela skill.
- README: tabelas de validação, mudanças intencionais, a ressalva de AP-07 parcial (que deixa de existir) e o checklist.
- `docs/HANDOFF.md` atualizado ao fim de cada etapa.
- Todo texto em prosa passa pelo humanizer antes do commit.
- Commits por etapa, como `Bruno Melo <brunousml@gmail.com>`. Push só com confirmação do usuário.

## 5. Fora do código

O usuário reenvia a URL na plataforma e atualiza o status para "Revisão necessária, ajustando".

## Verificação

- `diff -r` entre as 3 cópias da skill sem saída.
- Em cada projeto: a aplicação sobe, a suíte passa inteira, `compare.py` com flags off só mostra divergências intencionais e com flags on e token só as que já estavam documentadas.
- Box final de cada Fase 3 com ✓ em "Zero CRITICAL/HIGH remaining", `validate-refactor` PASSED e só MEDIUM ou LOW em "Anti-patterns remaining".

## Status

| Passo | Situação |
|---|---|
| 1. Skill | Feito, com as brechas da revisão fechadas |
| 2. P2 | Feito e commitado (70/70 testes, 0 divergências com flags on) |
| 2. P3 | Feito e commitado (184/184 testes, só a remoção de `password` com flags on) |
| 2. P1 | Rodando com a skill atual |
| 3. Revisão | Skill, P1 (versão anterior) e P2 feitas; P3 em andamento; novo P1 pendente |
| 4. Documentação | HANDOFF e este plano atualizados; README pendente |
| 5. Reenvio | Pendente, feito pelo usuário |
