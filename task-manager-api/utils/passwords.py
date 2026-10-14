from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    # Werkzeug 3 usa scrypt com salt aleatório por padrão
    return generate_password_hash(password)


def verify_password(password, stored_hash):
    # Hash em formato inesperado (ex.: MD5 antigo) devolve False, nunca exceção
    try:
        return check_password_hash(stored_hash or '', password)
    except (ValueError, TypeError):
        return False
