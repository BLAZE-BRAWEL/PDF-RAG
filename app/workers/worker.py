from .celery_app import celery_app
from ..ingestion import Ingestion, load_pdf
from ..utility import verify_pdf_finger_print, finger_print_for_pdf
from ..dependency import get_qdrant
import pymupdf4llm
from global_variables import COLLECTION_NAME
from fastapi import HTTPException, status, Depends 
import qdrant_client
from qdrant_client.models import PointStruct
from uuid import uuid4

ingestion = Ingestion()


@celery_app.task(name = "worker.pdf_work")
def pdf_work(file_path: str, user_id: str, qdrant: qdrant_client = Depends(get_qdrant)):
    
    document = load_pdf(file_path)
    
    point = verify_pdf_finger_print(COLLECTION_NAME , document)
    
    if point:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "File already exists"
        )
    
    embeddings , chunks = ingestion.chunk_documents_with_embedding(document)
    
    points = []
    
    for embedding , chunk in zip(embeddings, chunks):
        points.append(
            PointStruct(
                id = uuid4(),
                vector = embedding,
                payload = {
                    "text" : chunk,
                    "owner" : user_id,
                    "fingerprint" :  finger_print_for_pdf(document)
                }
            )
        )
    
    qdrant.upsert(
        collection_name = COLLECTION_NAME,
        points = points
    )