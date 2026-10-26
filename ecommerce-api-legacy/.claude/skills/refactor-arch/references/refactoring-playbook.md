# Playbook de refatoração (Fase 3)

Dezoito transformações, cada uma ligada a um ou mais anti-patterns do catálogo. Cada uma tem código **antes** e **depois** em Python e em JavaScript. Aplique a transformação do finding sem misturar outras no mesmo movimento.

**Sobre os exemplos:**
- O domínio é fictício (faturas, contas, assinaturas). Adapte nomes e campos ao projeto real.
- Funções como `json()`, `erro()`, `registrar()` e o objeto `request` são **pseudocódigo** do framework web. Use as equivalentes da stack detectada na Fase 1.
- Drivers de banco variam: o placeholder pode ser `?`, `%s`, `$1` ou `:nome`, e a API pode ser síncrona, com callback ou com promise. Confira antes de copiar.

**Regras gerais:**
- Preserve o contrato: método, caminho, status, nomes de campos e **porta** padrão.
- Depois de cada grupo de transformações, o boot precisa continuar sem erro.
- Toda mudança de comportamento observável, mesmo que intencional por segurança, vai para "Intentional changes".

Índice: T01 credenciais · T02 SQL parametrizado · T03 separar camadas · T04 hash de senha · T05 serialização explícita · T06 regra no serviço · T07 dependência injetada · T08 guards de acesso por flag · T09 consulta em lote · T10 erro central · T11 API moderna · T12 constantes nomeadas · T13 logger · T14 nomes descritivos · T15 remover código morto · T16 extrair regra duplicada · T17 validar na borda · T18 configuração segura.

---

## T01 — Credenciais para configuração por ambiente (AP-01)

O segredo sai do código. Para a aplicação continuar subindo em desenvolvimento e na validação, a ausência da variável gera um valor aleatório e um warning. Em produção (`APP_ENV=production`), a ausência derruba o boot. A porta padrão continua a mesma do projeto original. Crie também um `.env.example` com os nomes das variáveis, sem valores reais.

**Python — antes**
```python
app.config["SECRET_KEY"] = "s3gredo-fixo-da-api"
BILLING_API_KEY = "sk_live_9f8e7d6c"
```

**Python — depois**
```python
# config/settings.py
import logging
import os
import secrets

logger = logging.getLogger(__name__)
APP_ENV = os.environ.get("APP_ENV", "development")

def segredo(nome):
    valor = os.environ.get(nome)
    if valor:
        return valor
    if APP_ENV == "production":
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    logger.warning("%s não definida; usando valor aleatório de desenvolvimento", nome)
    return secrets.token_hex(32)

SECRET_KEY = segredo("SECRET_KEY")
BILLING_API_KEY = os.environ.get("BILLING_API_KEY", "")   # integração desligada se vazio
PORT = int(os.environ.get("PORT", "8080"))                 # mesmo default do projeto original
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

**JavaScript — antes**
```js
const settings = { dbPassword: "senha-fixa-do-banco", billingKey: "sk_live_9f8e7d6c", port: 8080 };
```

**JavaScript — depois**
```js
// config/settings.js
const crypto = require('crypto');
const appEnv = process.env.APP_ENV || 'development';

function segredo(nome) {
  if (process.env[nome]) return process.env[nome];
  if (appEnv === 'production') throw new Error(`Variável de ambiente obrigatória ausente: ${nome}`);
  console.warn(`${nome} não definida; usando valor aleatório de desenvolvimento`);
  return crypto.randomBytes(32).toString('hex');
}

module.exports = {
  dbPassword: segredo('DB_PASSWORD'),
  billingKey: process.env.BILLING_KEY || '',
  port: Number(process.env.PORT || 8080),   // mesmo default do projeto original
};
```

**Atenção:** um segredo que já esteve no repositório precisa ser **rotacionado**, porque tirá-lo do código não invalida a cópia que vazou. Registre isso. Se algum endpoint devolvia o segredo na resposta, a remoção do campo é mudança intencional.

---

## T02 — Consulta parametrizada no lugar de concatenação (AP-02)

**Python — antes**
```python
cursor.execute("SELECT * FROM contas WHERE email = '" + email + "'")
cursor.execute("UPDATE faturas SET descricao = '" + descricao + "' WHERE id = " + str(fatura_id))
```

**Python — depois**
```python
cursor.execute("SELECT * FROM contas WHERE email = ?", (email,))
cursor.execute("UPDATE faturas SET descricao = ? WHERE id = ?", (descricao, fatura_id))
```

**Login:** busque pelo identificador e verifique a senha em código (T04). Nunca compare senha ou hash no SQL.

```python
conta = cursor.execute("SELECT * FROM contas WHERE email = ?", (email,)).fetchone()
if conta is None or not verificar_senha(senha, conta["senha_hash"]):
    return None
```

**JavaScript — antes**
```js
db.all(`SELECT * FROM faturas WHERE descricao LIKE '%${termo}%'`, callback);
```

**JavaScript — depois**
```js
db.all('SELECT * FROM faturas WHERE descricao LIKE ?', [`%${termo}%`], callback);
```

**Identificadores dinâmicos** (nome de coluna, `ORDER BY`) não podem ser parâmetros. Use uma lista de valores permitidos:

```python
ORDENAVEIS = {"emitida_em", "valor", "vencimento"}
campo = request.args.get("ordenar", "emitida_em")
if campo not in ORDENAVEIS:
    campo = "emitida_em"
cursor.execute(f"SELECT * FROM faturas ORDER BY {campo}")   # seguro: campo vem da lista
```

---

## T03 — Separar um módulo que mistura camadas (AP-03)

Mova o código **sem mudar a lógica** primeiro. As correções vêm depois, já no lugar certo.

**Python — antes** (SQL, regra e rota no mesmo arquivo)
```python
@route("POST", "/faturas")
def emitir_fatura():
    dados = request.json
    total = 0
    for linha in dados["linhas"]:
        tarifa = db.execute("SELECT tarifa FROM planos WHERE id = ?", (linha["plano_id"],)).fetchone()[0]
        total += tarifa * linha["meses"]
    db.execute("INSERT INTO faturas (conta_id, total) VALUES (?, ?)", (dados["conta_id"], total))
    return json({"total": total}, 201)
```

**Python — depois**
```python
# models/fatura_model.py: só acesso a dados
def tarifa_do_plano(conn, plano_id):
    return conn.execute("SELECT tarifa FROM planos WHERE id = ?", (plano_id,)).fetchone()[0]

def inserir_fatura(conn, conta_id, total):
    return conn.execute("INSERT INTO faturas (conta_id, total) VALUES (?, ?)", (conta_id, total)).lastrowid

# services/fatura_service.py: regra de negócio
def emitir(conn, conta_id, linhas):
    total = sum(fatura_model.tarifa_do_plano(conn, l["plano_id"]) * l["meses"] for l in linhas)
    fatura_id = fatura_model.inserir_fatura(conn, conta_id, total)
    return {"fatura_id": fatura_id, "total": total}

# controllers/fatura_controller.py: adaptação HTTP
def emitir(request):
    dados = request.json
    if not dados or not dados.get("linhas"):
        return erro("Fatura deve ter pelo menos 1 linha", 400)
    return json(fatura_service.emitir(conexao_da_requisicao(), dados["conta_id"], dados["linhas"]), 201)

# routes/fatura_routes.py: só registro
registrar("POST", "/faturas", fatura_controller.emitir)
```

**JavaScript — antes**
```js
app.post('/faturas', (req, res) => {
  let total = 0;
  // consulta de tarifa por linha + soma...
  db.run('INSERT INTO faturas (conta_id, total) VALUES (?, ?)', [req.body.contaId, total], function () {
    res.status(201).json({ total });
  });
});
```

**JavaScript — depois**

Se o driver usa callbacks, crie primeiro um adaptador com promises. Em alguns drivers, o id inserido (`lastID`) fica em `this` dentro do callback. Nesse caso, use `function`, não arrow function:

```js
// models/db.js
function criarDb(driverDb) {
  return {
    get: (sql, params = []) => new Promise((ok, falha) =>
      driverDb.get(sql, params, (err, linha) => (err ? falha(err) : ok(linha)))),
    all: (sql, params = []) => new Promise((ok, falha) =>
      driverDb.all(sql, params, (err, linhas) => (err ? falha(err) : ok(linhas)))),
    run: (sql, params = []) => new Promise((ok, falha) =>
      driverDb.run(sql, params, function (err) {
        if (err) return falha(err);
        ok({ lastID: this.lastID, changes: this.changes });
      })),
  };
}
module.exports = { criarDb };
```

```js
// models/faturaModel.js
const tarifaDoPlano = (db, planoId) => db.get('SELECT tarifa FROM planos WHERE id = ?', [planoId]);
const inserirFatura = (db, contaId, total) =>
  db.run('INSERT INTO faturas (conta_id, total) VALUES (?, ?)', [contaId, total]);

// services/faturaService.js
async function emitir(db, contaId, linhas) {
  let total = 0;
  for (const linha of linhas) {
    const { tarifa } = await tarifaDoPlano(db, linha.planoId);
    total += tarifa * linha.meses;
  }
  const { lastID } = await inserirFatura(db, contaId, total);
  return { faturaId: lastID, total };
}

// controllers/faturaController.js
async function emitir(req, res) {
  if (!req.body?.linhas?.length) return res.status(400).json({ erro: 'Fatura deve ter pelo menos 1 linha' });
  res.status(201).json(await faturaService.emitir(req.app.locals.db, req.body.contaId, req.body.linhas));
}

// routes/faturaRoutes.js: asyncHandler leva a rejeição ao handler de erro (T10)
router.post('/faturas', asyncHandler(faturaController.emitir));
```

---

## T04 — Hash de senha com algoritmo forte e salt (AP-04)

A verificação nunca lança exceção: um hash em formato inesperado devolve `False`, para o login responder 401 e não 500.

**Python — antes**
```python
import hashlib
def hash_senha(s):
    return hashlib.sha1(s.encode()).hexdigest()
```

**Python — depois** (biblioteca padrão)
```python
import hashlib
import hmac
import os

PARAMS = {"n": 2**14, "r": 8, "p": 1}

def gerar_hash(senha):
    sal = os.urandom(16)
    digest = hashlib.scrypt(senha.encode(), salt=sal, **PARAMS)
    return f"{sal.hex()}:{digest.hex()}"

def verificar_senha(senha, armazenado):
    try:
        sal_hex, digest_hex = armazenado.split(":")
        digest = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal_hex), **PARAMS)
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
```

**JavaScript — antes**
```js
function hashCaseiro(senha) {
  return Buffer.from(senha).toString('base64').split('').reverse().join('');
}
```

**JavaScript — depois**
```js
const crypto = require('crypto');

function gerarHash(senha) {
  const sal = crypto.randomBytes(16);
  return `${sal.toString('hex')}:${crypto.scryptSync(senha, sal, 64).toString('hex')}`;
}

function verificarSenha(senha, armazenado) {
  const [salHex, digestHex] = String(armazenado).split(':');
  if (!salHex || !digestHex) return false;
  const esperado = Buffer.from(digestHex, 'hex');
  const digest = crypto.scryptSync(senha, Buffer.from(salHex, 'hex'), 64);
  return esperado.length === digest.length && crypto.timingSafeEqual(digest, esperado);
}
```

**Atenção:** senhas antigas deixam de validar. Gere o hash no **seed**, mantendo as mesmas senhas em texto que o seed original usava, para os logins de exemplo continuarem funcionando. Registre a ação.

---

## T05 — Serialização explícita (AP-04)

**Python — antes**
```python
def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}   # inclui senha_hash
```

**Python — depois**
```python
# serializers/conta_serializer.py
def conta_publica(c):
    return {"id": c.id, "nome": c.nome, "email": c.email, "plano": c.plano}
```

**JavaScript — antes**
```js
res.json(conta);   // inclui senha_hash
```

**JavaScript — depois**
```js
// serializers/contaSerializer.js
const contaPublica = (c) => ({ id: c.id, nome: c.nome, email: c.email, plano: c.plano });
res.json(contaPublica(conta));
```

A remoção de um campo sensível da resposta é mudança intencional. Liste-a.

---

## T06 — Regra de negócio fora da rota (AP-05)

**Python — antes**
```python
@route("POST", "/assinaturas")
def assinar():
    meses = request.json["meses"]
    valor = TARIFA * meses
    if meses >= 12:
        valor *= 0.85
    ...
```

**Python — depois**
```python
# services/assinatura_service.py
DESCONTO_ANUAL = 0.15      # ver T12
MESES_PLANO_ANUAL = 12

def calcular_valor(tarifa, meses):
    valor = tarifa * meses
    if meses >= MESES_PLANO_ANUAL:
        valor *= 1 - DESCONTO_ANUAL
    return valor

# controllers/assinatura_controller.py
def assinar(request):
    valor = assinatura_service.calcular_valor(TARIFA, request.json["meses"])
    return json({"valor": valor}, 201)
```

**JavaScript — antes**
```js
app.post('/assinaturas', (req, res) => {
  let valor = TARIFA * req.body.meses;
  if (req.body.meses >= 12) valor *= 0.85;
  res.status(201).json({ valor });
});
```

**JavaScript — depois**
```js
// services/assinaturaService.js
const DESCONTO_ANUAL = 0.15;
const MESES_PLANO_ANUAL = 12;

function calcularValor(tarifa, meses) {
  const valor = tarifa * meses;
  return meses >= MESES_PLANO_ANUAL ? valor * (1 - DESCONTO_ANUAL) : valor;
}

// controllers/assinaturaController.js
const assinar = (req, res) =>
  res.status(201).json({ valor: assinaturaService.calcularValor(TARIFA, req.body.meses) });
```

---

## T07 — Estado global substituído por dependência injetada (AP-06)

**Python — antes**
```python
_conexao = None
def obter_conexao():
    global _conexao
    if _conexao is None:
        _conexao = driver.connect(CAMINHO_BANCO)   # uma conexão para todas as requisições
    return _conexao
```

**Python — depois** (uma conexão por requisição, fechada no fim)
```python
# models/banco.py
class Banco:
    def __init__(self, caminho):
        self._caminho = caminho

    def abrir(self):
        return driver.connect(self._caminho)

# entry point: o banco é criado uma vez; a conexão é aberta por requisição
banco = Banco(settings.CAMINHO_BANCO)

def antes_da_requisicao(contexto):
    contexto.conn = banco.abrir()

def depois_da_requisicao(contexto, erro=None):
    conn = getattr(contexto, "conn", None)
    if conn is not None:
        if erro is None:
            conn.commit()
        else:
            conn.rollback()   # escrita parcial não vaza para a próxima requisição
        conn.close()
```

Use os hooks de início e fim de requisição do framework para chamar essas duas funções.

**JavaScript — antes**
```js
let contadores = {};
function contar(chave) { contadores[chave] = (contadores[chave] || 0) + 1; }
```

**JavaScript — depois**
```js
// utils/contadores.js
class Contadores {
  #valores = new Map();
  contar(chave) { this.#valores.set(chave, (this.#valores.get(chave) || 0) + 1); }
  valor(chave) { return this.#valores.get(chave) || 0; }
}

// entry point
const contadores = new Contadores();
app.locals.contadores = contadores;   // injetado; nenhum módulo cria o próprio
```

---

## T08 — Guards de acesso por flag (AP-07)

Corrige todo AP-07 sem inventar um sistema de autenticação, o que mudaria o contrato de todos os clientes. A rota continua registrada. Cada rota sem autenticação recebe **um** dos três guards, conforme o sinal do finding:

| Guard | Flag (default `false`) | Rotas |
|---|---|---|
| administração | `ENABLE_ADMIN_ROUTES` | reset, drop, execução de SQL ou comando, exclusão em massa, relatório ou exportação (inclusive relatório financeiro ou de vendas) |
| leitura sensível | `ENABLE_SENSITIVE_READS` | GET que devolve registros de pessoas ou contas: dados pessoais (usuários, e-mails), pedidos, pagamentos, saldos |
| escrita | `ENABLE_WRITE_ROUTES` | POST, PUT, PATCH e DELETE comuns, incluindo as que dependem de um "login" cujo token ninguém verifica |

Com a flag desligada, a rota responde **403**. Com a flag ligada, exige o header `X-Admin-Token` igual a `ADMIN_TOKEN` (comparação em tempo constante); sem ele, **401**. As três flags compartilham a mesma fábrica de guard, para não triplicar código. Rotas de saúde, login e leituras públicas (catálogo, listagens sem dados pessoais) ficam sem guard. Um relatório agregado vai para administração mesmo quando mostra valores financeiros: a regra "relatório/exportação" vence a de "dados financeiros". Se ficar em dúvida se uma leitura comum é sensível, trate como sensível e registre em "Intentional changes".

**Python — antes**
```python
@route("POST", "/admin/limpar-faturas")
def limpar():
    db.execute("DELETE FROM faturas")
    return json({"ok": True})

@route("GET", "/clientes")
def listar_clientes(): ...

@route("POST", "/faturas")
def criar_fatura(): ...
```

**Python — depois**
```python
# middlewares/guards.py
import hmac

def exigir_flag(nome_flag):
    def decorador(handler):
        def envolvido(*args, **kwargs):
            if not getattr(settings, nome_flag):
                return json({"erro": "Recurso desabilitado"}, 403)
            token = request.headers.get("X-Admin-Token", "")
            if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
                return json({"erro": "Não autorizado"}, 401)
            return handler(*args, **kwargs)
        return envolvido
    return decorador

exigir_admin = exigir_flag("ENABLE_ADMIN_ROUTES")
exigir_leitura_sensivel = exigir_flag("ENABLE_SENSITIVE_READS")
exigir_escrita = exigir_flag("ENABLE_WRITE_ROUTES")

# routes/*.py
registrar("POST", "/admin/limpar-faturas", exigir_admin(admin_controller.limpar))
registrar("GET", "/clientes", exigir_leitura_sensivel(cliente_controller.listar))
registrar("POST", "/faturas", exigir_escrita(fatura_controller.criar))
```

**JavaScript — antes**
```js
app.post('/admin/limpar-faturas', (req, res) => {
  db.run('DELETE FROM faturas', () => res.json({ ok: true }));
});
app.get('/clientes', listarClientes);
app.post('/faturas', criarFatura);
```

**JavaScript — depois**
```js
// middlewares/guards.js
const crypto = require('crypto');

function exigirFlag(nomeFlag) {
  return (req, res, next) => {
    if (!settings[nomeFlag]) return res.status(403).json({ erro: 'Recurso desabilitado' });
    const token = Buffer.from(req.get('X-Admin-Token') || '');
    const esperado = Buffer.from(settings.adminToken || '');
    if (!esperado.length || token.length !== esperado.length || !crypto.timingSafeEqual(token, esperado)) {
      return res.status(401).json({ erro: 'Não autorizado' });
    }
    next();
  };
}

const exigirAdmin = exigirFlag('enableAdminRoutes');
const exigirLeituraSensivel = exigirFlag('enableSensitiveReads');
const exigirEscrita = exigirFlag('enableWriteRoutes');

// routes/*.js
router.post('/admin/limpar-faturas', exigirAdmin, adminController.limpar);
router.get('/clientes', exigirLeituraSensivel, clienteController.listar);
router.post('/faturas', exigirEscrita, faturaController.criar);
```

`ADMIN_TOKEN` é obrigatório (T01) quando qualquer uma das três flags estiver ligada.

**Conta existente identificada pelo corpo.** Se a rota reaproveita uma conta pelo e-mail ou id enviado **e o contrato original já envia a senha**, confira a senha contra o hash (T04) e responda 401 se faltar ou não bater; quem mandava a senha certa não percebe a mudança. Se o contrato não tem credencial do dono, não invente uma: o guard de escrita com o token já limita quem age em nome da conta.

```js
const user = await userModel.findByEmail(db, email);
if (user) {
  if (!password || !verifyPassword(password, user.passwordHash)) throw new DomainError('Credenciais inválidas', 401);
  return user.id;
}
```

**Validação:** chame cada rota protegida com as flags desligadas (espera 403) e com as flags ligadas e o token (espera o comportamento original). Registre os dois resultados. Toda rota que virou 403 vai para "Intentional changes".

---

## T09 — Consulta em lote no lugar de consulta por item (AP-08)

**Python — antes**
```python
faturas = conn.execute("SELECT * FROM faturas").fetchall()
for f in faturas:
    f["linhas"] = conn.execute("SELECT * FROM linhas_fatura WHERE fatura_id = ?", (f["id"],)).fetchall()
```

**Python — depois**
```python
from collections import defaultdict

faturas = [dict(f) for f in conn.execute("SELECT * FROM faturas").fetchall()]   # linhas do driver são imutáveis
ids = [f["id"] for f in faturas]
por_fatura = defaultdict(list)
if ids:
    marcadores = ",".join("?" * len(ids))   # só "?" gerados; nenhuma entrada do cliente
    for linha in conn.execute(f"SELECT * FROM linhas_fatura WHERE fatura_id IN ({marcadores})", ids):
        por_fatura[linha["fatura_id"]].append(dict(linha))
for f in faturas:
    f["linhas"] = por_fatura[f["id"]]
```

Com ORM, o equivalente é carregar a relação de forma antecipada (eager loading / `JOIN`) ou contar com `GROUP BY` em vez de carregar a lista.

**JavaScript — antes**
```js
for (const f of faturas) {
  f.linhas = await db.all('SELECT * FROM linhas_fatura WHERE fatura_id = ?', [f.id]);
}
```

**JavaScript — depois**
```js
const ids = faturas.map(f => f.id);
const porFatura = new Map(ids.map(id => [id, []]));
if (ids.length) {
  const marcadores = ids.map(() => '?').join(',');
  const linhas = await db.all(`SELECT * FROM linhas_fatura WHERE fatura_id IN (${marcadores})`, ids);
  for (const linha of linhas) porFatura.get(linha.fatura_id).push(linha);
}
faturas.forEach(f => { f.linhas = porFatura.get(f.id); });
```

A ordem dos itens no resultado precisa continuar a mesma do original. Se o original não ordenava, mantenha a ordem de inserção ou use `ORDER BY id`.

---

## T10 — Tratamento de erro central (AP-09)

O handler trata os erros de domínio e os não tratados. Os **erros HTTP nativos do framework** (404 de rota inexistente, 405, 415) passam sem alteração, para o contrato não mudar.

**Python — antes**
```python
try:
    return json(servico.executar(dados))
except:
    return json({"erro": "Erro interno"}, 500)
```

**Python — depois**
```python
# middlewares/erros.py
import logging
logger = logging.getLogger(__name__)

class ErroDeNegocio(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.status = status

def tratar_erro(erro):
    if isinstance(erro, ErroHttpDoFramework):   # a classe base de erros HTTP da stack
        return erro                             # mantém 404/405/415 como o framework faria
    if isinstance(erro, ErroDeNegocio):
        return json({"erro": str(erro)}, erro.status)
    logger.exception("Erro não tratado")
    return json({"erro": "Erro interno"}, 500)  # mensagem genérica; detalhe só no log

# serviço: lança o erro de domínio
if saldo < valor:
    raise ErroDeNegocio("Saldo insuficiente", 422)
```

Registre `tratar_erro` como handler global de exceções no entry point.

Com conexão por requisição (T07), o handler de 500 precisa **desfazer a transação** antes de responder. Em vários frameworks (Flask, por exemplo), quando um handler trata a exceção, o hook de fim de requisição recebe `erro=None` e faz commit da escrita parcial. Chame o rollback no próprio handler, ou abra a transação explicitamente no serviço que faz várias escritas:

```python
def tratar_erro(erro):
    ...
    desfazer_transacao_da_requisicao()   # ex.: contexto.conn.rollback()
    logger.exception("Erro não tratado")
    return json({"erro": "Erro interno"}, 500)
```

Teste: falha simulada no meio de uma escrita com várias operações → 500, e nada gravado.

**JavaScript — antes**
```js
app.post('/x', async (req, res) => {
  try { res.json(await servico.executar(req.body)); }
  catch (e) { res.status(500).json({ erro: e.message }); }
});
```

**JavaScript — depois**
```js
// middlewares/erros.js
class ErroDeNegocio extends Error {
  constructor(mensagem, status = 400) { super(mensagem); this.status = status; }
}

// Frameworks que não capturam rejeição de handler async precisam deste wrapper
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function tratarErro(erro, req, res, next) {
  if (erro instanceof ErroDeNegocio) return res.status(erro.status).json({ erro: erro.message });
  console.error('Erro não tratado', erro);
  res.status(500).json({ erro: 'Erro interno' });
}

// entry point: registrado por último
app.use(tratarErro);
```

**Atenção:** se uma resposta de erro mudar (500 que vira 400, texto que vira JSON), registre como mudança intencional.

---

## T11 — API obsoleta pelo equivalente moderno (AP-10)

**Python — antes**
```python
from datetime import datetime
emitida_em = Column(DateTime, default=datetime.utcnow)   # referência, não chamada
prazo_vencido = vencimento < datetime.utcnow()
```

**Python — depois**
```python
from datetime import datetime, timezone

def agora_utc():
    # Se o banco guarda datetime sem fuso, mantenha sem fuso para não comparar aware com naive
    return datetime.now(timezone.utc).replace(tzinfo=None)

emitida_em = Column(DateTime, default=agora_utc)
prazo_vencido = vencimento < agora_utc()
```

**JavaScript — antes**
```js
const payload = new Buffer(texto);
const partes = url.parse(endereco);
```

**JavaScript — depois**
```js
const payload = Buffer.from(texto, 'utf8');
const partes = new URL(endereco);
```

Para as demais entradas da tabela do AP-10, troque pelo equivalente da versão instalada e confirme na documentação dela.

---

## T12 — Constantes nomeadas no lugar de magic numbers (AP-11)

**Python — antes**
```python
if consumo > 20000:
    taxa = 0.08
elif consumo > 8000:
    taxa = 0.04
```

**Python — depois**
```python
# config/regras.py
FAIXAS_DE_TAXA = [(20_000, 0.08), (8_000, 0.04)]   # (acima de, taxa)

def taxa_por_consumo(consumo):
    for limite, taxa in FAIXAS_DE_TAXA:
        if consumo > limite:
            return taxa
    return 0
```

**JavaScript — antes**
```js
if (fatura.estado === 'QUITADA' && fatura.atraso > 30) multa = fatura.valor * 0.02;
```

**JavaScript — depois**
```js
// config/regras.js
const ESTADO_QUITADA = 'QUITADA';
const DIAS_CARENCIA = 30;
const TAXA_MULTA = 0.02;

if (fatura.estado === ESTADO_QUITADA && fatura.atraso > DIAS_CARENCIA) multa = fatura.valor * TAXA_MULTA;
```

---

## T13 — Logger no lugar de print (AP-04 e AP-12)

**Python — antes**
```python
print("Cobrança enviada para " + conta.email + " com token " + api_token)
```

**Python — depois**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Cobrança enviada: conta_id=%s", conta.id)   # sem e-mail, sem token
```

**JavaScript — antes**
```js
console.log(`Cobrando conta ${conta.email} com a chave ${settings.billingKey}`);
```

**JavaScript — depois**
```js
logger.info({ contaId: conta.id }, 'Cobrança enviada');   // ex.: pino; sem e-mail, sem chave
```

**Regra:** senha, chave, token e número de cartão nunca entram em log. Se for indispensável, use só os últimos dígitos.

---

## T14 — Nomes descritivos (AP-12)

**Python — antes**
```python
a, t, d = corpo["acc"], corpo["tkn"], corpo["dt"]
```

**Python — depois**
```python
# Os nomes de campo do contrato ("acc", "tkn", "dt") continuam; só a variável muda.
conta_id, token_acesso, data_inicio = corpo["acc"], corpo["tkn"], corpo["dt"]
```

**JavaScript — antes**
```js
const { acc: a, tkn: t } = req.body;
```

**JavaScript — depois**
```js
const { acc: contaId, tkn: tokenAcesso } = req.body;   // a entrada continua "acc" e "tkn"
```

---

## T15 — Remover código morto (AP-12)

**Python — antes**
```python
import re, math, csv   # math e csv sem uso

def esta_vencida(self):
    if self.vencimento:
        if self.vencimento < agora_utc():
            return True
        else:
            return False
    else:
        return False
```

**Python — depois**
```python
import re

def esta_vencida(self):
    return bool(self.vencimento) and self.vencimento < agora_utc()
```

**JavaScript — antes**
```js
const path = require('path');   // sem uso
let totalProcessado = 0;        // exportado e nunca lido
module.exports = { gerarFatura, totalProcessado };
```

**JavaScript — depois**
```js
module.exports = { gerarFatura };
```

Antes de remover, busque o nome no projeto inteiro. Se ninguém usa, remova.

---

## T16 — Extrair regra duplicada (AP-13)

Escolha a versão mais completa da regra como a única. Se as cópias divergiam, unificar muda o comportamento da cópia mais fraca: registre como mudança intencional.

**Python — antes**
```python
# criar_fatura
if valor <= 0: return erro("Valor inválido", 400)
if len(descricao) > 140: return erro("Descrição longa", 400)
# atualizar_fatura (cópia que esqueceu a descrição)
if valor <= 0: return erro("Valor inválido", 400)
```

**Python — depois**
```python
# validators/fatura_validator.py
def validar_fatura(dados):
    if dados.get("valor") is None or dados["valor"] <= 0:
        return "Valor inválido"
    if len(dados.get("descricao", "")) > 140:
        return "Descrição longa"
    return None

# nos dois controllers
mensagem = validar_fatura(dados)
if mensagem:
    return erro(mensagem, 400)
```

**JavaScript — antes**
```js
// três handlers repetem a mesma regra de "vencida"
const vencida = f.vencimento && new Date(f.vencimento) < new Date() && f.estado !== 'QUITADA';
```

**JavaScript — depois**
```js
// models/fatura.js
const estaVencida = (f, agora = new Date()) =>
  Boolean(f.vencimento) && new Date(f.vencimento) < agora && f.estado !== ESTADO_QUITADA;

// nos handlers
const vencida = estaVencida(f);
```

---

## T17 — Validar a entrada na borda (AP-14)

Tipo errado, faixa inválida e corpo ausente devolvem **400** com mensagem clara, nunca 500.

**Python — antes**
```python
dados = request.json
if dados["meses"] < 1:   # string -> TypeError -> 500; corpo null -> TypeError
    ...
```

**Python — depois**
```python
def inteiro_em_faixa(valor, minimo, maximo):
    return isinstance(valor, int) and not isinstance(valor, bool) and minimo <= valor <= maximo

dados = request.json
if not isinstance(dados, dict):
    return erro("Corpo JSON inválido", 400)
if not inteiro_em_faixa(dados.get("meses"), 1, 36):
    return erro("meses deve ser um inteiro entre 1 e 36", 400)
```

**JavaScript — antes**
```js
const total = req.body.quantidade * tarifa;   // aceita negativo, string e undefined
```

**JavaScript — depois**
```js
const quantidade = req.body?.quantidade;
if (!Number.isInteger(quantidade) || quantidade < 1) {
  return res.status(400).json({ erro: 'quantidade deve ser um inteiro positivo' });
}
const total = quantidade * tarifa;
```

**Atenção:** um caso que antes respondia 500 e agora responde 400 é mudança intencional. Já um caso que antes era aceito e passa a ser rejeitado muda o contrato. Só rejeite valores que o domínio claramente não permite (negativos, tipo errado) e registre.

---

## T18 — Configuração segura (AP-15)

**Python — antes**
```python
app.run(debug=True)
papel = dados.get("papel", "leitor")   # cliente escolhe virar administrador
```

**Python — depois**
```python
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)   # DEBUG vem do ambiente, default false

PAPEL_PADRAO = "leitor"
papel = PAPEL_PADRAO   # o papel não vem do cadastro público
if "papel" in dados and dados["papel"] != PAPEL_PADRAO and not requisitante_eh_admin(request):
    return erro("Sem permissão para definir papel", 403)
```

**JavaScript — antes**
```js
const senha = req.body.senha || 'senha-padrao';
```

**JavaScript — depois**
```js
const senha = req.body.senha;
if (!senha) return res.status(400).json({ erro: 'senha é obrigatória' });
```

**Atenção:**
- Se o original aceitava o campo de papel, rejeitá-lo é mudança intencional. Registre.
- Se a linha de base cria contas privilegiadas pelo endpoint público, a validação dessa chamada vai divergir de propósito.
- Debug desligado por default muda só o modo do servidor, não as respostas.

---

## Ordem de aplicação

Esta é a única ordem. O `SKILL.md` e as guidelines a seguem.

1. **Estrutura sem mudar lógica.** Crie a configuração, as camadas e o entry point, e mova o código para o lugar (T03). Suba a aplicação depois de cada domínio movido.
2. **Segurança.** T01, T02, T04 (com o seed refeito), T05, T08, T18.
3. **Regra e erros.** T06, T07, T10, T16, T17.
4. **Desempenho e limpeza.** T09, T11, T12, T13, T14, T15.

Depois de cada grupo, suba a aplicação e compare com o snapshot.
