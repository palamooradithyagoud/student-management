from sqlalchemy import Column, Integer, String, Float
from backend.app.core.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(String(50), unique=True, index=True, nullable=False)
    subject_code = Column(String(50), index=True, nullable=False)
    subject_name = Column(String(200), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Float, nullable=True)
