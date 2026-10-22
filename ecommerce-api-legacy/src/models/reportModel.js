// Uma consulta para o relatório inteiro (antes: 1 + cursos + 2 × matrículas).
const listCourseEnrollments = (db) => db.all(`
    SELECT c.id AS course_id, c.title AS course_title,
           e.id AS enrollment_id, u.name AS user_name,
           p.amount AS payment_amount, p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id
`);

module.exports = { listCourseEnrollments };
