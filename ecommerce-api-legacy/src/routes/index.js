const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createRouter({ controllers, guards }) {
    const router = express.Router();

    router.post('/api/checkout', guards.requireWrite, asyncHandler(controllers.checkout.checkout));
    router.get('/api/admin/financial-report', guards.requireAdmin, asyncHandler(controllers.report.financialReport));
    router.delete('/api/users/:id', guards.requireAdmin, asyncHandler(controllers.user.remove));

    return router;
}

module.exports = { createRouter };
