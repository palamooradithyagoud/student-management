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
from backend.app.models.student import Student
from backend.app.models.subject import Subject
from backend.app.models.result import Result
from backend.app.models.attendance import Attendance
from backend.app.models.semester_summary import SemesterSummary
from backend.app.services.ingestion.inspector import FileInspector
from backend.app.services.integration.pipeline import DataPipelineOrchestrator
from datetime import datetime, timezone
from backend.app.models.batch import Batch
from backend.app.schemas.data import (
    UploadResponse,
    FileInspectionResult,
    ProcessPipelineResponse,
    CleaningLogEntry,
    MappingReportEntry,
    BatchCreate,
    BatchRead,
    BatchStatusResponse,
    SemesterStatus,
    SectionAttendanceSummary
)

router = APIRouter(prefix="/api/data", tags=["Data Management"])

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

DEFAULT_BATCHES = [
    {"name": "2024-2028", "regulation": "R22", "start_year": 2024, "end_year": 2028, "is_active": True},
    {"name": "2023-2027", "regulation": "R22", "start_year": 2023, "end_year": 2027, "is_active": False},
    {"name": "2022-2026", "regulation": "R22", "start_year": 2022, "end_year": 2026, "is_active": False},
    {"name": "2021-2025", "regulation": "R18", "start_year": 2021, "end_year": 2025, "is_active": False},
]

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    return cleaned

@router.get("/batches", response_model=list[BatchRead])
def list_batches(
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """List all academic batches; automatically seeds default batches if none exist."""
    batches = db.query(Batch).order_by(Batch.name.desc()).all()
    if not batches:
        for b in DEFAULT_BATCHES:
            db.add(Batch(
                name=b["name"],
                department="CSM",
                regulation=b["regulation"],
                start_year=b["start_year"],
                end_year=b["end_year"],
                is_active=b["is_active"]
            ))
        db.commit()
        batches = db.query(Batch).order_by(Batch.name.desc()).all()
    return batches

@router.post("/batches", response_model=BatchRead)
def create_batch(
    payload: BatchCreate,
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Create a new academic batch (e.g. 2025-2029)."""
    existing = db.query(Batch).filter(Batch.name == payload.name.strip()).first()
    if existing:
        return existing
    
    batch_obj = Batch(
        name=payload.name.strip(),
        department="CSM",
        regulation=payload.regulation,
        start_year=payload.start_year,
        end_year=payload.end_year,
        is_active=True
    )
    db.add(batch_obj)
    db.commit()
    db.refresh(batch_obj)
    return batch_obj

@router.get("/batch-status", response_model=BatchStatusResponse)
def get_batch_status(
    batch_name: str = "2024-2028",
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Get upload status for each semester (1 to 8) for the selected batch directly from database."""
    logs = db.query(UploadLog).filter(
        UploadLog.batch_name == batch_name
    ).order_by(UploadLog.uploaded_at.desc()).all()

    sem_statuses = []
    for sem in range(1, 9):
        sem_logs = [l for l in logs if l.semester == sem]
        res_log = next(
            (l for l in sem_logs if "result" in l.dataset_type.lower() or l.section == "OVERALL" or "res" in l.filename.lower()),
            None
        )

        att_sections = []
        seen_secs = set()
        for l in sem_logs:
            if "attendance" in l.dataset_type.lower() or "att" in l.filename.lower():
                sec = l.section or "A"
                if sec not in seen_secs:
                    seen_secs.add(sec)
                    att_sections.append(SectionAttendanceSummary(
                        section=sec,
                        filename=l.filename,
                        row_count=l.row_count,
                        uploaded_at=l.uploaded_at
                    ))

        sem_statuses.append(SemesterStatus(
            semester=sem,
            result_uploaded=bool(res_log),
            result_filename=res_log.filename if res_log else None,
            result_row_count=res_log.row_count if res_log else None,
            result_uploaded_at=res_log.uploaded_at if res_log else None,
            attendance_sections=att_sections
        ))

    return BatchStatusResponse(batch_name=batch_name, semesters=sem_statuses)

@router.post("/upload/attendance", response_model=UploadResponse)
async def upload_section_attendance(
    file: UploadFile = File(...),
    batch_name: str = Form("2024-2028"),
    semester: int = Form(...),      # 1 to 8
    section: str = Form(...),       # 'A', 'B', 'C', 'D'
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Upload attendance file for a specific section (e.g. Section A, B, C) in a semester."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only .xlsx, .xls, and .csv files are supported."
        )

    clean_sec = section.strip().upper()
    clean_batch = batch_name.strip()
    safe_name = sanitize_filename(f"attendance_{clean_batch}_sem{semester}_sec{clean_sec}_{file.filename}")
    save_path = settings.DATA_RAW_DIR / safe_name

    with open(save_path, "wb") as buffer:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed limit of 50MB."
            )
        buffer.write(content)

    try:
        inspection_data = FileInspector.inspect_file(save_path)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error inspecting attendance file: {str(e)}"
        )

    upload_record = UploadLog(
        filename=safe_name,
        dataset_type="attendance",
        batch_name=clean_batch,
        section=clean_sec,
        semester=semester,
        file_size=len(content),
        row_count=inspection_data.get("total_rows", 0),
        status="INSPECTED",
        meta_info=inspection_data
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    return UploadResponse(
        id=upload_record.id,
        filename=safe_name,
        dataset_type="attendance",
        batch_name=clean_batch,
        section=clean_sec,
        semester=semester,
        file_size=upload_record.file_size,
        row_count=upload_record.row_count,
        status=upload_record.status,
        uploaded_at=upload_record.uploaded_at,
        inspection=FileInspectionResult(**inspection_data)
    )

@router.post("/upload/results", response_model=UploadResponse)
async def upload_overall_results(
    file: UploadFile = File(...),
    batch_name: str = Form("2024-2028"),
    semester: int = Form(...),      # 1 to 8
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Upload overall semester result file covering all students/sections."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only .xlsx, .xls, and .csv files are supported."
        )

    clean_batch = batch_name.strip()
    safe_name = sanitize_filename(f"results_{clean_batch}_sem{semester}_overall_{file.filename}")
    save_path = settings.DATA_RAW_DIR / safe_name

    with open(save_path, "wb") as buffer:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed limit of 50MB."
            )
        buffer.write(content)

    try:
        inspection_data = FileInspector.inspect_file(save_path)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error inspecting result file: {str(e)}"
        )

    upload_record = UploadLog(
        filename=safe_name,
        dataset_type="results",
        batch_name=clean_batch,
        section="OVERALL",
        semester=semester,
        file_size=len(content),
        row_count=inspection_data.get("total_rows", 0),
        status="INSPECTED",
        meta_info=inspection_data
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    return UploadResponse(
        id=upload_record.id,
        filename=safe_name,
        dataset_type="results",
        batch_name=clean_batch,
        section="OVERALL",
        semester=semester,
        file_size=upload_record.file_size,
        row_count=upload_record.row_count,
        status=upload_record.status,
        uploaded_at=upload_record.uploaded_at,
        inspection=FileInspectionResult(**inspection_data)
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    semester: int = Form(...),
    batch_name: Optional[str] = Form("2024-2028"),
    section: Optional[str] = Form(None),
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Legacy upload endpoint."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only .xlsx, .xls, and .csv files are supported."
        )

    clean_sec = (section or ("OVERALL" if "result" in dataset_type else "A")).strip().upper()
    safe_name = sanitize_filename(f"{dataset_type}_{file.filename}")
    save_path = settings.DATA_RAW_DIR / safe_name

    with open(save_path, "wb") as buffer:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed limit of 50MB."
            )
        buffer.write(content)

    try:
        inspection_data = FileInspector.inspect_file(save_path)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error inspecting file: {str(e)}"
        )

    upload_record = UploadLog(
        filename=safe_name,
        dataset_type=dataset_type,
        batch_name=batch_name,
        section=clean_sec,
        semester=semester,
        file_size=len(content),
        row_count=inspection_data.get("total_rows", 0),
        status="INSPECTED",
        meta_info=inspection_data
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    return UploadResponse(
        id=upload_record.id,
        filename=safe_name,
        dataset_type=dataset_type,
        batch_name=batch_name,
        section=clean_sec,
        semester=semester,
        file_size=upload_record.file_size,
        row_count=upload_record.row_count,
        status=upload_record.status,
        uploaded_at=upload_record.uploaded_at,
        inspection=FileInspectionResult(**inspection_data)
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
            batch_name=r.batch_name,
            section=r.section,
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
    batch_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Trigger the complete data ingestion, cleaning, normalization,
    integration, validation, and master dataset generation pipeline for the batch.
    """
    orchestrator = DataPipelineOrchestrator(db=db)
    result = orchestrator.run_pipeline(batch_name=batch_name)

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
        records_requiring_review=result["records_requiring_review"],
        # Detained students are normal institutional outcomes, not errors
        detained_students_count=result.get("detained_students_count", 0),
        detained_students=result.get("detained_students", [])
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

@router.delete("/uploads/{upload_id}")
def delete_upload_record(
    upload_id: int,
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Delete a specific upload record and its underlying raw file."""
    record = db.query(UploadLog).filter(UploadLog.id == upload_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload record #{upload_id} not found."
        )

    raw_file = settings.DATA_RAW_DIR / record.filename
    if raw_file.exists():
        try:
            raw_file.unlink()
        except Exception as e:
            print(f"[DELETE_FILE_WARNING] Failed to remove {raw_file}: {e}")

    db.delete(record)
    db.commit()
    return {"status": "SUCCESS", "message": f"Upload record #{upload_id} ({record.filename}) deleted successfully."}

@router.delete("/section-attendance")
def delete_section_attendance(
    batch_name: str,
    semester: int,
    section: str,
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Delete section attendance upload records, raw files, and database attendance rows for a given semester & section."""
    sec_upper = section.strip().upper()
    records = db.query(UploadLog).filter(
        UploadLog.semester == semester,
        UploadLog.section == sec_upper,
        (UploadLog.batch_name == batch_name) | (UploadLog.batch_name.is_(None))
    ).all()

    for r in records:
        f_path = settings.DATA_RAW_DIR / r.filename
        if f_path.exists():
            try:
                f_path.unlink()
            except Exception:
                pass
        db.delete(r)

    pattern = f"*attendance*{batch_name}*sem{semester}*sec{sec_upper}*"
    for f in settings.DATA_RAW_DIR.glob(pattern):
        try:
            f.unlink()
        except Exception:
            pass

    # Delete matching records from Attendance table for this semester & students in this section
    try:
        students_in_sec = db.query(Student.roll_no).filter(
            Student.section == sec_upper
        ).all()
        sec_rolls = [s[0] for s in students_in_sec]
        if sec_rolls:
            db.query(Attendance).filter(
                Attendance.semester == semester,
                Attendance.roll_no.in_(sec_rolls)
            ).delete(synchronize_session=False)
    except Exception as e:
        print(f"[ATTENDANCE_DB_DELETE_WARN] {e}")

    db.commit()
    return {"status": "SUCCESS", "message": f"Attendance for Semester {semester} Section {sec_upper} deleted from database and file records."}

@router.delete("/semester-result")
def delete_semester_result(
    batch_name: str,
    semester: int,
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """Delete overall result upload records, raw files, and database results/summaries for a given semester."""
    records = db.query(UploadLog).filter(
        UploadLog.semester == semester,
        UploadLog.dataset_type == "results",
        (UploadLog.batch_name == batch_name) | (UploadLog.batch_name.is_(None))
    ).all()

    for r in records:
        f_path = settings.DATA_RAW_DIR / r.filename
        if f_path.exists():
            try:
                f_path.unlink()
            except Exception:
                pass
        db.delete(r)

    pattern = f"*results*{batch_name}*sem{semester}*"
    for f in settings.DATA_RAW_DIR.glob(pattern):
        try:
            f.unlink()
        except Exception:
            pass

    # Delete Result and SemesterSummary rows for this semester from database
    try:
        db.query(Result).filter(Result.semester == semester).delete(synchronize_session=False)
        db.query(SemesterSummary).filter(SemesterSummary.semester == semester).delete(synchronize_session=False)
    except Exception as e:
        print(f"[RESULT_DB_DELETE_WARN] {e}")

    db.commit()
    return {"status": "SUCCESS", "message": f"Overall results and summaries for Semester {semester} deleted from database."}

@router.delete("/clear-database")
def clear_ingested_database(
    purge_uploads: bool = True,
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Completely clear/reset all ingested academic records from database and processed files.
    Preserves HOD admin login in 'users' and academic batches in 'batches'.
    """
    try:
        db.query(Attendance).delete()
        db.query(Result).delete()
        db.query(SemesterSummary).delete()
        db.query(Subject).delete()
        db.query(Student).delete()
        db.query(UploadLog).delete()
        db.commit()

        # Delete all files in raw, processed, and reports directories
        for f in settings.DATA_RAW_DIR.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass

        for fname in ["students.csv", "subjects.csv", "results.csv", "attendance.csv", "semester_summary.csv", "master_dataset.csv", "student_semester_summary.csv", "subject_mapping.csv"]:
            p = settings.DATA_PROCESSED_DIR / fname
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        for rname in ["data_quality_report.json", "data_quality_report.md", "data_cleaning_log.csv", "mapping_report.csv"]:
            p = settings.DATA_REPORTS_DIR / rname
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        return {"status": "SUCCESS", "message": "All ingested academic records (students, subjects, results, attendance, summaries, uploads) have been completely cleared from the database."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing database: {str(e)}"
        )
