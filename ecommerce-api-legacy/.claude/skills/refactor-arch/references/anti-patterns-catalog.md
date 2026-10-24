# Catálogo de anti-patterns (Fase 2)

Quinze anti-patterns, agrupados por severidade. Os sinais de detecção descrevem o **padrão**, não a sintaxe de uma linguagem. Os exemplos entre parênteses mostram formas comuns em stacks diferentes e não esgotam os casos. Se o padrão aparecer em outra forma, aplique o mesmo critério.

A Fase 2 é **só leitura**: os sinais são confirmados lendo o código. Nada de subir a aplicação, instalar dependências ou executar scripts. Antes de citar `arquivo:linha`, leia o trecho.

## Escala de severidade

- **CRITICAL:** expõe segredo ou dado sensível; permite injeção; deixa uma operação destrutiva ou um dado sensível acessível sem autenticação; ou concentra acesso a dados, regra de negócio e roteamento no mesmo módulo.
- **HIGH:** impede teste isolado e manutenção (regra de negócio em rota, estado global mutável, configuração insegura, endpoint sem checagem de identidade que não é destrutivo).
- **MEDIUM:** degrada desempenho ou correção de forma moderada (consulta dentro de laço, erro engolido, API obsoleta, duplicação, validação ausente).
- **LOW:** atrapalha a leitura sem quebrar nada (magic numbers, nomes ruins, código morto, print usado como log).

A severidade de cada anti-pattern está na tabela abaixo. As exceções estão escritas no próprio anti-pattern (por exemplo, AP-07 vira CRITICAL quando a rota é destrutiva). Não existe promoção automática além dessas.

## Resumo

| ID | Severidade | Anti-pattern | Transformação |
| --- | --- | --- | --- |
| AP-01 | CRITICAL | Credenciais hardcoded | T01 |
| AP-02 | CRITICAL | Injeção de SQL | T02 |
| AP-03 | CRITICAL | God class ou god module | T03, T06 |
| AP-04 | CRITICAL | Dados sensíveis expostos (senha em resposta ou log, hash fraco) | T04, T05, T13 |
| AP-05 | HIGH | Regra de negócio em rota ou controller | T06 |
| AP-06 | HIGH | Estado global mutável | T07 |
| AP-07 | HIGH (CRITICAL se destrutivo ou sensível) | Endpoint sem autenticação | T08 |
| AP-15 | HIGH (CRITICAL se concede privilégio) | Configuração insegura | T18 |
| AP-08 | MEDIUM | Query N+1 | T09 |
| AP-09 | MEDIUM | Tratamento de erro ausente ou genérico | T10 |
| AP-10 | MEDIUM | API deprecated | T11 |
| AP-13 | MEDIUM | Lógica duplicada | T16 |
| AP-14 | MEDIUM | Validação de entrada ausente | T17 |
| AP-11 | LOW | Magic numbers e magic strings | T12 |
| AP-12 | LOW | Nomenclatura ruim, código morto, print como log | T13, T14, T15 |

---

## AP-01 — Credenciais hardcoded (CRITICAL)

**Sinais:**
- Literal de string atribuído a um nome que contém `secret`, `key`, `password`, `senha`, `passwd`, `pass`, `token`, `credential`, `api_key` ou `user` (no contexto de banco ou serviço), em qualquer escopo: módulo, classe, objeto de configuração.
- Literal com cara de chave real: prefixos como `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, ou string longa de alta entropia.
- Credencial dentro de URL de conexão (`usuario:senha@host`).
- Segredo devolvido numa resposta (por exemplo, health check que mostra a chave). Isso é também AP-04.
- Seed que cria usuário com senha fixa e roda no boot também em produção. Correção: o seed de usuários de exemplo só roda fora de produção (`APP_ENV`); um script de seed executado à mão não conta.

**Exceção:** valor claramente de exemplo (`changeme`, `your-key-here`) em arquivo de template. Rebaixe para LOW e explique.

**Correção:** T01.

## AP-02 — Injeção de SQL (CRITICAL)

**Sinais:**
- Texto de consulta montado com `+`, `%`, `.format()`, f-string, interpolação ou template literal que contém variável, passado a uma função de execução de query.
- Valor vindo da requisição (query string, body, parâmetro de caminho **sem** conversor de tipo) chegando a essa consulta. Rastreie a variável até a origem; duas ou três atribuições no caminho não mudam nada.
- Nome de coluna ou `ORDER BY` vindo da entrada sem lista de valores permitidos.
- Endpoint que recebe SQL como texto e executa. É também AP-07.

**Como classificar cada linha:** liste no finding só as concatenações em que um valor controlado pelo cliente chega à consulta. Se o parâmetro de caminho passa por conversor de tipo inteiro do framework, ou o valor vem do próprio banco, a linha é má prática, mas não é explorável. Mencione-a na descrição, sem contá-la como ponto de injeção.

**Correção:** T02.

## AP-03 — God class ou god module (CRITICAL)

**Sinais:** um arquivo ou classe que faz as três coisas ao mesmo tempo:
- (a) executa consultas, DDL ou seed de dados;
- (b) contém cálculo ou decisão de negócio;
- (c) registra rotas ou trata requisição HTTP.

Indicadores complementares: mais de 300 linhas com as três responsabilidades; classe com mais de dez métodos de naturezas diferentes; o mesmo módulo importa a camada de dados e a de transporte.

Se o módulo tem (a) e (b), mas não (c), classifique como AP-05 (HIGH): mistura de responsabilidades sem ser god module.

**Correção:** T03 (separar camadas) e T06 (tirar a regra da rota).

## AP-04 — Dados sensíveis expostos (CRITICAL)

**Sinais:**
- Senha, hash, token, chave, número de cartão ou dado de pagamento dentro de um objeto devolvido na resposta. Atenção a funções de serialização (`to_dict`, `toJSON`, serializers) que listam todos os campos. Liste as rotas que de fato usam a serialização vazada.
- `SELECT *` ou equivalente cujo resultado vai direto para a resposta.
- Campo sensível ou número de cartão (sequência de 13 a 19 dígitos) em `print`, `console.log` ou logger.
- Hash fraco de senha: MD5, SHA-1 sem salt, base64, texto puro, ou função caseira (laço que repete uma transformação simples).

**Correção:** T04 (hash forte), T05 (serialização explícita), T13 (logger sem dado sensível).

## AP-05 — Regra de negócio em rota ou controller (HIGH)

**Sinais:** handler de rota, ou módulo de dados, que contém:
- cálculo de valor, desconto, imposto ou prazo;
- decisão de estado (aprovar, cancelar, liberar acesso) com condicionais de domínio;
- validação de regra de domínio com mais de dez linhas;
- acesso direto ao banco a partir da rota.

Validação de formato (campo obrigatório, tipo, tamanho) pode ficar na borda (controller). Regra de domínio não pode.

**Correção:** T06.

## AP-06 — Estado global mutável (HIGH)

**Sinais:**
- Variável de escopo de módulo reatribuída em tempo de execução (`global x` em Python; `let` no topo do módulo reatribuído dentro de uma função).
- Objeto, lista ou mapa de módulo mutado por função (inserção, remoção, incremento).
- Conexão de banco única, criada sob demanda e compartilhada por todas as requisições.

**Exceção:** constantes e configuração lidas uma vez na inicialização.

**Correção:** T07.

## AP-07 — Endpoint sem autenticação (HIGH; CRITICAL se destrutivo ou sensível)

**Sinais:** rota sem middleware, decorator ou verificação de identidade, no registro ou no handler, que:
- **CRITICAL:** apaga ou altera dados em massa, executa comandos ou SQL, ou devolve dados sensíveis (financeiros, pessoais, de pagamento).
- **HIGH:** realiza operação administrativa ou de exportação sem esses efeitos.

Nomes de caminho e de função que costumam indicar isso: `admin`, `reset`, `drop`, `delete`, `query`, `execute`, `report`, `export`, `financ`.

Também se aplica (HIGH) ao "login" que devolve um token que nenhuma outra rota verifica: não existe autenticação real.

Também se aplica (HIGH) à operação que age sobre uma conta **existente** identificada só por e-mail ou id vindo do corpo, sem conferir senha ou token do dono (ex.: checkout que reaproveita o usuário pelo e-mail e ignora a senha). Se o contrato original já envia a senha do dono, confira-a (o guard do T08 sozinho não basta). Se o contrato não tem nenhuma credencial do dono, o guard do T08 resolve: só quem tem o token de administração age em nome da conta. Exigir uma credencial nova quebraria todos os clientes, então registre a decisão em "Intentional changes".

**Correção:** T08, com o guard que corresponde ao sinal: administração (reset, SQL, relatório ou exportação, mesmo financeiro), leitura sensível (registros pessoais, pedidos, pagamentos) ou escrita (demais POST/PUT/PATCH/DELETE). O login falso é resolvido protegendo as rotas que deveriam depender dele.

## AP-08 — Query N+1 (MEDIUM)

**Sinais:**
- Consulta ao banco dentro de laço (`for`, `forEach`, `map`, `while`) sobre o resultado de outra consulta.
- Chamada a método que consulta, dentro de laço.
- Relação carregada sob demanda (lazy) acessada dentro de laço, inclusive só para contar os itens.
- Callbacks aninhados que fazem uma consulta por item.

**Correção:** T09.

## AP-09 — Tratamento de erro ausente ou genérico (MEDIUM)

**Sinais:**
- Captura de exceção sem tipo específico que não relança nem registra o erro.
- Bloco de captura vazio.
- Callback que recebe o erro como parâmetro e não o verifica.
- Mensagem interna da exceção devolvida ao cliente (`str(e)`, `err.message`).
- Ausência de handler central: cada rota devolve "erro interno" para qualquer falha, sem distinguir validação de falha real.

**Correção:** T10.

## AP-10 — API deprecated (MEDIUM)

**Sinais:**
- Chamada **ou referência** a símbolo marcado como obsoleto na versão instalada. Referência sem chamada também conta (por exemplo, a função passada como default de coluna ou como callback).
- Warning de runtime. Ele só é observado na Fase 3, no snapshot. Na Fase 2, use a lista abaixo e a leitura do código.

**Como verificar:** use a tabela quando a stack estiver nela. Se não estiver, consulte a documentação da versão declarada no manifesto (README, changelog, `@deprecated` nos tipos) e procure `deprecated`, `obsolete` e `removed in`.

| Stack | Obsoleto | Equivalente moderno |
| --- | --- | --- |
| Python (stdlib) | `datetime.utcnow`, `datetime.utcfromtimestamp`, chamados ou referenciados | `datetime.now(timezone.utc)`; como default, `lambda: datetime.now(timezone.utc)` |
| Python (stdlib) | `asyncio.get_event_loop()` fora de contexto assíncrono | `asyncio.run()` ou `asyncio.get_running_loop()` |
| Python (stdlib) | `imp` | `importlib` |
| Python (stdlib) | `distutils` | `setuptools` ou implementação própria |
| Python (ORM) | Busca por chave primária pelo método legado do objeto de consulta do modelo | Método de busca por chave da sessão, na versão atual do ORM |
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

**Sinais:** literal numérico ou string de regra de negócio (faixas, taxas, limites, status, prefixos) sem nome, em cálculo ou condicional.

**Exceção:** `0`, `1`, `-1`, strings de formatação e valores de exemplo em configuração.

**Correção:** T12.

## AP-12 — Nomenclatura ruim, código morto, print como log (LOW)

**Sinais:**
- Identificador de uma ou duas letras fora de índice de laço curto.
- Import, variável, função ou export sem uso. Confirme com uma busca pelo nome no projeto.
- Condicionais aninhadas que só devolvem `True`/`False` e caberiam numa expressão.
- `print` ou `console.log` usado como log de produção ou como notificação simulada.

**Correção:** T13, T14, T15.

## AP-13 — Lógica duplicada (MEDIUM)

**Sinais:**
- A mesma regra (validação, cálculo, condição de estado) copiada em dois ou mais handlers ou módulos, com as mesmas comparações e literais.
- Cópias que **já divergem** (uma valida um campo e a outra não). Mencione isso na descrição, porque é a prova do risco.
- Método de modelo que implementa a regra, mas não é chamado, enquanto as rotas repetem o código.

**Correção:** T16.

## AP-14 — Validação de entrada ausente (MEDIUM)

**Sinais:**
- Campo da requisição usado em comparação ou aritmética sem checar o tipo (string comparada com número, conversão sem tratamento).
- Valor numérico de negócio sem faixa (quantidade ou preço negativos aceitos).
- Corpo da requisição usado sem checar se existe (`None`/`undefined`), o que gera 500 em vez de 400.

**Correção:** T17.

## AP-15 — Configuração insegura (HIGH; CRITICAL se concede privilégio)

**Sinais:**
- Modo debug ou depurador ligado no código, sem depender do ambiente.
- Valor padrão de senha ou credencial quando a entrada vem vazia (`password or "changeme"`, `password || "default"`).
- Cadastro ou atualização que aceita do cliente um campo de papel ou permissão (`role`, `is_admin`), sem autenticação. **CRITICAL**, porque qualquer um ganha privilégio.
- CORS liberado para qualquer origem em rotas que alteram dados.

**Correção:** T18.
