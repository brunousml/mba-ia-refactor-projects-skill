const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentService = require('./paymentService');
const { hashPassword } = require('../utils/password');
const { DomainError } = require('../errors/domainErrors');
const { PAYMENT_STATUS_DENIED } = require('../config/rules');

async function findOrCreateUser(db, name, email, password) {
    const user = await userModel.findIdByEmail(db, email);
    if (user) return user.id;
    if (!password) throw new DomainError('Senha obrigatória para novo usuário', 400);
    const { lastID } = await userModel.insert(db, name, email, hashPassword(password));
    return lastID;
}

async function checkout(db, { name, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(db, courseId);
    if (!course) throw new DomainError('Curso não encontrado', 404);

    const userId = await findOrCreateUser(db, name, email, password);

    const status = paymentService.authorize(cardNumber);
    if (status === PAYMENT_STATUS_DENIED) throw new DomainError('Pagamento recusado', 400);

    const { lastID: enrollmentId } = await enrollmentModel.insert(db, userId, courseId);
    await paymentModel.insert(db, enrollmentId, course.price, status);
    await auditLogModel.insert(db, `Checkout curso ${courseId} por ${userId}`);
    return { enrollmentId };
}

module.exports = { checkout };
