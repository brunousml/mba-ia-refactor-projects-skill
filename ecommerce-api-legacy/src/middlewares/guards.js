// Guards de acesso por flag (T08). Flag desligada: 403. Ligada: exige X-Admin-Token igual a ADMIN_TOKEN (401 sem ele).
const crypto = require('crypto');
const settings = require('../config/settings');

function requireFlag(enabled, adminToken) {
    return (req, res, next) => {
        if (!enabled) return res.status(403).json({ erro: 'Recurso desabilitado' });
        const token = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken || '');
        if (!expected.length || token.length !== expected.length || !crypto.timingSafeEqual(token, expected)) {
            return res.status(401).json({ erro: 'Não autorizado' });
        }
        next();
    };
}

const requireAdmin = requireFlag(settings.enableAdminRoutes, settings.adminToken);
const requireSensitiveRead = requireFlag(settings.enableSensitiveReads, settings.adminToken);
const requireWrite = requireFlag(settings.enableWriteRoutes, settings.adminToken);

module.exports = { requireFlag, requireAdmin, requireSensitiveRead, requireWrite };
