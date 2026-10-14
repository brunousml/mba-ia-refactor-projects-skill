// Express 4 não captura rejeição de handler async; o wrapper leva o erro ao handler central.
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

module.exports = { asyncHandler };
