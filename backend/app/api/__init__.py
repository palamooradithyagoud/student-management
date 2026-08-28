from backend.app.api.auth import router as auth_router
from backend.app.api.data import router as data_router
from backend.app.api.students import router as students_router
from backend.app.api.subjects import router as subjects_router
from backend.app.api.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "data_router",
    "students_router",
    "subjects_router",
    "dashboard_router"
]
