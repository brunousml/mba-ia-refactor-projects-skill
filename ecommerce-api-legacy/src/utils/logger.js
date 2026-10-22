// Logger mínimo. Nunca recebe número de cartão, senha ou chave.
const write = (level, stream) => (message, meta) => {
    const line = `[${new Date().toISOString()}] ${level} ${message}`;
    stream(meta ? `${line} ${JSON.stringify(meta)}` : line);
};

module.exports = {
    info: write('INFO', console.log),
    warn: write('WARN', console.warn),
    error: write('ERROR', console.error),
};
