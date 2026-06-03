import hashlib
import os

def hash_password(password: str) -> str:
    """Securely hashes a password using PBKDF2 with SHA-256 and a random salt."""
    salt = os.urandom(16).hex()
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${hash_bytes.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against a PBKDF2 hash."""
    try:
        parts = hashed.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = parts[2]
        stored_hash = parts[3]
        
        test_hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return test_hash_bytes.hex() == stored_hash
    except Exception:
        return False
