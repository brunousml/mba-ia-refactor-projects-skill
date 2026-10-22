const { APPROVED_CARD_PREFIX, PAYMENT_STATUS_PAID, PAYMENT_STATUS_DENIED } = require('../config/rules');
const logger = require('../utils/logger');

// Gateway simulado: aprova cartões com o prefixo configurado.
function authorize(cardNumber) {
    logger.info('Processando cartão', { cardLast4: cardNumber.slice(-4) });
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS_PAID : PAYMENT_STATUS_DENIED;
}

module.exports = { authorize };
