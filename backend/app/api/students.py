from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_hod
from backend.app.models.user import User
from backend.app.schemas.student import StudentRead, StudentListResponse

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("", response_model=StudentListResponse)
def list_students(
    search: Optional[str] = None,
    section: Optional[str] = None,
    sort_by: Optional[str] = Query("overall_sgpa", description="Field to sort by (e.g. overall_sgpa, rank, roll_no, name)"),
    order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(300, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_hod),
    db: Session = Depends(get_db)
):
    """
    Retrieve leaderboard ranking list of students in CSM department arranged top to bottom
    with student name, roll number, section, sem 1 sgpa/cgpa, sem 2 sgpa/cgpa, sem 1 backlogs, sem 2 backlogs, and overall sgpa.
    """
    students_csv = settings.DATA_PROCESSED_DIR / "students.csv"
    if not students_csv.exists():
        return StudentListResponse(total=0, items=[])

    df = pd.read_csv(students_csv).fillna("")
    
    # Check presence in master dataset
    master_csv = settings.DATA_PROCESSED_DIR / "master_dataset.csv"
    master_df = pd.read_csv(master_csv) if master_csv.exists() else pd.DataFrame()

    # Load semester summary for SGPA and Backlogs
    sum_csv = settings.DATA_PROCESSED_DIR / "student_semester_summary.csv"
    sum_df = pd.read_csv(sum_csv) if sum_csv.exists() else pd.DataFrame()

    all_students_data = []
    for _, r in df.iterrows():
        roll = str(r["roll_no"]).strip()
        s1_present = False
        s2_present = False
        has_results = False
        has_attendance = False

        if not master_df.empty:
            stu_records = master_df[master_df["roll_no"].astype(str) == roll]
            s1_present = not stu_records[stu_records["semester"] == 1].empty
            s2_present = not stu_records[stu_records["semester"] == 2].empty
            has_results = not stu_records["marks"].dropna().empty or not stu_records["grade"].dropna().empty
            has_attendance = not stu_records["attendance_percentage"].dropna().empty

        status_cat = "Active"
        if s1_present and not s2_present:
            if roll.upper() == "25881A66B5":
                status_cat = "Detained (Sem 2)"
            else:
                status_cat = "Missing from Sem 2"
        elif s2_present and not s1_present:
            status_cat = "Missing from Sem 1"

        # Extract Sem 1 & Sem 2 SGPA and Backlog counts
        s1_sgpa = None
        s2_sgpa = None
        s1_back = 0
        s2_back = 0
        
        if not sum_df.empty:
            s1_rows = sum_df[(sum_df["roll_no"].astype(str) == roll) & (sum_df["semester"] == 1)]
            s2_rows = sum_df[(sum_df["roll_no"].astype(str) == roll) & (sum_df["semester"] == 2)]
            
            if not s1_rows.empty and pd.notna(s1_rows.iloc[0].get("sgpa")):
                s1_sgpa = float(s1_rows.iloc[0]["sgpa"])
            if not s1_rows.empty and pd.notna(s1_rows.iloc[0].get("backlog_count")):
                s1_back = int(s1_rows.iloc[0]["backlog_count"])

            if not s2_rows.empty and pd.notna(s2_rows.iloc[0].get("sgpa")):
                s2_sgpa = float(s2_rows.iloc[0]["sgpa"])
            if not s2_rows.empty and pd.notna(s2_rows.iloc[0].get("backlog_count")):
                s2_back = int(s2_rows.iloc[0]["backlog_count"])

        # Calculate Overall SGPA
        if s1_sgpa is not None and s2_sgpa is not None:
            overall_sgpa = round((s1_sgpa + s2_sgpa) / 2.0, 2)
        elif s1_sgpa is not None:
            overall_sgpa = s1_sgpa
        elif s2_sgpa is not None:
            overall_sgpa = s2_sgpa
        else:
            overall_sgpa = None

        all_students_data.append({
            "id": int(r.name) + 1,
            "student_id": str(r.get("student_id", f"STU_{roll}")),
            "roll_no": roll,
            "student_name": r.get("student_name") or None,
            "section": r.get("section") or None,
            "batch": r.get("batch") or None,
            "sem1_present": s1_present,
            "sem2_present": s2_present,
            "has_results": has_results,
            "has_attendance": has_attendance,
            "status_category": status_cat,
            "sem1_sgpa": s1_sgpa,
            "sem2_sgpa": s2_sgpa,
            "sem1_back": s1_back,
            "sem2_back": s2_back,
            "overall_sgpa": overall_sgpa,
        })

    # Sort top to bottom by default: Overall SGPA descending, then tiebreak by least backlogs
    all_students_data.sort(
        key=lambda x: (
            1 if x["overall_sgpa"] is not None else 0,
            x["overall_sgpa"] or 0.0,
            -(x["sem1_back"] + x["sem2_back"])
        ),
        reverse=True
    )

    # Assign Leaderboard Rank from 1 to N
    for rank_idx, item in enumerate(all_students_data, start=1):
        item["rank"] = rank_idx

    # Apply Section and Search Filters
    filtered_students = all_students_data
    if section:
        filtered_students = [s for s in filtered_students if str(s["section"]).upper() == section.strip().upper()]

    if search:
        search_lower = search.strip().lower()
        filtered_students = [
            s for s in filtered_students
            if (s["roll_no"] and search_lower in str(s["roll_no"]).lower()) or
               (s["student_name"] and search_lower in str(s["student_name"]).lower())
        ]

    total_count = len(filtered_students)
    paged_students = filtered_students[offset:offset+limit]

    items = [StudentRead(**s) for s in paged_students]
    return StudentListResponse(total=total_count, items=items)

@router.get("/{roll_no}")
def get_student_detail(
    roll_no: str,
    current_user: User = Depends(get_current_hod)
):
    """
    Get comprehensive, in-depth academic intelligence & exact performance analysis
    for a specific student in the CSM department across all registered courses and semesters.
    """
    roll_clean = roll_no.strip().upper()
    students_csv = settings.DATA_PROCESSED_DIR / "students.csv"
    master_csv = settings.DATA_PROCESSED_DIR / "master_dataset.csv"
    sum_csv = settings.DATA_PROCESSED_DIR / "student_semester_summary.csv"
    res_csv = settings.DATA_PROCESSED_DIR / "results.csv"
    att_csv = settings.DATA_PROCESSED_DIR / "attendance.csv"
    sub_csv = settings.DATA_PROCESSED_DIR / "subjects.csv"

    if not students_csv.exists() and not master_csv.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic intelligence datasets are not yet processed."
        )

    students_df = pd.read_csv(students_csv) if students_csv.exists() else pd.DataFrame()
    sum_df = pd.read_csv(sum_csv) if sum_csv.exists() else pd.DataFrame()
    res_df = pd.read_csv(res_csv) if res_csv.exists() else pd.DataFrame()
    att_df = pd.read_csv(att_csv) if att_csv.exists() else pd.DataFrame()
    sub_df = pd.read_csv(sub_csv) if sub_csv.exists() else pd.DataFrame()
    master_df = pd.read_csv(master_csv) if master_csv.exists() else pd.DataFrame()

    # Find the target student row
    stu_row = pd.DataFrame()
    if not students_df.empty:
        stu_row = students_df[students_df["roll_no"].astype(str).str.upper() == roll_clean]
    if stu_row.empty and not master_df.empty:
        stu_row = master_df[master_df["roll_no"].astype(str).str.upper() == roll_clean]

    if stu_row.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number '{roll_no}' was not found in CSM Department records."
        )

    first = stu_row.iloc[0]
    student_name = str(first.get("student_name", "") or "")
    section = str(first.get("section", "") or "").upper()
    batch = str(first.get("batch", "2025-2029") or "2025-2029")
    student_id = str(first.get("student_id", f"STU_{roll_clean}"))

    # Compute overall Department and Section Rankings
    rank_map = {}
    for _, r in students_df.iterrows():
        r_roll = str(r["roll_no"]).strip().upper()
        s1_rows = sum_df[(sum_df["roll_no"].astype(str).str.upper() == r_roll) & (sum_df["semester"] == 1)]
        s2_rows = sum_df[(sum_df["roll_no"].astype(str).str.upper() == r_roll) & (sum_df["semester"] == 2)]
        s1_sgpa = float(s1_rows.iloc[0]["sgpa"]) if not s1_rows.empty and pd.notna(s1_rows.iloc[0].get("sgpa")) else None
        s2_sgpa = float(s2_rows.iloc[0]["sgpa"]) if not s2_rows.empty and pd.notna(s2_rows.iloc[0].get("sgpa")) else None
        s1_b = int(s1_rows.iloc[0]["backlog_count"]) if not s1_rows.empty and pd.notna(s1_rows.iloc[0].get("backlog_count")) else 0
        s2_b = int(s2_rows.iloc[0]["backlog_count"]) if not s2_rows.empty and pd.notna(s2_rows.iloc[0].get("backlog_count")) else 0
        
        if s1_sgpa is not None and s2_sgpa is not None:
            c = round((s1_sgpa + s2_sgpa) / 2.0, 2)
        elif s1_sgpa is not None:
            c = s1_sgpa
        elif s2_sgpa is not None:
            c = s2_sgpa
        else:
            c = 0.0
        rank_map[r_roll] = {
            "roll_no": r_roll,
            "section": str(r.get("section", "")).upper(),
            "cgpa": c,
            "backlogs": s1_b + s2_b
        }

    sorted_dept = sorted(rank_map.values(), key=lambda x: (x["cgpa"], -x["backlogs"]), reverse=True)
    dept_rank = next((idx for idx, s in enumerate(sorted_dept, 1) if s["roll_no"] == roll_clean), 1)
    total_dept_students = len(sorted_dept)

    sec_students = [s for s in sorted_dept if s["section"] == section]
    section_rank = next((idx for idx, s in enumerate(sec_students, 1) if s["roll_no"] == roll_clean), 1)
    total_section_students = len(sec_students)

    # Subject Catalog Lookup
    sub_map = {}
    for _, s in sub_df.iterrows():
        code = str(s["subject_code"]).strip().upper()
        sem = int(s["semester"])
        sub_map[(sem, code)] = {
            "subject_name": str(s.get("subject_name", "")),
            "credits": float(s["credits"]) if pd.notna(s.get("credits")) else 3.0
        }

    # Extract Course & Attendance & Result records
    stu_master = master_df[master_df["roll_no"].astype(str).str.upper() == roll_clean] if not master_df.empty else pd.DataFrame()
    stu_res = res_df[res_df["roll_no"].astype(str).str.upper() == roll_clean] if not res_df.empty else pd.DataFrame()
    stu_att = att_df[att_df["roll_no"].astype(str).str.upper() == roll_clean] if not att_df.empty else pd.DataFrame()

    records = []
    total_credits_earned = 0.0
    total_credits_registered = 0.0
    total_classes_att = 0
    total_classes_cond = 0
    courses_passed = 0
    courses_failed = 0

    for _, r in stu_master.iterrows():
        sem = int(r["semester"])
        code = str(r["subject_code"]).strip().upper()
        name = str(r.get("subject_name") or "")
        
        sub_info = sub_map.get((sem, code), {})
        credits = sub_info.get("credits", 3.0)
        total_credits_registered += credits
        
        att_sub = stu_att[(stu_att["semester"] == sem) & (stu_att["subject_code"].astype(str).str.upper() == code)]
        cls_att = int(att_sub.iloc[0]["classes_attended"]) if not att_sub.empty and pd.notna(att_sub.iloc[0].get("classes_attended")) else None
        cls_cond = int(att_sub.iloc[0]["classes_conducted"]) if not att_sub.empty and pd.notna(att_sub.iloc[0].get("classes_conducted")) else None
        
        if cls_att is not None and cls_cond is not None:
            total_classes_att += cls_att
            total_classes_cond += cls_cond
            
        res_sub = stu_res[(stu_res["semester"] == sem) & (stu_res["subject_code"].astype(str).str.upper() == code)]
        gp = float(res_sub.iloc[0]["grade_points"]) if not res_sub.empty and pd.notna(res_sub.iloc[0].get("grade_points")) else (
            float(r["grade_point"]) if pd.notna(r.get("grade_point")) else None
        )
        marks = float(res_sub.iloc[0]["marks"]) if not res_sub.empty and pd.notna(res_sub.iloc[0].get("marks")) else (
            float(r["marks"]) if pd.notna(r.get("marks")) else None
        )
        grade = str(r.get("grade") or (res_sub.iloc[0].get("grade") if not res_sub.empty else "")).strip()
        status_str = str(r.get("status") or (res_sub.iloc[0].get("status") if not res_sub.empty else "PASS")).strip().upper()
        attn_pct = float(r["attendance_percentage"]) if pd.notna(r.get("attendance_percentage")) else (
            float(att_sub.iloc[0]["attendance_percentage"]) if not att_sub.empty and pd.notna(att_sub.iloc[0].get("attendance_percentage")) else None
        )
        
        is_backlog = status_str == "FAIL" or (grade in ["F", "AB", "ABSENT"])
        if is_backlog:
            courses_failed += 1
        else:
            courses_passed += 1
            total_credits_earned += credits

        records.append({
            "semester": sem,
            "subject_code": code,
            "subject_name": name or sub_info.get("subject_name", code),
            "credits": credits,
            "marks": marks,
            "grade": grade or ("F" if is_backlog else "PASS"),
            "grade_point": gp,
            "status": "FAIL" if is_backlog else "PASS",
            "attendance_percentage": round(attn_pct, 1) if attn_pct is not None else None,
            "classes_attended": cls_att,
            "classes_conducted": cls_cond,
            "is_backlog": is_backlog,
            "is_low_attendance": (attn_pct is not None and attn_pct < 75.0)
        })

    records.sort(key=lambda x: (x["semester"], x["subject_code"]))

    # Semester summaries
    stu_sum_rows = sum_df[sum_df["roll_no"].astype(str).str.upper() == roll_clean] if not sum_df.empty else pd.DataFrame()
    semester_summaries = []
    sem1_sgpa = None
    sem2_sgpa = None
    total_backlogs = 0

    if not stu_sum_rows.empty:
        for _, srow in stu_sum_rows.sort_values("semester").iterrows():
            s_sem = int(srow["semester"])
            s_sgpa = float(srow["sgpa"]) if pd.notna(srow.get("sgpa")) else None
            s_back = int(srow["backlog_count"]) if pd.notna(srow.get("backlog_count")) else 0
            s_attn = float(srow["average_attendance"]) if pd.notna(srow.get("average_attendance")) else None
            s_pass = int(srow["passed_subject_count"]) if pd.notna(srow.get("passed_subject_count")) else 0
            s_fail = int(srow["failed_subject_count"]) if pd.notna(srow.get("failed_subject_count")) else 0
            s_sgpa_chg = float(srow["sgpa_change"]) if pd.notna(srow.get("sgpa_change")) else None
            s_attn_chg = float(srow["attendance_change"]) if pd.notna(srow.get("attendance_change")) else None
            s_back_chg = int(srow["backlog_change"]) if pd.notna(srow.get("backlog_change")) else None

            if s_sem == 1:
                sem1_sgpa = s_sgpa
            elif s_sem == 2:
                sem2_sgpa = s_sgpa
            total_backlogs += s_back

            sem_recs = [rec for rec in records if rec["semester"] == s_sem]
            sem_credits_earned = sum(rec["credits"] for rec in sem_recs if not rec["is_backlog"])
            sem_credits_reg = sum(rec["credits"] for rec in sem_recs)

            semester_summaries.append({
                "semester": s_sem,
                "sgpa": s_sgpa,
                "backlog_count": s_back,
                "average_attendance": round(s_attn, 1) if s_attn is not None else None,
                "passed_subject_count": s_pass,
                "failed_subject_count": s_fail,
                "credits_earned": sem_credits_earned,
                "credits_registered": sem_credits_reg,
                "sgpa_change": s_sgpa_chg,
                "attendance_change": s_attn_chg,
                "backlog_change": s_back_chg
            })

    # Overall CGPA
    if sem1_sgpa is not None and sem2_sgpa is not None:
        overall_cgpa = round((sem1_sgpa + sem2_sgpa) / 2.0, 2)
    elif sem1_sgpa is not None:
        overall_cgpa = sem1_sgpa
    elif sem2_sgpa is not None:
        overall_cgpa = sem2_sgpa
    else:
        overall_cgpa = 0.0

    # Overall Attendance
    if total_classes_cond > 0:
        overall_attn = round((total_classes_att / total_classes_cond) * 100.0, 1)
    elif semester_summaries:
        valid_attns = [s["average_attendance"] for s in semester_summaries if s["average_attendance"] is not None]
        overall_attn = round(sum(valid_attns) / len(valid_attns), 1) if valid_attns else 0.0
    else:
        overall_attn = 0.0

    # Academic Standing Classification
    if dept_rank == 1:
        academic_standing = "Department Topper (Rank #1)"
    elif overall_cgpa >= 9.0:
        academic_standing = "Outstanding (CGPA ≥ 9.0)"
    elif overall_cgpa >= 8.0:
        academic_standing = "First Class with Distinction (CGPA 8.0 - 8.99)"
    elif overall_cgpa >= 7.0:
        academic_standing = "First Class (CGPA 7.0 - 7.99)"
    elif overall_cgpa >= 6.0:
        academic_standing = "Second Class (CGPA 6.0 - 6.99)"
    elif total_backlogs > 0:
        academic_standing = f"Academic Risk ({total_backlogs} Active Backlog(s))"
    else:
        academic_standing = "Pass"

    # Attendance Standing Classification
    if roll_clean == "25881A66B5":
        attendance_standing = "Detained in Semester 2 (<65% Attendance)"
        status_category = "Detained (Sem 2)"
    elif overall_attn >= 90.0:
        attendance_standing = "Excellent Attendance (≥90%)"
        status_category = "Active"
    elif overall_attn >= 85.0:
        attendance_standing = "Safe Attendance (85% - 89.9%)"
        status_category = "Active"
    elif overall_attn >= 75.0:
        attendance_standing = "Moderate Attendance (75% - 84.9%)"
        status_category = "Active"
    else:
        attendance_standing = "Critical Shortage (<75%) - Detention Risk"
        status_category = "Attendance Shortage"

    # AI Diagnostic Strengths & Risks
    strengths = []
    risks_and_alerts = []

    o_grades = [r for r in records if str(r.get("grade")).upper() == "O"]
    aplus_grades = [r for r in records if str(r.get("grade")).upper() in ["A+", "A"]]
    if o_grades:
        strengths.append(f"Achieved highest academic grade 'O' (10.0 GP) in {len(o_grades)} course(s).")
    if aplus_grades:
        strengths.append(f"Secured top grade 'A+' / 'A' in {len(aplus_grades)} course(s).")

    high_attn_courses = [r for r in records if r.get("attendance_percentage") and r["attendance_percentage"] >= 95.0]
    if high_attn_courses:
        strengths.append(f"Exceptional attendance (≥95%) maintained across {len(high_attn_courses)} course(s).")

    if len(semester_summaries) >= 2:
        s2 = semester_summaries[1]
        if s2.get("sgpa_change") and s2["sgpa_change"] > 0:
            strengths.append(f"Positive semester progression: Sem 2 SGPA improved by +{s2['sgpa_change']} points.")

    # Risks & Alerts
    backlog_recs = [r for r in records if r["is_backlog"]]
    if backlog_recs:
        for b in backlog_recs:
            risks_and_alerts.append(f"Active Backlog in Sem {b['semester']}: {b['subject_name']} ({b['subject_code']}).")
    else:
        strengths.append("Clean academic record: Zero active backlogs across curriculum.")

    low_attn_recs = [r for r in records if r["is_low_attendance"]]
    if low_attn_recs:
        for la in low_attn_recs:
            risks_and_alerts.append(f"Attendance shortage in Sem {la['semester']}: {la['subject_name']} ({la['attendance_percentage']}%, below mandatory 75% threshold).")
    else:
        strengths.append("Satisfied 75%+ mandatory attendance requirement across all registered subjects.")

    if len(semester_summaries) >= 2:
        s2 = semester_summaries[1]
        if s2.get("sgpa_change") and s2["sgpa_change"] < -0.3:
            risks_and_alerts.append(f"Academic decline detected: SGPA dropped by {abs(s2['sgpa_change'])} points from Sem 1 to Sem 2.")

    if not risks_and_alerts:
        risks_and_alerts.append("No critical academic or attendance risks detected. Student is performing solidly.")

    return {
        "student_id": student_id,
        "roll_no": roll_clean,
        "student_name": student_name,
        "section": section,
        "batch": batch,
        "department": "Computer Science and Engineering (Artificial Intelligence & Machine Learning)",
        "department_code": "CSM",
        "status_category": status_category,
        "department_rank": dept_rank,
        "total_students_dept": total_dept_students,
        "section_rank": section_rank,
        "total_students_section": total_section_students,
        "overall_cgpa": overall_cgpa,
        "sem1_sgpa": sem1_sgpa,
        "sem2_sgpa": sem2_sgpa,
        "overall_attendance": overall_attn,
        "total_classes_attended": total_classes_att,
        "total_classes_conducted": total_classes_cond,
        "total_credits_earned": round(total_credits_earned, 1),
        "total_credits_registered": round(total_credits_registered, 1),
        "total_courses_registered": len(records),
        "total_courses_passed": courses_passed,
        "total_courses_failed": courses_failed,
        "total_active_backlogs": total_backlogs,
        "academic_standing": academic_standing,
        "attendance_standing": attendance_standing,
        "strengths": strengths,
        "risks_and_alerts": risks_and_alerts,
        "semester_summaries": semester_summaries,
        "records": records
    }
