import shutil
import re
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_hod
from backend.app.models.user import User
from backend.app.models.upload_log import UploadLog
from backend.app.services.ingestion.inspector import FileInspector
from backend.app.services.integration.pipeline import DataPipelineOrchestrator
from backend.app.schemas.data import (
    UploadResponse,
    FileInspectionResult,
    ProcessPipelineResponse,
    CleaningLogEntry,
    MappingReportEntry
)

router = APIRouter(prefix="/api/data", tags=["Data Management"])

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    return cleaned

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),  # sem1_results, sem2_results, sem1_attendance, sem2_attendance
    semester: int = Form(...),      # 1 or 2
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Upload and inspect an academic dataset (.xlsx, .xls, .csv) with full header & structure inspection.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only .xlsx, .xls, and .csv files are supported."
        )

    safe_name = sanitize_filename(f"{dataset_type}_{file.filename}")
    save_path = settings.DATA_RAW_DIR / safe_name

    # Save uploaded file
    with open(save_path, "wb") as buffer:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed limit of 50MB."
            )
        buffer.write(content)

    # Perform thorough inspection
    try:
        inspection_data = FileInspector.inspect_file(save_path)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error inspecting file: {str(e)}"
        )

    # Record in UploadLog database table
    upload_record = UploadLog(
        filename=safe_name,
        dataset_type=dataset_type,
        semester=semester,
        file_size=len(content),
        row_count=inspection_data.get("total_rows", 0),
        status="INSPECTED",
        meta_info=inspection_data
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    inspection_model = FileInspectionResult(**inspection_data)

    return UploadResponse(
        id=upload_record.id,
        filename=safe_name,
        dataset_type=dataset_type,
        semester=semester,
        file_size=upload_record.file_size,
        row_count=upload_record.row_count,
        status=upload_record.status,
        uploaded_at=upload_record.uploaded_at,
        inspection=inspection_model
    )

@router.get("/uploads", response_model=list[UploadResponse])
def list_uploads(
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """List all uploaded datasets with inspection metadata."""
    records = db.query(UploadLog).order_by(UploadLog.uploaded_at.desc()).all()
    out = []
    for r in records:
        insp = FileInspectionResult(**r.meta_info) if r.meta_info else None
        out.append(UploadResponse(
            id=r.id,
            filename=r.filename,
            dataset_type=r.dataset_type,
            semester=r.semester,
            file_size=r.file_size,
            row_count=r.row_count,
            status=r.status,
            uploaded_at=r.uploaded_at,
            inspection=insp
        ))
    return out

@router.post("/process", response_model=ProcessPipelineResponse)
def process_pipeline(
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Trigger the complete data ingestion, cleaning, normalization,
    integration, validation, and master dataset generation pipeline.
    """
    orchestrator = DataPipelineOrchestrator(db=db)
    result = orchestrator.run_pipeline()

    # Update upload statuses to PROCESSED
    db.query(UploadLog).update({"status": "PROCESSED"})
    db.commit()

    return ProcessPipelineResponse(
        status=result["status"],
        message=result["message"],
        execution_time_seconds=result["execution_time_seconds"],
        total_students=result["total_students"],
        sem1_students=result["sem1_students"],
        sem2_students=result["sem2_students"],
        total_results=result["total_results"],
        total_attendance=result["total_attendance"],
        matched_records=result["matched_records"],
        unmatched_records=result["unmatched_records"],
        mapping_success_rate=result["mapping_success_rate"],
        generated_files=result["generated_files"],
        critical_errors=result["critical_errors"],
        warnings=result["warnings"],
        records_requiring_review=result["records_requiring_review"]
    )

@router.get("/quality-report")
def get_quality_report(current_user: User = Depends(get_current_hod)):
    """Retrieve the generated CSM academic data quality report (JSON format)."""
    json_path = settings.DATA_REPORTS_DIR / "data_quality_report.json"
    if not json_path.exists():
        # Fallback: run pipeline once if files exist, else return empty structure
        orchestrator = DataPipelineOrchestrator()
        res = orchestrator.run_pipeline()
        return res["quality_report"]

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/quality-report-md")
def get_quality_report_md(current_user: User = Depends(get_current_hod)):
    """Retrieve the raw markdown text of the CSM academic data quality report."""
    md_path = settings.DATA_REPORTS_DIR / "data_quality_report.md"
    if not md_path.exists():
        return {"report_markdown": "No quality report generated yet. Please process the datasets."}
    with open(md_path, "r", encoding="utf-8") as f:
        return {"report_markdown": f.read()}

@router.get("/mapping-report", response_model=list[MappingReportEntry])
def get_mapping_report(
    limit: int = 200,
    offset: int = 0,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_hod)
):
    """Retrieve mapping report entries showing Result <-> Attendance match status."""
    csv_path = settings.DATA_REPORTS_DIR / "mapping_report.csv"
    if not csv_path.exists():
        return []
    df = pd.read_csv(csv_path)
    if status_filter:
        df = df[df["mapping_status"] == status_filter]
    df_paged = df.iloc[offset:offset+limit]
    return df_paged.to_dict(orient="records")

@router.get("/cleaning-logs", response_model=list[CleaningLogEntry])
def get_cleaning_logs(
    limit: int = 200,
    offset: int = 0,
    current_user: User = Depends(get_current_hod)
):
    """Retrieve the audit log of all transformations applied during cleaning."""
    csv_path = settings.DATA_REPORTS_DIR / "data_cleaning_log.csv"
    if not csv_path.exists():
        return []
    df = pd.read_csv(csv_path).fillna("")
    df_paged = df.iloc[offset:offset+limit]
    return df_paged.to_dict(orient="records")

@router.get("/download/{filename}")
def download_processed_file(filename: str, current_user: User = Depends(get_current_hod)):
    """Securely download a generated CSV dataset or report file."""
    allowed_files = {
        "students.csv": settings.DATA_PROCESSED_DIR / "students.csv",
        "subjects.csv": settings.DATA_PROCESSED_DIR / "subjects.csv",
        "results.csv": settings.DATA_PROCESSED_DIR / "results.csv",
        "attendance.csv": settings.DATA_PROCESSED_DIR / "attendance.csv",
        "semester_summary.csv": settings.DATA_PROCESSED_DIR / "semester_summary.csv",
        "master_dataset.csv": settings.DATA_PROCESSED_DIR / "master_dataset.csv",
        "student_semester_summary.csv": settings.DATA_PROCESSED_DIR / "student_semester_summary.csv",
        "subject_mapping.csv": settings.DATA_PROCESSED_DIR / "subject_mapping.csv",
        "data_quality_report.json": settings.DATA_REPORTS_DIR / "data_quality_report.json",
        "data_quality_report.md": settings.DATA_REPORTS_DIR / "data_quality_report.md",
        "data_cleaning_log.csv": settings.DATA_REPORTS_DIR / "data_cleaning_log.csv",
        "mapping_report.csv": settings.DATA_REPORTS_DIR / "mapping_report.csv",
    }

    if filename not in allowed_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requested file '{filename}' is not recognized or not available for download."
        )

    file_path = allowed_files[filename]
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' has not been generated yet. Please process the datasets first."
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
