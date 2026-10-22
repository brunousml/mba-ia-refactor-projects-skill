const crypto = require('crypto');

function hashPassword(password) {
    const salt = crypto.randomBytes(16);
    return `${salt.toString('hex')}:${crypto.scryptSync(password, salt, 64).toString('hex')}`;
}

function verifyPassword(password, stored) {
    const [saltHex, digestHex] = String(stored).split(':');
    if (!saltHex || !digestHex) return false;
    const expected = Buffer.from(digestHex, 'hex');
    const digest = crypto.scryptSync(password, Buffer.from(saltHex, 'hex'), 64);
    return expected.length === digest.length && crypto.timingSafeEqual(digest, expected);
}

module.exports = { hashPassword, verifyPassword };
