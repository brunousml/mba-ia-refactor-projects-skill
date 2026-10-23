# Architecture Audit Report: ecommerce-api-legacy

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 24) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
```

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials (AP-01)
File: src/utils.js:2-5
Description: O objeto `config` traz no código o usuário e a senha do banco (`admin_master` / `senha_super_secreta_prod_123`), uma chave de gateway de pagamento com cara de produção (`pk_live_1234567890abcdef`) e o usuário SMTP.
Impact: Qualquer pessoa com acesso ao repositório obtém credenciais de produção e a chave do gateway.
Recommendation: T01 — mover para variáveis de ambiente lidas num módulo de config, com `.env.example` sem valores reais.

### [CRITICAL] God Module (AP-03)
File: src/AppManager.js:10-23, src/AppManager.js:46, src/AppManager.js:108-110, src/AppManager.js:28-137
Description: A classe `AppManager` cria o schema e o seed (DDL e INSERTs), decide aprovação de pagamento e soma receita, e ainda registra e trata as três rotas HTTP, tudo no mesmo arquivo.
Impact: Nenhuma parte pode ser testada ou alterada isoladamente; qualquer mudança mexe em banco, regra e transporte ao mesmo tempo.
Recommendation: T03 (separar config, models, services, controllers, routes e entry point) e T06 (regra no serviço).

### [CRITICAL] Sensitive Data Exposed and Weak Password Hash (AP-04)
File: src/AppManager.js:18, src/AppManager.js:45, src/AppManager.js:68, src/utils.js:17-23
Description: O checkout escreve no log o número completo do cartão e a chave do gateway; a senha é "hasheada" por uma função caseira que repete base64 dos dois primeiros caracteres e corta em 10 (reversível e com colisões triviais); o seed grava a senha `123` em texto puro.
Impact: Logs vazam dados de cartão (PCI) e a chave de pagamento; senhas armazenadas são recuperáveis por quem lê o banco.
Recommendation: T04 (hash forte com salt, `crypto.scrypt`, seed refeito com a mesma senha de exemplo) e T13 (logger sem cartão nem chave; no máximo os 4 últimos dígitos).

### [CRITICAL] Unauthenticated Financial Report (AP-07)
File: src/AppManager.js:80
Description: `GET /api/admin/financial-report` não tem nenhuma verificação de identidade e devolve receita por curso e nome e valor pago de cada aluno.
Impact: Qualquer cliente lê dados financeiros e pessoais de todos os alunos.
Recommendation: T08 — guard `ENABLE_ADMIN_ROUTES` (relatório administrativo), 403 por default e `X-Admin-Token` quando ligado.

### [CRITICAL] Unauthenticated Destructive Endpoint (AP-07)
File: src/AppManager.js:131
Description: `DELETE /api/users/:id` apaga um usuário sem qualquer autenticação (e deixa matrículas e pagamentos órfãos).
Impact: Qualquer pessoa apaga qualquer usuário.
Recommendation: T08 — guard `ENABLE_ADMIN_ROUTES` (exclusão administrativa).

### [HIGH] Business Logic in Route Handler (AP-05)
File: src/AppManager.js:37-75, src/AppManager.js:46, src/AppManager.js:83-128
Description: Os handlers fazem SQL direto, decidem a aprovação do pagamento pelo prefixo do cartão, criam o usuário implicitamente e calculam a receita do relatório dentro dos callbacks da rota.
Impact: Regras de cobrança e de relatório não podem ser testadas nem reutilizadas sem subir HTTP e banco.
Recommendation: T06 — `checkoutService` e `reportService` com a regra; controller só traduz entrada e saída.

### [HIGH] Global Mutable State (AP-06)
File: src/utils.js:9-10, src/utils.js:14, src/AppManager.js:7
Description: `globalCache` é um objeto de módulo mutado a cada checkout (`logAndCache`) e exportado; `totalRevenue` é um `let` de módulo; a conexão SQLite é única, criada no construtor e compartilhada por todas as requisições.
Impact: Estado cresce sem limite e vaza entre requisições/testes; impossível isolar o banco em teste.
Recommendation: T07 — criar banco e cache no entry point e injetar nos models/serviços; remover o cache global sem leitor.

### [HIGH] Unauthenticated Write Endpoint (AP-07)
File: src/AppManager.js:28
Description: `POST /api/checkout` cria usuário, matrícula, pagamento e log de auditoria sem nenhuma identificação do cliente.
Impact: Qualquer um cria contas e matrículas em nome de qualquer e-mail.
Recommendation: T08 — guard `ENABLE_WRITE_ROUTES`.

### [HIGH] Insecure Default Password (AP-15)
File: src/AppManager.js:68
Description: Quando `pwd` vem vazio, o usuário é criado com a senha padrão `"123456"` (`p || "123456"`).
Impact: Contas criadas sem senha ficam acessíveis com uma senha conhecida.
Recommendation: T18 — não aplicar senha padrão; exigir `pwd` ao criar usuário novo (400 sem ele).

### [MEDIUM] N+1 Queries in Financial Report (AP-08)
File: src/AppManager.js:89-106
Description: Para cada curso faz uma consulta de matrículas e, para cada matrícula, uma consulta de usuário e outra de pagamento (callbacks aninhados).
Impact: O número de consultas cresce com cursos × matrículas × 2.
Recommendation: T09 — uma única consulta com `LEFT JOIN` entre courses, enrollments, users e payments, agregada no serviço.

### [MEDIUM] Missing or Generic Error Handling (AP-09)
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135
Description: Erro de banco no checkout vira 404 "Curso não encontrado"; o erro do insert de auditoria é ignorado; no relatório o `err` não é checado e `enrollments.length` quebra se a consulta falhar; o DELETE ignora o erro e responde 200 mesmo para id inexistente. Não há handler central.
Impact: Falhas reais são mascaradas ou derrubam a requisição sem resposta; o cliente não distingue erro de dado inexistente.
Recommendation: T10 — erros de domínio como classes e middleware de erro central; checar todo `err`.

### [MEDIUM] Missing Input Validation (AP-14)
File: src/AppManager.js:29-35, src/AppManager.js:46
Description: O corpo só é checado por presença; `card` numérico (ex.: `4111...` como number) chega a `cc.startsWith` e lança `TypeError` dentro do callback do sqlite, fora do tratamento do Express; `c_id`, `eml` e `usr` não têm tipo nem formato verificados.
Impact: Uma entrada malformada pode derrubar o processo em vez de devolver 400, e dados inválidos entram no banco.
Recommendation: T17 — validar tipos e formatos no controller (card string de dígitos, c_id inteiro positivo, e-mail com `@`), 400 em caso inválido.

### [LOW] Magic Numbers and Strings (AP-11)
File: src/AppManager.js:46, src/AppManager.js:108, src/utils.js:19
Description: O prefixo `"4"` que aprova o cartão, os status `"PAID"`/`"DENIED"` e as 10000 iterações do hash aparecem como literais.
Impact: Regras de pagamento ficam escondidas e são fáceis de divergir.
Recommendation: T12 — constantes nomeadas (`APPROVED_CARD_PREFIX`, `PAYMENT_STATUS`).

### [LOW] Poor Naming, Dead Code and console.log as Logger (AP-12)
File: src/AppManager.js:2, src/AppManager.js:29-33, src/AppManager.js:45, src/AppManager.js:89, src/utils.js:10, src/utils.js:13, src/utils.js:25
Description: Variáveis de uma letra (`u`, `e`, `p`, `cc`, `c`); `totalRevenue` é importado e exportado sem uso, e `globalCache` é exportado sem leitor; `console.log` usado como log de produção.
Impact: Leitura difícil e código morto que confunde quem mantém.
Recommendation: T14 (nomes descritivos internos, mantendo `usr`/`eml`/`pwd`/`c_id`/`card` na borda), T15 (remover código morto) e T13 (logger).

```
================================
Total: 14 findings
================================
```
