// Testes do domínio RELATÓRIO FINANCEIRO (GET /api/admin/financial-report).
// A ordem dos cursos no array não é determinística: as asserções localizam o curso pelo nome.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, FLAGS_OFF } = require('./helpers/server');

const URL = '/api/admin/financial-report';

function byCourse(report, name) {
    const item = report.find((r) => r.course === name);
    assert.ok(item, `curso ${name} ausente do relatório`);
    return item;
}

async function withServer(env, fn) {
    const server = await startServer(env);
    try { await fn(server); } finally { await server.stop(); }
}

test('estado inicial: 2 cursos com receita e alunos do seed', () => withServer(undefined, async (s) => {
    const res = await s.request('GET', URL);
    assert.equal(res.status, 200);
    assert.ok(Array.isArray(res.json));
    assert.equal(res.json.length, 2);
    for (const item of res.json) {
        assert.deepEqual(Object.keys(item).sort(), ['course', 'revenue', 'students']);
    }
    const clean = byCourse(res.json, 'Clean Architecture');
    assert.equal(clean.revenue, 997);
    assert.deepEqual(clean.students, [{ student: 'Leonan', paid: 997 }]);
    const docker = byCourse(res.json, 'Docker');
    assert.equal(docker.revenue, 0);
    assert.deepEqual(docker.students, []);
}));

test('checkout aprovado de usuário novo entra na receita do Docker', () => withServer(undefined, async (s) => {
    const co = await s.request('POST', '/api/checkout', {
        body: { usr: 'Maria', eml: 'maria@test.com', pwd: 'senha', c_id: 2, card: '4111222233334444' },
    });
    assert.equal(co.status, 200);
    const res = await s.request('GET', URL);
    assert.equal(res.status, 200);
    const docker = byCourse(res.json, 'Docker');
    assert.equal(docker.revenue, 497);
    assert.deepEqual(docker.students, [{ student: 'Maria', paid: 497 }]);
    assert.equal(byCourse(res.json, 'Clean Architecture').revenue, 997);
}));

test('pagamento recusado não altera a receita', () => withServer(undefined, async (s) => {
    const co = await s.request('POST', '/api/checkout', {
        body: { usr: 'Joao', eml: 'joao@test.com', pwd: 'senha', c_id: 2, card: '5111222233334444' },
    });
    assert.equal(co.status, 400);
    const res = await s.request('GET', URL);
    assert.equal(res.status, 200);
    const docker = byCourse(res.json, 'Docker');
    assert.equal(docker.revenue, 0);
    assert.deepEqual(docker.students, []);
    assert.equal(byCourse(res.json, 'Clean Architecture').revenue, 997);
}));

test('após deletar o usuário, aluno aparece como Unknown e receita se mantém', () => withServer(undefined, async (s) => {
    const del = await s.request('DELETE', '/api/users/1');
    assert.equal(del.status, 200);
    const res = await s.request('GET', URL);
    assert.equal(res.status, 200);
    const clean = byCourse(res.json, 'Clean Architecture');
    assert.equal(clean.revenue, 997);
    assert.deepEqual(clean.students, [{ student: 'Unknown', paid: 997 }]);
}));

test('[novo] flag desligada responde 403', () => withServer(FLAGS_OFF, async (s) => {
    const res = await s.request('GET', URL);
    assert.equal(res.status, 403);
}));

test('[novo] flag ligada sem token responde 401', () => withServer(undefined, async (s) => {
    const res = await s.request('GET', URL, { token: null });
    assert.equal(res.status, 401);
}));

test('[novo] flag ligada com token errado responde 401', () => withServer(undefined, async (s) => {
    const res = await s.request('GET', URL, { token: 'token-errado' });
    assert.equal(res.status, 401);
}));
