const { DomainError } = require('../errors/domainError');

function createUserService({ models }) {
    async function deleteUser(id) {
        const deleted = await models.users.deleteById(id);
        if (deleted === 0) throw new DomainError('Usuário não encontrado', 404);
    }

    return { deleteUser };
}

module.exports = { createUserService };
