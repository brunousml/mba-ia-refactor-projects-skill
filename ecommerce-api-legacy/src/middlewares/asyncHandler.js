// Express 4 não captura rejeição de handler async: encaminha para o handler central.
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

module.exports = { asyncHandler };
