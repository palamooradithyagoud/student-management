from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_hod
from backend.app.models.user import User
from backend.app.schemas.subject import SubjectRead, SubjectMappingRead, SubjectListResponse

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])

@router.get("", response_model=SubjectListResponse)
def list_subjects(
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_hod)
):
    """List standardized CSM subjects by semester."""
    subs_csv = settings.DATA_PROCESSED_DIR / "subjects.csv"
    if not subs_csv.exists():
        return SubjectListResponse(total=0, items=[], mappings=[])

    df = pd.read_csv(subs_csv).fillna("")
    if semester:
        df = df[df["semester"] == semester]

    res_csv = settings.DATA_PROCESSED_DIR / "results.csv"
    res_df = pd.read_csv(res_csv) if res_csv.exists() else pd.DataFrame()

    att_csv = settings.DATA_PROCESSED_DIR / "attendance.csv"
    att_df = pd.read_csv(att_csv) if att_csv.exists() else pd.DataFrame()

    items = []
    for idx, r in df.iterrows():
        code = str(r["subject_code"]).strip()
        sem = int(r["semester"])

        tot_students = 0
        tot_pass = 0
        tot_fail = 0
        pass_pct = 0.0
        avg_att = None

        if not res_df.empty:
            s_res = res_df[(res_df["subject_code"].astype(str).str.strip() == code) & (res_df["semester"] == sem)]
            if not s_res.empty:
                tot_students = len(s_res)
                tot_pass = int((s_res["status"].astype(str).str.upper() == "PASS").sum())
                tot_fail = int((s_res["status"].astype(str).str.upper() == "FAIL").sum())
                pass_pct = round(tot_pass / tot_students * 100.0, 1) if tot_students > 0 else 0.0

        if not att_df.empty:
            s_att = att_df[(att_df["subject_code"].astype(str).str.strip() == code) & (att_df["semester"] == sem)]
            if not s_att.empty and "attendance_percentage" in s_att.columns:
                valid_att = s_att["attendance_percentage"].dropna()
                if not valid_att.empty:
                    avg_att = round(float(valid_att.mean()), 1)

        items.append(SubjectRead(
            id=int(idx) + 1,
            subject_id=str(r["subject_id"]),
            subject_code=str(r["subject_code"]),
            subject_name=str(r["subject_name"]),
            semester=int(r["semester"]),
            credits=float(r["credits"]) if r.get("credits") != "" else None,
            total_students=tot_students,
            total_pass=tot_pass,
            total_fail=tot_fail,
            pass_percentage=pass_pct,
            avg_attendance=avg_att
        ))

    # Read mappings
    map_csv = settings.DATA_PROCESSED_DIR / "subject_mapping.csv"
    mappings = []
    if map_csv.exists():
        map_df = pd.read_csv(map_csv).fillna("")
        for _, mr in map_df.iterrows():
            mappings.append(SubjectMappingRead(
                source_file=str(mr["source_file"]),
                original_subject_code=str(mr["original_subject_code"]),
                original_subject_name=str(mr["original_subject_name"]),
                standard_subject_code=str(mr["standard_subject_code"]),
                standard_subject_name=str(mr["standard_subject_name"]),
                status=str(mr.get("status", "MATCHED"))
            ))

    return SubjectListResponse(
        total=len(items),
        items=items,
        mappings=mappings
    )

@router.get("/mappings", response_model=list[SubjectMappingRead])
def list_subject_mappings(
    current_user: User = Depends(get_current_hod)
):
    """Retrieve raw vs standardized subject code mappings."""
    map_csv = settings.DATA_PROCESSED_DIR / "subject_mapping.csv"
    if not map_csv.exists():
        return []
    df = pd.read_csv(map_csv).fillna("")
    return df.to_dict(orient="records")


@router.get("/{subject_code}/failed-students")
def get_failed_students(
    subject_code: str,
    semester: int = Query(..., description="Semester number (1 or 2)"),
    current_user: User = Depends(get_current_hod)
):
    """
    Return the list of students who FAILED a specific subject in a given semester,
    including name, roll number, section, grade, marks, and attendance percentage.
    """
    code_clean = subject_code.strip().upper()

    res_csv = settings.DATA_PROCESSED_DIR / "results.csv"
    att_csv = settings.DATA_PROCESSED_DIR / "attendance.csv"
    stu_csv = settings.DATA_PROCESSED_DIR / "students.csv"

    res_df = pd.read_csv(res_csv) if res_csv.exists() else pd.DataFrame()
    att_df = pd.read_csv(att_csv) if att_csv.exists() else pd.DataFrame()
    stu_df = pd.read_csv(stu_csv) if stu_csv.exists() else pd.DataFrame()

    if res_df.empty:
        return {"subject_code": code_clean, "semester": semester, "failed_students": [], "total": 0}

    # Filter to failed rows for this subject + semester
    sub_res = res_df[
        (res_df["subject_code"].astype(str).str.strip().str.upper() == code_clean) &
        (res_df["semester"] == semester) &
        (res_df["status"].astype(str).str.upper() == "FAIL")
    ]

    # Build student name lookup
    name_map = {}
    section_map = {}
    if not stu_df.empty:
        for _, sr in stu_df.iterrows():
            roll = str(sr["roll_no"]).strip().upper()
            name_map[roll] = str(sr.get("student_name", ""))
            section_map[roll] = str(sr.get("section", ""))

    # Build attendance lookup for this subject + semester
    att_map = {}
    if not att_df.empty:
        sub_att = att_df[
            (att_df["subject_code"].astype(str).str.strip().str.upper() == code_clean) &
            (att_df["semester"] == semester)
        ]
        for _, ar in sub_att.iterrows():
            roll = str(ar["roll_no"]).strip().upper()
            att_map[roll] = float(ar["attendance_percentage"]) if pd.notna(ar.get("attendance_percentage")) else None

    failed_students = []
    for _, row in sub_res.iterrows():
        roll = str(row["roll_no"]).strip().upper()
        s_name = name_map.get(roll) or (str(row.get("student_name", "")).strip() if pd.notna(row.get("student_name")) else "")
        s_sec = section_map.get(roll) or (str(row.get("section", "")).strip() if pd.notna(row.get("section")) else "")
        failed_students.append({
            "roll_no": roll,
            "student_name": s_name,
            "section": s_sec,
            "grade": str(row.get("grade", "")).strip() or "F",
            "marks": float(row["marks"]) if pd.notna(row.get("marks")) else None,
            "grade_points": float(row["grade_points"]) if pd.notna(row.get("grade_points")) else None,
            "attendance_percentage": att_map.get(roll),
        })

    # Sort by section then name
    failed_students.sort(key=lambda x: (x["section"], x["student_name"]))

    return {
        "subject_code": code_clean,
        "semester": semester,
        "total": len(failed_students),
        "failed_students": failed_students
    }

