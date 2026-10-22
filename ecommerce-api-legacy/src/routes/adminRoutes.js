const express = require('express');
const reportController = require('../controllers/reportController');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { requireAdmin } = require('../middlewares/guards');

const router = express.Router();
router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));

module.exports = router;
