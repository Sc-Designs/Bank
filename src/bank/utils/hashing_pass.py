import hashlib
import secrets


# For hash the password
def password_hash(password: str) -> str:
    salt = secrets.token_bytes(20)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


# For dehashing or compare the password
def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", maxsplit=2)

    except ValueError:
        return False

    if algorithm != "scyrpt" :
        return False

    try:
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)

    except ValueError:
        return False

    """
    Here we hash again the incoming password then,
    compare both previous and new password that they are match or not.
    If yes then return True and if not then return False
    """

    actual_digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return secrets.compare_digest(actual_digest, expected_digest)