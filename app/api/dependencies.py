from typing import Optional

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.db.repositories import UserRepository
from app.models import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    """Get current authenticated user."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedException(detail="Missing user ID in token")
    except (JWTError, ValidationError):
        raise UnauthorizedException(detail="Could not validate credentials")
    
    user_repo = UserRepository()
    user = await user_repo.get(user_id)
    
    if user is None:
        raise UnauthorizedException(detail="User not found")
    
    if not user.get("is_active", False):
        raise ForbiddenException(detail="Inactive user")
    
    return user

async def get_current_active_user(current_user = Depends(get_current_user)) -> UserModel:
    """Get current active user."""
    if not current_user.get("is_active", False):
        raise ForbiddenException(detail="Inactive user")
    return current_user

async def get_current_superuser(current_user = Depends(get_current_user)) -> UserModel:
    """Get current superuser."""
    if not current_user.get("is_superuser", False):
        raise ForbiddenException(detail="Not enough permissions")
    return current_user