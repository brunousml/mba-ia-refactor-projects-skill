const crypto = require('crypto');
const { logger } = require('../utils/logger');

const appEnv = process.env.APP_ENV || 'development';

// Segredo obrigatório: em produção a ausência derruba o boot; em desenvolvimento
// vira um valor aleatório com warning.
function secret(name) {
    if (process.env[name]) return process.env[name];
    if (appEnv === 'production') throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    logger.warn(`${name} não definida; usando valor aleatório de desenvolvimento`);
    return crypto.randomBytes(32).toString('hex');
}

const enableAdminRoutes = process.env.ENABLE_ADMIN_ROUTES === 'true';

const settings = {
    appEnv,
    port: Number(process.env.PORT || 3000), // mesmo default do projeto original
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '', // gateway simulado; vazio é aceito
    enableAdminRoutes,
    // Só exigido quando as rotas administrativas estão ligadas.
    adminToken: enableAdminRoutes ? secret('ADMIN_TOKEN') : '',
};

module.exports = { settings };
