// Relatório financeiro: GET /api/admin/financial-report.
// Cada teste sobe um servidor novo (banco em memória com seed) e para no fim.
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, AUTH } = require('./helpers/server');

const REPORT = '/api/admin/financial-report';
const NEW_STUDENT = {
  usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444',
};

async function withServer(env, fn) {
  const srv = env === undefined ? await startServer() : await startServer(env);
  try { await fn(srv); } finally { await srv.stop(); }
}

const byName = (a, b) => a.student.localeCompare(b.student);
// No original a ordem dos cursos segue o término das consultas assíncronas (curso sem
// matrícula sai primeiro), não o id. Comparamos como conjunto, ordenando pelo título.
const byCourse = (a, b) => a.course.localeCompare(b.course);
const sorted = (report) => [...report].sort(byCourse);
const getReport = (srv) => srv.request('GET', REPORT, { headers: AUTH });

describe('relatório financeiro: caracterização', () => {
  test('seed: estrutura, tipos e valores', () => withServer(undefined, async (srv) => {
    const res = await getReport(srv);
    assert.equal(res.status, 200);
    assert.ok(Array.isArray(res.json));
    for (const c of res.json) {
      assert.deepEqual(Object.keys(c).sort(), ['course', 'revenue', 'students']);
      assert.equal(typeof c.course, 'string');
      assert.equal(typeof c.revenue, 'number');
      assert.ok(Array.isArray(c.students));
      for (const s of c.students) {
        assert.deepEqual(Object.keys(s).sort(), ['paid', 'student']);
        assert.equal(typeof s.student, 'string');
        assert.equal(typeof s.paid, 'number');
      }
    }
    assert.deepEqual(sorted(res.json), [
      { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
      { course: 'Docker', revenue: 0, students: [] },
    ]);
  }));

  test('curso sem matrícula tem revenue 0 e students vazio', () => withServer(undefined, async (srv) => {
    const docker = (await getReport(srv)).json.find((c) => c.course === 'Docker');
    assert.equal(docker.revenue, 0);
    assert.deepEqual(docker.students, []);
  }));

  test('receita soma os checkouts pagos', () => withServer(undefined, async (srv) => {
    const co1 = await srv.request('POST', '/api/checkout', { body: NEW_STUDENT, headers: AUTH });
    assert.equal(co1.status, 200);
    const co2 = await srv.request('POST', '/api/checkout', {
      body: { ...NEW_STUDENT, c_id: 1 }, headers: AUTH,
    });
    assert.equal(co2.status, 200);
    const res = await getReport(srv);
    assert.equal(res.status, 200);
    const [clean, docker] = sorted(res.json);
    assert.deepEqual([clean.course, docker.course], ['Clean Architecture', 'Docker']);
    assert.equal(clean.revenue, 997 * 2);
    assert.deepEqual([...clean.students].sort(byName), [
      { student: 'Guilherme', paid: 997 }, { student: 'Leonan', paid: 997 },
    ]);
    assert.equal(docker.revenue, 497);
    assert.deepEqual(docker.students, [{ student: 'Guilherme', paid: 497 }]);
  }));

  test('pagamento recusado não entra no relatório', () => withServer(undefined, async (srv) => {
    const co = await srv.request('POST', '/api/checkout', {
      body: { ...NEW_STUDENT, card: '5111222233334444' }, headers: AUTH,
    });
    assert.equal(co.status, 400);
    const res = await getReport(srv);
    assert.deepEqual(sorted(res.json), [
      { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
      { course: 'Docker', revenue: 0, students: [] },
    ]);
  }));

  test('aluno apagado aparece como Unknown com paid mantido', () => withServer(undefined, async (srv) => {
    const co = await srv.request('POST', '/api/checkout', { body: NEW_STUDENT, headers: AUTH });
    assert.equal(co.status, 200);
    // Seed tem só o usuário 1; o novo aluno é o id 2.
    const del = await srv.request('DELETE', '/api/users/2', { headers: AUTH });
    assert.equal(del.status, 200);
    const res = await getReport(srv);
    const docker = res.json.find((c) => c.course === 'Docker');
    assert.equal(docker.revenue, 497);
    assert.deepEqual(docker.students, [{ student: 'Unknown', paid: 497 }]);
    const clean = res.json.find((c) => c.course === 'Clean Architecture');
    assert.deepEqual(clean.students, [{ student: 'Leonan', paid: 997 }]);
  }));

  test('resposta não expõe e-mail nem senha', () => withServer(undefined, async (srv) => {
    await srv.request('POST', '/api/checkout', { body: NEW_STUDENT, headers: AUTH });
    const res = await getReport(srv);
    assert.equal(res.status, 200);
    assert.ok(!res.text.includes('@'), 'relatório contém e-mail');
    assert.ok(!res.text.toLowerCase().includes('pass'), 'relatório contém senha');
    assert.ok(!res.text.includes('senhaforte'));
  }));

  test('flag ligada com token certo responde 200', () => withServer(
    { ENABLE_ADMIN_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' },
    async (srv) => {
      const res = await srv.request('GET', REPORT, { headers: { 'X-Admin-Token': 'test-admin-token' } });
      assert.equal(res.status, 200);
      assert.equal(res.json.length, 2);
    },
  ));
});

describe('relatório financeiro: guard admin (T08)', () => {
  test('[novo] flag desligada responde 403', () => withServer({}, async (srv) => {
    const res = await srv.request('GET', REPORT, { headers: AUTH });
    assert.equal(res.status, 403);
  }));

  test('[novo] flag ligada sem token responde 401', () => withServer(
    { ENABLE_ADMIN_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' },
    async (srv) => {
      const res = await srv.request('GET', REPORT);
      assert.equal(res.status, 401);
    },
  ));

  test('[novo] flag ligada com token errado responde 401', () => withServer(
    { ENABLE_ADMIN_ROUTES: 'true', ADMIN_TOKEN: 'test-admin-token' },
    async (srv) => {
      const res = await srv.request('GET', REPORT, { headers: { 'X-Admin-Token': 'errado' } });
      assert.equal(res.status, 401);
    },
  ));
});
