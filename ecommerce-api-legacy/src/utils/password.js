const crypto = require('crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;

// Formato armazenado: "<salt hex>:<digest hex>" (scrypt da stdlib).
function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    return `${salt.toString('hex')}:${crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex')}`;
}

// Nunca lança: hash em formato inesperado devolve false.
function verifyPassword(password, stored) {
    if (typeof password !== 'string') return false;
    const [saltHex, digestHex] = String(stored).split(':');
    if (!saltHex || !digestHex) return false;
    const expected = Buffer.from(digestHex, 'hex');
    const digest = crypto.scryptSync(password, Buffer.from(saltHex, 'hex'), KEY_LENGTH);
    return expected.length === digest.length && crypto.timingSafeEqual(digest, expected);
}

module.exports = { hashPassword, verifyPassword };
