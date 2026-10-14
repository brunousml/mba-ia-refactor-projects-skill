import hashlib
import hmac
import os

PREFIXO = "scrypt"
PARAMS = {"n": 2**14, "r": 8, "p": 1}


def gerar_hash(senha):
    sal = os.urandom(16)
    digest = hashlib.scrypt(senha.encode(), salt=sal, **PARAMS)
    return f"{PREFIXO}${sal.hex()}${digest.hex()}"


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(PREFIXO + "$")


def verificar_senha(senha, armazenado):
    try:
        prefixo, sal_hex, digest_hex = armazenado.split("$")
        if prefixo != PREFIXO:
            return False
        digest = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal_hex), **PARAMS)
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
