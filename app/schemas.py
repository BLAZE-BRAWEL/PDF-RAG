from pydantic import BaseModel, ConfigDict, SecretStr, EmailStr
from uuid import UUID

class Question(BaseModel):
    question : str


class Account_Details_Out(BaseModel):
    id: UUID
    email: str
    
    model_config = ConfigDict(
        from_attributes= True
    )

class Account_Details_In(BaseModel):
    email: EmailStr
    password: SecretStr
    
    model_config = ConfigDict(
        from_attributes= True
    )

class TaskOut(BaseModel):
    task_name: str
    task_status: str