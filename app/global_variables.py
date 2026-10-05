from pathlib import Path

COLLECTION_NAME = 'store'
GEMINI_MODEL = 'gemini-3.5-flash-lite'
ALGORITHM = "HS256"
UPLOAD_DIRECTORY = Path("users_pdf")
MAX_UPLOAD_LIMIT = (1024*1024) * 100