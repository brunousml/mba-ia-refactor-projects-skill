// Domínio CHECKOUT: POST /api/checkout.
// Caracterização (verde no original com FLAGS_ON + token) e comportamento novo ([novo], vermelho no original).
const { test, describe, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, FLAGS_OFF } = require('./helpers/server');

const CARD_OK = '4111111111111111';
const CARD_DENIED = '5111111111111111';
const GATEWAY_KEY = 'pk_live_1234567890abcdef';

const novoUsuario = (over = {}) => ({
    usr: 'Maria',
    eml: 'maria@example.com',
    pwd: 'senhaForte!42',
    c_id: 2,
    card: CARD_OK,
    ...over,
});

const findCourse = (report, title) => report.find((c) => c.course === title);

// Faz a requisição sem deixar um erro de rede (processo derrubado) virar exceção não tratada.
async function safeRequest(server, method, path, opts) {
    try {
        return await server.request(method, path, opts);
    } catch (err) {
        return { status: undefined, text: '', networkError: err };
    }
}

describe('checkout - caracterização', () => {
    test('usuário novo com cartão iniciado em 4 retorna 200 com msg Sucesso e enrollment_id numérico', async () => {
        const server = await startServer();
        try {
            const res = await server.request('POST', '/api/checkout', { body: novoUsuario() });
            assert.equal(res.status, 200);
            assert.equal(res.json.msg, 'Sucesso');
            assert.equal(typeof res.json.enrollment_id, 'number');
        } finally {
            await server.stop();
        }
    });

    test('primeiro checkout num servidor novo gera enrollment_id 2 e o seguinte gera 3', async () => {
        const server = await startServer();
        try {
            const r1 = await server.request('POST', '/api/checkout', { body: novoUsuario() });
            assert.equal(r1.status, 200);
            assert.equal(r1.json.enrollment_id, 2);
            const r2 = await server.request('POST', '/api/checkout', {
                body: novoUsuario({ eml: 'outra@example.com', c_id: 1 }),
            });
            assert.equal(r2.status, 200);
            assert.equal(r2.json.enrollment_id, 3);
        } finally {
            await server.stop();
        }
    });

    test('usuário existente (e-mail do seed) matricula e aparece no relatório financeiro do curso Docker', async () => {
        const server = await startServer();
        try {
            const res = await server.request('POST', '/api/checkout', {
                body: novoUsuario({ usr: 'Leonan', eml: 'leonan@fullcycle.com.br', c_id: 2 }),
            });
            assert.equal(res.status, 200);
            assert.equal(res.json.msg, 'Sucesso');

            const rep = await server.request('GET', '/api/admin/financial-report');
            assert.equal(rep.status, 200);
            const docker = findCourse(rep.json, 'Docker');
            assert.ok(docker, 'curso Docker deve estar no relatório');
            assert.equal(docker.revenue, 497);
            assert.ok(docker.students.some((s) => s.student === 'Leonan' && s.paid === 497));
        } finally {
            await server.stop();
        }
    });

    test('cartão iniciado em 5 retorna 400 Pagamento recusado e não cria matrícula', async () => {
        const server = await startServer();
        try {
            const before = await server.request('GET', '/api/admin/financial-report');
            const res = await server.request('POST', '/api/checkout', {
                body: novoUsuario({ card: CARD_DENIED }),
            });
            assert.equal(res.status, 400);
            assert.equal(res.text, 'Pagamento recusado');

            const afterRep = await server.request('GET', '/api/admin/financial-report');
            for (const title of ['Clean Architecture', 'Docker']) {
                const a = findCourse(before.json, title);
                const b = findCourse(afterRep.json, title);
                assert.equal(b.revenue, a.revenue);
                assert.equal(b.students.length, a.students.length);
            }
            assert.equal(findCourse(afterRep.json, 'Docker').students.length, 0);
        } finally {
            await server.stop();
        }
    });

    describe('campos obrigatórios ausentes', () => {
        let server;
        before(async () => { server = await startServer(); });
        after(async () => { await server.stop(); });

        for (const field of ['usr', 'eml', 'c_id', 'card']) {
            test(`sem ${field} retorna 400 Bad Request`, async () => {
                const body = novoUsuario();
                delete body[field];
                const res = await server.request('POST', '/api/checkout', { body });
                assert.equal(res.status, 400);
                assert.equal(res.text, 'Bad Request');
            });
        }

        test('curso inexistente (c_id 99) retorna 404 Curso não encontrado', async () => {
            const res = await server.request('POST', '/api/checkout', { body: novoUsuario({ c_id: 99 }) });
            assert.equal(res.status, 404);
            assert.equal(res.text, 'Curso não encontrado');
        });
    });
});

describe('checkout - comportamento novo', () => {
    test('[novo] com flags desligadas o checkout retorna 403', async () => {
        const server = await startServer(FLAGS_OFF);
        try {
            const res = await server.request('POST', '/api/checkout', { body: novoUsuario() });
            assert.equal(res.status, 403);
        } finally {
            await server.stop();
        }
    });

    test('[novo] com flags ligadas e sem X-Admin-Token o checkout retorna 401', async () => {
        const server = await startServer();
        try {
            const res = await server.request('POST', '/api/checkout', { body: novoUsuario(), token: null });
            assert.equal(res.status, 401);
        } finally {
            await server.stop();
        }
    });

    test('[novo] cartão numérico (não string) retorna 400 sem derrubar o processo', async () => {
        const server = await startServer();
        try {
            const res = await safeRequest(server, 'POST', '/api/checkout', {
                body: novoUsuario({ card: 4111222233334444 }),
            });
            assert.equal(res.status, 400, `esperado 400; erro de rede: ${res.networkError?.message ?? '-'}`);
            assert.equal(server.exited, false, 'o processo não deve encerrar');
        } finally {
            await server.stop();
        }
    });

    test('[novo] usuário novo sem pwd retorna 400 (sem senha padrão)', async () => {
        const server = await startServer();
        try {
            const body = novoUsuario();
            delete body.pwd;
            const res = await server.request('POST', '/api/checkout', { body });
            assert.equal(res.status, 400);
        } finally {
            await server.stop();
        }
    });

    test('[novo] checkout válido não grava número do cartão nem chave do gateway nos logs', async () => {
        const server = await startServer();
        try {
            const res = await server.request('POST', '/api/checkout', { body: novoUsuario() });
            assert.equal(res.status, 200);
            await new Promise((r) => setTimeout(r, 100)); // deixa o stdout chegar
            assert.ok(!server.logs.includes(CARD_OK), 'logs não devem conter o número do cartão');
            assert.ok(!server.logs.includes(GATEWAY_KEY), 'logs não devem conter a chave do gateway');
        } finally {
            await server.stop();
        }
    });
});
