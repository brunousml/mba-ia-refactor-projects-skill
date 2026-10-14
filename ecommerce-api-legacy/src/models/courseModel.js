const { COURSE_ACTIVE } = require('../config/rules');

function createCourseModel(db) {
    return {
        findActiveById: (id) => db.get("SELECT id, title, price FROM courses WHERE id = ? AND active = ?", [id, COURSE_ACTIVE]),
    };
}

module.exports = { createCourseModel };
