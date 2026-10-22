const express = require('express');
const settings = require('./config/settings');
const { createDb } = require('./models/db');
const { initSchema, seed } = require('./models/schema');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');
const { errorHandler } = require('./middlewares/errorHandler');
const logger = require('./utils/logger');

async function main() {
    const db = createDb(settings.dbPath);
    await initSchema(db);
    await seed(db);

    const app = express();
    app.locals.db = db;
    app.use(express.json());
    app.use(checkoutRoutes);
    app.use(adminRoutes);
    app.use(userRoutes);
    app.use(errorHandler);

    app.listen(settings.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha no boot', err);
    process.exit(1);
});
