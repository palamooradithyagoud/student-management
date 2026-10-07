import json
from pathlib import Path
from fastapi import APIRouter, Depends
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
from backend.app.schemas.dashboard import (
    DashboardOverviewResponse,
    AcademicDataOverview,
    QualityCounts,
    DatasetSummary,
    StudentPresenceBreakdown
)
from backend.app.schemas.data import UploadResponse, FileInspectionResult

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive CSM HOD Dashboard overview statistics,
    data quality health, mapping status, and recent uploads directly from database.
    """
    # 1. Check live database state
    db_students_count = db.query(Student).count()
    db_results_count = db.query(Result).count()
    db_attendance_count = db.query(Attendance).count()
    db_subjects_count = db.query(Subject).count()
    db_summary_count = db.query(SemesterSummary).count()

    recent_records = db.query(UploadLog).order_by(UploadLog.uploaded_at.desc()).limit(10).all()
    recent_uploads = []
    for r in recent_records:
        insp = FileInspectionResult(**r.meta_info) if r.meta_info else None
        recent_uploads.append(UploadResponse(
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

    # If database has NO students or NO results, return 100% clean empty state
    if db_students_count == 0 or db_results_count == 0:
        return {
            "department_code": settings.DEPARTMENT_CODE,
            "department_name": settings.DEPARTMENT_NAME,
            "hod_username": current_user.username,
            "overview": {
                "total_students": 0,
                "sem1_students": 0,
                "sem2_students": 0,
                "total_result_records": db_results_count,
                "total_attendance_records": db_attendance_count,
                "successfully_mapped_records": 0,
                "mapping_success_rate": 0.0,
                "data_quality_status": "NO_DATA"
            },
            "data_quality": {
                "valid_records": 0,
                "warnings": 0,
                "errors": 0,
                "records_requiring_review": 0
            },
            "student_presence": {
                "present_in_all_datasets": 0,
                "in_results_missing_attendance": 0,
                "in_attendance_missing_results": 0,
                "in_sem1_missing_sem2": 0,
                "in_sem2_missing_sem1": 0
            },
            "dataset_summary": {
                "master_rows": 0,
                "students_count": db_students_count,
                "subjects_count": db_subjects_count,
                "results_count": db_results_count,
                "attendance_count": db_attendance_count,
                "semester_summaries_count": db_summary_count
            },
            "subject_cards": [],
            "section_pass_rates": [],
            "toppers": [],
            "recent_student_activities": [],
            "recent_uploads": recent_uploads,
            "last_processed_at": None
        }

    json_path = settings.DATA_REPORTS_DIR / "data_quality_report.json"
    quality_data = {}
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            quality_data = json.load(f)

    def count_csv(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return len(pd.read_csv(path))
        except Exception:
            return 0

    master_rows = count_csv(settings.DATA_PROCESSED_DIR / "master_dataset.csv")
    students_count = db_students_count
    subjects_count = db_subjects_count
    results_count = db_results_count
    attendance_count = db_attendance_count
    semester_sum_count = db_summary_count

    stu_info = quality_data.get("students", {})
    mapping_info = quality_data.get("mapping", {})
    qual_info = quality_data.get("data_quality", {})

    total_stus = db_students_count
    sem1_stus = db.query(SemesterSummary.student_id).filter(SemesterSummary.semester == 1).distinct().count()
    sem2_stus = db.query(SemesterSummary.student_id).filter(SemesterSummary.semester == 2).distinct().count()

    raw_rate_str = str(mapping_info.get("mapping_success_rate", "0%")).replace("%", "")
    try:
        success_rate = float(raw_rate_str)
    except ValueError:
        success_rate = 0.0

    crit_errors = qual_info.get("critical_errors", 0)
    warnings = qual_info.get("warnings", 0)
    if master_rows == 0:
        quality_status = "NO_DATA"
    elif crit_errors == 0 and warnings < 5 and success_rate >= 95.0:
        quality_status = "EXCELLENT"
    elif crit_errors < 5 and success_rate >= 80.0:
        quality_status = "GOOD"
    else:
        quality_status = "NEEDS_REVIEW"

    # Calculate dynamic subject analytics and student performance from master_dataset
    master_csv = settings.DATA_PROCESSED_DIR / "master_dataset.csv"
    subject_cards = []
    subject_chart = []
    section_pass_rates = []
    toppers = []
    recent_student_activities = []

    if master_csv.exists():
        try:
            m_df = pd.read_csv(master_csv)
            
            # 1. Top 4 Most Failed Subject Hero Cards (Ranked dynamically by total_fail descending)
            color_themes = ["peach", "purple", "rose", "sky"]
            sub_stats = []
            
            for (code, sem), grp in m_df.groupby(["subject_code", "semester"]):
                tot_students = len(grp)
                tot_fail = int((grp["status"] == "FAIL").sum())
                tot_pass = int((grp["status"] == "PASS").sum())
                pass_rate = round(tot_pass / tot_students * 100.0, 1) if tot_students > 0 else 0.0
                avg_attn = round(grp["attendance_percentage"].mean(), 1) if ("attendance_percentage" in grp.columns and pd.notna(grp["attendance_percentage"].mean())) else 85.0
                resolved_name = str(grp["subject_name"].iloc[0]) if ("subject_name" in grp.columns and pd.notna(grp["subject_name"].iloc[0])) else str(code)
                
                sub_stats.append({
                    "subject_code": str(code),
                    "subject_name": resolved_name,
                    "semester": int(sem),
                    "student_count": int(grp["roll_no"].nunique()),
                    "total_pass": tot_pass,
                    "total_fail": tot_fail,
                    "pass_rate": pass_rate,
                    "pass_percentage": pass_rate,
                    "average_attendance": avg_attn,
                })
            
            # Sort by highest failure count descending, then lowest pass rate
            sub_stats.sort(key=lambda s: (-s["total_fail"], s["pass_rate"]))
            
            for idx, card in enumerate(sub_stats[:4]):
                card["theme"] = color_themes[idx % len(color_themes)]
                subject_cards.append(card)

            # 2. 6 Section-Wise Pass Percentages (Sem 1 A, Sem 2 A, Sem 1 B, Sem 2 B, Sem 1 C, Sem 2 C)
            section_pass_rates = []
            sec_sem_pairs = [
                (1, "A", "Sem 1 CSM A", "1-CSM-A"),
                (2, "A", "Sem 2 CSM A", "2-CSM-A"),
                (1, "B", "Sem 1 CSM B", "1-CSM-B"),
                (2, "B", "Sem 2 CSM B", "2-CSM-B"),
                (1, "C", "Sem 1 CSM C", "1-CSM-C"),
                (2, "C", "Sem 2 CSM C", "2-CSM-C"),
            ]

            max_pass_rate = 0.0
            temp_list = []
            for sem, sec, lbl, sh_lbl in sec_sem_pairs:
                ss_df = m_df[(m_df["section"] == sec) & (m_df["semester"] == sem)]
                if not ss_df.empty:
                    tot_exams = len(ss_df)
                    pass_exams = (ss_df["status"] == "PASS").sum()
                    exam_rate = round(pass_exams / tot_exams * 100.0, 1)

                    stu_grp = ss_df.groupby("roll_no")
                    tot_stus = len(stu_grp)
                    pass_stus = sum(1 for _, g in stu_grp if (g["status"] == "PASS").all())
                    stu_rate = round(pass_stus / tot_stus * 100.0, 1)

                    avg_sgpa = round(ss_df["sgpa"].dropna().mean(), 2) if not ss_df["sgpa"].dropna().empty else 7.5
                    avg_att = round(ss_df["attendance_percentage"].dropna().mean(), 1) if not ss_df["attendance_percentage"].dropna().empty else 85.0

                    if exam_rate > max_pass_rate:
                        max_pass_rate = exam_rate

                    temp_list.append({
                        "label": lbl,
                        "short_label": sh_lbl,
                        "semester": sem,
                        "section": sec,
                        "pass_rate": exam_rate,
                        "student_pass_rate": stu_rate,
                        "student_count": tot_stus,
                        "avg_sgpa": avg_sgpa,
                        "avg_attendance": avg_att,
                        "highlight": False
                    })

            for item in temp_list:
                item["highlight"] = (item["pass_rate"] == max_pass_rate)
                section_pass_rates.append(item)

            # 3. Real Top 5 Academic Toppers across CSM Department
            toppers = []
            student_stats = []
            for roll, grp in m_df.groupby("roll_no"):
                name = grp["student_name"].iloc[0] or f"Student {roll}"
                sec = grp["section"].iloc[0] or "A"

                sem1_grp = grp[grp["semester"] == 1]
                sem2_grp = grp[grp["semester"] == 2]

                s1_sgpa = float(sem1_grp["sgpa"].dropna().iloc[0]) if not sem1_grp["sgpa"].dropna().empty else None
                s2_sgpa = float(sem2_grp["sgpa"].dropna().iloc[0]) if not sem2_grp["sgpa"].dropna().empty else None

                sgpa_list = [x for x in [s1_sgpa, s2_sgpa] if x is not None and pd.notna(x)]
                cgpa = round(sum(sgpa_list) / len(sgpa_list), 2) if sgpa_list else 0.0
                avg_attn = round(float(grp["attendance_percentage"].dropna().mean()), 1) if not grp["attendance_percentage"].dropna().empty else 85.0

                student_stats.append({
                    "roll_no": str(roll),
                    "student_name": str(name),
                    "section": str(sec),
                    "cgpa": cgpa,
                    "s1_sgpa": s1_sgpa,
                    "s2_sgpa": s2_sgpa,
                    "attendance": avg_attn
                })

            # Sort by CGPA descending, then attendance descending
            student_stats.sort(key=lambda x: (x["cgpa"], x["attendance"]), reverse=True)
            rank_badges = ["Rank 1 🥇", "Rank 2 🥈", "Rank 3 🥉", "Rank 4 ⭐", "Rank 5 ⭐"]

            for idx, top in enumerate(student_stats[:5]):
                toppers.append({
                    "rank": idx + 1,
                    "roll_no": top["roll_no"],
                    "student_name": top["student_name"],
                    "section": top["section"],
                    "cgpa": top["cgpa"],
                    "s1_sgpa": top["s1_sgpa"],
                    "s2_sgpa": top["s2_sgpa"],
                    "attendance": top["attendance"],
                    "badge": rank_badges[idx]
                })

        except Exception as e:
            print(f"[DASHBOARD_DYNAMIC_METRICS_ERROR] {e}")

    details = stu_info.get("details", {})

    return {
        "department_code": settings.DEPARTMENT_CODE,
        "department_name": settings.DEPARTMENT_NAME,
        "hod_username": current_user.username,
        "overview": {
            "total_students": total_stus,
            "sem1_students": sem1_stus,
            "sem2_students": sem2_stus,
            "total_result_records": mapping_info.get("result_records", results_count),
            "total_attendance_records": mapping_info.get("attendance_records", attendance_count),
            "successfully_mapped_records": mapping_info.get("successfully_matched", 0),
            "mapping_success_rate": success_rate,
            "data_quality_status": quality_status
        },
        "data_quality": {
            "valid_records": master_rows,
            "warnings": warnings,
            "errors": crit_errors,
            "records_requiring_review": qual_info.get("records_requiring_review", 0)
        },
        "student_presence": {
            "present_in_all_datasets": stu_info.get("matched_students", 0),
            "in_results_missing_attendance": len(details.get("in_results_missing_attendance", [])),
            "in_attendance_missing_results": len(details.get("in_attendance_missing_results", [])),
            "in_sem1_missing_sem2": len(details.get("missing_from_sem2", [])),
            "in_sem2_missing_sem1": len(details.get("missing_from_sem1", []))
        },
        "dataset_summary": {
            "master_rows": master_rows,
            "students_count": students_count,
            "subjects_count": subjects_count,
            "results_count": results_count,
            "attendance_count": attendance_count,
            "semester_summaries_count": semester_sum_count
        },
        "subject_cards": subject_cards,
        "section_pass_rates": section_pass_rates,
        "toppers": toppers,
        "recent_uploads": recent_uploads,
        "last_processed_at": quality_data.get("generated_at")
    }
