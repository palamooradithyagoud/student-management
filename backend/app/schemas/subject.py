from typing import Optional
from pydantic import BaseModel

class SubjectRead(BaseModel):
    id: int
    subject_id: str
    subject_code: str
    subject_name: str
    semester: int
    credits: Optional[float] = None
    total_students: Optional[int] = 0
    total_pass: Optional[int] = 0
    total_fail: Optional[int] = 0
    pass_percentage: Optional[float] = 0.0
    avg_attendance: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

class SubjectMappingRead(BaseModel):
    source_file: str
    original_subject_code: str
    original_subject_name: str
    standard_subject_code: str
    standard_subject_name: str
    status: str = "MATCHED"

class SubjectListResponse(BaseModel):
    total: int
    items: list[SubjectRead]
    mappings: list[SubjectMappingRead] = []
