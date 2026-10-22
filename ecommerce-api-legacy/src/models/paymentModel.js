const insert = (db, enrollmentId, amount, status) =>
    db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);

module.exports = { insert };
