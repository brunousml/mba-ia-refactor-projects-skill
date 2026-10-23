const { DomainError } = require('../errors/domainError');
const { APPROVED_CARD_PREFIX, PAYMENT_STATUS } = require('../config/rules');
const { hashPassword, verifyPassword } = require('../utils/password');
const { logger, maskCard } = require('../utils/logger');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

function paymentStatusFor(card) {
    return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

async function findOrCreateUserId(db, { name, email, password }) {
    const user = await userModel.findByEmail(db, email);
    if (user) {
        // Conta existente: só o dono, com a senha, pode usá-la no checkout (AP-07).
        if (!password || !verifyPassword(password, user.passwordHash)) throw new DomainError('Credenciais inválidas', 401);
        return user.id;
    }
    if (!password) throw new DomainError('Senha obrigatória para novo usuário', 400);
    return (await userModel.create(db, { name, email, passwordHash: hashPassword(password) })).lastID;
}

async function checkout(db, { name, email, password, courseId, card }) {
    const course = await courseModel.findActiveById(db, courseId);
    if (!course) throw new DomainError('Curso não encontrado', 404);

    const userId = await findOrCreateUserId(db, { name, email, password });

    const status = paymentStatusFor(card);
    logger.info('Pagamento processado', { userId, courseId, card: maskCard(card), status });
    if (status === PAYMENT_STATUS.DENIED) throw new DomainError('Pagamento recusado', 400);

    const enrollmentId = (await enrollmentModel.create(db, { userId, courseId })).lastID;
    await paymentModel.create(db, { enrollmentId, amount: course.price, status });
    await auditLogModel.record(db, `Checkout curso ${courseId} por ${userId}`);

    return { enrollmentId };
}

module.exports = { checkout, paymentStatusFor };
