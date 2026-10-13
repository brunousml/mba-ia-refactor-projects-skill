# Handoff: Desafio 4 (skill `refactor-arch`)

Atualizado ao fim de cada etapa. O plano do desafio e o plano de execução ficam no repositório de planejamento, fora deste fork.

## Estado atual

**Etapa 3b concluída:** a revisão do checkpoint 1 foi feita por 3 subagentes independentes (análise manual, skill, baseline/scripts) e as correções foram aplicadas. Próximo: rodar as Fases 1–2 headless no projeto 1.

| Etapa | Status | Artefato |
| --- | --- | --- |
| 0. Preparação | Feito | `docs/`, `scripts/`, [`reports/`](../reports/) |
| 1. Linha de base | Feito (P1, P2, P3) | [`docs/baseline/`](baseline/) |
| 2. Análise manual | Feito e revisado | [`docs/analise-manual.md`](analise-manual.md) |
| 3. Skill | v2 (pós-revisão) | [`code-smells-project/.claude/skills/refactor-arch/`](../code-smells-project/.claude/skills/refactor-arch/) |
| 3b. Revisão do checkpoint 1 | Feito | ver "Revisão do checkpoint 1" abaixo |
| 4. Projeto 1 (Fases 1–2 headless) | Próximo | — |
| 5. Projeto 2 | Pendente | — |
| 6. Projeto 3 | Pendente | — |
| 7. Fechamento e README | Pendente | — |

## Linha de base

Cada `requests-project-N.json` lista as chamadas, e cada `before-project-N.json` guarda o status e o corpo gravados no código **original**.

| Projeto | Chamadas | Porta | Status observados | Arquivos |
| --- | --- | --- | --- | --- |
| 1 (Flask) | 35 | 5001 | 200, 201, 400, 401, 404, 500 | [requests](baseline/requests-project-1.json), [before](baseline/before-project-1.json), [log](runs/project-1/baseline-server.log) |
| 2 (Express) | 7 | 3000 | 200, 400, 404 | [requests](baseline/requests-project-2.json), [before](baseline/before-project-2.json), [log](runs/project-2/baseline-server.log) |
| 3 (Flask + ORM) | 44 | 5001 | 200, 201, 400, 401, 404, 409 | [requests](baseline/requests-project-3.json), [before](baseline/before-project-3.json), [log](runs/project-3/baseline-server.log) |

Ferramentas:
- [`scripts/smoke.py`](../scripts/smoke.py) executa as chamadas.
- [`scripts/compare.py`](../scripts/compare.py) compara status e estrutura do corpo; com `--valores`, compara também os campos indicados.

### Como reproduzir (estado inicial obrigatório)

Os IDs das chamadas dependem do estado inicial do banco. **Antes de cada execução:**

| Projeto | Reset | Subir |
| --- | --- | --- |
| 1 | `rm -f code-smells-project/loja.db` (o `AUTOINCREMENT` não volta com `DELETE`) | `cd code-smells-project && .venv/bin/python -m flask --app app run -p 5001` |
| 2 | Reiniciar o processo (banco em memória) | `cd ecommerce-api-legacy && npm start` |
| 3 | `cd task-manager-api && .venv/bin/python seed.py` (o banco fica em `instance/tasks.db`) | `cd task-manager-api && .venv/bin/python -m flask --app app run -p 5001` |

```bash
python3 scripts/smoke.py docs/baseline/requests-project-1.json http://localhost:5001 /tmp/after-1.json
python3 scripts/compare.py docs/baseline/before-project-1.json /tmp/after-1.json
```

## Revisão do checkpoint 1

Três subagentes revisaram, cada um, uma parte do trabalho. O que foi corrigido:

- **Análise manual.** 10 itens com linha, descrição ou severidade errada. Exemplos:
  - SQL injection no P1 citava linhas protegidas pelo conversor `<int:>`.
  - No P3, o `GET /users` **não** vaza o hash; as rotas que vazam são outras quatro.
  - `datetime` **é** usado no `app.py` do P3.

  Também entraram 6 problemas que faltavam, como o cadastro anônimo de `admin` no P3 (CRITICAL). Foi adicionada a coluna AP, que liga cada item ao catálogo.
- **Skill:**
  - Catálogo: de 12 para 15 anti-patterns (duplicação, validação ausente, configuração insegura). A regra de severidade deixou de ser contraditória, e a Fase 2 passou a ser só leitura.
  - Playbook: de 15 para 18 transformações. Agora usa um domínio neutro, para não copiar código dos projetos. O T01 não derruba mais o boot sem `.env`. Entraram o adaptador callback → promise, o `asyncHandler`, um handler de erro que preserva 404/405 e um hash que não gera 500 com formato inválido.
  - `SKILL.md`: frontmatter YAML válido. O snapshot passou a usar reset de estado, diretório temporário fora do projeto e verificação de porta. Ficou uma ordem única de aplicação, e o checklist MVC do enunciado entrou na saída da Fase 3.
- **Scripts:**
  - `compare.py` agora trata erro de conexão como divergência, une os tipos de todos os itens de uma lista, considera `int` e `float` como "número", recusa IDs duplicados e aceita `--valores`.
  - `smoke.py` captura timeout e queda de conexão.

## Decisões e desvios

- **Porta 5000 ocupada no macOS (ControlCenter/AirPlay).** A primeira linha de base do P3 subiu na 5000 e recebeu 403 em tudo. Foi descartada e refeita na 5001.
- **A linha de base do Flask rodou com `flask run`, com debug desligado.** O original roda com `python app.py`, debug ligado. As respostas não mudam, porque todos os handlers capturam as exceções, mas a diferença fica registrada.
- **Comportamentos ruins preservados na linha de base, que a Fase 3 deve mudar de propósito:**
  - `POST /produtos` sem corpo devolve 500 (P1).
  - O checkout cria o usuário antes de validar o pagamento (P2).
  - `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `/login` devolvem o hash da senha (P3).
  - `/health` devolve a `secret_key` (P1).
- **O log de baseline do P2 contém o número de cartão de teste (`4111…`)** e a chave fictícia do gateway, porque o próprio código original os imprime (`AppManager.js:45`). São dados de teste do `api.http`, não dados reais.
- **Node 26.7:** o `sqlite3@5.1.6` compilou sem precisar do plano B.
- **O `CLAUDE.md` da raiz do fork está no `.gitignore`.** Ele vira `CLAUDE.md.off` durante as execuções headless, para não dar à skill informação sobre os projetos.
- **Comando headless:** `--add-dir ../reports`, porque o relatório é gravado fora do diretório do projeto.

## Próximo passo

1. `mv CLAUDE.md CLAUDE.md.off`
2. `cd code-smells-project && claude -p "/refactor-arch ../reports/audit-project-1.md" --add-dir ../reports --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash"`, com saída em `docs/runs/project-1/phase-1-2.log`.
3. Conferir com `git status` que a Fase 2 não alterou código. Checkpoint: revisão do relatório antes da Fase 3.

## Checklist de entrega (enunciado)

- [ ] Fork público de `mba-ia-refactor-projects-skill`
- [ ] `.claude/skills/refactor-arch/` idêntica nos 3 projetos, com `SKILL.md` e as 5 áreas de conhecimento
- [x] Catálogo com ≥ 8 anti-patterns (incluindo APIs deprecated): 15. Playbook com ≥ 8 transformações: 18.
- [ ] Código refatorado dos 3 projetos commitado
- [ ] `reports/audit-project-1.md`, `-2.md` e `-3.md` na raiz
- [ ] Nos 3 projetos: stack detectada, ≥ 5 findings, ≥ 1 CRITICAL ou HIGH, aplicação no ar e endpoints respondendo
- [ ] README com Análise Manual, Construção da Skill, Resultados e Como Executar
- [ ] URL do fork enviada na área de entrega da plataforma
