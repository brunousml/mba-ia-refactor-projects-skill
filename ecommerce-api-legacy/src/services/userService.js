const { DomainError } = require('../errors/domainErrors');

function createUserService({ userModel }) {
    async function deleteUser(id) {
        const deleted = await userModel.deleteById(id);
        if (deleted === 0) throw new DomainError("Usuário não encontrado", 404);
    }

    return { deleteUser };
}

module.exports = { createUserService };
