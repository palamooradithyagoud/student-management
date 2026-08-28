import pytest
import pandas as pd
from backend.app.services.validation.validator import DataValidator
from backend.app.services.validation.quality_reporter import QualityReporter

def test_cross_dataset_validation():
    s1_res = {"23CSM1001", "23CSM1002", "23CSM1003", "23CSM1004"}
    s2_res = {"23CSM1001", "23CSM1002", "23CSM1005"}  # 1003, 1004 missing in sem 2; 1005 new
    s1_att = {"23CSM1001", "23CSM1002", "23CSM1003", "23CSM1004"}
    s2_att = {"23CSM1001", "23CSM1002", "23CSM1005"}

    val = DataValidator.validate_cross_dataset_students(s1_res, s2_res, s1_att, s2_att)
    assert val["total_distinct_students"] == 5
    assert set(val["present_in_all_datasets"]) == {"23CSM1001", "23CSM1002"}
    assert set(val["missing_from_sem2_dataset"]) == {"23CSM1003", "23CSM1004"}
    assert set(val["missing_from_sem1_dataset"]) == {"23CSM1005"}

def test_duplicate_detection():
    df_with_dups = pd.DataFrame([
        {"roll_no": "23CSM1001", "semester": 1, "subject_code": "23CSM1101", "marks": 85.0, "grade": "A+"},
        {"roll_no": "23CSM1001", "semester": 1, "subject_code": "23CSM1101", "marks": 85.0, "grade": "A+"},
        {"roll_no": "23CSM1002", "semester": 1, "subject_code": "23CSM1101", "marks": 78.0, "grade": "A"}
    ])
    res = DataValidator.validate_results_data(df_with_dups)
    assert res["duplicate_records"] == 2
    assert len(res["duplicates_list"]) == 2

def test_quality_reporter_output_format(tmp_path):
    json_p = tmp_path / "test_report.json"
    md_p = tmp_path / "test_report.md"

    s_val = {"sem1_total_students": 60, "sem2_total_students": 58, "counts": {"present_in_all": 56, "missing_from_sem2_dataset": 4}}
    r_val = {"sem1_records": 420, "sem2_records": 406, "missing_marks": 1, "missing_grades": 1, "duplicate_records": 1, "duplicates_list": []}
    a_val = {"sem1_records": 420, "sem2_records": 406, "missing_attendance": 0, "invalid_attendance": 2, "duplicate_records": 0, "duplicates_list": []}
    sub_stats = {"total_subjects": 14, "matched_subjects": 14, "unmatched_subjects": 0, "unmatched_list": []}
    map_stats = {"total_result_records": 826, "total_attendance_records": 826, "matched_records": 826, "unmatched_records": 0, "mapping_success_rate": 100.0}

    report = QualityReporter.generate_report(
        student_val=s_val,
        results_val=r_val,
        attendance_val=a_val,
        subject_stats=sub_stats,
        mapping_stats=map_stats,
        critical_errors=3,
        warnings=5,
        records_requiring_review=8,
        json_path=json_p,
        md_path=md_p
    )

    assert json_p.exists()
    assert md_p.exists()
    
    with open(md_p, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "CSM ACADEMIC DATA QUALITY REPORT" in md_text
    assert "Sem 1 students: 60" in md_text
    assert "Students missing from Sem 2: 4" in md_text
    assert "Mapping success rate: 100.0%" in md_text
