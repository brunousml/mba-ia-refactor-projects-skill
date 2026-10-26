// Testes unitários das peças de segurança: hash de senha (T04), guards por flag (T08),
// senha obrigatória (T18) e configuração sem segredo literal (T01).
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { hashPassword, verifyPassword } = require('../../src/utils/password');
const { requireFlag } = require('../../src/middlewares/guards');
const { openDatabase } = require('../../src/models/database');
const { initSchema } = require('../../src/models/schema');
const checkoutService = require('../../src/services/checkoutService');
const { DomainError } = require('../../src/errors/domainError');

describe('password', () => {
  it('gera hash com salt diferente do texto e verificável', () => {
    const a = hashPassword('senhaforte');
    const b = hashPassword('senhaforte');
    assert.notEqual(a, 'senhaforte');
    assert.notEqual(a, b);
    assert.equal(verifyPassword('senhaforte', a), true);
    assert.equal(verifyPassword('errada', a), false);
  });

  it('hash em formato inesperado não lança, devolve false', () => {
    assert.equal(verifyPassword('123', '123'), false);
    assert.equal(verifyPassword('123', null), false);
  });
});

describe('senhas no banco', () => {
  let db;
  beforeEach(async () => { db = openDatabase(':memory:'); await initSchema(db); });
  afterEach(async () => { await db.close(); });

  it('seed guarda hash da senha de exemplo 123', async () => {
    const { pass } = await db.get('SELECT pass FROM users WHERE id = 1');
    assert.notEqual(pass, '123');
    assert.equal(verifyPassword('123', pass), true);
  });

  it('checkout de usuário novo guarda hash forte', async () => {
    await checkoutService.checkout(db, {
      name: 'Gui', email: 'gui@x.com', password: 'senhaforte', courseId: 2, card: '4111222233334444',
    });
    const { pass } = await db.get('SELECT pass FROM users WHERE email = ?', ['gui@x.com']);
    assert.equal(verifyPassword('senhaforte', pass), true);
  });

  it('usuário novo sem senha é rejeitado com 400 (sem senha padrão)', async () => {
    await assert.rejects(
      checkoutService.checkout(db, { name: 'Gui', email: 'gui@x.com', courseId: 2, card: '4111222233334444' }),
      (err) => err instanceof DomainError && err.status === 400,
    );
    assert.equal(await db.get('SELECT id FROM users WHERE email = ?', ['gui@x.com']), undefined);
  });
});

describe('guards (T08)', () => {
  function call(guard, headers = {}) {
    const res = { statusCode: 200, status(c) { this.statusCode = c; return this; }, json(b) { this.body = b; return this; } };
    let nextCalled = false;
    guard({ get: (h) => headers[h.toLowerCase()] }, res, () => { nextCalled = true; });
    return { status: res.statusCode, nextCalled };
  }

  it('flag desligada responde 403', () => {
    assert.deepEqual(call(requireFlag(false, 'tok')), { status: 403, nextCalled: false });
  });
  it('flag ligada sem token ou com token errado responde 401', () => {
    assert.deepEqual(call(requireFlag(true, 'tok')), { status: 401, nextCalled: false });
    assert.deepEqual(call(requireFlag(true, 'tok'), { 'x-admin-token': 'outro' }), { status: 401, nextCalled: false });
  });
  it('flag ligada sem ADMIN_TOKEN configurado nunca libera', () => {
    assert.deepEqual(call(requireFlag(true, ''), { 'x-admin-token': '' }), { status: 401, nextCalled: false });
  });
  it('flag ligada com token certo chama o próximo', () => {
    assert.deepEqual(call(requireFlag(true, 'tok'), { 'x-admin-token': 'tok' }), { status: 200, nextCalled: true });
  });
});

describe('config (T01)', () => {
  it('nenhum segredo literal em src/', () => {
    const files = [];
    const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).forEach((e) =>
      (e.isDirectory() ? walk(path.join(d, e.name)) : files.push(path.join(d, e.name))));
    walk(path.join(__dirname, '..', '..', 'src'));
    for (const f of files) {
      const src = fs.readFileSync(f, 'utf8');
      assert.doesNotMatch(src, /pk_live_|senha_super_secreta|admin_master/, f);
    }
  });
});
