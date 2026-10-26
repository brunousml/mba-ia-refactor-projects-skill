const userService = require('../services/userService');

async function deleteUser(req, res) {
    await userService.deleteUser(req.app.locals.db, req.params.id);
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
}

module.exports = { deleteUser };
