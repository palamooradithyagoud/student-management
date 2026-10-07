from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from backend.app.core.config import settings

class StudentSemesterSummaryBuilder:
    """
    Builds student_semester_summary.csv containing aggregated metrics per student per semester,
    including Sem 1 -> Sem 2 deltas when both semesters exist.
    """

    @staticmethod
    def build_student_semester_summary(
        master_df: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        out_path = output_path or (settings.DATA_PROCESSED_DIR / "student_semester_summary.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if master_df.empty:
            empty_df = pd.DataFrame(columns=[
                "roll_no", "student_name", "section", "semester", "sgpa",
                "backlog_count", "average_attendance", "failed_subject_count",
                "passed_subject_count", "sgpa_change", "attendance_change", "backlog_change"
            ])
            empty_df.to_csv(out_path, index=False, encoding="utf-8")
            return empty_df

        # Group by student and semester
        rows = []
        grouped = master_df.groupby(["roll_no", "semester"])

        for (roll_no, sem), group in grouped:
            student_name = group["student_name"].dropna().iloc[0] if not group["student_name"].dropna().empty else None
            section = group["section"].dropna().iloc[0] if not group["section"].dropna().empty else None
            
            # Attendance average
            valid_att = group["attendance_percentage"].dropna()
            avg_att = round(valid_att.mean(), 2) if not valid_att.empty else np.nan

            # Pass/Fail counts
            statuses = group["status"].fillna("").astype(str).str.upper()
            failed_count = int((statuses == "FAIL").sum())
            passed_count = int((statuses == "PASS").sum())

            # Backlogs and SGPA from data if present
            sgpa_val = group["sgpa"].dropna().iloc[0] if not group["sgpa"].dropna().empty else np.nan
            if "backlog_count" in group.columns and not group["backlog_count"].dropna().empty and pd.notna(group["backlog_count"].dropna().iloc[0]):
                backlog_val = int(float(group["backlog_count"].dropna().iloc[0]))
            else:
                backlog_val = failed_count

            rows.append({
                "roll_no": roll_no,
                "student_name": student_name,
                "section": section,
                "semester": int(sem),
                "sgpa": sgpa_val,
                "backlog_count": backlog_val,
                "average_attendance": avg_att,
                "failed_subject_count": failed_count,
                "passed_subject_count": passed_count,
                "sgpa_change": np.nan,
                "attendance_change": np.nan,
                "backlog_change": np.nan
            })

        summary_df = pd.DataFrame(rows)

        # Compute consecutive semester progression deltas per student (e.g. S1 -> S2, S2 -> S3, ...)
        for roll, student_records in summary_df.groupby("roll_no"):
            sorted_recs = student_records.sort_values("semester")
            prev_row = None
            for curr_idx, curr_row in sorted_recs.iterrows():
                if prev_row is not None:
                    curr_sgpa = curr_row["sgpa"]
                    prev_sgpa = prev_row["sgpa"]
                    if pd.notna(curr_sgpa) and pd.notna(prev_sgpa):
                        summary_df.loc[curr_idx, "sgpa_change"] = round(float(curr_sgpa) - float(prev_sgpa), 2)

                    curr_att = curr_row["average_attendance"]
                    prev_att = prev_row["average_attendance"]
                    if pd.notna(curr_att) and pd.notna(prev_att):
                        summary_df.loc[curr_idx, "attendance_change"] = round(float(curr_att) - float(prev_att), 2)

                    curr_back = curr_row["backlog_count"]
                    prev_back = prev_row["backlog_count"]
                    if pd.notna(curr_back) and pd.notna(prev_back):
                        summary_df.loc[curr_idx, "backlog_change"] = int(curr_back) - int(prev_back)
                prev_row = curr_row

        summary_df = summary_df.sort_values(by=["roll_no", "semester"])
        summary_df.to_csv(out_path, index=False, encoding="utf-8")
        return summary_df
