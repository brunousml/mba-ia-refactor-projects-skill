const { DomainError } = require('../errors/domainErrors');
const { logger } = require('../utils/logger');

// Registrado por último no entry point.
function errorHandler(err, req, res, next) {
    if (err instanceof DomainError) return res.status(err.status).send(err.message);
    // Erros HTTP nativos (ex.: JSON malformado do body-parser) seguem para o handler padrão do Express.
    if (err.status && err.status < 500) return next(err);
    logger.error('Erro não tratado', err);
    res.status(500).send('Erro interno');
}

module.exports = { errorHandler };
