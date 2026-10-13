# Playbook de refatoração (Fase 3)

Quinze transformações, uma ou mais por anti-pattern. Cada uma mostra o código **antes** e **depois** em Python e em JavaScript. Aplique a transformação que corresponde ao finding do relatório, sem misturar outras no mesmo movimento.

Regras gerais:
- Preserve o contrato: método, caminho, status e nomes de campos da resposta.
- Depois de cada transformação, o boot precisa continuar sem erro.
- Quando a transformação altera comportamento observável por segurança, registre em "Intentional changes".

Índice: T01 credenciais · T02 SQL parametrizado · T03 separar camadas · T04 hash de senha · T05 serialização explícita · T06 regra no serviço · T07 dependência injetada · T08 guard de administração · T09 consulta em lote · T10 erro central · T11 API moderna · T12 constantes nomeadas · T13 logger · T14 nomes descritivos · T15 remover imports mortos.

---

## T01 — Credenciais para configuração por ambiente (AP-01)

**Python — antes**
```python
app.config["SECRET_KEY"] = "troque-isto-123"
DB_PASSWORD = "senha-do-banco-prod"
```

**Python — depois**
```python
# config/settings.py
import os

def _obrigatorio(nome):
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {nome}")
    return valor

SECRET_KEY = _obrigatorio("SECRET_KEY")
DB_PASSWORD = _obrigatorio("DB_PASSWORD")
PORT = int(os.environ.get("PORT", "8000"))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

**JavaScript — antes**
```js
const config = { dbPass: "senha-do-banco-prod", paymentKey: "pk_live_abc123" };
```

**JavaScript — depois**
```js
// config/settings.js
function obrigatorio(nome) {
  const valor = process.env[nome];
  if (!valor) throw new Error(`Variável de ambiente obrigatória ausente: ${nome}`);
  return valor;
}

module.exports = {
  dbPass: obrigatorio('DB_PASS'),
  paymentKey: obrigatorio('PAYMENT_KEY'),
  port: Number(process.env.PORT || 8000),
};
```

**Atenção:** o segredo que esteve no repositório precisa ser **rotacionado**. Trocar no código não invalida a cópia que já vazou. Registre isso no relatório.

---

## T02 — Consulta parametrizada no lugar de concatenação (AP-02)

**Python — antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Python — depois**
```python
# O placeholder depende do driver: ?, %s ou :nome
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?", (email, senha_hash))
```

**JavaScript — antes**
```js
db.all(`SELECT * FROM produtos WHERE nome LIKE '%${termo}%'`, (err, rows) => { /* ... */ });
```

**JavaScript — depois**
```js
// O placeholder depende do driver: ?, $1 ou @nome
db.all("SELECT * FROM produtos WHERE nome LIKE ?", [`%${termo}%`], (err, rows) => { /* ... */ });
```

**Identificadores dinâmicos** (nome de coluna, `ORDER BY`) não podem ser parâmetros. Use lista permitida:

```python
COLUNAS_ORDENAVEIS = {"nome", "preco", "criado_em"}
campo = request.args.get("ordenar", "nome")
if campo not in COLUNAS_ORDENAVEIS:
    campo = "nome"
cursor.execute(f"SELECT * FROM produtos ORDER BY {campo}")
```

---

## T03 — Separar um módulo que mistura camadas (AP-03)

**Python — antes** (um arquivo com SQL, regra e rota)
```python
# pedidos.py
@route("POST", "/pedidos")
def criar_pedido():
    dados = request.json
    total = 0
    for item in dados["itens"]:
        preco = db.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()[0]
        total += preco * item["quantidade"]
    db.execute("INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)", (dados["usuario_id"], total))
    return json({"total": total}, 201)
```

**Python — depois**
```python
# models/pedido_model.py: só acesso a dados
def preco_do_produto(produto_id):
    return db.execute("SELECT preco FROM produtos WHERE id = ?", (produto_id,)).fetchone()[0]

def inserir_pedido(usuario_id, total):
    cursor = db.execute("INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)", (usuario_id, total))
    return cursor.lastrowid

# services/pedido_service.py: regra de negócio
def criar(usuario_id, itens):
    total = sum(pedido_model.preco_do_produto(i["produto_id"]) * i["quantidade"] for i in itens)
    pedido_id = pedido_model.inserir_pedido(usuario_id, total)
    return {"pedido_id": pedido_id, "total": total}

# controllers/pedido_controller.py: adaptação HTTP
def criar(request):
    dados = request.json()
    if not dados.get("itens"):
        return erro("Pedido deve ter pelo menos 1 item", 400)
    return json(pedido_service.criar(dados["usuario_id"], dados["itens"]), 201)

# routes/pedido_routes.py: só registro
registrar("POST", "/pedidos", pedido_controller.criar)
```

**JavaScript — antes**
```js
app.post('/pedidos', (req, res) => {
  let total = 0;
  req.body.itens.forEach(i => { /* consulta + soma */ });
  db.run('INSERT INTO pedidos ...', [req.body.usuarioId, total], function () {
    res.status(201).json({ total });
  });
});
```

**JavaScript — depois**
```js
// models/pedidoModel.js
const precoDoProduto = (db, id) => db.get('SELECT preco FROM produtos WHERE id = ?', [id]);
const inserirPedido = (db, usuarioId, total) => db.run('INSERT INTO pedidos ...', [usuarioId, total]);

// services/pedidoService.js
async function criar(db, usuarioId, itens) {
  let total = 0;
  for (const item of itens) {
    const { preco } = await precoDoProduto(db, item.produtoId);
    total += preco * item.quantidade;
  }
  const { lastID } = await inserirPedido(db, usuarioId, total);
  return { pedidoId: lastID, total };
}

// controllers/pedidoController.js
async function criar(req, res) {
  if (!req.body.itens?.length) return res.status(400).json({ erro: 'Pedido deve ter pelo menos 1 item' });
  res.status(201).json(await pedidoService.criar(req.db, req.body.usuarioId, req.body.itens));
}

// routes/pedidoRoutes.js
router.post('/pedidos', pedidoController.criar);
```

---

## T04 — Hash de senha com algoritmo forte e salt (AP-04)

**Python — antes**
```python
import hashlib
def set_senha(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()
```

**Python — depois** (biblioteca padrão, sem dependência nova)
```python
import hashlib, hmac, os

def gerar_hash(senha):
    sal = os.urandom(16)
    digest = hashlib.scrypt(senha.encode(), salt=sal, n=2**14, r=8, p=1)
    return sal.hex() + ":" + digest.hex()

def verificar_senha(senha, armazenado):
    sal_hex, digest_hex = armazenado.split(":")
    digest = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(digest.hex(), digest_hex)
```

**JavaScript — antes**
```js
function hashCaseiro(senha) {
  let hash = '';
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}
```

**JavaScript — depois**
```js
const crypto = require('crypto');

function gerarHash(senha) {
  const sal = crypto.randomBytes(16);
  const digest = crypto.scryptSync(senha, sal, 64);
  return `${sal.toString('hex')}:${digest.toString('hex')}`;
}

function verificarSenha(senha, armazenado) {
  const [salHex, digestHex] = armazenado.split(':');
  const digest = crypto.scryptSync(senha, Buffer.from(salHex, 'hex'), 64);
  return crypto.timingSafeEqual(digest, Buffer.from(digestHex, 'hex'));
}
```

**Atenção:** senhas antigas deixam de validar. Recrie o seed com senhas novas e registre a ação. Se houver usuários reais, a migração precisa de reset de senha ou de verificação do hash antigo no primeiro login.

---

## T05 — Serialização explícita (AP-04)

**Python — antes**
```python
def to_dict(self):
    return {"id": self.id, "nome": self.nome, "email": self.email, "senha": self.senha}
```

**Python — depois**
```python
# serializers/usuario_serializer.py
def usuario_publico(u):
    return {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo}
```

**JavaScript — antes**
```js
res.json(usuario);   // inclui senha e hash
```

**JavaScript — depois**
```js
// serializers/usuarioSerializer.js
const usuarioPublico = (u) => ({ id: u.id, nome: u.nome, email: u.email, tipo: u.tipo });
res.json(usuarioPublico(usuario));
```

---

## T06 — Regra de negócio fora da rota (AP-05)

**Python — antes**
```python
@route("POST", "/checkout")
def checkout():
    total = sum(i["preco"] * i["qtd"] for i in dados["itens"])
    if total > 10000:
        total *= 0.9
    ...
```

**Python — depois**
```python
# services/checkout_service.py
DESCONTO_ACIMA_DE = 10_000   # ver T12
TAXA_DESCONTO = 0.10

def calcular_total(itens):
    total = sum(i["preco"] * i["qtd"] for i in itens)
    if total > DESCONTO_ACIMA_DE:
        total *= 1 - TAXA_DESCONTO
    return total

# controllers/checkout_controller.py
def checkout(request):
    total = checkout_service.calcular_total(request.json()["itens"])
    return json({"total": total})
```

**JavaScript — antes**
```js
app.post('/checkout', (req, res) => {
  let total = req.body.itens.reduce((s, i) => s + i.preco * i.qtd, 0);
  if (total > 10000) total *= 0.9;
  res.json({ total });
});
```

**JavaScript — depois**
```js
// services/checkoutService.js
const DESCONTO_ACIMA_DE = 10000;
const TAXA_DESCONTO = 0.1;

function calcularTotal(itens) {
  const total = itens.reduce((soma, i) => soma + i.preco * i.qtd, 0);
  return total > DESCONTO_ACIMA_DE ? total * (1 - TAXA_DESCONTO) : total;
}

// controllers/checkoutController.js
const checkout = (req, res) => res.json({ total: checkoutService.calcularTotal(req.body.itens) });
```

---

## T07 — Estado global substituído por instância injetada (AP-06)

**Python — antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = driver.connect(CAMINHO_BANCO)
    return db_connection
```

**Python — depois**
```python
# models/banco.py
class Banco:
    def __init__(self, caminho):
        self._caminho = caminho
        self._conexao = None

    def conexao(self):
        if self._conexao is None:
            self._conexao = conectar(self._caminho)
        return self._conexao

# entry point: cria uma vez e passa adiante
banco = Banco(settings.DB_PATH)
pedido_model = PedidoModel(banco)
```

**JavaScript — antes**
```js
let cache = {};
function registrar(chave, valor) { cache[chave] = valor; }
```

**JavaScript — depois**
```js
// utils/cache.js
class Cache {
  #itens = new Map();
  definir(chave, valor) { this.#itens.set(chave, valor); }
  obter(chave) { return this.#itens.get(chave); }
}

// entry point
const cache = new Cache();
const checkoutService = criarCheckoutService({ cache });
```

---

## T08 — Guard de administração (AP-07)

**Python — antes**
```python
@route("POST", "/admin/reset")
def reset():
    db.execute("DELETE FROM pedidos")
    return json({"ok": True})
```

**Python — depois**
```python
# middlewares/admin.py
def exigir_admin(handler):
    def envolvido(request, *args, **kwargs):
        if not settings.ENABLE_ADMIN_ROUTES:
            return json({"erro": "Recurso desabilitado"}, 403)
        if not verificar_token_admin(request.headers.get("Authorization", "")):
            return json({"erro": "Não autorizado"}, 401)
        return handler(request, *args, **kwargs)
    return envolvido

# routes/admin_routes.py
registrar("POST", "/admin/reset", exigir_admin(admin_controller.reset))
```

**JavaScript — antes**
```js
app.post('/admin/reset', (req, res) => {
  db.run('DELETE FROM pedidos', () => res.json({ ok: true }));
});
```

**JavaScript — depois**
```js
// middlewares/admin.js
function exigirAdmin(req, res, next) {
  if (!config.enableAdminRoutes) return res.status(403).json({ erro: 'Recurso desabilitado' });
  if (!verificarTokenAdmin(req.headers.authorization)) return res.status(401).json({ erro: 'Não autorizado' });
  next();
}

// routes/adminRoutes.js
router.post('/admin/reset', exigirAdmin, adminController.reset);
```

**Nota:** a flag `ENABLE_ADMIN_ROUTES` vem desligada por default. Registre no relatório que, sem a flag, a rota responde 403, e como ligá-la para testes.

---

## T09 — Consulta em lote no lugar de consulta por item (AP-08)

**Python — antes**
```python
pedidos = db.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    itens = db.execute("SELECT * FROM itens WHERE pedido_id = ?", (p["id"],)).fetchall()
    p["itens"] = itens
```

**Python — depois**
```python
from collections import defaultdict

pedidos = db.execute("SELECT * FROM pedidos").fetchall()
ids = [p["id"] for p in pedidos]
if ids:
    marcadores = ",".join("?" * len(ids))   # só "?" gerados, nenhuma entrada do usuário
    linhas = db.execute(f"SELECT * FROM itens WHERE pedido_id IN ({marcadores})", ids).fetchall()
    por_pedido = defaultdict(list)
    for linha in linhas:
        por_pedido[linha["pedido_id"]].append(linha)
    for p in pedidos:
        p["itens"] = por_pedido[p["id"]]
```

**JavaScript — antes**
```js
for (const p of pedidos) {
  p.itens = await db.all('SELECT * FROM itens WHERE pedido_id = ?', [p.id]);
}
```

**JavaScript — depois**
```js
const ids = pedidos.map(p => p.id);
if (ids.length) {
  const marcadores = ids.map(() => '?').join(',');
  const linhas = await db.all(`SELECT * FROM itens WHERE pedido_id IN (${marcadores})`, ids);
  const porPedido = new Map();
  for (const linha of linhas) {
    if (!porPedido.has(linha.pedido_id)) porPedido.set(linha.pedido_id, []);
    porPedido.get(linha.pedido_id).push(linha);
  }
  pedidos.forEach(p => { p.itens = porPedido.get(p.id) || []; });
}
```

---

## T10 — Tratamento de erro central (AP-09)

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
class ErroDeNegocio(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.status = status

def tratar_erro(erro):
    if isinstance(erro, ErroDeNegocio):
        return json({"erro": str(erro)}, erro.status)
    logger.exception("Erro não tratado")
    return json({"erro": "Erro interno"}, 500)

# serviço: lança o erro de domínio
if saldo < valor:
    raise ErroDeNegocio("Saldo insuficiente", 422)
```

**JavaScript — antes**
```js
app.post('/x', async (req, res) => {
  try { res.json(await servico.executar(req.body)); }
  catch (e) { res.status(500).json({ erro: 'Erro interno' }); }
});
```

**JavaScript — depois**
```js
// middlewares/erros.js
class ErroDeNegocio extends Error {
  constructor(mensagem, status = 400) { super(mensagem); this.status = status; }
}

function tratarErro(erro, req, res, next) {
  if (erro instanceof ErroDeNegocio) return res.status(erro.status).json({ erro: erro.message });
  logger.error({ err: erro }, 'Erro não tratado');
  res.status(500).json({ erro: 'Erro interno' });
}

// registrado por último no entry point
app.use(tratarErro);
```

**Atenção:** erros que hoje viram 500 e viram 400 com a mudança são alterações de comportamento. Liste-as.

---

## T11 — API obsoleta pelo equivalente moderno (AP-10)

**Python — antes**
```python
from datetime import datetime
agora = datetime.utcnow()
```

**Python — depois**
```python
from datetime import datetime, timezone
agora = datetime.now(timezone.utc)
# Se o banco guarda datetimes sem fuso, converta na borda, durante a transição:
agora_naive = agora.replace(tzinfo=None)
```

**JavaScript — antes**
```js
const buffer = new Buffer(texto);
```

**JavaScript — depois**
```js
const buffer = Buffer.from(texto, 'utf8');
```

Para as demais entradas da tabela de AP-10, aplique o mesmo critério: troque pelo equivalente da versão instalada e confirme na documentação da versão.

---

## T12 — Constantes nomeadas no lugar de magic numbers (AP-11)

**Python — antes**
```python
if total > 10000:
    desconto = total * 0.1
elif total > 5000:
    desconto = total * 0.05
```

**Python — depois**
```python
# config/regras.py
FAIXAS_DESCONTO = [(10_000, 0.10), (5_000, 0.05), (1_000, 0.02)]   # (acima de, taxa)

def calcular_desconto(total):
    for limite, taxa in FAIXAS_DESCONTO:
        if total > limite:
            return total * taxa
    return 0
```

**JavaScript — antes**
```js
if (status === 'PAID' && valor > 500) desconto = valor * 0.05;
```

**JavaScript — depois**
```js
// config/regras.js
const STATUS_PAGO = 'PAID';
const LIMITE_DESCONTO = 500;
const TAXA_DESCONTO = 0.05;

if (status === STATUS_PAGO && valor > LIMITE_DESCONTO) desconto = valor * TAXA_DESCONTO;
```

---

## T13 — Logger no lugar de print (AP-04 e AP-12)

**Python — antes**
```python
print("ENVIANDO EMAIL: pedido " + str(pedido_id) + " para " + email)
```

**Python — depois**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Notificação enviada: pedido=%s", pedido_id)   # sem e-mail completo, sem dado de pagamento
```

**JavaScript — antes**
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentKey}`);
```

**JavaScript — depois**
```js
// Logger estruturado (ex.: pino)
logger.info({ pedidoId, cartaoFinal: cc.slice(-4) }, 'Processando pagamento');
```

**Regra:** número de cartão, senha e chave nunca entram em log. Use só os últimos dígitos quando for indispensável.

---

## T14 — Nomes descritivos (AP-12)

**Python — antes**
```python
u, e, p = dados["usr"], dados["eml"], dados["pwd"]
```

**Python — depois**
```python
# Os nomes de campo da API continuam os mesmos; só a variável muda.
nome, email, senha = dados["usr"], dados["eml"], dados["pwd"]
```

**JavaScript — antes**
```js
let cc = req.body.card;
```

**JavaScript — depois**
```js
const numeroCartao = req.body.card;   // o campo de entrada continua "card"
```

**Regra:** mantenha os nomes de campo do contrato na borda (controller ou serializer). Renomeie apenas variáveis internas.

---

## T15 — Remover imports mortos (AP-12)

**Python — antes**
```python
import os, sys, json, datetime
from web import jsonify   # sem uso
```

**Python — depois**
```python
# Remova os imports que o linter marcar como não usados (F401 no ruff/pyflakes).
```

**JavaScript — antes**
```js
const fs = require('fs');   // não usado
const { config } = require('./utils');
```

**JavaScript — depois**
```js
const { config } = require('./utils');
// Confirme com o linter (no-unused-vars) antes de remover.
```

---

## Ordem de aplicação

1. T01 (segredos) antes de tudo: é o risco de maior impacto e não muda comportamento.
2. T02 (SQL) antes de mover código: o movimento copia a consulta, e ela já deve estar segura.
3. T04 e T05 (senha e serialização) junto com a recriação do seed.
4. T03, T06, T07 (estrutura e regra).
5. T08, T10 (guards e erros).
6. T09, T11, T12, T13, T14, T15 (limpeza sem mudança de contrato).

Depois de cada grupo, suba a aplicação e rode a comparação com o snapshot.
