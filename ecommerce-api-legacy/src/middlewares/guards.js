const crypto = require('crypto');

// T08: rota registrada, mas atrás de flag (default desligada → 403) e de X-Admin-Token (→ 401).
function createGuards(settings) {
    const requireFlag = (flagName) => (req, res, next) => {
        if (!settings[flagName]) return res.status(403).json({ erro: 'Recurso desabilitado' });
        const token = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(settings.adminToken || '');
        if (!expected.length || token.length !== expected.length || !crypto.timingSafeEqual(token, expected)) {
            return res.status(401).json({ erro: 'Não autorizado' });
        }
        next();
    };

    return {
        requireAdmin: requireFlag('enableAdminRoutes'),
        requireSensitiveRead: requireFlag('enableSensitiveReads'),
        requireWrite: requireFlag('enableWriteRoutes'),
    };
}

module.exports = { createGuards };
