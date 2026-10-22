const { DomainError } = require('../errors/domainError');

const isFilledString = (value) => typeof value === 'string' && value.trim() !== '';
const isCourseId = (value) => Number.isInteger(Number(value)) && String(value).trim() !== '';

// A API recebe nomes abreviados (usr, eml, pwd, c_id, card); dentro das camadas os nomes são descritivos.
function readCheckoutInput(body = {}) {
    const { usr, eml, pwd, c_id: courseId, card } = body;
    if (!usr || !eml || !courseId || !card) throw new DomainError('Bad Request', 400);
    if (!isFilledString(usr) || !isFilledString(eml) || !isCourseId(courseId) || !isFilledString(card)) {
        throw new DomainError('Bad Request', 400);
    }
    if (pwd !== undefined && typeof pwd !== 'string') throw new DomainError('Bad Request', 400);
    return { name: usr, email: eml, password: pwd, courseId: Number(courseId), cardNumber: card };
}

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const { enrollmentId } = await checkoutService.checkout(readCheckoutInput(req.body));
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
