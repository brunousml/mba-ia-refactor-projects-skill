// Acesso a dados. Cada model recebe a conexão injetada e só monta consultas parametrizadas.

const createUserModel = (db) => ({
    findIdByEmail: (email) => db.get("SELECT id FROM users WHERE email = ?", [email]),
    async create({ name, email, passwordHash }) {
        const { lastID } = await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, passwordHash]);
        return lastID;
    },
    async deleteById(id) {
        const { changes } = await db.run("DELETE FROM users WHERE id = ?", [id]);
        return changes;
    },
});

const createCourseModel = (db) => ({
    findActiveById: (id) => db.get("SELECT id, title, price FROM courses WHERE id = ? AND active = 1", [id]),
});

const createEnrollmentModel = (db) => ({
    async create({ userId, courseId }) {
        const { lastID } = await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, courseId]);
        return lastID;
    },
});

const createPaymentModel = (db) => ({
    create: ({ enrollmentId, amount, status }) =>
        db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]),
});

const createAuditLogModel = (db) => ({
    record: (action) => db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]),
});

const createReportModel = (db) => ({
    // Uma consulta só (sem N+1): cada linha é um curso com, no máximo, uma matrícula.
    listCourseEnrollments: () => db.all(`
        SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
               u.name AS student_name, p.amount, p.status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        ORDER BY c.id, e.id`),
});

function createModels(db) {
    return {
        users: createUserModel(db),
        courses: createCourseModel(db),
        enrollments: createEnrollmentModel(db),
        payments: createPaymentModel(db),
        auditLogs: createAuditLogModel(db),
        reports: createReportModel(db),
    };
}

module.exports = { createModels };
