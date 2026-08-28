from sqlalchemy import Column, Integer, String, Float
from backend.app.core.database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(String(100), unique=True, index=True, nullable=False)
    student_id = Column(String(50), index=True, nullable=False)
    roll_no = Column(String(50), index=True, nullable=False)
    subject_id = Column(String(50), index=True, nullable=False)
    subject_code = Column(String(50), index=True, nullable=False)
    semester = Column(Integer, nullable=False)
    attendance_percentage = Column(Float, nullable=False)
