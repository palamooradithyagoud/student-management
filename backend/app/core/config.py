import json
import os
from pathlib import Path
from typing import Any, Union
from urllib.parse import unquote, quote_plus
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Dynamically resolve project directory structure
_CONFIG_DIR = Path(__file__).resolve().parent
_APP_DIR = _CONFIG_DIR.parent
_BACKEND_DIR = _APP_DIR.parent
_REPO_ROOT = _BACKEND_DIR.parent

# Prefer REPO_ROOT if it contains the data directory or database, else BACKEND_DIR
if (_REPO_ROOT / "data").exists() or (_REPO_ROOT / "academic_intelligence.db").exists():
    BASE_DIR = _REPO_ROOT
else:
    BASE_DIR = _BACKEND_DIR

def sanitize_database_url(url: str) -> str:
    """Sanitize database URL for SQLAlchemy 2.0+ and URL-encode special chars in password."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "://" in url:
        scheme, remainder = url.split("://", 1)
        if "@" in remainder:
            last_at_idx = remainder.rfind("@")
            user_pass = remainder[:last_at_idx]
            host_db = remainder[last_at_idx + 1:]
            if ":" in user_pass:
                first_colon_idx = user_pass.find(":")
                username = user_pass[:first_colon_idx]
                raw_password = user_pass[first_colon_idx + 1:]
                clean_password = quote_plus(unquote(raw_password))
                return f"{scheme}://{username}:{clean_password}@{host_db}"
    return url

_raw_db_url = sanitize_database_url(os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'academic_intelligence.db'}"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Based Student Academic Risk & Performance Intelligence System"
    COLLEGE_NAME: str = "VCE College"
    COLLEGE_FULL_NAME: str = "Vardhaman College of Engineering"
    DEPARTMENT_CODE: str = "CSM"
    DEPARTMENT_NAME: str = "Computer Science and Engineering (Artificial Intelligence & Machine Learning)"
    ALLOWED_ROLE: str = "HOD"

    BASE_DIR: Path = BASE_DIR

    # Database
    DATABASE_URL: str = _raw_db_url

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        return sanitize_database_url(v)

    # Security / JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "csm_academic_intelligence_super_secret_jwt_key_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Initial HOD Credentials
    HOD_USERNAME: str = os.getenv("HOD_USERNAME", "hod.csm")
    HOD_PASSWORD: str = os.getenv("HOD_PASSWORD", "hod_csm_secure_2026")

    # Data Storage Paths
    DATA_DIR: Path = BASE_DIR / "data"
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    DATA_REPORTS_DIR: Path = BASE_DIR / "data" / "reports"

    # CORS
    ALLOWED_ORIGINS: Any = [
        # Production — Vercel frontend
        "https://student-management-csm.vercel.app",
        "https://student-management-palamooradithyagouds-projects.vercel.app",
        # Production — old Render deploy (kept for compatibility)
        "https://student-management-frontend-hr9l.onrender.com",
        # Local development
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [o.strip() for o in v.replace(";", ",").split(",") if o.strip()]
        if isinstance(v, (list, tuple, set)):
            return list(v)
        return []

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "extra": "ignore"
    }

settings = Settings()

# Ensure directories exist
settings.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
