from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Request
from ..ingestion import Ingestion
from qdrant_client import models as qdrant_models
from uuid import uuid4
from ..dependency import get_qdrant
from qdrant_client import QdrantClient
from ..global_variables import MAX_UPLOAD_LIMIT, COLLECTION_NAME, GEMINI_MODEL, UPLOAD_DIRECTORY
from ..schemas import Question
from google import genai
from ..config import settings
from ..oauth2 import get_current_user
from ..import models
from ..workers.worker import pdf_work_worker
from pathlib import Path
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import aiofiles
import os
from sqlalchemy import select
from ..logger.logging import logger
from ..limiter import limiter
from ..import schemas

router = APIRouter(
    tags= ['RAG']
)


ingest = Ingestion()

@router.post('/upload', status_code = status.HTTP_202_ACCEPTED)
@limiter.limit('5/minute')
async def upload_pdf(
    request: Request,
    file: UploadFile= File(...),
    user_info: models.Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF Supported"
        )
    
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Only PDF Supported"
        )
    
    first_chunk = await file.read(1024)
    
    if not first_chunk.startswith(b"%PDF"):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Only PDF Supported"
        )
    
    file_id = str(uuid4())
    
    file_name = f"{file_id}_{Path(file.filename).name}"
    
    file_path = UPLOAD_DIRECTORY / file_name
    
    total_size = len(first_chunk)
    
    async with aiofiles.open(file_path, "wb") as file_write:
        
        await file_write.write(first_chunk)
        
        while True:
            
            content = await file.read(1024 * 1024)
            
            if not content:
                break
            
            total_size += len(content)
            
            if total_size > MAX_UPLOAD_LIMIT:
                
                await file_write.close()
                
                os.remove(file_path)
                
                raise HTTPException(
                    status_code = status.HTTP_406_NOT_ACCEPTABLE,
                    detail = "File to large maximum size 100 MB"
                )
            
            await file_write.write(content)
    
    celery_unique_id = str(uuid4())
    
    task_entry = models.BackGroundTasks(
        user_id = user_info.id,
        celery_id = celery_unique_id,
        task_name = "process_pdf",
        task_status = models.Status.PENDING
    )
    
    try:
        db.add(task_entry)
        
        await db.commit()
        
        task = pdf_work_worker.apply_async(
            kwargs = {
                "file_path" : str(file_path),
                "user_id" : str(user_info.id),
            },
            
            task_id = celery_unique_id
            
        )
    
    except IntegrityError:
        await db.rollback()
        
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Something went wrong."
        )
    
    return {
        "status" : "Processing",
        "task_id" : celery_unique_id
    }

@router.get('/tasks/{task_id}', response_model = schemas.TaskOut)
@limiter.limit('50/minute')
async def get_task_status(
    request: Request,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_info: models.Users = Depends(get_current_user)
    ):
    
    task_statement = await db.execute(
        select(models.BackGroundTasks)
        .where(models.BackGroundTasks.user_id == user_info.id,
                models.BackGroundTasks.celery_id == task_id)
    )
    
    task = task_statement.scalars().first()
    
    if not task:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Task with this ID does not exist"
        )
    
    if not task:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Task with this ID does not exist"
        )
    
    return task

@router.post('/ask')
@limiter.limit('10/minute')
async def ask(
    request: Request,
    question: Question,
    qdrant: QdrantClient= Depends(get_qdrant),
    user_info: models.Users = Depends(get_current_user)
    ):
    
    ai_client = genai.Client(
        api_key = settings.gemini_api_key
    )
    dense_question_embedding, sparse_question_embedding = ingest.embed(question.question)
    
    results = await qdrant.query_points(
        collection_name = COLLECTION_NAME,
        
        prefetch = [
            
            qdrant_models.Prefetch(
                query = dense_question_embedding,
                using = "dense",
                limit = 20
            ),
            
            qdrant_models.Prefetch(
                query = qdrant_models.SparseVector(
                    indices = sparse_question_embedding[0].indices.tolist(),
                    values = sparse_question_embedding[0].values.tolist()
                ),

                
                using = "sparse",
                limit = 20
            )
            
        ],
        
        query = qdrant_models.FusionQuery(
            fusion = qdrant_models.Fusion.RRF),
        with_payload =True,
        limit = 5
    )
    
    retrieved_data = [
        result.payload.get('text', '')
        for result in results.points
    ]
    
    if not retrieved_data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail= "PDF File not detected."
        )
    
    try: 
        
        interaction = await ai_client.aio.interactions.create(
            model= GEMINI_MODEL,
            input= question.question,
            system_instruction= f"""
            You are an Helpful AI Assistain you answer questions from context data and if the answer is not inside context 
            You say cannot retrieve the data. Here is your context
        
            {retrieved_data}
        
            """
        )
    
    except Exception:
        
        logger.exception(
            "Failed to connect to Model"
        )
        
        raise
    
    return {
        'answer' : interaction.output_text
    }