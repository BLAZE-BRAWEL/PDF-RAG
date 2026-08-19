from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from pathlib import Path
from dotenv import load_dotenv
import os
from fastapi import HTTPException, status
from .config import settings

DATABASE_URL = settings.database_url

if not DATABASE_URL:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Not Found")

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session