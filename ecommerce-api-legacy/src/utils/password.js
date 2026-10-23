// Hash de senha com scrypt e salt aleatório (T04). O formato armazenado é "<salt hex>:<digest hex>".
const crypto = require('crypto');

const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(16);
    return `${salt.toString('hex')}:${crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex')}`;
}

function verifyPassword(password, stored) {
    const [saltHex, digestHex] = String(stored).split(':');
    if (!saltHex || !digestHex) return false;
    const expected = Buffer.from(digestHex, 'hex');
    const digest = crypto.scryptSync(password, Buffer.from(saltHex, 'hex'), KEY_LENGTH);
    return expected.length === digest.length && crypto.timingSafeEqual(digest, expected);
}

module.exports = { hashPassword, verifyPassword };
