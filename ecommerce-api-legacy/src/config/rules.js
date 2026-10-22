// Regras de negócio nomeadas.
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const UNKNOWN_STUDENT_NAME = 'Unknown';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, UNKNOWN_STUDENT_NAME };
