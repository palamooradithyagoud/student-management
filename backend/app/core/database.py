from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

# Configure SQLite or PostgreSQL engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create tables and ensure the default HOD user exists."""
    from backend.app.models.user import User
    from backend.app.core.security import get_password_hash
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        hod_user = db.query(User).filter(User.username == settings.HOD_USERNAME).first()
        if not hod_user:
            hod_user = User(
                username=settings.HOD_USERNAME,
                password_hash=get_password_hash(settings.HOD_PASSWORD),
                role=settings.ALLOWED_ROLE,
                department=settings.DEPARTMENT_CODE,
                is_active=True
            )
            db.add(hod_user)
            db.commit()
            print(f"[INIT_DB] Seeded default HOD user: {settings.HOD_USERNAME}")
    except Exception as e:
        db.rollback()
        print(f"[INIT_DB] Error seeding initial HOD user: {e}")
    finally:
        db.close()
