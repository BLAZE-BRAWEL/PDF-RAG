from pydantic import SecretStr
from pwdlib import PasswordHash
import hashlib
from .dependency import get_qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import MatchValue, FieldCondition, Filter
from fastapi import Depends


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

def finger_print_for_pdf(file: bytes) -> str:
    
    return hashlib.sha256(file).hexdigest()

def verify_pdf_finger_print(collection_name: str,file: bytes ,qdrant: QdrantClient= Depends(get_qdrant)):
    
    finger_print = finger_print_for_pdf(file)
    
    duplicate_check = qdrant.scroll(
        collection_name= collection_name,
        scroll_filter= Filter(
            must = [
                FieldCondition(
                    key = "fignerprint",
                    match = MatchValue(value = finger_print)
                )
            ]
        ),
        
        limit = 1,
        with_payload = False,
        with_vectors = False
    )
    
    point , next_starting_point = duplicate_check
    
    return point