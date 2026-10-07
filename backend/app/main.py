import os
import sys
from pathlib import Path

# Ensure both project root and backend directory are in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CURRENT_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent

for _p in [str(_ROOT_DIR), str(_BACKEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.auth import router as auth_router
from backend.app.api.data import router as data_router
from backend.app.api.students import router as students_router
from backend.app.api.subjects import router as subjects_router
from backend.app.api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables & seed initial HOD credentials on startup
    init_db()
    yield

app = FastAPI(
    title=f"{settings.PROJECT_NAME} ({settings.DEPARTMENT_CODE})",
    description="Phase 1: Academic Data Ingestion, Inspection, Cleaning, Normalization, Integration, Validation & HOD Intelligence Platform.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
if isinstance(settings.ALLOWED_ORIGINS, (list, tuple, set)):
    origins = list(settings.ALLOWED_ORIGINS)
elif isinstance(settings.ALLOWED_ORIGINS, str) and settings.ALLOWED_ORIGINS.strip():
    origins = [s.strip() for s in settings.ALLOWED_ORIGINS.split(",") if s.strip()]
else:
    origins = []

# Dynamically add from FRONTEND_URL or ALLOWED_ORIGINS env var if present
extra_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("FRONTEND_URL")
if extra_origins:
    for o in extra_origins.split(","):
        cleaned = o.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(students_router)
app.include_router(subjects_router)
app.include_router(dashboard_router)

@app.get("/")
def root():
    return {
        "status": "ONLINE",
        "system": settings.PROJECT_NAME,
        "college": settings.COLLEGE_NAME,
        "college_full_name": settings.COLLEGE_FULL_NAME,
        "department": settings.DEPARTMENT_NAME,
        "department_code": settings.DEPARTMENT_CODE,
        "authorized_user_role": settings.ALLOWED_ROLE,
        "phase": "PHASE 1 - Foundation & Data Intelligence",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "college": settings.COLLEGE_NAME,
        "department": settings.DEPARTMENT_CODE,
        "role": settings.ALLOWED_ROLE
    }
