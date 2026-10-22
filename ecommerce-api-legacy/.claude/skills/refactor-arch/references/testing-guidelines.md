# Testes antes de refatorar (Fase 3)

Os testes provam que a refatoração preserva o comportamento e que as correções foram feitas. São escritos **antes** da mudança e rodados depois de cada grupo de transformações.

## Framework por stack

Prefira o que já está no projeto. Se não houver nada, use a opção sem dependência nova; só adicione dependência de teste se ela for o padrão da stack, e registre no manifesto como dependência de desenvolvimento.

| Stack | Framework | Cliente HTTP de teste | Comando |
|---|---|---|---|
| Python + Flask | `pytest` (ou `unittest`, se não puder instalar) | `app.test_client()` | `python -m pytest -q tests` |
| Python + FastAPI | `pytest` | `fastapi.testclient.TestClient` | `python -m pytest -q tests` |
| Python + Django | `django.test` | `self.client` | `python manage.py test` |
| Node + Express | `node:test` + `node:assert` (nativos) | `app.listen(0)` + `fetch` | `node --test 'tests/**/*.test.js'` (registre como `npm test`) |
| Outra | o runner padrão da linguagem | cliente HTTP do framework ou servidor em porta efêmera | — |

Se o entry point original sobe o servidor ao ser importado (`app.listen` no topo, `app.run` sem `if __name__ == "__main__"`), os testes de caracterização sobem a aplicação como processo filho numa porta livre e chamam por HTTP. Não altere o código original para torná-lo testável antes de ter os testes.

## Isolamento

- Cada teste parte de um banco conhecido: arquivo temporário copiado do backup, banco em memória ou seed antes de cada teste. Nunca use o banco real do projeto.
- Nada de ordem implícita entre testes. Rotas destrutivas criam os próprios dados.
- Flags e tokens do T08 vêm do ambiente do teste (`ENABLE_*`, `ADMIN_TOKEN`). Cubra os dois estados: desligada (403) e ligada com token (comportamento original), além de ligada sem token (401).

## O que cobrir

**Caracterização** (verde no original e depois):
- todas as rotas do inventário: status e chaves do corpo no caso válido, de erro de validação e de não encontrado;
- regras de negócio pelo resultado observável: totais, descontos, estoque baixado, contagens de relatório, mensagens de erro;
- ignore ids e timestamps; compare valores estáveis.

**Comportamento novo** (vermelho no original, verde depois), um por correção do relatório que muda o contrato:
- rota guardada responde 403 com a flag desligada e 401 sem token (T08);
- campo sensível ausente da resposta (T05);
- senha armazenada não é o texto puro (T04);
- entrada inválida responde 400, não 500 (T17);
- segredo não aparece em resposta nem em log (T01, T13).

**Unitários das camadas novas** (escritos na 3.4, antes de cada serviço ou model): regra de negócio isolada, sem HTTP, com o banco de teste.

## Regras

- Teste vermelho não se conserta afrouxando o teste. Corrija o código ou, se a mudança for intencional, registre em "Intentional changes" e transforme o teste em teste de comportamento novo.
- Nomes descrevem o comportamento: `test_criar_pedido_sem_estoque_retorna_400`, `checkout com cartão recusado responde 400`.
- A suíte roda com um comando só e termina em menos de um minuto.
