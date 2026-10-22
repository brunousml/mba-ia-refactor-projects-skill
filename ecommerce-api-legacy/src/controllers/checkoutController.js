const checkoutService = require('../services/checkoutService');

const isNonEmptyString = (value) => typeof value === 'string' && value.length > 0;
const isPositiveIntegerLike = (value) =>
    (Number.isInteger(value) && value > 0) || (typeof value === 'string' && /^[1-9]\d*$/.test(value));

async function checkout(req, res) {
    // Nomes do contrato (usr, eml, pwd, c_id, card) ficam só na borda.
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body || {};

    if (!isNonEmptyString(name) || !isNonEmptyString(email) || !isPositiveIntegerLike(courseId)
        || !isNonEmptyString(cardNumber) || (password !== undefined && typeof password !== 'string')) {
        return res.status(400).send('Bad Request');
    }

    const { enrollmentId } = await checkoutService.checkout(req.app.locals.db, {
        name, email, password, courseId: Number(courseId), cardNumber,
    });
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
}

module.exports = { checkout };
