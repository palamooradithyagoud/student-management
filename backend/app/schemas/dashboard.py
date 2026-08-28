from typing import Optional, Any, List
from pydantic import BaseModel
from backend.app.schemas.data import UploadResponse

class AcademicDataOverview(BaseModel):
    total_students: int
    sem1_students: int
    sem2_students: int
    total_result_records: int
    total_attendance_records: int
    successfully_mapped_records: int
    mapping_success_rate: float
    data_quality_status: str  # "EXCELLENT", "GOOD", "NEEDS_REVIEW", "NO_DATA"

class QualityCounts(BaseModel):
    valid_records: int
    warnings: int
    errors: int
    records_requiring_review: int

class DatasetSummary(BaseModel):
    master_rows: int
    students_count: int
    subjects_count: int
    results_count: int
    attendance_count: int
    semester_summaries_count: int

class StudentPresenceBreakdown(BaseModel):
    present_in_all_datasets: int
    in_results_missing_attendance: int
    in_attendance_missing_results: int
    in_sem1_missing_sem2: int
    in_sem2_missing_sem1: int

class SubjectCardItem(BaseModel):
    subject_code: str
    subject_name: str
    semester: int
    student_count: int
    total_pass: Optional[int] = 0
    total_fail: Optional[int] = 0
    pass_rate: float
    pass_percentage: Optional[float] = 0.0
    average_attendance: float
    theme: str

class SectionPassRateItem(BaseModel):
    label: str
    short_label: str
    semester: int
    section: str
    pass_rate: float
    student_pass_rate: float
    student_count: int
    avg_sgpa: float
    avg_attendance: float
    highlight: bool = False

class TopStudentItem(BaseModel):
    rank: int
    roll_no: str
    student_name: str
    section: str
    cgpa: float
    s1_sgpa: Optional[float] = None
    s2_sgpa: Optional[float] = None
    attendance: float
    badge: str

class StudentActivityItem(BaseModel):
    roll_no: str
    student_name: str
    section: str
    status: str
    status_type: str
    time: str
    sgpa: float
    attendance: float

class DashboardOverviewResponse(BaseModel):
    department_code: str = "CSM"
    department_name: str
    hod_username: str
    overview: AcademicDataOverview
    data_quality: QualityCounts
    student_presence: StudentPresenceBreakdown
    dataset_summary: DatasetSummary
    subject_cards: List[SubjectCardItem] = []
    section_pass_rates: List[SectionPassRateItem] = []
    toppers: List[TopStudentItem] = []
    recent_student_activities: List[StudentActivityItem] = []
    recent_uploads: List[UploadResponse] = []
    last_processed_at: Optional[str] = None
