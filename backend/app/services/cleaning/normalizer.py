import re
from typing import Any, Optional
import pandas as pd
import numpy as np
from backend.app.services.cleaning.logger import CleaningAuditLogger

class DataNormalizer:
    """
    Normalizes roll numbers, student names, subject codes, attendance values,
    grades, marks, and SGPA while logging every adjustment to the audit logger.
    """

    def __init__(self, logger: Optional[CleaningAuditLogger] = None):
        self.logger = logger or CleaningAuditLogger()

    @staticmethod
    def normalize_roll_no(raw_val: Any) -> Optional[str]:
        """
        Normalize roll number: uppercase, strip whitespace, remove internal spaces.
        Example: ' 25881a6606 ' -> '25881A6606'
        """
        if raw_val is None or pd.isna(raw_val):
            return None
        val_str = str(raw_val).strip().upper()
        # Remove internal spaces / non-alphanumeric except hyphen
        val_str = re.sub(r'[\s]+', '', val_str)
        # If float representation like '258816606.0', fix it
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return val_str if val_str else None

    @staticmethod
    def normalize_subject_code(raw_val: Any) -> Optional[str]:
        """
        Normalize subject code: uppercase, strip whitespace, remove internal spaces.
        Example: ' 22CSM-101 ' -> '22CSM101' or '22CSM-101'
        """
        if raw_val is None or pd.isna(raw_val):
            return None
        val_str = str(raw_val).strip().upper()
        val_str = re.sub(r'\s+', '', val_str)
        return val_str if val_str else None

    @staticmethod
    def normalize_name(raw_val: Any) -> Optional[str]:
        """
        Normalize student/subject name: clean whitespace, title case or clean upper.
        """
        if raw_val is None or pd.isna(raw_val):
            return None
        val_str = str(raw_val).strip()
        val_str = re.sub(r'\s+', ' ', val_str)
        return val_str if val_str else None

    def clean_results_dataframe(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """
        Clean and normalize raw Results DataFrame.
        """
        df_clean = df.copy()
        
        # Ensure roll_no column
        if "roll_no" not in df_clean.columns:
            raise ValueError(f"Results file '{source_file}' missing required 'roll_no' column.")

        # Clean roll numbers
        original_rolls = df_clean["roll_no"].copy()
        df_clean["roll_no"] = df_clean["roll_no"].apply(self.normalize_roll_no)

        # Log roll number transformations
        for idx, (orig, norm) in enumerate(zip(original_rolls, df_clean["roll_no"])):
            if pd.isna(norm):
                self.logger.log(
                    source_file=source_file,
                    record_identifier=f"Row_{idx+1}",
                    issue="Missing or empty Roll Number",
                    action_taken="Flagged as missing roll_no",
                    reason="Student roll number cannot be empty"
                )
            elif str(orig) != str(norm):
                self.logger.log(
                    source_file=source_file,
                    record_identifier=str(orig),
                    issue=f"Inconsistent roll number format '{orig}'",
                    action_taken=f"Normalized to '{norm}'",
                    reason="Standardized whitespace and uppercase casing"
                )

        # Drop rows where roll_no is missing after logging
        df_clean = df_clean.dropna(subset=["roll_no"])

        # Subject code & name normalization
        if "subject_code" in df_clean.columns:
            orig_codes = df_clean["subject_code"].copy()
            df_clean["subject_code"] = df_clean["subject_code"].apply(self.normalize_subject_code)
            for idx, (orig, norm) in enumerate(zip(orig_codes, df_clean["subject_code"])):
                if str(orig) != str(norm) and pd.notna(orig):
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=f"Row_{idx+1}",
                        issue=f"Inconsistent subject code '{orig}'",
                        action_taken=f"Normalized to '{norm}'",
                        reason="Standardized subject code casing and whitespace"
                    )

        if "student_name" in df_clean.columns:
            df_clean["student_name"] = df_clean["student_name"].apply(self.normalize_name)

        if "subject_name" in df_clean.columns:
            df_clean["subject_name"] = df_clean["subject_name"].apply(self.normalize_name)

        # Marks cleaning: convert numeric, preserve NaN (do not invent)
        if "marks" in df_clean.columns:
            def clean_mark(val, row_id):
                if pd.isna(val) or val == "" or str(val).strip().lower() in ["ab", "absent", "null", "none", "-"]:
                    return np.nan
                try:
                    m = float(str(val).strip())
                    return m
                except ValueError:
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=str(row_id),
                        issue=f"Non-numeric mark value '{val}'",
                        action_taken="Preserved as NULL",
                        reason="Marks must be numeric or NULL"
                    )
                    return np.nan

            df_clean["marks"] = [clean_mark(val, r) for val, r in zip(df_clean["marks"], df_clean["roll_no"])]

        # Grade cleaning
        if "grade" in df_clean.columns:
            def clean_grade(val):
                if pd.isna(val) or val == "":
                    return None
                g = str(val).strip().upper()
                return g
            df_clean["grade"] = df_clean["grade"].apply(clean_grade)

        # Grade point cleaning
        if "grade_point" in df_clean.columns:
            def clean_gp(val):
                if pd.isna(val) or val == "":
                    return np.nan
                try:
                    return float(val)
                except ValueError:
                    return np.nan
            df_clean["grade_point"] = df_clean["grade_point"].apply(clean_gp)

        # Status cleaning
        if "status" in df_clean.columns:
            def clean_status(val):
                if pd.isna(val) or val == "":
                    return None
                s = str(val).strip().upper()
                if "PASS" in s or s == "P":
                    return "PASS"
                elif "FAIL" in s or s == "F":
                    return "FAIL"
                elif "ABSENT" in s or s == "AB":
                    return "ABSENT"
                return s
            df_clean["status"] = df_clean["status"].apply(clean_status)

        return df_clean

    def clean_attendance_dataframe(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """
        Clean and normalize raw Attendance DataFrame, validating bounds (0 <= attendance <= 100).
        """
        df_clean = df.copy()

        if "roll_no" not in df_clean.columns:
            raise ValueError(f"Attendance file '{source_file}' missing required 'roll_no' column.")

        # Clean roll numbers
        original_rolls = df_clean["roll_no"].copy()
        df_clean["roll_no"] = df_clean["roll_no"].apply(self.normalize_roll_no)

        for idx, (orig, norm) in enumerate(zip(original_rolls, df_clean["roll_no"])):
            if pd.isna(norm):
                self.logger.log(
                    source_file=source_file,
                    record_identifier=f"Row_{idx+1}",
                    issue="Missing or empty Roll Number",
                    action_taken="Flagged as missing roll_no",
                    reason="Student roll number cannot be empty"
                )
            elif str(orig) != str(norm):
                self.logger.log(
                    source_file=source_file,
                    record_identifier=str(orig),
                    issue=f"Inconsistent roll number format '{orig}'",
                    action_taken=f"Normalized to '{norm}'",
                    reason="Standardized whitespace and uppercase casing"
                )

        df_clean = df_clean.dropna(subset=["roll_no"])

        if "subject_code" in df_clean.columns:
            df_clean["subject_code"] = df_clean["subject_code"].apply(self.normalize_subject_code)

        if "student_name" in df_clean.columns:
            df_clean["student_name"] = df_clean["student_name"].apply(self.normalize_name)

        if "subject_name" in df_clean.columns:
            df_clean["subject_name"] = df_clean["subject_name"].apply(self.normalize_name)

        # Attendance percentage cleaning and bounds validation
        if "attendance_percentage" in df_clean.columns:
            def clean_att(val, r_id, s_code):
                if pd.isna(val) or val == "" or str(val).strip().lower() in ["null", "none", "-"]:
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=f"{r_id}_{s_code}",
                        issue="Missing attendance value",
                        action_taken="Logged missing attendance",
                        reason="Attendance value is required"
                    )
                    return np.nan
                
                # Parse string percentage e.g. "85%", "75.5"
                s = str(val).replace("%", "").strip()
                try:
                    num = float(s)
                except ValueError:
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=f"{r_id}_{s_code}",
                        issue=f"Unparseable attendance '{val}'",
                        action_taken="Marked as NaN",
                        reason="Attendance must be a valid numeric percentage"
                    )
                    return np.nan

                # If stored as ratio 0.0 - 1.0 (e.g. 0.85 instead of 85%), handle thoughtfully
                if 0.0 < num <= 1.0 and not (num == 1.0 and "100" in str(val)):
                    # Check if all numbers are small or if it's decimal representation
                    # E.g., 0.75 -> 75%
                    num_scaled = num * 100.0
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=f"{r_id}_{s_code}",
                        issue=f"Decimal attendance ratio detected '{num}'",
                        action_taken=f"Converted to percentage '{num_scaled}'",
                        reason="Standardized 0-1 ratio to 0-100 percentage"
                    )
                    num = num_scaled

                # Bounds check [0..100]
                if num < 0 or num > 100:
                    self.logger.log(
                        source_file=source_file,
                        record_identifier=f"{r_id}_{s_code}",
                        issue=f"Invalid attendance percentage '{num}' out of bounds [0..100]",
                        action_taken="Flagged as invalid attendance value",
                        reason="Attendance percentage must logically satisfy 0 <= attendance <= 100"
                    )

                return num

            df_clean["attendance_percentage"] = [
                clean_att(val, r, sc) for val, r, sc in zip(
                    df_clean["attendance_percentage"],
                    df_clean["roll_no"],
                    df_clean.get("subject_code", [""] * len(df_clean))
                )
            ]

        return df_clean
