const { DomainError } = require('../errors/domainError');

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            const id = Number(req.params.id);
            if (!Number.isInteger(id)) throw new DomainError('Usuário não encontrado', 404);
            await userService.deleteUser(id);
            res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
        },
    };
}

module.exports = { createUserController };
