const sqlite3 = require('sqlite3');

function createDb(path) {
    const driverDb = new sqlite3.Database(path);
    return {
        get: (sql, params = []) => new Promise((ok, fail) =>
            driverDb.get(sql, params, (err, row) => (err ? fail(err) : ok(row)))),
        all: (sql, params = []) => new Promise((ok, fail) =>
            driverDb.all(sql, params, (err, rows) => (err ? fail(err) : ok(rows)))),
        run: (sql, params = []) => new Promise((ok, fail) =>
            driverDb.run(sql, params, function (err) {
                if (err) return fail(err);
                ok({ lastID: this.lastID, changes: this.changes });
            })),
        close: () => new Promise((ok, fail) => driverDb.close((err) => (err ? fail(err) : ok()))),
    };
}

module.exports = { createDb };
