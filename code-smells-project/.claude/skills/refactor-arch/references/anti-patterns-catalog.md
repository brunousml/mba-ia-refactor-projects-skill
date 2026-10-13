# Catálogo de anti-patterns (Fase 2)

Doze anti-patterns, agrupados por severidade. Cada um traz sinais de detecção que descrevem o **padrão**, não a sintaxe de uma linguagem. Os exemplos entre parênteses mostram formas comuns em stacks diferentes; a lista não é exaustiva. Quando encontrar o padrão em outra forma, use o mesmo critério.

Para cada finding, ao confirmar um sinal, leia o trecho e registre o `arquivo:linha`.

## Escala de severidade

- **CRITICAL:** expõe segredo ou dado sensível, permite injeção, deixa operação destrutiva pública, ou concentra acesso a dados, regra de negócio e roteamento no mesmo módulo.
- **HIGH:** impede teste isolado e manutenção: regra de negócio em rota, estado global mutável, endpoint sensível sem checagem de identidade.
- **MEDIUM:** degrada desempenho ou correção de forma moderada: consulta repetida dentro de laço, erro engolido, API obsoleta, duplicação.
- **LOW:** atrapalha leitura sem quebrar nada: magic numbers, nomes ruins, imports mortos, print usado como log.

**Promoção:** se um anti-pattern MEDIUM atinge um endpoint público que altera dados, classifique como HIGH. Se um HIGH expõe dados sensíveis, classifique como CRITICAL.

## Resumo

| ID | Severidade | Anti-pattern | Transformação |
| --- | --- | --- | --- |
| AP-01 | CRITICAL | Credenciais hardcoded | T01 |
| AP-02 | CRITICAL | Injeção de SQL | T02 |
| AP-03 | CRITICAL | God class ou god module | T03, T06 |
| AP-04 | CRITICAL | Dados sensíveis expostos (senha em resposta ou log, hash fraco) | T04, T05, T13 |
| AP-05 | HIGH | Regra de negócio em rota ou controller | T06 |
| AP-06 | HIGH | Estado global mutável | T07 |
| AP-07 | HIGH | Endpoint sensível sem autenticação | T08 |
| AP-08 | MEDIUM | Query N+1 | T09 |
| AP-09 | MEDIUM | Tratamento de erro ausente ou genérico | T10 |
| AP-10 | MEDIUM | API deprecated | T11 |
| AP-11 | LOW | Magic numbers e magic strings | T12 |
| AP-12 | LOW | Nomenclatura ruim, imports mortos, print como log | T13, T14, T15 |

---

## AP-01 — Credenciais hardcoded (CRITICAL)

**Sinais:**
- Literal de string atribuído a um nome que contém `secret`, `key`, `password`, `senha`, `passwd`, `token`, `credential` ou `api_key`, em qualquer escopo: módulo, classe, objeto de configuração.
- Literal com cara de chave real: prefixos como `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, ou string longa de alta entropia.
- Credencial dentro de URL de conexão (`usuario:senha@host`).

**Exceção:** valor claramente de exemplo (`changeme`, `your-key-here`) em arquivo de template. Rebaixe para LOW e diga o motivo.

**Correção:** T01.

## AP-02 — Injeção de SQL (CRITICAL)

**Sinais:**
- Texto de consulta montado com `+`, `%`, `.format()`, f-string, interpolação ou template literal que contém variável, passado a uma função de execução de query.
- Valor vindo da requisição (query string, body, parâmetro de caminho) chegando a essa consulta, mesmo após duas ou três atribuições. Rastreie a variável até a origem.
- Nome de coluna ou cláusula `ORDER BY` vindo da entrada sem lista de valores permitidos.
- Endpoint que recebe SQL como texto e o executa: CRITICAL, e também AP-07.

**Correção:** T02.

## AP-03 — God class ou god module (CRITICAL)

**Sinais:** um arquivo ou classe que, ao mesmo tempo:
- (a) executa consultas, DDL ou seed de dados,
- (b) contém cálculo ou decisão de negócio,
- (c) registra rotas ou trata requisição HTTP.

Indicadores complementares: mais de 300 linhas com as três responsabilidades; classe com mais de dez métodos de natureza diferente; o mesmo módulo importa a camada de dados e a camada de transporte.

**Correção:** T03 (separar camadas) e T06 (tirar a regra da rota).

## AP-04 — Dados sensíveis expostos (CRITICAL)

**Sinais:**
- Campo de senha, hash, token, chave, número de cartão ou dado de pagamento dentro de objeto devolvido na resposta. Atenção a funções `to_dict`, `toJSON` e serializadores que listam todos os campos automaticamente.
- Consulta `SELECT *` ou equivalente cujo resultado vai direto para a resposta.
- Campo sensível ou número de cartão (sequência de 13 a 19 dígitos) em `print`, `console.log` ou logger.
- Hash fraco para senha: MD5, SHA-1 sem salt, base64, texto puro, ou função de hash caseira (laço que repete uma transformação simples).

**Correção:** T04 (hash forte), T05 (serialização explícita), T13 (logger sem dado sensível).

## AP-05 — Regra de negócio em rota ou controller (HIGH)

**Sinais:** handler de rota que contém:
- cálculo de valor, desconto, imposto ou prazo,
- decisão de estado (aprovar, cancelar, liberar acesso) com condicionais de domínio,
- validação de regra de domínio com mais de dez linhas,
- acesso direto ao banco.

Validação de formato (campo obrigatório, tipo, tamanho) pode ficar na rota ou no controller. O que não pode é a regra de domínio.

**Correção:** T06.

## AP-06 — Estado global mutável (HIGH)

**Sinais:**
- Variável de escopo de módulo reatribuída em tempo de execução (`global x` em Python; `let` no topo do módulo reatribuído dentro de função).
- Objeto, lista ou mapa de módulo mutado por função (inserção, remoção, incremento).
- Conexão de banco única, criada sob demanda e compartilhada por todas as requisições.

**Exceção:** constantes e configuração lidas uma vez na inicialização.

**Correção:** T07.

## AP-07 — Endpoint sensível sem autenticação (HIGH)

**Sinais:** rota que realiza operação destrutiva, de administração, de exportação de dados ou de relatório financeiro, sem middleware, decorator ou verificação de identidade no registro ou no handler. Nomes de caminho e função que costumam indicar isso: `admin`, `reset`, `drop`, `delete`, `query`, `execute`, `report`, `export`, `financ`.

Também se aplica a "login" que devolve um token que nenhuma outra rota verifica: não há autenticação real.

**Correção:** T08.

## AP-08 — Query N+1 (MEDIUM)

**Sinais:**
- Consulta ao banco dentro de laço (`for`, `forEach`, `map`, `while`) sobre o resultado de outra consulta.
- Chamada de método que consulta, dentro de laço.
- Acesso a relação carregada de forma preguiçosa dentro de laço, inclusive para contar (`len(x.relacao)`).
- Callbacks aninhados que consultam por item.

**Correção:** T09.

## AP-09 — Tratamento de erro ausente ou genérico (MEDIUM)

**Sinais:**
- Bloco de captura de exceção sem tipo específico que não relança nem registra o erro.
- Bloco de captura vazio.
- Callback que recebe o erro como parâmetro e não o verifica.
- Ausência de handler central: cada rota devolve "erro interno" para qualquer falha, sem distinguir validação de falha real.

**Correção:** T10.

## AP-10 — API deprecated (MEDIUM)

**Sinais:**
- Chamada a símbolo marcado como obsoleto na versão instalada.
- Warning de runtime observado na execução (`DeprecationWarning`, `(node:…) DeprecationWarning`).

**Como verificar:** use a lista abaixo quando a stack estiver nela. Para stacks que não estão na lista, consulte a documentação da versão instalada (README, changelog, `pip show`, `npm view <pacote> deprecated`, `@deprecated` nos tipos) e procure `deprecated`, `obsolete` e `removed in`. Um warning observado na execução real é o sinal mais forte.

| Stack | Obsoleto | Equivalente moderno |
| --- | --- | --- |
| Python (stdlib) | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` |
| Python (stdlib) | `asyncio.get_event_loop()` fora de contexto assíncrono | `asyncio.run()` ou `asyncio.get_running_loop()` |
| Python (stdlib) | `imp` | `importlib` |
| Python (stdlib) | `distutils` | `setuptools` ou implementação própria |
| Python (ORM) | Busca por chave primária pelo método legado de consulta do modelo (ex.: `Model.query.get(id)`) | Método de busca por chave da versão nova do ORM (ex.: `session.get(Model, id)`) |
| Python (web, Django) | `django.conf.urls.url()` | `re_path()` ou `path()` |
| Python (validação, Pydantic v1) | `Model.dict()`, `@validator` | `model_dump()`, `@field_validator` |
| JavaScript (Node) | `new Buffer(texto)` | `Buffer.from(texto)` |
| JavaScript (Node) | `url.parse()` | `new URL()` |
| JavaScript (Node) | `fs.exists()` | `fs.promises.access()` ou `fs.existsSync()` |
| JavaScript (Node) | `crypto.createCipher()` | `crypto.createCipheriv()` |
| JavaScript (Node) | Pacote `request` (descontinuado) | `fetch` nativo |
| JavaScript (Node) | `util.isArray()` | `Array.isArray()` |

**Correção:** T11.

## AP-11 — Magic numbers e magic strings (LOW)

**Sinais:** literal numérico ou string repetido na regra de negócio (faixas, taxas, limites, status, prefixos de cartão) sem nome, em cálculo ou condicional.

**Exceção:** `0`, `1`, `-1`, strings de formatação, valores de exemplo em configuração.

**Correção:** T12.

## AP-12 — Nomenclatura ruim, imports mortos, print como log (LOW)

**Sinais:**
- Identificador de uma ou duas letras fora de índice de laço curto.
- Import sem uso. Confirme com o linter da stack, quando houver.
- `print` ou `console.log` como log de produção ou como notificação simulada.

**Correção:** T13, T14, T15.
