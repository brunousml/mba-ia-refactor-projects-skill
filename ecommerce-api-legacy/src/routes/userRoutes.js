const express = require('express');
const userController = require('../controllers/userController');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { requireAdmin } = require('../middlewares/guards');

const router = express.Router();
router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.deleteUser));

module.exports = router;
