const { DomainError } = require('../errors/domainErrors');
const logger = require('../utils/logger');

// Respostas de erro continuam em texto puro, como no contrato original.
function errorHandler(err, req, res, next) {
    if (err instanceof DomainError) return res.status(err.status).send(err.message);
    if (err.type === 'entity.parse.failed') return next(err); // 400 nativo do Express (JSON inválido)
    logger.error('Erro não tratado', err);
    res.status(500).send('Erro interno');
}

module.exports = { errorHandler };
