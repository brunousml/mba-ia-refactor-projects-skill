const findIdByEmail = (db, email) => db.get('SELECT id FROM users WHERE email = ?', [email]);

const insert = (db, name, email, passHash) =>
    db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passHash]);

const deleteById = (db, id) => db.run('DELETE FROM users WHERE id = ?', [id]);

module.exports = { findIdByEmail, insert, deleteById };
