const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, AUTH } = require('./helpers/server');

const MSG = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';
const NEW_USER = {
  usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444',
};

function cleanArch(report) {
  return report.find((c) => c.course === 'Clean Architecture');
}

describe('DELETE /api/users/:id (caracterização)', () => {
  let srv;
  before(async () => { srv = await startServer(); });
  after(async () => { await srv.stop(); });

  it('apaga usuário existente: 200 com texto exato', async () => {
    const co = await srv.request('POST', '/api/checkout', { body: NEW_USER, headers: AUTH });
    assert.equal(co.status, 200);
    const r = await srv.request('DELETE', '/api/users/2', { headers: AUTH });
    assert.equal(r.status, 200);
    assert.equal(r.text, MSG);
  });

  it('usuário inexistente: 200 com o mesmo texto', async () => {
    const r = await srv.request('DELETE', '/api/users/999', { headers: AUTH });
    assert.equal(r.status, 200);
    assert.equal(r.text, MSG);
  });

  it('id não numérico ("abc"): 200 com o mesmo texto (comportamento atual)', async () => {
    const r = await srv.request('DELETE', '/api/users/abc', { headers: AUTH });
    assert.equal(r.status, 200);
    assert.equal(r.text, MSG);
  });
});

describe('DELETE /api/users/:id efeitos observáveis (caracterização)', () => {
  let srv;
  before(async () => { srv = await startServer(); });
  after(async () => { await srv.stop(); });

  it('após apagar o usuário 1, relatório mostra "Unknown" com paid e revenue 997 mantidos', async () => {
    const before = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
    assert.equal(before.status, 200);
    assert.deepEqual(cleanArch(before.json).students, [{ student: 'Leonan', paid: 997 }]);

    const del = await srv.request('DELETE', '/api/users/1', { headers: AUTH });
    assert.equal(del.status, 200);
    assert.equal(del.text, MSG);

    const r = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
    assert.equal(r.status, 200);
    const ca = cleanArch(r.json);
    assert.equal(ca.revenue, 997);
    assert.deepEqual(ca.students, [{ student: 'Unknown', paid: 997 }]);
  });

  it('após apagar, novo checkout com o mesmo e-mail recria o usuário (200)', async () => {
    const r = await srv.request('POST', '/api/checkout', {
      headers: AUTH,
      body: { usr: 'Leonan', eml: 'leonan@fullcycle.com.br', pwd: 'x', c_id: 2, card: '4111222233334444' },
    });
    assert.equal(r.status, 200);
    assert.equal(r.json.msg, 'Sucesso');
    const rep = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
    const docker = rep.json.find((c) => c.course === 'Docker');
    assert.deepEqual(docker.students, [{ student: 'Leonan', paid: 497 }]);
  });
});

describe('[novo] DELETE /api/users/:id com rotas admin desligadas', () => {
  let srv;
  before(async () => { srv = await startServer({}); });
  after(async () => { await srv.stop(); });

  it('[novo] flag desligada: DELETE responde 403 (mesmo com token)', async () => {
    const r = await srv.request('DELETE', '/api/users/1', { headers: AUTH });
    assert.equal(r.status, 403);
  });
});

describe('[novo] DELETE /api/users/:id exige token admin', () => {
  let srv;
  before(async () => {
    srv = await startServer({ ENABLE_ADMIN_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' });
  });
  after(async () => { await srv.stop(); });

  it('[novo] sem header: 401', async () => {
    const r = await srv.request('DELETE', '/api/users/1');
    assert.equal(r.status, 401);
  });

  it('[novo] token errado: 401', async () => {
    const r = await srv.request('DELETE', '/api/users/1', { headers: { 'X-Admin-Token': 'errado' } });
    assert.equal(r.status, 401);
  });

  it('[novo] após tentativas sem token válido, Leonan continua no relatório', async () => {
    const r = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
    assert.equal(r.status, 200);
    assert.deepEqual(cleanArch(r.json).students, [{ student: 'Leonan', paid: 997 }]);
  });
});
