const sqlite3 = require('sqlite3');

// Adaptador com promises sobre o driver de callbacks. lastID e changes ficam em `this`
// dentro do callback de run, por isso a function tradicional.
function openDatabase(filename = ':memory:') {
    const driver = new sqlite3.Database(filename);
    return {
        get: (sql, params = []) => new Promise((resolve, reject) =>
            driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)))),
        all: (sql, params = []) => new Promise((resolve, reject) =>
            driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)))),
        run: (sql, params = []) => new Promise((resolve, reject) =>
            driver.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            })),
        exec: (sql) => new Promise((resolve, reject) =>
            driver.exec(sql, (err) => (err ? reject(err) : resolve()))),
        close: () => new Promise((resolve, reject) =>
            driver.close((err) => (err ? reject(err) : resolve()))),
    };
}

module.exports = { openDatabase };
