import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from .import  models
from .database import get_db
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path
from .config import settings
from .global_variables import ALGORITHM

oauth2schema = OAuth2PasswordBearer(tokenUrl="login")

dotenv_path = Path(__file__).resolve().parent.parent/ '.env'
load_dotenv(dotenv_path=dotenv_path)

SECRET_KEY = settings.secret_key
ALGORITHM = ALGORITHM

def create_access_token(user_id: int):
    payload = {
        'sub' : str(user_id),
        'iat' : datetime.now(timezone.utc),
        'exp' : datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    
    token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
    
    return token

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id = payload['user_id']
        
        if not user_id:
            raise credentials_exception
        
        return int(user_id)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token Expired"
        )
    
    except jwt.InvalidSignatureError:
        raise credentials_exception

async def get_current_user(token: str= Depends(oauth2schema), db: AsyncSession= Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token Invalid"
    )
    
    user_id = verify_access_token(token, credentials_exception)
    
    command = await db.execute(select(models.Users).where(models.Users.id == user_id))
    
    user = command.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="I don't know what to write"
        )
    
    return user