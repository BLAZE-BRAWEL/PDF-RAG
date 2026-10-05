from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent / '.env'

class Settings(BaseSettings):
    database_url: str
    database_url_sync: str
    secret_key: str
    qdrant_url: str
    gemini_api_key: str
    celery_broker_url: str
    celery_backend_url: str
    qdrant_url: str
    
    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        extra = "ignore"
    )
    

settings = Settings()