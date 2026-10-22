const userModel = require('../models/userModel');

// Comportamento original preservado: matrículas e pagamentos do usuário não são removidos.
const deleteUser = (db, userId) => userModel.deleteById(db, userId);

module.exports = { deleteUser };
