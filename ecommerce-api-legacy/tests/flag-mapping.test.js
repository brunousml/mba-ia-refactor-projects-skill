// Mapeamento flag -> rota (T08). Liga UMA flag por vez, com ADMIN_TOKEN e X-Admin-Token corretos.
// Rota da flag ligada não pode responder 403 "Recurso desabilitado"; as demais respondem 403.
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, ADMIN_TOKEN, AUTH } = require('./helpers/server');

const DESABILITADO = { erro: 'Recurso desabilitado' };
const BODY = {
  usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444',
};

const ROTAS = {
  checkout: (srv) => srv.request('POST', '/api/checkout', { body: BODY, headers: AUTH }),
  relatorio: (srv) => srv.request('GET', '/api/admin/financial-report', { headers: AUTH }),
  deleteUser: (srv) => srv.request('DELETE', '/api/users/999', { headers: AUTH }),
};

// Flag ligada -> rotas que ela libera (as outras duas flags liberam nenhuma das três).
const CASOS = [
  { flag: 'ENABLE_WRITE_ROUTES', libera: ['checkout'] },
  { flag: 'ENABLE_ADMIN_ROUTES', libera: ['relatorio', 'deleteUser'] },
  { flag: 'ENABLE_SENSITIVE_READS', libera: [] },
];

async function withServer(env, fn) {
  const srv = await startServer(env);
  try { await fn(srv); } finally { await srv.stop(); }
}

describe('mapeamento de flags: uma flag por vez', () => {
  for (const { flag, libera } of CASOS) {
    const nome = libera.length ? libera.join(' e ') : 'nenhuma rota';
    test(`${flag} sozinha libera ${nome} e mantém as demais em 403`, () =>
      withServer({ [flag]: 'true', ADMIN_TOKEN }, async (srv) => {
        for (const [rota, chamar] of Object.entries(ROTAS)) {
          const r = await chamar(srv);
          if (libera.includes(rota)) {
            assert.notEqual(r.status, 403, `${rota} deveria passar pelo guard com ${flag}`);
            assert.notEqual(r.status, 401, `${rota} deveria aceitar o token correto`);
            assert.notDeepEqual(r.json, DESABILITADO);
          } else {
            assert.equal(r.status, 403, `${rota} deveria estar bloqueada com só ${flag}`);
            assert.deepEqual(r.json, DESABILITADO);
          }
        }
      }));
  }
});
