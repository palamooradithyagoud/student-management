from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from backend.app.core.database import Base

class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    dataset_type = Column(String(50), nullable=False)  # sem1_results, sem2_results, sem1_attendance, sem2_attendance
    semester = Column(Integer, nullable=False)          # 1 or 2
    file_size = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="UPLOADED")  # UPLOADED, INSPECTED, PROCESSED, ERROR
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    meta_info = Column(JSON, nullable=True)
