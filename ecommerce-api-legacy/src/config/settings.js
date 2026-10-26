// Configuração lida do ambiente uma vez, no boot. Nenhum segredo fica no código (T01).
const crypto = require('crypto');
const { logger } = require('../utils/logger');

const appEnv = process.env.APP_ENV || 'development';
const flag = (name) => (process.env[name] || 'false').toLowerCase() === 'true';

function secret(name) {
    if (process.env[name]) return process.env[name];
    if (appEnv === 'production') throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    logger.warn(`${name} não definida; usando valor aleatório de desenvolvimento`);
    return crypto.randomBytes(32).toString('hex');
}

const enableAdminRoutes = flag('ENABLE_ADMIN_ROUTES');
const enableSensitiveReads = flag('ENABLE_SENSITIVE_READS');
const enableWriteRoutes = flag('ENABLE_WRITE_ROUTES');
const anyGuardEnabled = enableAdminRoutes || enableSensitiveReads || enableWriteRoutes;

module.exports = {
    appEnv,
    port: Number(process.env.PORT || 3000),
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    enableAdminRoutes,
    enableSensitiveReads,
    enableWriteRoutes,
    // Só é exigido quando alguma rota guardada está ligada.
    adminToken: anyGuardEnabled ? secret('ADMIN_TOKEN') : '',
};
