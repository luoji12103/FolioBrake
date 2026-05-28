import hashlib
import hmac
import os

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + key.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt = bytes.fromhex(stored_hash[:64])
        stored_key = stored_hash[64:]
    except (ValueError, IndexError):
        return False
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hmac.compare_digest(key.hex(), stored_key)
