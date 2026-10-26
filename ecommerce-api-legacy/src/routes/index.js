const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { requireAdmin, requireWrite } = require('../middlewares/guards');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');

const router = express.Router();

router.post('/api/checkout', requireWrite, asyncHandler(checkoutController.checkout));
router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));
router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.deleteUser));

module.exports = router;
