const sqlite3 = require('sqlite3');

// Envolve a API de callbacks do sqlite3 em promises. A conexão é criada no entry point e injetada.
function openDatabase(filename = ':memory:') {
    const connection = new sqlite3.Database(filename);

    return {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                connection.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },
        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },
        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
            });
        },
        close() {
            return new Promise((resolve, reject) => connection.close((err) => (err ? reject(err) : resolve())));
        },
    };
}

module.exports = { openDatabase };
