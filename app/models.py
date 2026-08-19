from .database import Base
from sqlalchemy import String, Integer, UUID, func, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4
import uuid
from datetime import datetime

class Users(Base):
    __tablename__ = 'users'
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    
    email: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )
    
    password: Mapped[str] = mapped_column(
        String, nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )