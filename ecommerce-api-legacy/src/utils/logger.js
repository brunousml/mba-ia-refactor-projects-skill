// Logger mínimo: nunca recebe senha, chave ou número completo de cartão.
const format = (level, message, context) =>
    `[${new Date().toISOString()}] ${level} ${message}${context ? ' ' + JSON.stringify(context) : ''}`;

module.exports = {
    info: (message, context) => console.log(format('INFO', message, context)),
    error: (message, error) => console.error(format('ERROR', message), error),
};
