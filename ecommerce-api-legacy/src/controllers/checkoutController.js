const checkoutService = require('../services/checkoutService');

const isPositiveInteger = (value) => Number.isInteger(value) && value > 0;

// Validação de formato na borda (T17). Os nomes curtos (usr, eml, pwd, c_id, card) são o contrato da API;
// internamente usamos nomes descritivos.
function parseCheckoutInput(body) {
    const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card } = body || {};
    if (!name || !email || !rawCourseId || !card) return { ok: false, message: "Bad Request" };
    if (typeof name !== 'string' || typeof email !== 'string') return { ok: false, message: "usr e eml devem ser texto" };
    if (password !== undefined && password !== null && typeof password !== 'string') return { ok: false, message: "pwd deve ser texto" };
    if (typeof card !== 'string' || !/^\d+$/.test(card)) return { ok: false, message: "card deve conter apenas dígitos" };

    const courseId = typeof rawCourseId === 'string' && /^\d+$/.test(rawCourseId) ? Number(rawCourseId) : rawCourseId;
    if (!isPositiveInteger(courseId)) return { ok: false, message: "c_id deve ser um inteiro positivo" };

    return { ok: true, value: { name, email, password: password || undefined, courseId, card } };
}

async function checkout(req, res) {
    const input = parseCheckoutInput(req.body);
    if (!input.ok) return res.status(400).send(input.message);

    const { enrollmentId } = await checkoutService.checkout(req.app.locals.db, input.value);
    res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
}

module.exports = { checkout, parseCheckoutInput };
