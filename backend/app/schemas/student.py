from typing import Optional
from pydantic import BaseModel

class StudentBase(BaseModel):
    student_id: str
    roll_no: str
    student_name: Optional[str] = None
    section: Optional[str] = None
    batch: Optional[str] = None

class StudentRead(StudentBase):
    id: int
    sem1_present: bool = False
    sem2_present: bool = False
    has_results: bool = False
    has_attendance: bool = False
    status_category: str = "Active"
    sem1_sgpa: Optional[float] = None
    sem2_sgpa: Optional[float] = None
    sem1_back: Optional[int] = 0
    sem2_back: Optional[int] = 0
    overall_sgpa: Optional[float] = None
    rank: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class StudentSemesterSummaryRead(BaseModel):
    roll_no: str
    student_name: Optional[str] = None
    section: Optional[str] = None
    semester: int
    sgpa: Optional[float] = None
    backlog_count: Optional[int] = None
    average_attendance: Optional[float] = None
    failed_subject_count: int = 0
    passed_subject_count: int = 0
    sgpa_change: Optional[float] = None
    attendance_change: Optional[float] = None
    backlog_change: Optional[int] = None

class StudentListResponse(BaseModel):
    total: int
    items: list[StudentRead]
