const crypto = require('crypto');
const settings = require('../config/settings');

function requireFlag(flagName) {
    return (req, res, next) => {
        if (!settings[flagName]) return res.status(403).json({ erro: 'Recurso desabilitado' });
        const token = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(settings.adminToken || '');
        if (!expected.length || token.length !== expected.length || !crypto.timingSafeEqual(token, expected)) {
            return res.status(401).json({ erro: 'Não autorizado' });
        }
        next();
    };
}

module.exports = {
    requireAdmin: requireFlag('enableAdminRoutes'),
    requireSensitiveRead: requireFlag('enableSensitiveReads'),
    requireWrite: requireFlag('enableWriteRoutes'),
};
