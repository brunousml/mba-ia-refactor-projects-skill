"""Hash de senha com scrypt e salt (T04). Só biblioteca padrão."""
import hashlib
import hmac
import os

PARAMS = {"n": 2**14, "r": 8, "p": 1}


def gerar_hash(senha):
    sal = os.urandom(16)
    digest = hashlib.scrypt(senha.encode(), salt=sal, **PARAMS)
    return f"{sal.hex()}:{digest.hex()}"


def verificar_senha(senha, armazenado):
    try:
        sal_hex, digest_hex = armazenado.split(":")
        digest = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal_hex), **PARAMS)
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
