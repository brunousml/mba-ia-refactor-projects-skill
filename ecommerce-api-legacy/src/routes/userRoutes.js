const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createUserRoutes({ userController, adminGuard }) {
    const router = express.Router();
    router.delete('/api/users/:id', adminGuard, asyncHandler(userController.deleteUser));
    return router;
}

module.exports = { createUserRoutes };
