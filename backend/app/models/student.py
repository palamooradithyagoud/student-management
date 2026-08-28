from sqlalchemy import Column, Integer, String
from backend.app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    roll_no = Column(String(50), unique=True, index=True, nullable=False)
    student_name = Column(String(200), nullable=True)
    section = Column(String(20), nullable=True)
    batch = Column(String(50), nullable=True)
