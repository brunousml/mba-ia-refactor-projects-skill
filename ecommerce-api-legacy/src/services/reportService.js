const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../config/rules');

function createReportService({ reportModel }) {
    async function buildFinancialReport() {
        const reportByCourse = new Map();
        for (const row of await reportModel.findCourseEnrollmentRows()) {
            if (!reportByCourse.has(row.courseId)) {
                reportByCourse.set(row.courseId, { course: row.courseTitle, revenue: 0, students: [] });
            }
            if (row.enrollmentId === null) continue;

            const courseData = reportByCourse.get(row.courseId);
            if (row.paymentStatus === PAYMENT_STATUS.PAID) courseData.revenue += row.paymentAmount;
            courseData.students.push({
                student: row.studentName ?? UNKNOWN_STUDENT,
                paid: row.paymentAmount ?? 0,
            });
        }
        return [...reportByCourse.values()];
    }

    return { buildFinancialReport };
}

module.exports = { createReportService };
