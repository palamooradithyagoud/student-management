from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel

class FileInspectionResult(BaseModel):
    filename: str
    extension: str
    num_sheets: int
    sheet_names: list[str]
    detected_header_row: int
    original_columns: list[str]
    column_mappings: dict[str, str]
    total_rows: int
    sample_records: list[dict[str, Any]]
    missing_value_summary: dict[str, int]
    duplicate_rows_detected: int
    detected_dataset_type: Optional[str] = None
    detected_semester: Optional[int] = None
    warnings: list[str] = []

class UploadResponse(BaseModel):
    id: int
    filename: str
    dataset_type: str
    semester: int
    file_size: int
    row_count: int
    status: str
    uploaded_at: datetime
    inspection: Optional[FileInspectionResult] = None

class ProcessPipelineResponse(BaseModel):
    status: str
    message: str
    execution_time_seconds: float
    total_students: int
    sem1_students: int
    sem2_students: int
    total_results: int
    total_attendance: int
    matched_records: int
    unmatched_records: int
    mapping_success_rate: float
    generated_files: list[str]
    critical_errors: int
    warnings: int
    records_requiring_review: int

class CleaningLogEntry(BaseModel):
    source_file: str
    record_identifier: str
    issue: str
    action_taken: str
    reason: str

class MappingReportEntry(BaseModel):
    roll_no: str
    semester: int
    subject_code: str
    has_result: bool
    has_attendance: bool
    mapping_status: str
