// Unitários das camadas novas: serviços e models com banco em memória, sem HTTP.
const { test } = require('node:test');
const assert = require('node:assert/strict');

const { openDatabase } = require('../../src/models/database');
const { initSchema } = require('../../src/models/schema');
const { createModels } = require('../../src/models');
const { createCheckoutService } = require('../../src/services/checkoutService');
const { createReportService } = require('../../src/services/reportService');
const { createUserService } = require('../../src/services/userService');
const { DomainError } = require('../../src/errors/domainError');
const { hashPassword, verifyPassword } = require('../../src/utils/password');

const silentLogger = { info() {}, warn() {}, error() {} };

async function setup() {
    const db = openDatabase(':memory:');
    await initSchema(db);
    const models = createModels(db);
    return {
        db,
        models,
        checkout: createCheckoutService({ models, logger: silentLogger }),
        report: createReportService({ models }),
        users: createUserService({ models }),
    };
}

const byCourse = (report, title) => report.find((c) => c.course === title);

test('hash de senha é salgado e verificável', () => {
    const a = hashPassword('123');
    const b = hashPassword('123');
    assert.notEqual(a, '123');
    assert.notEqual(a, b);
    assert.equal(verifyPassword('123', a), true);
    assert.equal(verifyPassword('errada', a), false);
    assert.equal(verifyPassword('123', 'formato-invalido'), false);
});

test('seed grava a senha do usuário de exemplo com hash', async () => {
    const { db } = await setup();
    const user = await db.get('SELECT pass FROM users WHERE id = 1');
    assert.notEqual(user.pass, '123');
    assert.equal(verifyPassword('123', user.pass), true);
});

test('checkout aprovado cria usuário, matrícula, pagamento e auditoria', async () => {
    const { db, checkout } = await setup();
    const result = await checkout.checkout({
        name: 'Ana', email: 'ana@x.com', password: 's3nha', courseId: 2, cardNumber: '4111222233334444',
    });
    assert.equal(result.enrollmentId, 2);
    const user = await db.get('SELECT pass FROM users WHERE email = ?', ['ana@x.com']);
    assert.equal(verifyPassword('s3nha', user.pass), true);
    const payment = await db.get('SELECT amount, status FROM payments WHERE enrollment_id = 2');
    assert.deepEqual({ ...payment }, { amount: 497, status: 'PAID' });
    const audit = await db.get('SELECT COUNT(*) AS n FROM audit_logs');
    assert.equal(audit.n, 1);
});

test('checkout com cartão recusado lança 400 sem criar matrícula', async () => {
    const { db, checkout } = await setup();
    await assert.rejects(
        checkout.checkout({ name: 'Ana', email: 'ana@x.com', password: 'x', courseId: 1, cardNumber: '5111' }),
        (e) => e instanceof DomainError && e.status === 400 && e.message === 'Pagamento recusado',
    );
    const row = await db.get('SELECT COUNT(*) AS n FROM enrollments');
    assert.equal(row.n, 1);
});

test('checkout de curso inexistente lança 404', async () => {
    const { checkout } = await setup();
    await assert.rejects(
        checkout.checkout({ name: 'Ana', email: 'ana@x.com', password: 'x', courseId: 99, cardNumber: '4111' }),
        (e) => e instanceof DomainError && e.status === 404,
    );
});

test('checkout de usuário novo sem senha lança 400', async () => {
    const { checkout } = await setup();
    await assert.rejects(
        checkout.checkout({ name: 'Ana', email: 'ana@x.com', courseId: 1, cardNumber: '4111' }),
        (e) => e instanceof DomainError && e.status === 400,
    );
});

test('relatório soma só pagamentos PAID e lista alunos por curso', async () => {
    const { db, report } = await setup();
    await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 2)");
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (2, 497, 'DENIED')");
    const result = await report.financialReport();
    assert.equal(result.length, 2);
    assert.deepEqual(byCourse(result, 'Clean Architecture'), {
        course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }],
    });
    assert.deepEqual(byCourse(result, 'Docker'), {
        course: 'Docker', revenue: 0, students: [{ student: 'Leonan', paid: 497 }],
    });
});

test('exclusão de usuário inexistente lança 404', async () => {
    const { users } = await setup();
    await users.deleteUser(1);
    await assert.rejects(users.deleteUser(1), (e) => e instanceof DomainError && e.status === 404);
});
