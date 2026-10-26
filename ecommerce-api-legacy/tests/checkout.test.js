const { describe, test } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, AUTH } = require('./helpers/server');

const VALID = { usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444' };

async function withServer(env, fn) {
  const srv = env === undefined ? await startServer() : await startServer(env);
  try { await fn(srv); } finally { await srv.stop(); }
}

const checkout = (srv, body, headers = AUTH) => srv.request('POST', '/api/checkout', { body, headers });

async function report(srv) {
  const r = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
  assert.equal(r.status, 200);
  return r.json;
}
const course = (rep, title) => rep.find((c) => c.course === title);

describe('checkout - caracterização', () => {
  test('checkout válido de usuário novo responde 200 com msg Sucesso e enrollment_id numérico', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, VALID);
      assert.equal(r.status, 200);
      assert.equal(r.json.msg, 'Sucesso');
      assert.equal(typeof r.json.enrollment_id, 'number');
    }));

  test('checkout com e-mail existente e senha correta reaproveita o usuário e responde 200', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, { ...VALID, usr: 'Outro Nome', eml: 'leonan@fullcycle.com.br', pwd: '123' });
      assert.equal(r.status, 200);
      assert.equal(r.json.msg, 'Sucesso');
      const docker = course(await report(srv), 'Docker');
      assert.ok(docker.students.some((s) => s.student === 'Leonan'));
    }));

  test('usuário existente sem pwd responde 401 e não matricula (AP-07)', () =>
    withServer(undefined, async (srv) => {
      const { pwd, ...body } = VALID;
      const leonanNoCurso = async () => course(await report(srv), 'Docker').students.filter((s) => s.student === 'Leonan').length;
      const antes = await leonanNoCurso();
      const r = await checkout(srv, { ...body, eml: 'leonan@fullcycle.com.br' });
      assert.equal(r.status, 401);
      assert.equal(await leonanNoCurso(), antes);
    }));

  test('usuário existente com pwd errada responde 401 (AP-07)', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, { ...VALID, eml: 'leonan@fullcycle.com.br', pwd: 'errada' });
      assert.equal(r.status, 401);
    }));

  test('cartão que não começa com 4 responde 400 Pagamento recusado', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, { ...VALID, card: '5111222233334444' });
      assert.equal(r.status, 400);
      assert.equal(r.text, 'Pagamento recusado');
    }));

  for (const field of ['usr', 'eml', 'c_id', 'card']) {
    test(`checkout sem ${field} responde 400 Bad Request`, () =>
      withServer(undefined, async (srv) => {
        const body = { ...VALID };
        delete body[field];
        const r = await checkout(srv, body);
        assert.equal(r.status, 400);
        assert.equal(r.text, 'Bad Request');
      }));
  }

  test('checkout de curso inexistente responde 404 Curso não encontrado', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, { ...VALID, c_id: 999 });
      assert.equal(r.status, 404);
      assert.equal(r.text, 'Curso não encontrado');
    }));

  test('checkout válido aparece no relatório financeiro com aluno e receita somada', () =>
    withServer(undefined, async (srv) => {
      const before = course(await report(srv), 'Docker');
      const r = await checkout(srv, VALID);
      assert.equal(r.status, 200);
      const after = await report(srv);
      const docker = course(after, 'Docker');
      assert.equal(docker.revenue, before.revenue + 497);
      assert.ok(docker.students.some((s) => s.student === 'Guilherme' && s.paid === 497));
      assert.equal(course(after, 'Clean Architecture').revenue, 997);
    }));

  test('pagamento recusado não soma receita no relatório', () =>
    withServer(undefined, async (srv) => {
      const before = await report(srv);
      const r = await checkout(srv, { ...VALID, card: '5111222233334444' });
      assert.equal(r.status, 400);
      const after = await report(srv);
      for (const title of ['Docker', 'Clean Architecture']) {
        assert.equal(course(after, title).revenue, course(before, title).revenue);
      }
      assert.ok(!course(after, 'Docker').students.some((s) => s.student === 'Guilherme'));
    }));
});

describe('checkout - comportamento novo', () => {
  test('[novo] com flags desligadas o checkout responde 403', () =>
    withServer({}, async (srv) => {
      const r = await checkout(srv, VALID);
      assert.equal(r.status, 403);
    }));

  test('[novo] com escrita ligada e sem X-Admin-Token o checkout responde 401', () =>
    withServer({ ENABLE_WRITE_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' }, async (srv) => {
      const r = await checkout(srv, VALID, {});
      assert.equal(r.status, 401);
    }));

  test('[novo] com escrita ligada e X-Admin-Token errado o checkout responde 401', () =>
    withServer({ ENABLE_WRITE_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' }, async (srv) => {
      const r = await checkout(srv, VALID, { 'X-Admin-Token': 'errado' });
      assert.equal(r.status, 401);
    }));

  test('[novo] card numérico responde 400 e o servidor continua vivo', () =>
    withServer(undefined, async (srv) => {
      let r;
      try { r = await checkout(srv, { ...VALID, card: 4111222233334444 }); } catch (e) { r = { status: `erro de rede: ${e.message}` }; }
      assert.equal(r.status, 400);
      assert.ok(srv.alive(), 'processo do servidor morreu');
      const next = await checkout(srv, VALID);
      assert.equal(next.status, 200);
    }));

  for (const cid of ['abc', -1]) {
    test(`[novo] c_id não inteiro positivo (${JSON.stringify(cid)}) responde 400`, () =>
      withServer(undefined, async (srv) => {
        const r = await checkout(srv, { ...VALID, c_id: cid });
        assert.equal(r.status, 400);
      }));
  }

  test('[novo] usuário novo sem pwd responde 400 em vez de usar senha padrão', () =>
    withServer(undefined, async (srv) => {
      const { pwd, ...body } = VALID;
      const r = await checkout(srv, body);
      assert.equal(r.status, 400);
    }));

  test('[novo] checkout válido não escreve número do cartão nem chave pk_live_ no log', () =>
    withServer(undefined, async (srv) => {
      const r = await checkout(srv, VALID);
      assert.equal(r.status, 200);
      await new Promise((res) => setTimeout(res, 100));
      assert.ok(!srv.logs().includes(VALID.card), 'log contém o número do cartão');
      assert.ok(!srv.logs().includes('pk_live_'), 'log contém a chave do gateway');
    }));
});
