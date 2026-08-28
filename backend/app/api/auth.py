from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token, decode_access_token
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_hod(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency to validate HOD JWT and enforce single-user HOD CSM role.
    Rejects any unauthenticated or unauthorized access with 401.
    """
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    role: str = payload.get("role")
    dept: str = payload.get("department")

    if not username or role != settings.ALLOWED_ROLE or dept != settings.DEPARTMENT_CODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or unauthorized role",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate HOD of CSM Department and return JWT Bearer token.
    Strictly accepts only valid HOD credentials.
    """
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.role != settings.ALLOWED_ROLE or user.department != settings.DEPARTMENT_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted exclusively to HOD of CSM Department"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_hod)):
    """
    Retrieve details of currently authenticated HOD.
    """
    return current_user
