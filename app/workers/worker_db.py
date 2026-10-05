from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..config import settings

DATABASE_URL = settings.database_url_sync

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush = False,
    autocommit = False
)