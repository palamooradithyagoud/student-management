from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_current_hod(db: Session = Depends(get_db)) -> User:
    """
    Returns the CSM HOD user automatically without requiring token authentication.
    """
    user = db.query(User).filter(User.username == "hod.csm").first()
    if not user:
        user = User(
            id=1,
            username="hod.csm",
            full_name="Prof. M A JABBAR",
            email="hod.csm@vce.ac.in",
            role=settings.ALLOWED_ROLE,
            department=settings.DEPARTMENT_CODE,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    return user

@router.post("/login", response_model=Token)
def login(req: Optional[LoginRequest] = None, db: Session = Depends(get_db)):
    """
    Open login endpoint for backward compatibility.
    """
    return {"access_token": "open_access_token", "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_hod)):
    """
    Retrieve details of CSM HOD.
    """
    return current_user


