from contextlib import asynccontextmanager
from fastapi import FastAPI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from .global_variables import COLLECTION_NAME
from .database import engine
from .models import Base
from .routers.query import router as query_router
from .routers.account import router as account_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    qdrant = QdrantClient("http://localhost:6333")
    app.state.qdrant = qdrant

    try:
        collections = qdrant.get_collections().collections
        collection_names = [collection.name for collection in collections]

        if COLLECTION_NAME not in collection_names:
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                ),
            )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield

    finally:
        await engine.dispose()
        qdrant.close()

app = FastAPI(lifespan=lifespan)

@app.get('/')
def main_page():
    return {
        "nothing" : "nothing"
    }

app.include_router(query_router)
app.include_router(account_router)