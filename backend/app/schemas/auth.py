from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    department: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

