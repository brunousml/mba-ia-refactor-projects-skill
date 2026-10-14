const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createAdminRoutes({ reportController, adminGuard }) {
    const router = express.Router();
    router.get('/api/admin/financial-report', adminGuard, asyncHandler(reportController.financialReport));
    return router;
}

module.exports = { createAdminRoutes };
