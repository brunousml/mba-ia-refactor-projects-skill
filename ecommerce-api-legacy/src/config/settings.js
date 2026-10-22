const crypto = require('crypto');

const appEnv = process.env.APP_ENV || 'development';
const flag = (name) => (process.env[name] || 'false').toLowerCase() === 'true';

function secret(name) {
    if (process.env[name]) return process.env[name];
    if (appEnv === 'production') throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    console.warn(`${name} não definida; usando valor aleatório de desenvolvimento`);
    return crypto.randomBytes(32).toString('hex');
}

const enableAdminRoutes = flag('ENABLE_ADMIN_ROUTES');
const enableSensitiveReads = flag('ENABLE_SENSITIVE_READS');
const enableWriteRoutes = flag('ENABLE_WRITE_ROUTES');
const anyGuardEnabled = enableAdminRoutes || enableSensitiveReads || enableWriteRoutes;

module.exports = {
    appEnv,
    port: Number(process.env.PORT || 3000),
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    enableAdminRoutes,
    enableSensitiveReads,
    enableWriteRoutes,
    adminToken: anyGuardEnabled ? secret('ADMIN_TOKEN') : process.env.ADMIN_TOKEN || '',
};
