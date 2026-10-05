from qdrant_client import QdrantClient
from .config import settings

qdrant  = QdrantClient(url = settings.qdrant_url)
