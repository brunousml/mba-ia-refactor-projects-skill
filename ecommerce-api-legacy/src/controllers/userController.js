const userService = require('../services/userService');

async function deleteUser(req, res) {
    if (!/^\d+$/.test(req.params.id)) return res.status(400).send('Bad Request');
    await userService.deleteUser(req.app.locals.db, Number(req.params.id));
    res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
}

module.exports = { deleteUser };
