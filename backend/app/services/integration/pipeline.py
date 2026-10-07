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
from backend.app.models.upload_log import UploadLog

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
        batch_name: Optional[str] = None,
        sem1_res_path: Optional[Path] = None,
        sem2_res_path: Optional[Path] = None,
        sem1_att_path: Optional[Path] = None,
        sem2_att_path: Optional[Path] = None
    ) -> dict[str, Any]:
        start_time = time.time()
        self.logger.clear()

        # 1. Discover all uploaded input datasets for this batch
        base_data = settings.DATA_DIR
        raw_dir = base_data / "raw"

        # Query upload logs from DB if available
        upload_records = []
        if self.db:
            q = self.db.query(UploadLog)
            if batch_name:
                q = q.filter(UploadLog.batch_name == batch_name)
            upload_records = q.all()

        all_res_dfs = []
        all_att_dfs = []

        # Iterate through Semesters 1 to 8
        for sem in range(1, 9):
            # Locate Result file for this semester
            res_file = None
            if sem == 1 and sem1_res_path and sem1_res_path.exists():
                res_file = sem1_res_path
            elif sem == 2 and sem2_res_path and sem2_res_path.exists():
                res_file = sem2_res_path
            else:
                # Find in DB upload logs first
                res_log = next(
                    (l for l in upload_records if l.semester == sem and ("result" in l.dataset_type.lower() or l.section == "OVERALL")),
                    None
                )
                if res_log and (raw_dir / res_log.filename).exists():
                    res_file = raw_dir / res_log.filename
                else:
                    # Look in raw_dir for uploaded results matching pattern
                    patterns = [
                        f"*results*{batch_name}*sem{sem}*" if batch_name else None,
                        f"*results*sem{sem}*",
                    ]
                    for pat in filter(None, patterns):
                        matches = list(raw_dir.glob(pat))
                        if matches:
                            res_file = matches[0]
                            break

            if res_file and res_file.exists():
                df_res = self._load_and_clean_results(res_file, semester=sem, dataset_type=f"sem{sem}_results")
                if not df_res.empty:
                    all_res_dfs.append(df_res)

            # Locate Section-wise Attendance files for this semester
            att_files_with_sec = []
            if sem == 1 and sem1_att_path and sem1_att_path.exists():
                att_files_with_sec.append((sem1_att_path, "A"))
            elif sem == 2 and sem2_att_path and sem2_att_path.exists():
                att_files_with_sec.append((sem2_att_path, "A"))
            else:
                # Find in DB upload logs
                att_logs = [l for l in upload_records if l.semester == sem and ("attendance" in l.dataset_type.lower() or l.section != "OVERALL")]
                for l in att_logs:
                    f = raw_dir / l.filename
                    if f.exists():
                        att_files_with_sec.append((f, l.section or "A"))

                if not att_files_with_sec:
                    # Check raw_dir matching pattern
                    raw_att_matches = list(raw_dir.glob(f"*attendance*{batch_name}*sem{sem}*")) if batch_name else list(raw_dir.glob(f"*attendance*sem{sem}*"))
                    for f in raw_att_matches:
                        import re
                        sec_m = re.search(r'sec([A-Za-z0-9]+)', f.name, re.IGNORECASE)
                        sec_val = sec_m.group(1).upper() if sec_m else "A"
                        att_files_with_sec.append((f, sec_val))

            for f_path, sec_val in att_files_with_sec:
                df_att = self._load_and_clean_attendance(f_path, semester=sem, dataset_type=f"sem{sem}_attendance", section=sec_val)
                if not df_att.empty:
                    all_att_dfs.append(df_att)

        # Combine results and attendance across all semesters
        results_df = pd.concat(all_res_dfs, ignore_index=True) if all_res_dfs else pd.DataFrame()
        attendance_df = pd.concat(all_att_dfs, ignore_index=True) if all_att_dfs else pd.DataFrame()

        if results_df.empty and attendance_df.empty:
            return {
                "status": "NO_DATA",
                "message": f"No uploaded academic datasets found for batch '{batch_name or 'selected'}'. Please upload semester results and section attendance first.",
                "execution_time_seconds": round(time.time() - start_time, 2),
                "total_students": 0,
                "sem1_students": 0,
                "sem2_students": 0,
                "total_results": 0,
                "total_attendance": 0,
                "matched_records": 0,
                "unmatched_records": 0,
                "mapping_success_rate": 0.0,
                "generated_files": [],
                "critical_errors": 0,
                "warnings": 0,
                "records_requiring_review": 0,
                "quality_report": {}
            }

        # Extract & Standardize Students Master Table with batch
        students_df = self._build_students_table(results_df, attendance_df, batch_name=batch_name)

        # Extract & Standardize Subjects and Mappings
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
        all_res_rolls = set(results_df["roll_no"].astype(str)) if not results_df.empty and "roll_no" in results_df.columns else set()
        all_att_rolls = set(attendance_df["roll_no"].astype(str)) if not attendance_df.empty and "roll_no" in attendance_df.columns else set()

        s1_res_stus = set(results_df[results_df["semester"] == 1]["roll_no"].astype(str)) if not results_df.empty and "semester" in results_df.columns else set()
        s2_res_stus = set(results_df[results_df["semester"] == 2]["roll_no"].astype(str)) if not results_df.empty and "semester" in results_df.columns else set()
        s1_att_stus = set(attendance_df[attendance_df["semester"] == 1]["roll_no"].astype(str)) if not attendance_df.empty and "semester" in attendance_df.columns else set()
        s2_att_stus = set(attendance_df[attendance_df["semester"] == 2]["roll_no"].astype(str)) if not attendance_df.empty and "semester" in attendance_df.columns else set()

        student_val = DataValidator.validate_cross_dataset_students(
            sem1_res_students=s1_res_stus,
            sem2_res_students=s2_res_stus,
            sem1_att_students=s1_att_stus,
            sem2_att_students=s2_att_stus,
            all_res_students=all_res_rolls,
            all_att_students=all_att_rolls
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
            self._sync_to_db(students_df, subjects_df, results_df, attendance_df, semester_summary_df, batch_name=batch_name)

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

    def _load_and_clean_attendance(self, file_path: Optional[Path], semester: int, dataset_type: str, section: Optional[str] = None) -> pd.DataFrame:
        if not file_path or not file_path.exists():
            return pd.DataFrame()
        df_raw = RawDataLoader.load_dataset(file_path, dataset_type=dataset_type, semester=semester, section=section)
        df_clean = self.normalizer.clean_attendance_dataframe(df_raw, source_file=file_path.name)
        if section:
            df_clean["section"] = section
        df_clean["attendance_id"] = [f"ATT_S{semester}_{r}_{sc}" for r, sc in zip(df_clean["roll_no"], df_clean.get("subject_code", [""]*len(df_clean)))]
        df_clean["student_id"] = "STU_" + df_clean["roll_no"].astype(str)
        return df_clean

    def _build_students_table(self, results_df: pd.DataFrame, attendance_df: pd.DataFrame, batch_name: Optional[str] = None) -> pd.DataFrame:
        records = []
        batch_val = batch_name or "2024-2028"
        if not results_df.empty:
            for _, r in results_df.iterrows():
                records.append({
                    "roll_no": r.get("roll_no"),
                    "student_name": r.get("student_name"),
                    "section": r.get("section", "A"),
                    "batch": batch_val
                })
        if not attendance_df.empty:
            for _, r in attendance_df.iterrows():
                records.append({
                    "roll_no": r.get("roll_no"),
                    "student_name": r.get("student_name"),
                    "section": r.get("section", "A"),
                    "batch": batch_val
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

    def _sync_to_db(self, students_df: pd.DataFrame, subjects_df: pd.DataFrame, results_df: pd.DataFrame, attendance_df: pd.DataFrame, semester_summary_df: pd.DataFrame, batch_name: Optional[str] = None):
        if not self.db:
            return
        try:
            if batch_name:
                batch_rolls = [str(r["roll_no"]).strip() for _, r in students_df.iterrows()]
                if batch_rolls:
                    self.db.query(Attendance).filter(Attendance.roll_no.in_(batch_rolls)).delete(synchronize_session=False)
                    self.db.query(Result).filter(Result.roll_no.in_(batch_rolls)).delete(synchronize_session=False)
                    self.db.query(SemesterSummary).filter(SemesterSummary.roll_no.in_(batch_rolls)).delete(synchronize_session=False)
                    self.db.query(Student).filter(Student.roll_no.in_(batch_rolls)).delete(synchronize_session=False)
            else:
                self.db.query(Attendance).delete()
                self.db.query(Result).delete()
                self.db.query(SemesterSummary).delete()
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
                s_id = str(r["subject_id"])
                existing_sub = self.db.query(Subject).filter(Subject.subject_id == s_id).first()
                if not existing_sub:
                    self.db.add(Subject(
                        subject_id=s_id,
                        subject_code=str(r["subject_code"]),
                        subject_name=str(r["subject_name"]),
                        semester=int(r["semester"]),
                        credits=float(r["credits"]) if pd.notna(r.get("credits")) else None
                    ))
                else:
                    existing_sub.subject_name = str(r["subject_name"])
                    existing_sub.credits = float(r["credits"]) if pd.notna(r.get("credits")) else None

            for _, r in results_df.iterrows():
                self.db.add(Result(
                    result_id=str(r.get("result_id", f"RES_S{r['semester']}_{r['roll_no']}_{r['subject_code']}")),
                    student_id=str(r.get("student_id", f"STU_{r['roll_no']}")),
                    roll_no=str(r["roll_no"]),
                    subject_id=str(r.get("subject_id", f"SUB_{r['semester']}_{r['subject_code']}")),
                    subject_code=str(r["subject_code"]),
                    semester=int(r["semester"]),
                    marks=float(r["marks"]) if pd.notna(r.get("marks")) else None,
                    grade=str(r["grade"]) if pd.notna(r.get("grade")) else None,
                    grade_point=float(r.get("grade_points", r.get("grade_point", 0.0))) if pd.notna(r.get("grade_points", r.get("grade_point"))) else None,
                    status=str(r["status"]) if pd.notna(r.get("status")) else None
                ))

            for _, r in attendance_df.iterrows():
                self.db.add(Attendance(
                    attendance_id=str(r.get("attendance_id", f"ATT_S{r['semester']}_{r['roll_no']}_{r['subject_code']}")),
                    student_id=str(r.get("student_id", f"STU_{r['roll_no']}")),
                    roll_no=str(r["roll_no"]),
                    subject_id=str(r.get("subject_id", f"SUB_{r['semester']}_{r['subject_code']}")),
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
