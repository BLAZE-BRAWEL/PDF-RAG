from qdrant_client import AsyncQdrantClient
from .config import settings

qdrant  = AsyncQdrantClient(url = settings.qdrant_url)
