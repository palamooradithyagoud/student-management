import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root directory is code/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Based Student Academic Risk & Performance Intelligence System"
    COLLEGE_NAME: str = "VCE College"
    COLLEGE_FULL_NAME: str = "Vardhaman College of Engineering"
    DEPARTMENT_CODE: str = "CSM"
    DEPARTMENT_NAME: str = "Computer Science and Engineering (Artificial Intelligence & Machine Learning)"
    ALLOWED_ROLE: str = "HOD"

    BASE_DIR: Path = BASE_DIR

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'academic_intelligence.db'}")

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
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "extra": "ignore"
    }

settings = Settings()

# Ensure directories exist
settings.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
