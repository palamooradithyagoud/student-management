import os
import re
from pathlib import Path
from typing import Any, Optional
import pandas as pd
import openpyxl

CANONICAL_ALIASES = {
    "roll_no": [
        "roll_no", "roll no", "rollno", "roll number", "roll_number", "hall ticket", "hall ticket no",
        "hall ticket number", "htno", "ht_no", "student id", "student_id", "regd no", "regd_no",
        "regno", "pin", "pin no", "usn", "id"
    ],
    "student_name": [
        "student_name", "student name", "name", "candidate name", "student", "full name", "name of the student"
    ],
    "section": [
        "section", "sec", "class_sec", "branch_sec"
    ],
    "batch": [
        "batch", "academic year", "ay", "year of joining", "regulation"
    ],
    "subject_code": [
        "subject_code", "subject code", "sub code", "sub_code", "course code", "course_code", "subcode", "code"
    ],
    "subject_name": [
        "subject_name", "subject name", "subject", "sub_name", "course", "course name", "course_name", "course title", "subject title"
    ],
    "marks": [
        "marks", "total_marks", "total marks", "total", "external_marks", "final_marks", "marks_obtained", "score", "total score"
    ],
    "grade": [
        "grade", "letter_grade", "letter grade", "final_grade"
    ],
    "grade_point": [
        "grade_point", "grade point", "grade_points", "grade points", "gp", "points", "credits_earned"
    ],
    "status": [
        "status", "result", "pass_fail", "pass/fail", "remark", "remarks", "outcome"
    ],
    "attendance_percentage": [
        "attendance_percentage", "attendance %", "attendance percentage", "attendance", "percentage",
        "avg_attendance", "att_%", "total_%", "present_%", "attendance_pct", "att_percentage"
    ],
    "sgpa": [
        "sgpa", "gpa", "semester_gpa", "sem_gpa", "spi"
    ],
    "backlog_count": [
        "backlog_count", "backlogs", "backlog count", "no of backlogs", "failed_count", "no_of_backlogs", "arrears"
    ]
}

def clean_str(val: Any) -> str:
    """Normalize string for alias matching."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = re.sub(r'[\r\n\t_]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def match_column_to_canonical(col_name: str) -> Optional[str]:
    """Find canonical name for a given column header string."""
    cleaned = clean_str(col_name)
    if not cleaned:
        return None
    
    # Exact match first
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            if cleaned == alias:
                return canonical
    
    # Partial substring / token match
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            if alias in cleaned or cleaned in alias:
                return canonical

    return None

class FileInspector:
    """
    Inspects Excel and CSV files to dynamically identify headers,
    structures, sheets, missing values, duplicates, and canonical mappings.
    """

    @staticmethod
    def inspect_file(file_path: Path) -> dict[str, Any]:
        ext = file_path.suffix.lower()
        if ext not in [".xlsx", ".xls", ".csv"]:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats are .xlsx, .xls, .csv")

        num_sheets = 1
        sheet_names = ["Sheet1"]

        if ext in [".xlsx", ".xls"]:
            if ext == ".xlsx":
                wb = openpyxl.load_workbook(file_path, read_only=True)
                sheet_names = wb.sheetnames
                num_sheets = len(sheet_names)
                wb.close()
            # Read first sheet with no header to inspect raw rows
            df_raw = pd.read_excel(file_path, sheet_name=0, header=None)
        else:
            try:
                df_raw = pd.read_csv(file_path, header=None, encoding='utf-8')
            except UnicodeDecodeError:
                df_raw = pd.read_csv(file_path, header=None, encoding='latin1')

        # Detect actual header row among the top 15 rows
        detected_header_idx = FileInspector.detect_header_row(df_raw)
        
        # Reload with identified header
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, sheet_name=0, skiprows=detected_header_idx)
        else:
            try:
                df = pd.read_csv(file_path, skiprows=detected_header_idx, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, skiprows=detected_header_idx, encoding='latin1')

        # Drop entirely empty rows
        df = df.dropna(how='all')

        orig_cols = [str(c).strip() for c in df.columns]
        mapping = {}
        for col in orig_cols:
            canon = match_column_to_canonical(col)
            if canon:
                mapping[col] = canon

        # Analyze missing values and duplicate rows
        missing_summary = {str(col): int(df[col].isna().sum()) for col in df.columns}
        duplicate_rows = int(df.duplicated().sum())

        # Sample records (top 5 formatted)
        sample_df = df.head(5).fillna("")
        sample_records = sample_df.to_dict(orient="records")

        # Detect dataset type and semester if identifiable
        text_corpus = " ".join([file_path.name] + [str(x) for x in df_raw.head(detected_header_idx + 1).values.flatten()]).lower()
        detected_type = None
        detected_semester = 1 if ("sem 1" in text_corpus or "sem-1" in text_corpus or "sem1" in text_corpus or "1st sem" in text_corpus or "i sem" in text_corpus or "i-i" in text_corpus) else (2 if ("sem 2" in text_corpus or "sem-2" in text_corpus or "sem2" in text_corpus or "2nd sem" in text_corpus or "ii sem" in text_corpus or "i-ii" in text_corpus) else None)
        
        if "attend" in text_corpus:
            detected_type = f"sem{detected_semester or 1}_attendance"
        elif "result" in text_corpus or "mark" in text_corpus or "grade" in text_corpus:
            detected_type = f"sem{detected_semester or 1}_results"

        warnings = []
        if "roll_no" not in mapping.values():
            warnings.append("Could not automatically detect a Roll Number / Student ID column. Please verify column headers.")
        if duplicate_rows > 0:
            warnings.append(f"Detected {duplicate_rows} duplicate rows in raw dataset.")

        return {
            "filename": file_path.name,
            "extension": ext,
            "num_sheets": num_sheets,
            "sheet_names": sheet_names,
            "detected_header_row": detected_header_idx,
            "original_columns": orig_cols,
            "column_mappings": mapping,
            "total_rows": len(df),
            "sample_records": sample_records,
            "missing_value_summary": missing_summary,
            "duplicate_rows_detected": duplicate_rows,
            "detected_dataset_type": detected_type,
            "detected_semester": detected_semester,
            "warnings": warnings
        }

    @staticmethod
    def detect_header_row(df_raw: pd.DataFrame) -> int:
        """
        Scan top 15 rows to find the row that has the highest density
        of recognized academic column names.
        """
        max_rows_to_check = min(15, len(df_raw))
        best_row_idx = 0
        best_score = -1

        for r_idx in range(max_rows_to_check):
            row_values = df_raw.iloc[r_idx].dropna().tolist()
            if not row_values:
                continue
            
            score = 0
            for val in row_values:
                canon = match_column_to_canonical(str(val))
                if canon:
                    score += 2
                # Extra weight for roll_no and subject indicators
                if canon in ["roll_no", "subject_code", "subject_name", "marks", "attendance_percentage"]:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_row_idx = r_idx

        # If no recognizable keywords found, default to row 0
        if best_score <= 0:
            return 0
        return best_row_idx
