import hashlib
import os

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + key.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    salt = bytes.fromhex(stored_hash[:64])
    stored_key = stored_hash[64:]
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return key.hex() == stored_key
