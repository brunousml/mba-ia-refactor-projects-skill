const crypto = require('crypto');

const appEnv = process.env.APP_ENV || 'development';

function secret(name) {
    if (process.env[name]) return process.env[name];
    if (appEnv === 'production') throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    console.warn(`${name} não definida; usando valor aleatório de desenvolvimento`);
    return crypto.randomBytes(32).toString('hex');
}

const flag = (name) => (process.env[name] || 'false').toLowerCase() === 'true';

const enableAdminRoutes = flag('ENABLE_ADMIN_ROUTES');
const enableSensitiveReads = flag('ENABLE_SENSITIVE_READS');
const enableWriteRoutes = flag('ENABLE_WRITE_ROUTES');
const anyFlagOn = enableAdminRoutes || enableSensitiveReads || enableWriteRoutes;

// ADMIN_TOKEN é obrigatório quando alguma flag está ligada; sem flag, fica vazio e os guards respondem 403.
if (anyFlagOn && !process.env.ADMIN_TOKEN && appEnv === 'production') {
    throw new Error('ADMIN_TOKEN é obrigatório quando alguma flag ENABLE_* está ligada');
}

module.exports = {
    appEnv,
    port: Number(process.env.PORT || 3000),
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: anyFlagOn ? secret('ADMIN_TOKEN') : (process.env.ADMIN_TOKEN || ''),
    enableAdminRoutes,
    enableSensitiveReads,
    enableWriteRoutes,
};
