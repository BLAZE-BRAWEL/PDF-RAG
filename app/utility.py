from pydantic import SecretStr
from pwdlib import PasswordHash
import hashlib
from qdrant_client.models import MatchValue, FieldCondition, Filter
from .qdrant_setup import qdrant


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

def finger_print_for_pdf(file: str) -> str:
    
    
    if isinstance(file , str ):
        file_bytes = file.encode('utf-8')
    else:
        file_bytes = str(file).encode('utf-8')
    
    return hashlib.sha256(file_bytes).hexdigest()

def verify_pdf_finger_print(
    collection_name: str,
    file: str,
    user_id: str
):
    
    finger_print = finger_print_for_pdf(file)
    
    duplicate_check = qdrant.scroll(
        collection_name= collection_name,
        scroll_filter= Filter(
            must = [
                FieldCondition(
                    key = "fingerprint",
                    match = MatchValue(value = finger_print)
                ),
                
                FieldCondition(
                    key = "owner",
                    match = MatchValue(value = user_id)
                )
            ]
            
        ),
        
        limit = 1,
        with_payload = False,
        with_vectors = False
    )
    
    point , next_starting_point = duplicate_check
    
    return point