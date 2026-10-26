const userModel = require('../models/userModel');

async function deleteUser(db, id) {
    await userModel.deleteById(db, id);
}

module.exports = { deleteUser };
