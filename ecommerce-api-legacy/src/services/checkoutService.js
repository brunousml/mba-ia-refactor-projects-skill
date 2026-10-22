const { DomainError } = require('../errors/domainError');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/rules');

function createCheckoutService({ models, logger }) {
    // Gateway simulado: a decisão depende só do prefixo do cartão.
    const authorizePayment = (cardNumber) =>
        (cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED);

    async function findOrCreateUser({ name, email, password }) {
        const user = await models.users.findIdByEmail(email);
        if (user) return user.id;
        if (!password) throw new DomainError('Senha obrigatória para novo usuário', 400);
        return models.users.create({ name, email, passwordHash: hashPassword(password) });
    }

    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = await models.courses.findActiveById(courseId);
        if (!course) throw new DomainError('Curso não encontrado', 404);

        const userId = await findOrCreateUser({ name, email, password });

        logger.info('Processando pagamento', { courseId, userId });
        const status = authorizePayment(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new DomainError('Pagamento recusado', 400);

        const enrollmentId = await models.enrollments.create({ userId, courseId });
        await models.payments.create({ enrollmentId, amount: course.price, status });
        await models.auditLogs.record(`Checkout curso ${courseId} por ${userId}`);
        logger.info('Checkout concluído', { enrollmentId });

        return { enrollmentId };
    }

    return { checkout };
}

module.exports = { createCheckoutService };
