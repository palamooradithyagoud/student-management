from typing import Any, Optional
import pandas as pd
import numpy as np

class DataValidator:
    """
    Performs comprehensive validation across students, results, attendance,
    subjects, and cross-dataset student presence.
    """

    @staticmethod
    def validate_cross_dataset_students(
        sem1_res_students: set[str],
        sem2_res_students: set[str],
        sem1_att_students: set[str],
        sem2_att_students: set[str],
        all_res_students: Optional[set[str]] = None,
        all_att_students: Optional[set[str]] = None
    ) -> dict[str, Any]:
        """
        Cross-validates student presence across the datasets.
        """
        all_res = all_res_students if all_res_students is not None else sem1_res_students.union(sem2_res_students)
        all_att = all_att_students if all_att_students is not None else sem1_att_students.union(sem2_att_students)
        all_students = all_res.union(all_att)
        
        # A. Present in both results and attendance
        present_in_all = all_res.intersection(all_att)

        # B. In results but missing attendance
        in_res_missing_att = all_res - all_att

        # C. In attendance but missing results
        in_att_missing_res = all_att - all_res

        # D. In Sem 1 but missing Sem 2 ("Missing from Sem 2 dataset", NOT labeled dropout)
        sem1_all = sem1_res_students.union(sem1_att_students)
        sem2_all = sem2_res_students.union(sem2_att_students)
        in_sem1_missing_sem2 = sem1_all - sem2_all

        # E. In Sem 2 but missing Sem 1
        in_sem2_missing_sem1 = sem2_all - sem1_all

        return {
            "total_distinct_students": len(all_students),
            "sem1_total_students": len(sem1_all),
            "sem2_total_students": len(sem2_all),
            "present_in_all_datasets": sorted(list(present_in_all)),
            "in_results_missing_attendance": sorted(list(in_res_missing_att)),
            "in_attendance_missing_results": sorted(list(in_att_missing_res)),
            "missing_from_sem2_dataset": sorted(list(in_sem1_missing_sem2)),
            "missing_from_sem1_dataset": sorted(list(in_sem2_missing_sem1)),
            "counts": {
                "present_in_all": len(present_in_all),
                "in_results_missing_attendance": len(in_res_missing_att),
                "in_attendance_missing_results": len(in_att_missing_res),
                "missing_from_sem2_dataset": len(in_sem1_missing_sem2),
                "missing_from_sem1_dataset": len(in_sem2_missing_sem1)
            }
        }

    @staticmethod
    def validate_results_data(results_df: pd.DataFrame) -> dict[str, Any]:
        """
        Validates results records for duplicates, missing marks, missing grades.
        """
        if results_df.empty:
            return {
                "total_records": 0,
                "sem1_records": 0,
                "sem2_records": 0,
                "missing_marks": 0,
                "missing_grades": 0,
                "duplicate_records": 0,
                "duplicates_list": []
            }

        sem1_recs = int((results_df["semester"] == 1).sum()) if "semester" in results_df.columns else 0
        sem2_recs = int((results_df["semester"] == 2).sum()) if "semester" in results_df.columns else 0
        missing_marks = int(results_df["marks"].isna().sum()) if "marks" in results_df.columns else 0
        missing_grades = int(results_df["grade"].isna().sum()) if "grade" in results_df.columns else 0

        # Duplicate check on (roll_no, semester, subject_code)
        dup_mask = results_df.duplicated(subset=["roll_no", "semester", "subject_code"], keep=False)
        duplicate_records = int(dup_mask.sum())
        duplicates_list = results_df[dup_mask][["roll_no", "semester", "subject_code"]].to_dict(orient="records") if duplicate_records > 0 else []

        return {
            "total_records": len(results_df),
            "sem1_records": sem1_recs,
            "sem2_records": sem2_recs,
            "missing_marks": missing_marks,
            "missing_grades": missing_grades,
            "duplicate_records": duplicate_records,
            "duplicates_list": duplicates_list
        }

    @staticmethod
    def validate_attendance_data(attendance_df: pd.DataFrame) -> dict[str, Any]:
        """
        Validates attendance records for duplicates, missing attendance, out-of-bounds attendance.
        """
        if attendance_df.empty:
            return {
                "total_records": 0,
                "sem1_records": 0,
                "sem2_records": 0,
                "missing_attendance": 0,
                "invalid_attendance": 0,
                "duplicate_records": 0,
                "duplicates_list": []
            }

        sem1_recs = int((attendance_df["semester"] == 1).sum()) if "semester" in attendance_df.columns else 0
        sem2_recs = int((attendance_df["semester"] == 2).sum()) if "semester" in attendance_df.columns else 0
        missing_att = int(attendance_df["attendance_percentage"].isna().sum()) if "attendance_percentage" in attendance_df.columns else 0
        
        invalid_att = 0
        if "attendance_percentage" in attendance_df.columns:
            valid_nums = attendance_df["attendance_percentage"].dropna()
            invalid_att = int(((valid_nums < 0) | (valid_nums > 100)).sum())

        dup_mask = attendance_df.duplicated(subset=["roll_no", "semester", "subject_code"], keep=False)
        duplicate_records = int(dup_mask.sum())
        duplicates_list = attendance_df[dup_mask][["roll_no", "semester", "subject_code"]].to_dict(orient="records") if duplicate_records > 0 else []

        return {
            "total_records": len(attendance_df),
            "sem1_records": sem1_recs,
            "sem2_records": sem2_recs,
            "missing_attendance": missing_att,
            "invalid_attendance": invalid_att,
            "duplicate_records": duplicate_records,
            "duplicates_list": duplicates_list
        }
