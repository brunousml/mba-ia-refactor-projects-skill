const express = require('express');
const { settings } = require('./config/settings');
const { createDatabase } = require('./models/db');
const { createSchema, seed } = require('./models/schema');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createReportModel } = require('./models/reportModel');
const { createCheckoutService } = require('./services/checkoutService');
const { createPaymentService } = require('./services/paymentService');
const { createReportService } = require('./services/reportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { createAdminRoutes } = require('./routes/adminRoutes');
const { createUserRoutes } = require('./routes/userRoutes');
const { errorHandler } = require('./middlewares/errorHandler');
const { createAdminGuard } = require('./middlewares/adminGuard');
const { logger } = require('./utils/logger');

async function main() {
    const db = createDatabase(':memory:');
    await createSchema(db);
    await seed(db);

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);
    const reportModel = createReportModel(db);

    const paymentService = createPaymentService({ logger });
    const checkoutService = createCheckoutService({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService });
    const reportService = createReportService({ reportModel });
    const userService = createUserService({ userModel });

    const adminGuard = createAdminGuard(settings);

    const app = express();
    app.use(express.json());
    app.use(createCheckoutRoutes({ checkoutController: createCheckoutController({ checkoutService }) }));
    app.use(createAdminRoutes({ reportController: createReportController({ reportService }), adminGuard }));
    app.use(createUserRoutes({ userController: createUserController({ userService }), adminGuard }));
    app.use(errorHandler);

    app.listen(settings.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

main().catch((err) => {
    logger.error('Falha no boot', err);
    process.exit(1);
});
