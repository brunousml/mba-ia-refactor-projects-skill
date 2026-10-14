const isFilledString = (value) => typeof value === 'string' && value.trim() !== '';

// c_id aceita número inteiro positivo ou texto só com dígitos (o original aceitava os dois).
function parseCourseId(value) {
    if (Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) > 0) return Number(value);
    return null;
}

function createCheckoutController({ checkoutService }) {
    async function checkout(req, res) {
        // Os nomes de campo do contrato (usr, eml, pwd, c_id, card) ficam só aqui.
        const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card: cardNumber } = req.body ?? {};
        const courseId = parseCourseId(rawCourseId);

        const passwordIsValid = password === undefined || password === null || typeof password === 'string';
        if (!isFilledString(name) || !isFilledString(email) || !courseId || !isFilledString(cardNumber) || !passwordIsValid) {
            return res.status(400).send("Bad Request");
        }

        const { enrollmentId } = await checkoutService.checkout({ name, email, password, courseId, cardNumber });
        res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
    }

    return { checkout };
}

module.exports = { createCheckoutController };
