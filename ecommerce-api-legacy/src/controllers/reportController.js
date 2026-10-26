const reportService = require('../services/reportService');

async function financialReport(req, res) {
    res.json(await reportService.financialReport(req.app.locals.db));
}

module.exports = { financialReport };
