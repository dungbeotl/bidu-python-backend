from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token
from app.db.repositories.user import UserRepository
from app.schemas.user import UserSchema

router = APIRouter()

@router.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user_repo = UserRepository()
    user = await user_repo.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise UnauthorizedException(detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user["_id"]), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
    }
