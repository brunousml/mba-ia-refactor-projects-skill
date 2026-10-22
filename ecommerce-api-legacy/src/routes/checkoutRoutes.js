const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { requireWrite } = require('../middlewares/guards');

const router = express.Router();
router.post('/api/checkout', requireWrite, asyncHandler(checkoutController.checkout));

module.exports = router;
