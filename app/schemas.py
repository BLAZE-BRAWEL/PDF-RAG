from pydantic import BaseModel, ConfigDict, SecretStr
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
    email: str
    password: SecretStr
    
    model_config = ConfigDict(
        from_attributes= True
    )