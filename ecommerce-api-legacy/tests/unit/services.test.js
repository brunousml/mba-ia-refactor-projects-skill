// Testes unitários das camadas novas: serviços e models sobre um banco SQLite em memória, sem HTTP.
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

const { openDatabase } = require('../../src/models/database');
const { initSchema } = require('../../src/models/schema');
const checkoutService = require('../../src/services/checkoutService');
const reportService = require('../../src/services/reportService');
const userService = require('../../src/services/userService');
const { DomainError } = require('../../src/errors/domainError');

const validOrder = {
  name: 'Guilherme',
  email: 'gui@fullcycle.com.br',
  password: 'senhaforte',
  courseId: 2,
  card: '4111222233334444',
};

let db;
beforeEach(async () => {
  db = openDatabase(':memory:');
  await initSchema(db);
});
afterEach(async () => {
  await db.close();
});

describe('schema', () => {
  it('cria as tabelas e o seed', async () => {
    const users = await db.all('SELECT id, name, email FROM users');
    assert.deepEqual(users, [{ id: 1, name: 'Leonan', email: 'leonan@fullcycle.com.br' }]);
    const courses = await db.all('SELECT title, price, active FROM courses ORDER BY id');
    assert.deepEqual(courses, [
      { title: 'Clean Architecture', price: 997, active: 1 },
      { title: 'Docker', price: 497, active: 1 },
    ]);
    const payment = await db.get('SELECT enrollment_id, amount, status FROM payments');
    assert.deepEqual(payment, { enrollment_id: 1, amount: 997, status: 'PAID' });
  });

  it('em produção não cria o usuário de exemplo nem a matrícula dele (AP-01)', async () => {
    const prod = await openDatabase(':memory:');
    try {
      await initSchema(prod, { appEnv: 'production' });
      assert.equal((await prod.get('SELECT COUNT(*) AS n FROM users')).n, 0);
      assert.equal((await prod.get('SELECT COUNT(*) AS n FROM enrollments')).n, 0);
      assert.equal((await prod.get('SELECT COUNT(*) AS n FROM payments')).n, 0);
      assert.equal((await prod.get('SELECT COUNT(*) AS n FROM courses')).n, 2);
    } finally {
      await prod.close();
    }
  });
});

describe('checkoutService', () => {
  it('cartão aprovado cria usuário, matrícula, pagamento e auditoria', async () => {
    const { enrollmentId } = await checkoutService.checkout(db, validOrder);
    assert.equal(enrollmentId, 2);
    const user = await db.get('SELECT id FROM users WHERE email = ?', [validOrder.email]);
    assert.ok(user);
    const enrollment = await db.get('SELECT user_id, course_id FROM enrollments WHERE id = ?', [enrollmentId]);
    assert.deepEqual(enrollment, { user_id: user.id, course_id: 2 });
    const payment = await db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enrollmentId]);
    assert.deepEqual(payment, { amount: 497, status: 'PAID' });
    const audit = await db.get('SELECT action FROM audit_logs');
    assert.equal(audit.action, `Checkout curso 2 por ${user.id}`);
  });

  it('e-mail existente com a senha correta reaproveita o usuário', async () => {
    await checkoutService.checkout(db, { ...validOrder, email: 'leonan@fullcycle.com.br', password: '123' });
    const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
    assert.equal(count, 1);
  });

  it('e-mail existente com senha errada ou ausente é recusado com 401', async () => {
    const { count: antes } = await db.get('SELECT COUNT(*) AS count FROM enrollments');
    for (const password of ['errada', undefined]) {
      await assert.rejects(
        checkoutService.checkout(db, { ...validOrder, email: 'leonan@fullcycle.com.br', password }),
        (err) => err instanceof DomainError && err.status === 401,
      );
    }
    const { count } = await db.get('SELECT COUNT(*) AS count FROM enrollments');
    assert.equal(count, antes);
  });

  it('cartão que não começa com 4 é recusado com erro de domínio 400', async () => {
    await assert.rejects(
      checkoutService.checkout(db, { ...validOrder, card: '5111222233334444' }),
      (err) => err instanceof DomainError && err.status === 400 && err.message === 'Pagamento recusado',
    );
    const { count } = await db.get('SELECT COUNT(*) AS count FROM payments');
    assert.equal(count, 1);
  });

  it('curso inexistente gera erro de domínio 404', async () => {
    await assert.rejects(
      checkoutService.checkout(db, { ...validOrder, courseId: 999 }),
      (err) => err instanceof DomainError && err.status === 404 && err.message === 'Curso não encontrado',
    );
  });
});

describe('reportService', () => {
  it('agrega receita e alunos por curso a partir do seed', async () => {
    const report = await reportService.financialReport(db);
    assert.deepEqual(report, [
      { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
      { course: 'Docker', revenue: 0, students: [] },
    ]);
  });

  it('soma só pagamentos PAID e mostra Unknown para aluno apagado', async () => {
    await checkoutService.checkout(db, validOrder);
    await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 2)");
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (3, 497, 'DENIED')");
    await userService.deleteUser(db, 2);
    const docker = (await reportService.financialReport(db)).find((c) => c.course === 'Docker');
    assert.equal(docker.revenue, 497);
    assert.deepEqual(
      [...docker.students].sort((a, b) => a.student.localeCompare(b.student)),
      [{ student: 'Leonan', paid: 497 }, { student: 'Unknown', paid: 497 }],
    );
  });
});

describe('userService', () => {
  it('apaga o usuário pelo id', async () => {
    await userService.deleteUser(db, 1);
    assert.equal(await db.get('SELECT id FROM users WHERE id = 1'), undefined);
  });

  it('id inexistente não gera erro', async () => {
    await userService.deleteUser(db, 999);
  });
});
