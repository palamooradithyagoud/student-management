import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.subject import Subject
from backend.app.models.result import Result
from backend.app.models.attendance import Attendance
from backend.app.models.semester_summary import SemesterSummary
from backend.app.models.upload_log import UploadLog
from backend.app.main import app

# Use in-memory SQLite with StaticPool so the tables persist across sessions in the test process
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    # Create test HOD user
    hod_user = User(
        username="hod.csm",
        password_hash=get_password_hash("hod_csm_secure_2026"),
        role="HOD",
        department="CSM",
        is_active=True
    )
    db.add(hod_user)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def hod_token(client):
    res = client.post("/api/auth/login", json={
        "username": "hod.csm",
        "password": "hod_csm_secure_2026"
    })
    return res.json()["access_token"]

@pytest.fixture
def auth_headers(hod_token):
    return {"Authorization": f"Bearer {hod_token}"}
