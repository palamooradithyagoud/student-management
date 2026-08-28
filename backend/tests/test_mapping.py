import pandas as pd
import pytest
from backend.app.services.integration.mapper import SubjectMapper, ResultAttendanceMapper

def test_subject_mapper_curriculum_resolution():
    # Sem 1: A9001 / MAC is Matrices and Calculus (4 credits)
    std_c, std_n, status = SubjectMapper.map_subject("A9001", "Matrices and Calculus", semester=1)
    assert std_c == "A9001"
    assert std_n == "Matrices and Calculus"
    assert status == "MATCHED"
    assert SubjectMapper.get_subject_credits("A9001", 1) == 4.0

    # Sem 1 Alias match MAC
    std_c_mac, std_n_mac, status_mac = SubjectMapper.map_subject("MAC", "MAC", semester=1)
    assert std_c_mac == "A9001"
    assert std_n_mac == "Matrices and Calculus"
    assert status_mac == "MATCHED"

    # Sem 1: CCDT is Community Centered Design Thinking (1 credit)
    std_c_ccdt, std_n_ccdt, _ = SubjectMapper.map_subject("CCDT", "CCDT", semester=1)
    assert std_c_ccdt == "A9021"
    assert std_n_ccdt == "Community Centered Design Thinking"
    assert SubjectMapper.get_subject_credits("A9021", 1) == 1.0

    # Sem 2: A9011 / ESE / ECS is English for Skills Enhancement (2 credits)
    std_c2, std_n2, status2 = SubjectMapper.map_subject("A9011", "English for Skills Enhancement", semester=2)
    assert std_c2 == "A9011"
    assert "English" in std_n2
    assert status2 == "MATCHED"
    assert SubjectMapper.get_subject_credits("A9011", 2) == 2.0

    std_c_ese, std_n_ese, _ = SubjectMapper.map_subject("ESE", "ESE", semester=2)
    assert std_c_ese == "A9011"
    assert "English" in std_n_ese

    std_c_ecs, std_n_ecs, _ = SubjectMapper.map_subject("ECS", "ECS", semester=2)
    assert std_c_ecs == "A9011"
    assert "English" in std_n_ecs

    # Sem 2: PDP / PDD is Product Design and Development (1 credit)
    std_c_pdp, std_n_pdp, _ = SubjectMapper.map_subject("PDP", "PDP", semester=2)
    assert std_c_pdp == "A9022"
    assert std_n_pdp == "Product Design and Development"
    assert SubjectMapper.get_subject_credits("A9022", 2) == 1.0

    # Fuzzy match by alias / name
    std_c, std_n, status = SubjectMapper.map_subject("DS", "Data Structures", semester=2)
    assert std_c == "A9503"
    assert status == "MATCHED"
    assert SubjectMapper.get_subject_credits("A9503", 2) == 3.0

def test_result_attendance_mapping(tmp_path):
    rep_path = tmp_path / "test_mapping_report.csv"
    r_df = pd.DataFrame([
        {"roll_no": "23CSM1001", "semester": 1, "subject_code": "23CSM1101", "marks": 85.0},
        {"roll_no": "23CSM1002", "semester": 1, "subject_code": "23CSM1101", "marks": 90.0},
        {"roll_no": "23CSM1003", "semester": 1, "subject_code": "23CSM1101", "marks": 75.0},
    ])
    a_df = pd.DataFrame([
        {"roll_no": "23CSM1001", "semester": 1, "subject_code": "23CSM1101", "attendance_percentage": 92.0},
        {"roll_no": "23CSM1002", "semester": 1, "subject_code": "23CSM1101", "attendance_percentage": 88.0},
        {"roll_no": "23CSM1004", "semester": 1, "subject_code": "23CSM1101", "attendance_percentage": 70.0}, # In att, not in res
    ])

    merged, stats = ResultAttendanceMapper.map_results_and_attendance(r_df, a_df, output_report_path=rep_path)
    assert stats["total_result_records"] == 3
    assert stats["total_attendance_records"] == 3
    assert stats["matched_records"] == 2
    assert stats["results_without_attendance"] == 1
    assert stats["attendance_without_results"] == 1
    assert round(stats["mapping_success_rate"], 1) == 66.7
    assert rep_path.exists()
