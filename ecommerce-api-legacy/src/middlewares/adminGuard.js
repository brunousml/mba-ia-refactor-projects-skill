const crypto = require('crypto');

// Rotas administrativas: 403 com a flag desligada (default); com a flag ligada,
// exigem o header X-Admin-Token igual ao ADMIN_TOKEN.
function createAdminGuard({ enableAdminRoutes, adminToken }) {
    return function adminGuard(req, res, next) {
        if (!enableAdminRoutes) return res.status(403).send("Recurso desabilitado");
        const token = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken || '');
        if (!expected.length || token.length !== expected.length || !crypto.timingSafeEqual(token, expected)) {
            return res.status(401).send("Não autorizado");
        }
        next();
    };
}

module.exports = { createAdminGuard };
