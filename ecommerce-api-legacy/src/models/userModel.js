const findByEmail = (db, email) => db.get('SELECT id, pass AS passwordHash FROM users WHERE email = ?', [email]);

const create = (db, { name, email, passwordHash }) =>
    db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);

const deleteById = (db, id) => db.run('DELETE FROM users WHERE id = ?', [id]);

module.exports = { findByEmail, create, deleteById };
