// Token errado (T08): 401 com corpo exato do guard e nenhum efeito colateral.
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, ADMIN_TOKEN, AUTH } = require('./helpers/server');

const NAO_AUTORIZADO = { erro: 'Não autorizado' };
const ENV = { ENABLE_ADMIN_ROUTES: 'true', ENABLE_WRITE_ROUTES: 'true', ADMIN_TOKEN };
const NEW_STUDENT = {
  usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444',
};

// Mesmo tamanho do token esperado, conteúdo diferente; e tamanhos menor e maior.
const TOKENS_ERRADOS = {
  'mesmo tamanho': 'x'.repeat(ADMIN_TOKEN.length),
  'mais curto': 'x',
  'mais longo': `${ADMIN_TOKEN}-extra`,
};

const SEED = [
  { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
  { course: 'Docker', revenue: 0, students: [] },
];
const sorted = (rep) => [...rep].sort((a, b) => a.course.localeCompare(b.course));

async function withServer(fn) {
  const srv = await startServer(ENV);
  try { await fn(srv); } finally { await srv.stop(); }
}

async function relatorio(srv) {
  const r = await srv.request('GET', '/api/admin/financial-report', { headers: AUTH });
  assert.equal(r.status, 200);
  return sorted(r.json);
}

describe('token errado: POST /api/checkout', () => {
  for (const [rotulo, token] of Object.entries(TOKENS_ERRADOS)) {
    test(`[novo] token ${rotulo} responde 401 com corpo do guard e não matricula`, () =>
      withServer(async (srv) => {
        const r = await srv.request('POST', '/api/checkout', {
          body: NEW_STUDENT, headers: { 'X-Admin-Token': token },
        });
        assert.equal(r.status, 401);
        assert.deepEqual(r.json, NAO_AUTORIZADO);
        assert.deepEqual(await relatorio(srv), SEED);
      }));
  }
});

describe('token errado: DELETE /api/users/:id', () => {
  for (const [rotulo, token] of Object.entries(TOKENS_ERRADOS)) {
    test(`[novo] token ${rotulo} responde 401 com corpo do guard e o usuário permanece`, () =>
      withServer(async (srv) => {
        const r = await srv.request('DELETE', '/api/users/1', { headers: { 'X-Admin-Token': token } });
        assert.equal(r.status, 401);
        assert.deepEqual(r.json, NAO_AUTORIZADO);
        // Se o Leonan tivesse sido apagado, o relatório mostraria "Unknown".
        assert.deepEqual(await relatorio(srv), SEED);
      }));
  }
});
