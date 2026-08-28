import time
from pathlib import Path
from typing import Optional, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.services.ingestion.inspector import FileInspector
from backend.app.services.ingestion.loader import RawDataLoader
from backend.app.services.cleaning.logger import CleaningAuditLogger
from backend.app.services.cleaning.normalizer import DataNormalizer
from backend.app.services.integration.mapper import SubjectMapper, ResultAttendanceMapper
from backend.app.services.integration.master_builder import MasterDatasetBuilder
from backend.app.services.integration.summary_builder import StudentSemesterSummaryBuilder
from backend.app.services.validation.validator import DataValidator
from backend.app.services.validation.quality_reporter import QualityReporter
from backend.app.models.student import Student
from backend.app.models.subject import Subject
from backend.app.models.result import Result
from backend.app.models.attendance import Attendance
from backend.app.models.semester_summary import SemesterSummary

class DataPipelineOrchestrator:
    """
    Executes the comprehensive Phase 1 Data Pipeline on authentic college data:
    Raw Files -> Ingestion -> Cleaning -> Subject Standardization ->
    Entity Resolution & Mapping -> Master Dataset -> Validation -> Quality Reports.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.logger = CleaningAuditLogger()
        self.normalizer = DataNormalizer(logger=self.logger)

    def run_pipeline(
        self,
        sem1_res_path: Optional[Path] = None,
        sem2_res_path: Optional[Path] = None,
        sem1_att_path: Optional[Path] = None,
        sem2_att_path: Optional[Path] = None
    ) -> dict[str, Any]:
        start_time = time.time()
        self.logger.clear()

        # 1. Discover all authentic input datasets
        base_data = settings.DATA_DIR
        sem_res_dir = base_data / "sem result"
        att_dir = base_data / "ATTENDENCE"
        raw_dir = base_data / "raw"

        # Locate Sem 1 and Sem 2 Results
        p_s1_res = sem1_res_path
        p_s2_res = sem2_res_path

        if not p_s1_res or not p_s1_res.exists():
            for f in list(sem_res_dir.glob("*1-1*")) + list(raw_dir.glob("*sem1*res*")) + list(raw_dir.glob("*sem1*")):
                p_s1_res = f
                break

        if not p_s2_res or not p_s2_res.exists():
            for f in list(sem_res_dir.glob("*1-2*")) + list(raw_dir.glob("*sem2*res*")) + list(raw_dir.glob("*sem2*")):
                p_s2_res = f
                break

        # Locate Section-wise Attendance files
        s1_att_files: List[Path] = []
        s2_att_files: List[Path] = []

        if sem1_att_path and sem1_att_path.exists():
            s1_att_files = [sem1_att_path]
        else:
            s1_att_files = sorted(list(att_dir.glob("*I Semester*.xlsx")) + list(raw_dir.glob("*sem1*att*.xlsx")))

        if sem2_att_path and sem2_att_path.exists():
            s2_att_files = [sem2_att_path]
        else:
            s2_att_files = sorted(list(att_dir.glob("*II _*.xlsx")) + list(raw_dir.glob("*sem2*att*.xlsx")))

        # 2. Load & Clean Results Data
        s1_res_df = self._load_and_clean_results(p_s1_res, semester=1, dataset_type="sem1_results")
        s2_res_df = self._load_and_clean_results(p_s2_res, semester=2, dataset_type="sem2_results")

        # 3. Load & Clean Attendance Data (all sections combined)
        s1_att_df_list = [self._load_and_clean_attendance(f, semester=1, dataset_type="sem1_attendance") for f in s1_att_files]
        s2_att_df_list = [self._load_and_clean_attendance(f, semester=2, dataset_type="sem2_attendance") for f in s2_att_files]

        s1_att_df = pd.concat(s1_att_df_list, ignore_index=True) if s1_att_df_list else pd.DataFrame()
        s2_att_df = pd.concat(s2_att_df_list, ignore_index=True) if s2_att_df_list else pd.DataFrame()

        # Combine results and attendance
        results_df = pd.concat([s1_res_df, s2_res_df], ignore_index=True) if (not s1_res_df.empty or not s2_res_df.empty) else pd.DataFrame()
        attendance_df = pd.concat([s1_att_df, s2_att_df], ignore_index=True) if (not s1_att_df.empty or not s2_att_df.empty) else pd.DataFrame()

        # 4. Extract & Standardize Students Master Table
        students_df = self._build_students_table(results_df, attendance_df)

        # 5. Extract & Standardize Subjects and Mappings
        subjects_df, subject_mappings_stats = self._build_subjects_table(results_df, attendance_df)

        # Apply standard subject codes
        results_df, attendance_df = self._apply_standard_subject_codes(results_df, attendance_df)

        # 6. Save results.csv and attendance.csv
        res_csv = settings.DATA_PROCESSED_DIR / "results.csv"
        att_csv = settings.DATA_PROCESSED_DIR / "attendance.csv"
        results_df.to_csv(res_csv, index=False, encoding="utf-8")
        attendance_df.to_csv(att_csv, index=False, encoding="utf-8")

        # 7. Extract Semester Summary (SGPA / Backlog count)
        semester_summary_df = self._build_semester_summary(results_df)
        sem_sum_csv = settings.DATA_PROCESSED_DIR / "semester_summary.csv"
        semester_summary_df.to_csv(sem_sum_csv, index=False, encoding="utf-8")

        # 8. Result <-> Attendance Mapping & Success Rate
        merged_records, mapping_stats = ResultAttendanceMapper.map_results_and_attendance(results_df, attendance_df)

        # 9. Master Dataset Generation
        master_df = MasterDatasetBuilder.build_master_dataset(
            students_df=students_df,
            subjects_df=subjects_df,
            results_df=results_df,
            attendance_df=attendance_df,
            semester_summary_df=semester_summary_df
        )

        # 10. Student Semester Summary Generation (with Sem 1 -> Sem 2 deltas)
        student_sem_summary_df = StudentSemesterSummaryBuilder.build_student_semester_summary(master_df)

        # 11. Validation & Quality Checks
        s1_res_stus = set(s1_res_df["roll_no"]) if not s1_res_df.empty else set()
        s2_res_stus = set(s2_res_df["roll_no"]) if not s2_res_df.empty else set()
        s1_att_stus = set(s1_att_df["roll_no"]) if not s1_att_df.empty else set()
        s2_att_stus = set(s2_att_df["roll_no"]) if not s2_att_df.empty else set()

        student_val = DataValidator.validate_cross_dataset_students(
            sem1_res_students=s1_res_stus,
            sem2_res_students=s2_res_stus,
            sem1_att_students=s1_att_stus,
            sem2_att_students=s2_att_stus
        )

        results_val = DataValidator.validate_results_data(results_df)
        attendance_val = DataValidator.validate_attendance_data(attendance_df)

        critical_errors = (
            results_val.get("missing_marks", 0) +
            attendance_val.get("invalid_attendance", 0) +
            (1 if student_val.get("total_distinct_students", 0) == 0 else 0)
        )
        warnings = (
            results_val.get("duplicate_records", 0) +
            attendance_val.get("duplicate_records", 0) +
            subject_mappings_stats.get("unmatched_subjects", 0) +
            student_val.get("counts", {}).get("in_results_missing_attendance", 0) +
            student_val.get("counts", {}).get("in_attendance_missing_results", 0) +
            student_val.get("counts", {}).get("missing_from_sem2_dataset", 0)
        )
        records_requiring_review = warnings + critical_errors

        # 12. Generate Official Markdown & JSON Reports
        quality_report = QualityReporter.generate_report(
            student_val=student_val,
            results_val=results_val,
            attendance_val=attendance_val,
            subject_stats=subject_mappings_stats,
            mapping_stats=mapping_stats,
            critical_errors=critical_errors,
            warnings=warnings,
            records_requiring_review=records_requiring_review
        )

        # 13. Sync to Database
        if self.db:
            self._sync_to_db(students_df, subjects_df, results_df, attendance_df, semester_summary_df)

        elapsed = round(time.time() - start_time, 2)

        generated_files = [
            "data/processed/students.csv",
            "data/processed/subjects.csv",
            "data/processed/results.csv",
            "data/processed/attendance.csv",
            "data/processed/semester_summary.csv",
            "data/processed/master_dataset.csv",
            "data/processed/student_semester_summary.csv",
            "data/processed/subject_mapping.csv",
            "data/reports/data_quality_report.json",
            "data/reports/data_quality_report.md",
            "data/reports/data_cleaning_log.csv",
            "data/reports/mapping_report.csv"
        ]

        return {
            "status": "SUCCESS",
            "message": "Phase 1 Data Ingestion, Cleaning, Normalization, Integration, and Validation completed successfully.",
            "execution_time_seconds": elapsed,
            "total_students": student_val.get("total_distinct_students", 0),
            "sem1_students": student_val.get("sem1_total_students", 0),
            "sem2_students": student_val.get("sem2_total_students", 0),
            "total_results": len(results_df),
            "total_attendance": len(attendance_df),
            "matched_records": mapping_stats.get("matched_records", 0),
            "unmatched_records": mapping_stats.get("unmatched_records", 0),
            "mapping_success_rate": mapping_stats.get("mapping_success_rate", 0.0),
            "generated_files": generated_files,
            "critical_errors": critical_errors,
            "warnings": warnings,
            "records_requiring_review": records_requiring_review,
            "quality_report": quality_report
        }

    def _load_and_clean_results(self, file_path: Optional[Path], semester: int, dataset_type: str) -> pd.DataFrame:
        if not file_path or not file_path.exists():
            return pd.DataFrame()
        df_raw = RawDataLoader.load_dataset(file_path, dataset_type=dataset_type, semester=semester)
        df_clean = self.normalizer.clean_results_dataframe(df_raw, source_file=file_path.name)
        df_clean["result_id"] = [f"RES_S{semester}_{r}_{sc}" for r, sc in zip(df_clean["roll_no"], df_clean.get("subject_code", [""]*len(df_clean)))]
        df_clean["student_id"] = "STU_" + df_clean["roll_no"].astype(str)
        return df_clean

    def _load_and_clean_attendance(self, file_path: Optional[Path], semester: int, dataset_type: str) -> pd.DataFrame:
        if not file_path or not file_path.exists():
            return pd.DataFrame()
        df_raw = RawDataLoader.load_dataset(file_path, dataset_type=dataset_type, semester=semester)
        df_clean = self.normalizer.clean_attendance_dataframe(df_raw, source_file=file_path.name)
        df_clean["attendance_id"] = [f"ATT_S{semester}_{r}_{sc}" for r, sc in zip(df_clean["roll_no"], df_clean.get("subject_code", [""]*len(df_clean)))]
        df_clean["student_id"] = "STU_" + df_clean["roll_no"].astype(str)
        return df_clean

    def _build_students_table(self, results_df: pd.DataFrame, attendance_df: pd.DataFrame) -> pd.DataFrame:
        records = []
        if not results_df.empty:
            for _, r in results_df.iterrows():
                records.append({
                    "roll_no": r.get("roll_no"),
                    "student_name": r.get("student_name"),
                    "section": r.get("section", "A"),
                    "batch": r.get("batch", "2025-2029")
                })
        if not attendance_df.empty:
            for _, r in attendance_df.iterrows():
                records.append({
                    "roll_no": r.get("roll_no"),
                    "student_name": r.get("student_name"),
                    "section": r.get("section", "A"),
                    "batch": r.get("batch", "2025-2029")
                })

        if not records:
            df = pd.DataFrame(columns=["student_id", "roll_no", "student_name", "section", "batch"])
        else:
            raw_df = pd.DataFrame(records).dropna(subset=["roll_no"])
            df = raw_df.groupby("roll_no").first().reset_index()
            df["student_id"] = "STU_" + df["roll_no"].astype(str)
            df = df[["student_id", "roll_no", "student_name", "section", "batch"]]

        out_path = settings.DATA_PROCESSED_DIR / "students.csv"
        df.to_csv(out_path, index=False, encoding="utf-8")
        return df

    def _build_subjects_table(self, results_df: pd.DataFrame, attendance_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        raw_subjects = []
        
        def collect_subs(df, s_file):
            if df.empty:
                return
            for _, r in df.iterrows():
                sc = r.get("subject_code")
                sn = r.get("subject_name")
                sem = r.get("semester", 1)
                if pd.notna(sc) or pd.notna(sn):
                    raw_subjects.append({
                        "source_file": s_file,
                        "original_subject_code": str(sc) if pd.notna(sc) else "",
                        "original_subject_name": str(sn) if pd.notna(sn) else "",
                        "semester": int(sem)
                    })

        collect_subs(results_df, "results")
        collect_subs(attendance_df, "attendance")

        SubjectMapper.generate_subject_mapping_csv(raw_subjects)

        unique_std_subjects = {}
        unmatched_list = []
        for rec in raw_subjects:
            sem = rec["semester"]
            orig_c = rec["original_subject_code"]
            orig_n = rec["original_subject_name"]
            std_c, std_n, status = SubjectMapper.map_subject(orig_c, orig_n, sem)

            key = (std_c, sem)
            if key not in unique_std_subjects:
                unique_std_subjects[key] = {
                    "subject_id": f"SUB_{sem}_{std_c}",
                    "subject_code": std_c,
                    "subject_name": std_n,
                    "semester": sem,
                    "credits": SubjectMapper.get_subject_credits(std_c, sem)
                }
            if status == "UNMATCHED" and orig_c not in unmatched_list:
                unmatched_list.append(orig_c)

        subs_df = pd.DataFrame(list(unique_std_subjects.values())) if unique_std_subjects else pd.DataFrame(columns=["subject_id", "subject_code", "subject_name", "semester", "credits"])
        out_path = settings.DATA_PROCESSED_DIR / "subjects.csv"
        subs_df.to_csv(out_path, index=False, encoding="utf-8")

        matched_count = len([s for s in unique_std_subjects.keys() if s[0] not in unmatched_list])
        subject_stats = {
            "total_subjects": len(subs_df),
            "matched_subjects": matched_count,
            "unmatched_subjects": len(unmatched_list),
            "unmatched_list": unmatched_list
        }

        return subs_df, subject_stats

    def _apply_standard_subject_codes(self, results_df: pd.DataFrame, attendance_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not results_df.empty:
            for idx, r in results_df.iterrows():
                std_c, std_n, _ = SubjectMapper.map_subject(r.get("subject_code"), r.get("subject_name"), int(r.get("semester", 1)))
                results_df.at[idx, "subject_code"] = std_c
                results_df.at[idx, "subject_name"] = std_n
                results_df.at[idx, "subject_id"] = f"SUB_{r.get('semester', 1)}_{std_c}"

        if not attendance_df.empty:
            for idx, r in attendance_df.iterrows():
                std_c, std_n, _ = SubjectMapper.map_subject(r.get("subject_code"), r.get("subject_name"), int(r.get("semester", 1)))
                attendance_df.at[idx, "subject_code"] = std_c
                attendance_df.at[idx, "subject_name"] = std_n
                attendance_df.at[idx, "subject_id"] = f"SUB_{r.get('semester', 1)}_{std_c}"

        return results_df, attendance_df

    def _build_semester_summary(self, results_df: pd.DataFrame) -> pd.DataFrame:
        if results_df.empty:
            return pd.DataFrame(columns=["student_id", "roll_no", "semester", "sgpa", "backlog_count"])

        rows = []
        for (roll, sem), group in results_df.groupby(["roll_no", "semester"]):
            # Use authentic backlog_count parsed from Excel 'No. of Backlog' section
            if "backlog_count" in group.columns and not group["backlog_count"].dropna().empty:
                backlog_val = int(group["backlog_count"].dropna().iloc[0])
            else:
                backlog_val = int((group["status"] == "FAIL").sum())

            sgpa_val = group["sgpa"].dropna().iloc[0] if ("sgpa" in group.columns and not group["sgpa"].dropna().empty) else np.nan
            if pd.isna(sgpa_val) and "grade_point" in group.columns:
                valid_gp = group["grade_point"].dropna()
                if not valid_gp.empty and len(valid_gp) == len(group):
                    sgpa_val = round(valid_gp.mean(), 2)

            rows.append({
                "student_id": f"STU_{roll}",
                "roll_no": roll,
                "semester": int(sem),
                "sgpa": sgpa_val,
                "backlog_count": backlog_val
            })

        return pd.DataFrame(rows)

    def _sync_to_db(self, students_df: pd.DataFrame, subjects_df: pd.DataFrame, results_df: pd.DataFrame, attendance_df: pd.DataFrame, semester_summary_df: pd.DataFrame):
        if not self.db:
            return
        try:
            self.db.query(Attendance).delete()
            self.db.query(Result).delete()
            self.db.query(SemesterSummary).delete()
            self.db.query(Subject).delete()
            self.db.query(Student).delete()
            self.db.commit()

            for _, r in students_df.iterrows():
                self.db.add(Student(
                    student_id=str(r["student_id"]),
                    roll_no=str(r["roll_no"]),
                    student_name=r.get("student_name"),
                    section=r.get("section"),
                    batch=r.get("batch")
                ))

            for _, r in subjects_df.iterrows():
                self.db.add(Subject(
                    subject_id=str(r["subject_id"]),
                    subject_code=str(r["subject_code"]),
                    subject_name=str(r["subject_name"]),
                    semester=int(r["semester"]),
                    credits=float(r["credits"]) if pd.notna(r.get("credits")) else None
                ))

            for _, r in results_df.iterrows():
                self.db.add(Result(
                    result_id=str(r.get("result_id", f"RES_{r['roll_no']}_{r['subject_code']}")),
                    student_id=str(r.get("student_id", f"STU_{r['roll_no']}")),
                    roll_no=str(r["roll_no"]),
                    subject_id=str(r.get("subject_id", f"SUB_{r['subject_code']}")),
                    subject_code=str(r["subject_code"]),
                    semester=int(r["semester"]),
                    marks=float(r["marks"]) if pd.notna(r.get("marks")) else None,
                    grade=str(r["grade"]) if pd.notna(r.get("grade")) else None,
                    grade_point=float(r.get("grade_points", r.get("grade_point", 0.0))) if pd.notna(r.get("grade_points", r.get("grade_point"))) else None,
                    status=str(r["status"]) if pd.notna(r.get("status")) else None
                ))

            for _, r in attendance_df.iterrows():
                self.db.add(Attendance(
                    attendance_id=str(r.get("attendance_id", f"ATT_{r['roll_no']}_{r['subject_code']}")),
                    student_id=str(r.get("student_id", f"STU_{r['roll_no']}")),
                    roll_no=str(r["roll_no"]),
                    subject_id=str(r.get("subject_id", f"SUB_{r['subject_code']}")),
                    subject_code=str(r["subject_code"]),
                    semester=int(r["semester"]),
                    attendance_percentage=float(r["attendance_percentage"]) if pd.notna(r.get("attendance_percentage")) else 0.0
                ))

            for _, r in semester_summary_df.iterrows():
                self.db.add(SemesterSummary(
                    student_id=str(r["student_id"]),
                    roll_no=str(r["roll_no"]),
                    semester=int(r["semester"]),
                    sgpa=float(r["sgpa"]) if pd.notna(r.get("sgpa")) else None,
                    backlog_count=int(r["backlog_count"]) if pd.notna(r.get("backlog_count")) else None
                ))

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"[PIPELINE_DB_SYNC_ERROR] {e}")
