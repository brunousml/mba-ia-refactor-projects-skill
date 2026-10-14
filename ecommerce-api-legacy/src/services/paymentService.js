const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/rules');

// Gateway simulado: a aprovação depende só do prefixo do cartão.
function createPaymentService({ logger }) {
    function authorize({ cardNumber, courseId }) {
        logger.info(`Processando cartão final ${cardNumber.slice(-4)} para o curso ${courseId}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }

    return { authorize };
}

module.exports = { createPaymentService };
