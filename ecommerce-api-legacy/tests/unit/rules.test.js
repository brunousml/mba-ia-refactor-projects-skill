// Grupo 3: regra de pagamento isolada (T06), erros de banco não mascarados (T10) e validação na borda (T17).
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const checkoutService = require('../../src/services/checkoutService');
const userService = require('../../src/services/userService');
const { parseCheckoutInput } = require('../../src/controllers/checkoutController');

const brokenDb = {
  get: () => Promise.reject(new Error('disk I/O error')),
  all: () => Promise.reject(new Error('disk I/O error')),
  run: () => Promise.reject(new Error('disk I/O error')),
};

describe('paymentStatusFor (T06)', () => {
  it('cartão que começa com 4 é aprovado; outro prefixo é recusado', () => {
    assert.equal(checkoutService.paymentStatusFor('4111222233334444'), 'PAID');
    assert.equal(checkoutService.paymentStatusFor('5111222233334444'), 'DENIED');
  });
});

describe('erros de banco (T10)', () => {
  it('falha de banco no checkout propaga, não vira 404', async () => {
    await assert.rejects(
      checkoutService.checkout(brokenDb, { name: 'a', email: 'a@a', password: 'x', courseId: 1, card: '4111' }),
      /disk I\/O error/,
    );
  });
  it('falha de banco ao apagar usuário propaga', async () => {
    await assert.rejects(userService.deleteUser(brokenDb, 1), /disk I\/O error/);
  });
});

describe('parseCheckoutInput (T17)', () => {
  const valid = { usr: 'Gui', eml: 'g@x.com', pwd: 's', c_id: 2, card: '4111222233334444' };

  it('aceita entrada válida e traduz para nomes internos', () => {
    assert.deepEqual(parseCheckoutInput(valid), {
      ok: true,
      value: { name: 'Gui', email: 'g@x.com', password: 's', courseId: 2, card: '4111222233334444' },
    });
  });
  it('aceita c_id como string de dígitos', () => {
    assert.equal(parseCheckoutInput({ ...valid, c_id: '2' }).value.courseId, 2);
  });
  it('rejeita card numérico, c_id inválido e corpo ausente', () => {
    assert.equal(parseCheckoutInput({ ...valid, card: 4111222233334444 }).ok, false);
    assert.equal(parseCheckoutInput({ ...valid, card: '41a1' }).ok, false);
    assert.equal(parseCheckoutInput({ ...valid, c_id: 'abc' }).ok, false);
    assert.equal(parseCheckoutInput({ ...valid, c_id: -1 }).ok, false);
    assert.equal(parseCheckoutInput({ ...valid, c_id: 1.5 }).ok, false);
    assert.equal(parseCheckoutInput(undefined).ok, false);
  });
  it('campo obrigatório ausente mantém a mensagem original Bad Request', () => {
    assert.deepEqual(parseCheckoutInput({ ...valid, usr: undefined }), { ok: false, message: 'Bad Request' });
  });
});
