// Entry point: só compõe a aplicação (config, banco, middlewares, rotas) e sobe o servidor.
const express = require('express');
const config = require('./config/settings');
const { openDatabase } = require('./models/database');
const { initSchema } = require('./models/schema');
const routes = require('./routes');
const { errorHandler } = require('./middlewares/errorHandler');
const { logger } = require('./utils/logger');

async function main() {
    // Banco criado uma vez no boot e injetado via app.locals (T07); nenhum módulo abre conexão sozinho.
    const db = openDatabase(config.databaseFile);
    await initSchema(db);

    const app = express();
    app.locals.db = db;
    app.use(express.json());
    app.use(routes);
    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha no boot', { error: err.stack || String(err) });
    process.exit(1);
});
