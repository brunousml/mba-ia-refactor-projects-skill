function createReportController({ reportService }) {
    async function financialReport(req, res) {
        res.json(await reportService.buildFinancialReport());
    }

    return { financialReport };
}

module.exports = { createReportController };
