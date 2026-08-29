from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from pathlib import Path
from ..ingestion import load_pdf, Ingestion
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from uuid import uuid4
from ..dependency import get_qdrant
from qdrant_client import QdrantClient
from ..global_variables import COLLECTION_NAME, GEMINI_MODEL
from ..schemas import Question
from google import genai
from ..config import settings
from ..oauth2 import get_current_user
from ..import models
from ..utility import finger_print_for_pdf, verify_pdf_finger_print

router = APIRouter(
    tags= ['RAG']
)

ingest = Ingestion()

@router.post('/upload')
async def upload_pdf(
    file: UploadFile= File(...),
    qdrant: QdrantClient= Depends(get_qdrant),
    user_info: models.Users = Depends(get_current_user),
    ):
    
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
    
    embeddings, chunks = ingest.chunk_documents_with_embedding(documents)
    
    
    point = verify_pdf_finger_print(COLLECTION_NAME, contents)
    
    if point:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "You already uploaded this PDF"
        )
    
    
    points = []
    
    for embedding, chunk in zip(embeddings, chunks):
        points.append(
            PointStruct(
                id = uuid4(),
                vector = embedding,
                payload={
                    "text" : chunk,
                    "owner" : str(user_info.id),
                    "fignerprint" : finger_print_for_pdf(contents)
                }
            )
        )
    

    qdrant.upsert(
        collection_name= COLLECTION_NAME,
        points= points
    )

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