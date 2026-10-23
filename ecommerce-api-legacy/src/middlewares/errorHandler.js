const { DomainError } = require('../errors/domainError');
const { logger } = require('../utils/logger');

// Handler central (T10). O contrato original responde erros em texto puro; o handler mantém esse formato.
// Erro não tratado vira 500 genérico, com o detalhe só no log do servidor.
function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);
    if (err instanceof DomainError) return res.status(err.status).send(err.message);
    if (err.type === 'entity.parse.failed') return res.status(400).send("Bad Request");
    logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.stack || String(err) });
    res.status(500).send("Erro interno");
}

module.exports = { errorHandler };
