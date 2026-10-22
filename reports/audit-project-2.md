# Architecture Audit Report: ecommerce-api-legacy

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
```

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] God Class Mixing Data Access, Business Rules and Routing (AP-03)
File: src/AppManager.js:4-139, src/AppManager.js:10-23, src/AppManager.js:25-137
Description: A classe `AppManager` abre a conexão (linha 7), cria o schema e roda o seed (`initDb`, linhas 10-23), registra as três rotas HTTP (`setupRoutes`, linhas 25-137) e decide regra de negócio dentro delas (aprovação do pagamento na linha 46, soma de receita nas linhas 108-110).
Impact: Nenhuma regra pode ser testada sem subir Express e SQLite juntos, e mudar uma rota arrisca quebrar as outras.
Recommendation: T03 (separar config, models, services, controllers e routes por domínio) e T06 (tirar a regra de pagamento e o cálculo do relatório das rotas).

### [CRITICAL] Card Number and Gateway Key in Logs, Weak Password Hash (AP-04)
File: src/AppManager.js:18, src/AppManager.js:45, src/AppManager.js:68, src/utils.js:17-23
Description: O checkout escreve no console o número completo do cartão e a chave do gateway (linha 45). `badCrypto` (utils.js:17-23) é uma função caseira que repete os dois primeiros caracteres do base64 da senha: o resultado depende só do início da senha, não tem salt e é reversível. O seed grava a senha `'123'` em texto puro (linha 18).
Impact: Quem lê os logs obtém cartões e a chave de produção; quem lê o banco recupera ou colide qualquer senha.
Recommendation: T13 (log sem cartão nem chave; no máximo os 4 últimos dígitos), T04 (hash com salt via `crypto.scrypt` da stdlib) e refazer o seed com a mesma senha de exemplo hasheada.

### [CRITICAL] Unauthenticated Destructive and Financial Endpoints (AP-07)
File: src/AppManager.js:80, src/AppManager.js:131-136
Description: `GET /api/admin/financial-report` devolve receita por curso e nome/valor pago por aluno sem nenhuma checagem de identidade. `DELETE /api/users/:id` apaga qualquer usuário sem autenticação (e deixa matrículas e pagamentos órfãos, como a própria resposta admite).
Impact: Qualquer cliente lê dados financeiros e pessoais e apaga contas.
Recommendation: T08 com guard de administração (`ENABLE_ADMIN_ROUTES` + `X-Admin-Token`) nas duas rotas; 403 com a flag desligada.

### [CRITICAL] Hardcoded Credentials and Live Payment Key (AP-01)
File: src/utils.js:2-5
Description: O objeto `config` contém `dbUser`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` como literais no código.
Impact: Qualquer pessoa com acesso ao repositório obtém a senha do banco e a chave de produção do gateway.
Recommendation: T01 (ler de variáveis de ambiente num módulo de config, sem default para segredos, com `.env.example`).

### [HIGH] Business Rules and Data Access Inside Route Handler (AP-05)
File: src/AppManager.js:28-78, src/AppManager.js:46, src/AppManager.js:80-129
Description: O handler de checkout faz as consultas e inserções diretamente (linhas 37-72), decide aprovação de pagamento pelo prefixo do cartão (linha 46) e cria usuário implicitamente. O handler do relatório monta a agregação de receita (linhas 89-127) dentro da rota.
Impact: Regra de pagamento e de relatório não podem ser testadas nem reutilizadas sem HTTP.
Recommendation: T06 (mover para `checkoutService` e `reportService`; rota só repassa).

### [HIGH] Mutable Module-Level State (AP-06)
File: src/utils.js:9-10, src/utils.js:14, src/AppManager.js:59
Description: `globalCache` é um objeto de módulo mutado por `logAndCache` a cada checkout (sem limite de tamanho), e `totalRevenue` é um `let` de módulo exportado.
Impact: Estado compartilhado entre requisições cresce sem limite e torna o comportamento dependente da ordem das chamadas.
Recommendation: T07 (remover o cache global, que ninguém lê; remover `totalRevenue`).

### [HIGH] Default Password When Input Is Empty (AP-15)
File: src/AppManager.js:68
Description: Se o checkout vem sem `pwd`, o usuário é criado com a senha padrão `"123456"` (`badCrypto(p || "123456")`).
Impact: Contas criadas sem senha ficam acessíveis com uma senha conhecida.
Recommendation: T18 (exigir `pwd` quando o usuário ainda não existe; 400 se ausente).

### [HIGH] Unauthenticated Write Endpoint (AP-07)
File: src/AppManager.js:28
Description: `POST /api/checkout` cria usuários, matrículas, pagamentos e logs de auditoria sem checagem de identidade.
Impact: Qualquer cliente cria contas e matrículas em nome de qualquer e-mail.
Recommendation: T08 com guard de escrita (`ENABLE_WRITE_ROUTES` + `X-Admin-Token`).

### [MEDIUM] N+1 Queries in Financial Report (AP-08)
File: src/AppManager.js:89-127
Description: Para cada curso há uma consulta de matrículas (linha 92) e, para cada matrícula, uma consulta de usuário (linha 104) e outra de pagamento (linha 106), em callbacks aninhados.
Impact: O número de consultas cresce com cursos × matrículas e a ordem de resposta fica não determinística.
Recommendation: T09 (uma consulta com `LEFT JOIN` entre courses, enrollments, users e payments, agregada no service).

### [MEDIUM] Ignored or Generic Error Handling (AP-09)
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133
Description: Callbacks recebem `err` e não verificam (linhas 57, 104, 106, 133); na linha 92 `enrollments.length` quebra se a consulta falhar; na linha 38 erro de banco vira 404 "Curso não encontrado". Não há handler central.
Impact: Falhas reais viram respostas de sucesso, 404 enganosos ou derrubam o processo.
Recommendation: T10 (callbacks viram Promises, erros sobem para um middleware central de erro).

### [MEDIUM] Missing Input Type Validation (AP-14)
File: src/AppManager.js:29-35, src/AppManager.js:46, src/AppManager.js:132
Description: Só há checagem de presença. `card` é usado com `cc.startsWith` sem checar tipo: um `card` numérico lança `TypeError` dentro do callback do sqlite e derruba o processo. `c_id` e `:id` não são validados como inteiros; corpo ausente/não-JSON não é tratado.
Impact: Uma requisição malformada derruba a API para todos.
Recommendation: T17 (validar tipos de `usr`, `eml`, `pwd`, `card` como string e `c_id`/`id` como inteiro; 400 em vez de crash).

### [LOW] Magic Strings in Payment Rules (AP-11)
File: src/AppManager.js:46, src/AppManager.js:108, src/AppManager.js:21
Description: O prefixo `"4"` de aprovação e os status `"PAID"`/`"DENIED"` aparecem como literais soltos.
Impact: Mudar a regra exige caçar literais espalhados.
Recommendation: T12 (constantes em `config/rules.js`).

### [LOW] Poor Naming, Dead Code and console.log as Logger (AP-12)
File: src/AppManager.js:2, src/AppManager.js:26, src/AppManager.js:29-33, src/utils.js:2, src/utils.js:5, src/utils.js:10, src/utils.js:13, src/utils.js:25
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`; `self` para contornar `this`; `totalRevenue`, `dbUser`, `dbPass`, `smtpUser` e o export `globalCache` não são usados; `console.log` como log de produção.
Impact: Leitura difícil e código morto que confunde manutenção.
Recommendation: T14 (nomes descritivos), T15 (remover código morto) e T13 (logger simples).

```
================================
Total: 13 findings
================================
```
