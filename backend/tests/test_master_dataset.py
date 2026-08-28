import pandas as pd
import numpy as np
import pytest
from backend.app.core.config import settings
from backend.app.services.integration.master_builder import MasterDatasetBuilder
from backend.app.services.integration.summary_builder import StudentSemesterSummaryBuilder
from backend.app.services.integration.pipeline import DataPipelineOrchestrator

def test_master_dataset_structure_and_no_fabrication(tmp_path):
    out_master = tmp_path / "test_master.csv"
    students_df = pd.DataFrame([
        {"student_id": "STU_23CSM1001", "roll_no": "23CSM1001", "student_name": "Aarav Sharma", "section": "A", "batch": "2023-2027"}
    ])
    subjects_df = pd.DataFrame([
        {"subject_id": "SUB_1_23CSM1101", "subject_code": "23CSM1101", "subject_name": "Linear Algebra", "semester": 1, "credits": 4.0}
    ])
    results_df = pd.DataFrame([
        {"student_id": "STU_23CSM1001", "roll_no": "23CSM1001", "subject_code": "23CSM1101", "semester": 1, "marks": np.nan, "grade": None, "grade_point": np.nan, "status": None}
    ])
    attendance_df = pd.DataFrame([
        {"student_id": "STU_23CSM1001", "roll_no": "23CSM1001", "subject_code": "23CSM1101", "semester": 1, "attendance_percentage": 88.5}
    ])

    master_df = MasterDatasetBuilder.build_master_dataset(
        students_df=students_df,
        subjects_df=subjects_df,
        results_df=results_df,
        attendance_df=attendance_df,
        output_path=out_master
    )

    assert len(master_df) == 1
    assert list(master_df.columns) == [
        "student_id", "roll_no", "student_name", "section", "semester",
        "subject_id", "subject_code", "subject_name", "attendance_percentage",
        "marks", "grade", "grade_point", "status", "sgpa", "backlog_count"
    ]
    # Verify missing marks is preserved as NaN (NO fabrication)
    assert pd.isna(master_df.loc[0, "marks"])
    assert master_df.loc[0, "attendance_percentage"] == 88.5

def test_student_semester_summary_deltas(tmp_path):
    out_sum = tmp_path / "test_summary.csv"
    master_df = pd.DataFrame([
        # Sem 1 for student
        {"roll_no": "23CSM1001", "student_name": "Aarav Sharma", "section": "A", "semester": 1, "subject_code": "23CSM1101", "attendance_percentage": 80.0, "status": "PASS", "grade": "A", "sgpa": 8.0, "backlog_count": 0},
        {"roll_no": "23CSM1001", "student_name": "Aarav Sharma", "section": "A", "semester": 1, "subject_code": "23CSM1102", "attendance_percentage": 80.0, "status": "PASS", "grade": "A", "sgpa": 8.0, "backlog_count": 0},
        # Sem 2 for student (improved attendance and SGPA)
        {"roll_no": "23CSM1001", "student_name": "Aarav Sharma", "section": "A", "semester": 2, "subject_code": "23CSM1201", "attendance_percentage": 90.0, "status": "PASS", "grade": "A+", "sgpa": 9.0, "backlog_count": 0},
        {"roll_no": "23CSM1001", "student_name": "Aarav Sharma", "section": "A", "semester": 2, "subject_code": "23CSM1202", "attendance_percentage": 90.0, "status": "PASS", "grade": "A+", "sgpa": 9.0, "backlog_count": 0},
    ])

    sum_df = StudentSemesterSummaryBuilder.build_student_semester_summary(master_df, output_path=out_sum)
    assert len(sum_df) == 2
    
    sem1_row = sum_df[sum_df["semester"] == 1].iloc[0]
    sem2_row = sum_df[sum_df["semester"] == 2].iloc[0]

    assert sem1_row["average_attendance"] == 80.0
    assert sem2_row["average_attendance"] == 90.0
    assert sem2_row["attendance_change"] == 10.0
    assert sem2_row["sgpa_change"] == 1.0

def test_full_pipeline_execution():
    orchestrator = DataPipelineOrchestrator()
    result = orchestrator.run_pipeline()

    assert result["status"] == "SUCCESS"
    assert result["total_students"] > 0
    assert result["total_results"] > 0
    assert result["total_attendance"] > 0
    assert result["mapping_success_rate"] > 90.0
    assert len(result["generated_files"]) == 12

    # Check that all 12 output files exist on disk
    for rel_path in result["generated_files"]:
        p = settings.BASE_DIR / rel_path
        assert p.exists(), f"Generated file {rel_path} must exist on disk"
