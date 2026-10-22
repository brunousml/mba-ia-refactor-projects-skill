const { test, describe, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, FLAGS_ON, FLAGS_OFF } = require('./helpers/server');

const DELETE_MSG = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

describe('usuários: caracterização (FLAGS_ON + token)', () => {
    test('DELETE /api/users/1 responde 200 com a mensagem original', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            const r = await s.request('DELETE', '/api/users/1');
            assert.equal(r.status, 200);
            assert.equal(r.text, DELETE_MSG);
        } finally { await s.stop(); }
    });

    test('após o delete, o relatório financeiro mostra o aluno como Unknown', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('DELETE', '/api/users/1')).status, 200);
            const r = await s.request('GET', '/api/admin/financial-report');
            assert.equal(r.status, 200);
            const course = r.json.find((c) => c.course === 'Clean Architecture');
            assert.ok(course, 'curso Clean Architecture presente');
            assert.equal(course.students.length, 1);
            assert.equal(course.students[0].student, 'Unknown');
        } finally { await s.stop(); }
    });

    test('após o delete, checkout com o mesmo email cria usuário novo e responde 200', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('DELETE', '/api/users/1')).status, 200);
            const r = await s.request('POST', '/api/checkout', {
                body: { usr: 'Leonan', eml: 'leonan@fullcycle.com.br', pwd: '123', c_id: 2, card: '4111222233334444' },
            });
            assert.equal(r.status, 200);
            assert.equal(r.json.msg, 'Sucesso');
        } finally { await s.stop(); }
    });

    test('GET /api/users/1 não existe (404 padrão do Express)', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('GET', '/api/users/1')).status, 404);
        } finally { await s.stop(); }
    });
});

describe('usuários: comportamento novo', () => {
    test('[novo] DELETE com flag desligada responde 403', async () => {
        const s = await startServer(FLAGS_OFF);
        try {
            assert.equal((await s.request('DELETE', '/api/users/1')).status, 403);
        } finally { await s.stop(); }
    });

    test('[novo] DELETE sem token responde 401', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('DELETE', '/api/users/1', { token: null })).status, 401);
        } finally { await s.stop(); }
    });

    test('[novo] DELETE de usuário inexistente responde 404', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('DELETE', '/api/users/999')).status, 404);
        } finally { await s.stop(); }
    });

    test('[novo] segundo DELETE do mesmo usuário responde 404', async () => {
        const s = await startServer(FLAGS_ON);
        try {
            assert.equal((await s.request('DELETE', '/api/users/1')).status, 200);
            assert.equal((await s.request('DELETE', '/api/users/1')).status, 404);
        } finally { await s.stop(); }
    });
});
