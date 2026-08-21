import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from .import  models
from .database import get_db
from datetime import datetime, timezone, timedelta
from .config import settings
from .global_variables import ALGORITHM
from uuid import UUID

oauth2schema = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key

def create_access_token(user_id: UUID):
    payload = {
        'sub' : str(user_id),
        'iat' : datetime.now(timezone.utc),
        'exp' : datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return token

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id = payload['sub']
        
        if not user_id:
            raise credentials_exception
        
        return user_id
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Expired"
        )
    
    except jwt.InvalidTokenError as e:
        print(f"DEBUG TOKEN ERROR: {type(e).__name__} - {e}")
        raise credentials_exception

async def get_current_user(token: str= Depends(oauth2schema), db: AsyncSession= Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token Invalid"
    )
    
    user_id_str = verify_access_token(token, credentials_exception)
    
    user_id = UUID(user_id_str)
    
    command = await db.execute(select(models.Users).where(models.Users.id == user_id))
    
    user = command.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="I don't know what to write"
        )
    
    return user