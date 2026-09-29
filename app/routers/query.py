from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from ..ingestion import Ingestion
from qdrant_client.models import Filter, FieldCondition, MatchValue
from uuid import uuid4
from ..dependency import get_qdrant
from qdrant_client import QdrantClient
from ..global_variables import COLLECTION_NAME, GEMINI_MODEL, UPLOAD_DIRECTORY
from ..schemas import Question
from google import genai
from ..config import settings
from ..oauth2 import get_current_user
from ..import models
from ..workers.worker import pdf_work, celery_app
from pathlib import Path
from celery.result import AsyncResult

router = APIRouter(
    tags= ['RAG']
)

ingest = Ingestion()

@router.post('/upload', status_code = status.HTTP_202_ACCEPTED)
async def upload_pdf(
    file: UploadFile= File(...),
    user_info: models.Users = Depends(get_current_user),
    ):
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF Supported"
        )
    
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Only PDF supported"
        )
    
    contents = await file.read()
    
    UPLOAD_DIRECTORY.mkdir(exist_ok=True)
    
    file_id = str(uuid4())
    
    file_name = f"{file_id}_{Path(file.filename).name}"
    
    file_path = UPLOAD_DIRECTORY / file_name
    
    file_path.write_bytes(contents)
    
    task = pdf_work.delay(
        file_path = file_path,
        user_id = user_info.id,
    )
    
    return {
        "status" : "Processing",
        "task_id" : task.id
    }

@router.post('/ask')
async def ask(
    question: Question,
    qdrant: QdrantClient= Depends(get_qdrant),
    user_info: models.Users = Depends(get_current_user)
    ):
    
    ai_client = genai.Client(
        api_key= settings.gemini_api_key
    )
    questinon_embedding = ingest.embed(question.question)
    
    results = qdrant.query_points(
        collection_name= COLLECTION_NAME,
        query= questinon_embedding,
        with_payload=True,
        query_filter= Filter(
            must= [
                FieldCondition(
                    key="owner",
                    match= MatchValue(value = str(user_info.id))
                )
            ]
        )
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
    
    interaction = await ai_client.aio.interactions.create(
        model= GEMINI_MODEL,
        input= question.question,
        system_instruction= f"""
        You are an Helpful AI Assistain you answer questions from context data and if the answer is not inside context 
        You say cannot retrieve the data. Here is your context
        
        {retrieved_data}
        
        """
    )
    
    return {
        'answer' : interaction.output_text
    }