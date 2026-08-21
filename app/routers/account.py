from fastapi import APIRouter, Depends, HTTPException, status
from ..oauth2 import create_access_token
from ..schemas import Account_Details_In, Account_Details_Out
from ..utility import hash_password, verify_password
from ..import models
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(tags=["User Related EndPoints"])

@router.post('/signup')
async def sign_up(details: Account_Details_In, db: AsyncSession= Depends(get_db)):
    
    user = models.Users(**details.model_dump())
    
    user.password = hash_password(user.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)

@router.post('/login')
async def log_in(details: Account_Details_In, db: AsyncSession= Depends(get_db)):
    
    command = await db.execute(select(models.Users).where(models.Users.email == details.email))
    
    user = command.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or Password invalid"
        )
    
    password = details.password.get_secret_value()
    
    correct_password = verify_password(password, user.password)
    
    if not correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or Password invalid"
        )
    
    token = create_access_token(user.id)
    
    return {
        "access_token" : token,
        "token_type" : "bearer"
    }