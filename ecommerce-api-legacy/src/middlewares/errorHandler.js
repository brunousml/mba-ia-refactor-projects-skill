const { DomainError } = require('../errors/domainError');

// Erros de domínio mantêm o contrato original (texto puro). Erros HTTP do Express (ex.: JSON malformado) passam com o status dele.
function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof DomainError) return res.status(err.status).send(err.message);
        if (err.status && err.status >= 400 && err.status < 500) return res.status(err.status).send('Bad Request');
        logger.error('Erro não tratado', { message: err.message, stack: err.stack });
        res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
