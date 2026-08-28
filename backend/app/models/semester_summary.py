from sqlalchemy import Column, Integer, String, Float
from backend.app.core.database import Base

class SemesterSummary(Base):
    __tablename__ = "semester_summary"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), index=True, nullable=False)
    roll_no = Column(String(50), index=True, nullable=False)
    semester = Column(Integer, nullable=False)
    sgpa = Column(Float, nullable=True)
    backlog_count = Column(Integer, nullable=True)
