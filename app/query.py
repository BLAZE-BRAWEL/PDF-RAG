from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from pathlib import Path
from .ingestion import load_pdf, Ingestion
from qdrant_client.models import PointStruct
from uuid import uuid4
from .dependency import get_qdrant
from qdrant_client import QdrantClient
from .global_variables import COLLECTION_NAME, GEMINI_MODEL
from .schemas import Question
from google import genai
from typing import List
from .config import settings

router = APIRouter(
    tags= ['RAG']
)

ingest = Ingestion()

@router.post('/upload')
async def upload_pdf(file: UploadFile= File(...), qdrant: QdrantClient= Depends(get_qdrant)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF Supported"
        )
    
    contents = await file.read()
    
    upload_directory = Path("users_pdf")
    upload_directory.mkdir(exist_ok=True)
    
    file_path = upload_directory / file.filename
    
    file_path.write_bytes(contents)
    
    documents = load_pdf(file_path)
    
    embeddings, chunks = ingest.chunk_documents_with_embedding(documents, chunk_size=1000, chunk_overlap=100)
    
    points = []
    
    for embedding, chunk in zip(embeddings, chunks):
        points.append(
            PointStruct(
                id = uuid4(),
                vector = embedding,
                payload={
                    "text" : chunk,
                }
            )
        )
    
    qdrant.upsert(
        collection_name= COLLECTION_NAME,
        points= points
    )

@router.post('/ask')
async def ask(question: Question, qdrant: QdrantClient= Depends(get_qdrant)):
    ai_client = genai.Client(
        api_key= settings.gemini_api_key
    )
    
    
    questinon_embedding = ingest.embed(question.question)
    
    results = qdrant.query_points(
        collection_name= COLLECTION_NAME,
        query= questinon_embedding,
        with_payload=True
    )
    
    retrieved_data = [
        result.payload.get('text', '')
        for result in results.points
    ]
    
    interaction = ai_client.interactions.create(
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