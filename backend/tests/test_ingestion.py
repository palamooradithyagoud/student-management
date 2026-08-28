import io
from pathlib import Path
import pandas as pd
import pytest
from fastapi import status
from backend.app.core.config import settings
from backend.app.services.ingestion.inspector import FileInspector, match_column_to_canonical
from backend.app.services.ingestion.loader import RawDataLoader

def test_column_alias_matching():
    assert match_column_to_canonical("Roll No") == "roll_no"
    assert match_column_to_canonical("Hall Ticket No") == "roll_no"
    assert match_column_to_canonical("HTNO") == "roll_no"
    assert match_column_to_canonical("Candidate Name") == "student_name"
    assert match_column_to_canonical("Sub Code") == "subject_code"
    assert match_column_to_canonical("Attendance %") == "attendance_percentage"
    assert match_column_to_canonical("Total Marks") == "marks"
    assert match_column_to_canonical("Letter Grade") == "grade"

def test_excel_inspection_with_banner():
    sample_file = settings.DATA_DIR / "sem result" / "RESULT 1-1.xlsx"
    assert sample_file.exists(), "Original college dataset must exist"
    
    inspection = FileInspector.inspect_file(sample_file)
    assert inspection["num_sheets"] >= 1
    assert inspection["total_rows"] > 0
    assert len(inspection["sample_records"]) > 0

def test_raw_data_loader():
    sample_file = settings.DATA_DIR / "sem result" / "RESULT 1-1.xlsx"
    df = RawDataLoader.load_dataset(sample_file, dataset_type="sem1_results", semester=1)
    assert "roll_no" in df.columns
    assert "semester" in df.columns
    assert (df["semester"] == 1).all()
    assert len(df) > 1000

def test_invalid_file_type_upload(client, auth_headers):
    file_content = b"Fake malicious executable or script"
    response = client.post(
        "/api/data/upload",
        headers=auth_headers,
        data={"dataset_type": "sem1_results", "semester": 1},
        files={"file": ("malicious.exe", file_content, "application/octet-stream")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file extension" in response.json()["detail"]
