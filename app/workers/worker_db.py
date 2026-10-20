from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..config import settings
from qdrant_client import QdrantClient

DATABASE_URL = settings.database_url_sync

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush = False,
    autocommit = False
)

qdrant = QdrantClient(url = settings.qdrant_url)