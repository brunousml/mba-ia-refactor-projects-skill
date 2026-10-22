const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const digest = crypto.scryptSync(password, salt, KEY_LENGTH);
    return `${salt.toString('hex')}:${digest.toString('hex')}`;
}

// Nunca lança: hash em formato inesperado devolve false.
function verifyPassword(password, stored) {
    const [saltHex, digestHex] = String(stored).split(':');
    if (!saltHex || !digestHex) return false;
    const expected = Buffer.from(digestHex, 'hex');
    const digest = crypto.scryptSync(String(password), Buffer.from(saltHex, 'hex'), KEY_LENGTH);
    return expected.length === digest.length && crypto.timingSafeEqual(digest, expected);
}

module.exports = { hashPassword, verifyPassword };
