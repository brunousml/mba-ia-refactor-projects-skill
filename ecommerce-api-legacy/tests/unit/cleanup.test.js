// Grupo 4: relatório sem N+1 (T09), constantes nomeadas (T12) e logger sem dado sensível (T13).
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

const { openDatabase } = require('../../src/models/database');
const { initSchema } = require('../../src/models/schema');
const checkoutService = require('../../src/services/checkoutService');
const reportService = require('../../src/services/reportService');
const rules = require('../../src/config/rules');
const { createLogger, maskCard } = require('../../src/utils/logger');

describe('reportService sem N+1 (T09)', () => {
  let db;
  beforeEach(async () => { db = openDatabase(':memory:'); await initSchema(db); });
  afterEach(async () => { await db.close(); });

  it('monta o relatório com uma única consulta, qualquer que seja o número de matrículas', async () => {
    for (let i = 0; i < 5; i++) {
      await checkoutService.checkout(db, { name: `A${i}`, email: `a${i}@x.com`, password: 'p', courseId: 2, card: '4111' });
    }
    let queries = 0;
    const counting = { ...db, get: (...a) => { queries++; return db.get(...a); }, all: (...a) => { queries++; return db.all(...a); } };
    const report = await reportService.financialReport(counting);
    assert.equal(queries, 1);
    const docker = report.find((c) => c.course === 'Docker');
    assert.equal(docker.revenue, 497 * 5);
    assert.equal(docker.students.length, 5);
  });
});

describe('rules (T12)', () => {
  it('expõe prefixo aprovado e status de pagamento nomeados', () => {
    assert.equal(rules.APPROVED_CARD_PREFIX, '4');
    assert.deepEqual(rules.PAYMENT_STATUS, { PAID: 'PAID', DENIED: 'DENIED' });
  });
});

describe('logger (T13)', () => {
  it('maskCard mantém só os 4 últimos dígitos', () => {
    assert.equal(maskCard('4111222233334444'), '****4444');
  });
  it('escreve nível e mensagem no destino injetado', () => {
    const lines = [];
    const logger = createLogger((l) => lines.push(l));
    logger.info('Pagamento processado', { enrollmentId: 2 });
    assert.equal(lines.length, 1);
    assert.match(lines[0], /INFO Pagamento processado \{"enrollmentId":2\}/);
  });
});
