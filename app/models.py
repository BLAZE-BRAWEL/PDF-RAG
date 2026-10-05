from .database import Base
from sqlalchemy import String, UUID, func, DateTime, ForeignKey, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from datetime import datetime
from enum import Enum as py_Enum


class Status(py_Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"

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
    
    tasks: Mapped[list["BackGroundTasks"]] = relationship(
        "BackGroundTasks", back_populates = "user", cascade = "all, delete-orphan"
    )

class BackGroundTasks(Base):
    __tablename__ = 'tasks'
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True), primary_key = True, server_default = func.gen_random_uuid()
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True), ForeignKey('users.id', ondelete= "CASCADE")
    )
    
    celery_id: Mapped[str] = mapped_column(
        String, nullable = False, unique = True
    )
    
    task_name: Mapped[str] = mapped_column(
        String, nullable = False
    )

    task_status: Mapped[Status] = mapped_column(
        Enum(Status), nullable = False, default = Status.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True) , server_default = func.now()
    )
    
    user: Mapped["Users"] = relationship(
        "Users" , back_populates = "tasks"
    )