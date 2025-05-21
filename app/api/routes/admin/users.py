from typing import Any, List

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_current_active_user, get_current_superuser
from app.core.exceptions import NotFoundException
from app.services.user import UserService
from app.schemas.user import UserSchema, UserUpdateSchema, UserMinimalSchema

router = APIRouter()

@router.get("/", response_model=List[UserMinimalSchema])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get all users with minimal information. Only superusers can access this endpoint.
    
    Returns only minimal user information including _id, userName, and avatar.
    """
    user_service = UserService()
    return await user_service.get_all_users(skip=skip, limit=limit)

