from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent / '.env'

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    qdrant_url: str
    
    model_config = SettingsConfigDict(
        env_file=dotenv_path
    )
    

settings = Settings()