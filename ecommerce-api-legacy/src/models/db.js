const sqlite3 = require('sqlite3');

// Adaptador com Promise sobre o driver de callbacks. O lastID/changes do run
// ficam em `this` dentro do callback, por isso `function` e não arrow.
function createDatabase(filename) {
    const driverDb = new sqlite3.Database(filename);
    return {
        get: (sql, params = []) => new Promise((resolve, reject) =>
            driverDb.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)))),
        all: (sql, params = []) => new Promise((resolve, reject) =>
            driverDb.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)))),
        run: (sql, params = []) => new Promise((resolve, reject) =>
            driverDb.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            })),
    };
}

module.exports = { createDatabase };
