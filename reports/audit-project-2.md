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
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139, src/AppManager.js:10-23, src/AppManager.js:46, src/AppManager.js:108-110, src/AppManager.js:28, src/AppManager.js:80, src/AppManager.js:131
Description: A classe `AppManager` cria o schema e o seed (10-23), decide aprovação de pagamento e soma receita (46, 108-110) e registra e trata as três rotas HTTP (28, 80, 131), tudo no mesmo módulo.
Impact: Nenhuma regra pode ser testada ou alterada sem subir HTTP e banco juntos, e qualquer mudança arrisca as três rotas.
Recommendation: T03 (separar em config, models, services, controllers e routes) e T06 (regra de pagamento e de receita em serviços).

### [CRITICAL] Sensitive Data Exposure (AP-04)
File: src/AppManager.js:18, src/AppManager.js:45, src/AppManager.js:68, src/utils.js:17-23
Description: O número completo do cartão e a chave do gateway vão para o `console.log` (45); a senha é "hasheada" por `badCrypto`, que repete base64 e trunca em 10 caracteres (utils 17-23, usada em 68); o seed grava a senha `'123'` em texto puro (18).
Impact: Logs expõem cartões e a chave de pagamento, e senhas são recuperáveis por qualquer um com acesso ao banco.
Recommendation: T04 (hash forte com salt via `crypto.scrypt`, refazendo o seed com a mesma senha de exemplo) e T13 (log sem cartão nem chave).

### [CRITICAL] Unauthenticated Destructive and Sensitive Endpoints (AP-07)
File: src/AppManager.js:80, src/AppManager.js:131
Description: `GET /api/admin/financial-report` devolve receita e nomes de alunos com valores pagos, e `DELETE /api/users/:id` apaga usuários (deixando matrículas e pagamentos órfãos, como a própria resposta admite em 135), ambos sem nenhuma checagem de identidade.
Impact: Qualquer cliente lê dados financeiros e pessoais ou apaga usuários.
Recommendation: T08 com o guard de administração (`ENABLE_ADMIN_ROUTES` + `X-Admin-Token`) nas duas rotas.

### [CRITICAL] Hardcoded Credentials (AP-01)
File: src/utils.js:2-4
Description: `dbUser`, `dbPass` (`senha_super_secreta_prod_123`) e `paymentGatewayKey` (`pk_live_1234567890abcdef`) estão como literais no objeto `config`.
Impact: Quem tem acesso ao repositório tem as credenciais de produção do banco e do gateway.
Recommendation: T01 (ler de variáveis de ambiente num módulo de config, com `.env.example` sem valores reais).

### [HIGH] Business Logic in Route Handlers (AP-05)
File: src/AppManager.js:37-75, src/AppManager.js:46-48, src/AppManager.js:108-110
Description: O handler de checkout consulta o banco direto, cria usuário, aprova o pagamento pelo prefixo do cartão (`startsWith("4")`) e grava matrícula, pagamento e auditoria; o handler do relatório calcula a receita somando pagamentos `PAID`.
Impact: As regras de pagamento e receita não podem ser testadas nem reutilizadas fora da rota.
Recommendation: T06 (serviços de checkout e de relatório chamados pelo controller).

### [HIGH] Global Mutable State (AP-06)
File: src/utils.js:9, src/utils.js:14, src/AppManager.js:7
Description: `globalCache` é um objeto de módulo mutado a cada checkout por `logAndCache` e exportado; a conexão SQLite única é criada no construtor e compartilhada por todas as requisições.
Impact: Estado cresce sem limite e vaza entre requisições e testes, e a conexão não pode ser substituída em teste.
Recommendation: T07 (injetar a conexão nos models e remover o cache global, que nenhuma rota lê).

### [HIGH] Insecure Default Password (AP-15)
File: src/AppManager.js:68
Description: Quando o checkout chega sem `pwd`, o usuário é criado com a senha padrão `"123456"` (`p || "123456"`).
Impact: Toda conta criada sem senha é acessível com uma senha conhecida.
Recommendation: T18 (sem senha default: exigir `pwd` para criar usuário novo e devolver 400).

### [HIGH] Unauthenticated Write Endpoint (AP-07)
File: src/AppManager.js:28
Description: `POST /api/checkout` cria usuários, matrículas e pagamentos sem nenhuma checagem de identidade.
Impact: Qualquer cliente cria contas e matrículas em nome de qualquer e-mail.
Recommendation: T08 com o guard de escrita (`ENABLE_WRITE_ROUTES` + `X-Admin-Token`).

### [MEDIUM] N+1 Queries (AP-08)
File: src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106
Description: O relatório faz uma consulta de matrículas por curso e, para cada matrícula, uma de usuário e uma de pagamento, em callbacks aninhados.
Impact: O número de consultas cresce com cursos × matrículas e o relatório fica lento com volume real.
Recommendation: T09 (uma consulta com `LEFT JOIN` de cursos, matrículas, usuários e pagamentos, agrupada no serviço).

### [MEDIUM] Missing or Swallowed Error Handling (AP-09)
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135
Description: Erro de banco no checkout vira 404 "Curso não encontrado" (38); os callbacks de auditoria, matrículas, usuário e pagamento ignoram `err` (57, 92, 104, 106), e em 93 `enrollments.length` quebra o processo se a consulta falhar; o DELETE ignora o erro e responde sucesso mesmo para id inexistente (133-135). Não há handler central.
Impact: Falhas reais ficam escondidas ou derrubam o processo, e o cliente recebe status enganoso.
Recommendation: T10 (erros de domínio e middleware central de erro; `async/await` com propagação).

### [MEDIUM] Duplicated Logic (AP-13)
File: src/AppManager.js:96-98, src/AppManager.js:119-121
Description: O bloco que fecha um curso no relatório (`report.push`, decremento de `coursesPending` e `res.json`) está copiado em dois pontos.
Impact: Corrigir a contagem em um ponto e esquecer o outro faz a resposta sair incompleta ou nunca sair.
Recommendation: T16 (some com a T09: a montagem do relatório fica numa única função do serviço).

### [MEDIUM] Missing Input Validation (AP-14)
File: src/AppManager.js:29-35, src/AppManager.js:46
Description: Só a presença dos campos é checada; `card` numérico (`4111...` sem aspas) quebra em `cc.startsWith` (TypeError → 500), e `c_id` e `eml` não têm checagem de tipo ou formato.
Impact: Entrada malformada gera 500 em vez de 400.
Recommendation: T17 (validar tipos na borda e devolver 400).

### [LOW] Magic Numbers and Strings (AP-11)
File: src/AppManager.js:46, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:6, src/utils.js:19
Description: Prefixo de cartão aprovado `"4"`, status `"PAID"`/`"DENIED"`, senha `"123456"`, porta `3000` e as `10000` iterações aparecem como literais.
Impact: Regras de negócio ficam escondidas e fáceis de divergir.
Recommendation: T12 (constantes nomeadas num módulo de regras).

### [LOW] Poor Naming, Dead Code and console.log as Logger (AP-12)
File: src/AppManager.js:2, src/AppManager.js:26, src/AppManager.js:29-33, src/AppManager.js:45, src/utils.js:2-5, src/utils.js:10, src/utils.js:13, src/utils.js:25
Description: Variáveis `u`, `e`, `p`, `cid`, `cc` e `self`; `totalRevenue` é importado e nunca usado, `globalCache` é exportado sem leitor, e `dbUser`, `dbPass`, `smtpUser` não são usados; `console.log` serve de log de produção.
Impact: Leitura difícil e código morto que parece ter efeito.
Recommendation: T14 (nomes descritivos), T15 (remover código morto) e T13 (logger).

```
================================
Total: 14 findings
================================
```
