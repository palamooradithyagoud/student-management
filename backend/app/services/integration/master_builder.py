from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from backend.app.core.config import settings

class MasterDatasetBuilder:
    """
    Builds the unified, normalized master_dataset.csv where each row represents:
    ONE STUDENT + ONE SEMESTER + ONE SUBJECT.
    
    Preserves NULL for any unavailable data (NO FABRICATED VALUES).
    """

    @staticmethod
    def build_master_dataset(
        students_df: pd.DataFrame,
        subjects_df: pd.DataFrame,
        results_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        semester_summary_df: Optional[pd.DataFrame] = None,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        out_path = output_path or (settings.DATA_PROCESSED_DIR / "master_dataset.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Base is results if available, else outer join with attendance
        if not results_df.empty:
            df = results_df.copy()
            if not attendance_df.empty:
                # Merge attendance on roll_no + semester + subject_code
                att_sub = attendance_df[["roll_no", "semester", "subject_code", "attendance_percentage"]].copy()
                # Deduplicate if necessary
                att_sub = att_sub.drop_duplicates(subset=["roll_no", "semester", "subject_code"], keep="first")
                df = pd.merge(df, att_sub, on=["roll_no", "semester", "subject_code"], how="left")
            else:
                df["attendance_percentage"] = np.nan
        elif not attendance_df.empty:
            df = attendance_df.copy()
            df["marks"] = np.nan
            df["grade"] = None
            df["grade_point"] = np.nan
            df["status"] = None
        else:
            # Empty fallback
            df = pd.DataFrame(columns=[
                "student_id", "roll_no", "student_name", "section", "semester",
                "subject_id", "subject_code", "subject_name", "attendance_percentage",
                "marks", "grade", "grade_point", "status", "sgpa", "backlog_count"
            ])
            df.to_csv(out_path, index=False, encoding="utf-8")
            return df

        # Enrich with student metadata (name, section)
        if not students_df.empty:
            stu_meta = students_df[["roll_no", "student_id", "student_name", "section"]].drop_duplicates(subset=["roll_no"], keep="first")
            # Avoid clobbering existing non-null student_name if present
            for col in ["student_id", "student_name", "section"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
            df = pd.merge(df, stu_meta, on="roll_no", how="left")
        else:
            if "student_id" not in df.columns:
                df["student_id"] = "STU_" + df["roll_no"].astype(str)
            if "student_name" not in df.columns:
                df["student_name"] = None
            if "section" not in df.columns:
                df["section"] = "A"

        # Enrich with subject metadata (subject_id, subject_name)
        if not subjects_df.empty:
            sub_meta = subjects_df[["subject_code", "semester", "subject_id", "subject_name"]].drop_duplicates(subset=["subject_code", "semester"], keep="first")
            for col in ["subject_id", "subject_name"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
            df = pd.merge(df, sub_meta, on=["subject_code", "semester"], how="left")
        else:
            if "subject_id" not in df.columns:
                df["subject_id"] = "SUB_" + df["subject_code"].astype(str)
            if "subject_name" not in df.columns:
                df["subject_name"] = df["subject_code"]

        # Enrich with SGPA and Backlog count from semester_summary if available
        if semester_summary_df is not None and not semester_summary_df.empty:
            sem_meta = semester_summary_df[["roll_no", "semester", "sgpa", "backlog_count"]].drop_duplicates(subset=["roll_no", "semester"], keep="first")
            for col in ["sgpa", "backlog_count"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
            df = pd.merge(df, sem_meta, on=["roll_no", "semester"], how="left")
        else:
            if "sgpa" not in df.columns:
                df["sgpa"] = np.nan
            if "backlog_count" not in df.columns:
                df["backlog_count"] = np.nan

        # Ensure all required columns are present in exact order
        required_cols = [
            "student_id",
            "roll_no",
            "student_name",
            "section",
            "semester",
            "subject_id",
            "subject_code",
            "subject_name",
            "attendance_percentage",
            "marks",
            "grade",
            "grade_point",
            "status",
            "sgpa",
            "backlog_count"
        ]

        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        master_df = df[required_cols].copy()
        # Sort predictably
        master_df = master_df.sort_values(by=["semester", "roll_no", "subject_code"])

        master_df.to_csv(out_path, index=False, encoding="utf-8")
        return master_df
