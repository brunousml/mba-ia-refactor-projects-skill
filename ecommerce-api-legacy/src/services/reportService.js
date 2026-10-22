const { PAYMENT_STATUS, UNKNOWN_STUDENT_NAME } = require('../config/rules');

function createReportService({ models }) {
    async function financialReport() {
        const rows = await models.reports.listCourseEnrollments();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            const entry = byCourse.get(row.course_id);
            if (row.enrollment_id === null) continue;

            if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
            entry.students.push({
                student: row.student_name ?? UNKNOWN_STUDENT_NAME,
                paid: row.amount ?? 0,
            });
        }

        return [...byCourse.values()];
    }

    return { financialReport };
}

module.exports = { createReportService };
