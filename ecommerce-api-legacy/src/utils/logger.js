// Logger mínimo (T13). Regra: senha, chave, token e número de cartão nunca entram no log.
function createLogger(write = console.log) {
    const log = (level) => (message, context) =>
        write(`${new Date().toISOString()} ${level} ${message}${context ? ` ${JSON.stringify(context)}` : ''}`);
    return { info: log('INFO'), warn: log('WARN'), error: log('ERROR') };
}

const maskCard = (card) => `****${String(card).slice(-4)}`;

module.exports = { createLogger, maskCard, logger: createLogger() };
