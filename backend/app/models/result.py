from sqlalchemy import Column, Integer, String, Float
from backend.app.core.database import Base

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(String(100), unique=True, index=True, nullable=False)
    student_id = Column(String(50), index=True, nullable=False)
    roll_no = Column(String(50), index=True, nullable=False)
    subject_id = Column(String(50), index=True, nullable=False)
    subject_code = Column(String(50), index=True, nullable=False)
    semester = Column(Integer, nullable=False)
    marks = Column(Float, nullable=True)
    grade = Column(String(20), nullable=True)
    grade_point = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)
