// Logger mínimo com nível; nunca recebe senha, chave ou número de cartão completo.
const logger = {
    info: (message) => console.log(`[INFO] ${message}`),
    warn: (message) => console.warn(`[WARN] ${message}`),
    error: (message, err) => console.error(`[ERROR] ${message}`, err ?? ''),
};

module.exports = { logger };
