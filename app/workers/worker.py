from .celery_app import celery_app
from ..ingestion import Ingestion, load_pdf
from ..utility import verify_pdf_finger_print, finger_print_for_pdf
from ..global_variables import COLLECTION_NAME
from qdrant_client.models import PointStruct
from uuid import uuid4
from ..database import SessionLocal
from ..qdrant_setup import qdrant
from ..import models
from pathlib import Path
from .worker_db import SessionLocal

ingestion = Ingestion()


class PDFAlreadyExists(Exception):
    pass

class TaskNotFound(Exception):
    pass

def update_task_status(task_id: str, status: models.Status):
    with SessionLocal() as db:
        
        db_task = db.query(models.BackGroundTasks).filter(
            models.BackGroundTasks.celery_id == task_id
        ).first()
        
        if not db_task:
            raise TaskNotFound(f"Task with celery_id {task_id} does not exist")
        
        db.query(models.BackGroundTasks).filter(
            models.BackGroundTasks.celery_id == task_id
        ).update({"task_status": status})
        
        db.commit() 


def pdf_work(
    file_path: str,
    user_id: str,
    task_id: str
    ):
    
    try:
    
        document = load_pdf(Path(file_path))
        
        point = verify_pdf_finger_print(COLLECTION_NAME , file = document, user_id = user_id)
        
        if point:
            update_task_status(
                task_id = task_id,
                status = models.Status.FAILED
            )
            
            return {
                "status" : "SKIPPED",
                "reason" : "PDF Already exists"
            }
        
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
        
        update_task_status(
            task_id = task_id,
            status = models.Status.SUCCESS
        )
    
    except Exception as e:
        update_task_status(
            task_id = task_id,
            status = models.Status.FAILED
        )
        
        raise e


@celery_app.task(bind = True, name = "worker.pdf_work", max_retries = 3, retry_backoff = True, retry_jitter = True)
def pdf_work_worker(
    self,
    file_path: str,
    user_id: str,
    ):
    
    try:
        
        return pdf_work(
            file_path = file_path,
            user_id = user_id,
            task_id = self.request.id
        )
    
    except Exception as e:
        raise self.retry(exc = e)
