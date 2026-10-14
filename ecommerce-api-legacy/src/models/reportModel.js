function createReportModel(db) {
    return {
        // Uma linha por matrícula (ou uma por curso sem matrícula). Cada matrícula usa
        // o primeiro pagamento, como o `get` por matrícula do código original.
        findCourseEnrollmentRows: () => db.all(`
            SELECT c.id AS courseId, c.title AS courseTitle, e.id AS enrollmentId,
                   u.name AS studentName, p.amount AS paymentAmount, p.status AS paymentStatus
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
            ORDER BY c.id, e.id`),
    };
}

module.exports = { createReportModel };
