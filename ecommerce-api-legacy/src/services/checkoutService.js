const { DomainError } = require('../errors/domainErrors');
const { PAYMENT_STATUS } = require('../config/rules');
const { hashPassword, verifyPassword } = require('../utils/password');

function createCheckoutService({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService }) {
    // Usuário existente precisa da senha correta; usuário novo precisa informar uma senha.
    async function resolveUserId({ name, email, password }) {
        const user = await userModel.findCredentialsByEmail(email);
        if (user) {
            if (!verifyPassword(password, user.passwordHash)) throw new DomainError("Não autorizado", 401);
            return user.id;
        }
        if (!password) throw new DomainError("Senha obrigatória", 400);
        return userModel.create({ name, email, passwordHash: hashPassword(password) });
    }

    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = await courseModel.findActiveById(courseId);
        if (!course) throw new DomainError("Curso não encontrado", 404);

        const userId = await resolveUserId({ name, email, password });

        const status = paymentService.authorize({ cardNumber, courseId });
        if (status === PAYMENT_STATUS.DENIED) throw new DomainError("Pagamento recusado", 400);

        const enrollmentId = await enrollmentModel.create({ userId, courseId });
        await paymentModel.create({ enrollmentId, amount: course.price, status });
        await auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);

        return { enrollmentId };
    }

    return { checkout };
}

module.exports = { createCheckoutService };
