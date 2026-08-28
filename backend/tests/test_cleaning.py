import pandas as pd
import numpy as np
import pytest
from backend.app.services.cleaning.normalizer import DataNormalizer
from backend.app.services.cleaning.logger import CleaningAuditLogger

def test_roll_number_normalization():
    assert DataNormalizer.normalize_roll_no(" 23CSM1001 ") == "23CSM1001"
    assert DataNormalizer.normalize_roll_no("23csm1001") == "23CSM1001"
    assert DataNormalizer.normalize_roll_no("23CSM 1001") == "23CSM1001"
    assert DataNormalizer.normalize_roll_no("23CSM1001.0") == "23CSM1001"
    assert DataNormalizer.normalize_roll_no(None) is None
    assert DataNormalizer.normalize_roll_no("") is None

def test_subject_code_normalization():
    assert DataNormalizer.normalize_subject_code(" 23csm1101 ") == "23CSM1101"
    assert DataNormalizer.normalize_subject_code("23CSM 1101") == "23CSM1101"

def test_cleaning_audit_logger_records_entries(tmp_path):
    log_file = tmp_path / "test_cleaning_log.csv"
    logger = CleaningAuditLogger(log_path=log_file)
    logger.log(
        source_file="test_sem1.xlsx",
        record_identifier="23csm1005",
        issue="Lowercase roll number",
        action_taken="Normalized to 23CSM1005",
        reason="Casing standardization"
    )
    entries = logger.get_entries()
    assert len(entries) == 1
    assert entries[0]["record_identifier"] == "23csm1005"
    assert log_file.exists()

def test_attendance_bounds_cleaning(tmp_path):
    log_file = tmp_path / "test_cleaning_log.csv"
    logger = CleaningAuditLogger(log_path=log_file)
    normalizer = DataNormalizer(logger=logger)

    df_raw = pd.DataFrame([
        {"roll_no": " 23CSM1001 ", "subject_code": "23CSM1101", "attendance_percentage": "85%"},
        {"roll_no": "23csm1002", "subject_code": "23CSM1101", "attendance_percentage": "105.0"},
        {"roll_no": "23CSM1003", "subject_code": "23CSM1101", "attendance_percentage": "-5.0"},
        {"roll_no": "23CSM1004", "subject_code": "23CSM1101", "attendance_percentage": "0.75"}
    ])

    df_clean = normalizer.clean_attendance_dataframe(df_raw, source_file="test_att.xlsx")
    assert df_clean.loc[0, "roll_no"] == "23CSM1001"
    assert df_clean.loc[0, "attendance_percentage"] == 85.0
    assert df_clean.loc[3, "attendance_percentage"] == 75.0  # Converted 0.75 ratio to 75%
    
    # Check that out of bounds issues were logged
    logged_issues = [e["issue"] for e in logger.get_entries()]
    assert any("out of bounds" in issue for issue in logged_issues)
