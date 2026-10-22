const express = require('express');
const settings = require('./config/settings');
const logger = require('./utils/logger');
const { openDatabase } = require('./models/database');
const { initSchema } = require('./models/schema');
const { createModels } = require('./models');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createGuards } = require('./middlewares/guards');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createRouter } = require('./routes');

async function main() {
    const db = openDatabase(settings.databaseFile);
    await initSchema(db);
    const models = createModels(db);

    const controllers = {
        checkout: createCheckoutController({ checkoutService: createCheckoutService({ models, logger }) }),
        report: createReportController({ reportService: createReportService({ models }) }),
        user: createUserController({ userService: createUserService({ models }) }),
    };

    const app = express();
    app.use(express.json());
    app.use(createRouter({ controllers, guards: createGuards(settings) }));
    app.use(createErrorHandler({ logger }));

    app.listen(settings.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha no boot', { message: err.message });
    process.exit(1);
});
