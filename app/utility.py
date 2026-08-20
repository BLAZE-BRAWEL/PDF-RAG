from pydantic import SecretStr
from pwdlib import PasswordHash

hashing_algorithm = PasswordHash.recommended()

def hash_password(password: str | SecretStr) -> str:
    if isinstance(password, SecretStr):
        password = password.get_secret_value()
    
    hashed_password = hashing_algorithm.hash(password)
    
    return hashed_password

def verify_password(password: str, hashed_password: str):
    return hashing_algorithm.verify(
        password,
        hashed_password
    )

