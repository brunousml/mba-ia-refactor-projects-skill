"""Hash de senha com salt (scrypt via werkzeug, que já vem com o Flask)."""
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password, method='scrypt')


def verify_password(password, stored_hash):
    try:
        return check_password_hash(stored_hash or '', password)
    except (ValueError, TypeError):
        return False
