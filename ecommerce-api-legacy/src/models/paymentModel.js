function createPaymentModel(db) {
    return {
        async create({ enrollmentId, amount, status }) {
            const { lastID } = await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]);
            return lastID;
        },
    };
}

module.exports = { createPaymentModel };
