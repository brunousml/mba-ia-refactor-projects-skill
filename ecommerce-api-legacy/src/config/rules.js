// Regras de domínio nomeadas (pagamento simulado e cursos).
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
const APPROVED_CARD_PREFIX = '4'; // gateway simulado: só cartões iniciados em 4 são aprovados
const COURSE_ACTIVE = 1;
const UNKNOWN_STUDENT = 'Unknown'; // matrícula cujo usuário foi apagado

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, COURSE_ACTIVE, UNKNOWN_STUDENT };
