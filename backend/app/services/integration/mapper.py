import csv
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from backend.app.core.config import settings

# Standard CSM (B.Tech AI & ML) Subject Catalog for Sem 1 and Sem 2
CSM_STANDARD_CURRICULUM = {
    1: {
        "A9001": "Matrices and Calculus",
        "A9007": "Engineering Physics",
        "A9008": "Engineering Physics Laboratory",
        "A9021": "Community Centered Design Thinking",
        "A9204": "Basic Electrical Engineering",
        "A9205": "Basic Electrical Engineering Laboratory",
        "A9302": "Engineering Workshop",
        "A9501": "Programming for Problem Solving",
        "A9502": "Programming for Problem Solving Laboratory",
        "A9801": "Foundations of Data Science",
    },
    2: {
        "A9002": "Ordinary Differential Equations and Vector Calculus",
        "A9009": "Engineering Chemistry",
        "A9010": "Engineering Chemistry Laboratory",
        "A9011": "English for Skills Enhancement",
        "A9012": "English Language and Communication Skills Laboratory",
        "A9022": "Product Design and Development",
        "A9304": "Computer Aided Engineering Graphics",
        "A9402": "Digital Electronics",
        "A9503": "Data Structures",
        "A9504": "Data Structures Laboratory",
    }
}

# Exact Credit allocations from official curriculum register
CSM_SUBJECT_CREDITS = {
    (1, "A9001"): 4.0,
    (1, "A9007"): 3.0,
    (1, "A9008"): 1.0,
    (1, "A9021"): 1.0,
    (1, "A9204"): 2.0,
    (1, "A9205"): 1.0,
    (1, "A9302"): 1.0,
    (1, "A9501"): 3.0,
    (1, "A9502"): 1.0,
    (1, "A9801"): 3.0,
    (2, "A9002"): 4.0,
    (2, "A9009"): 3.0,
    (2, "A9010"): 1.0,
    (2, "A9011"): 2.0,
    (2, "A9012"): 1.0,
    (2, "A9022"): 1.0,
    (2, "A9304"): 1.0,
    (2, "A9402"): 3.0,
    (2, "A9503"): 3.0,
    (2, "A9504"): 1.0,
}

# Alias Map for common abbreviations
SUBJECT_ALIAS_MAP = {
    # Sem 1
    "MAC": ("A9001", "Matrices and Calculus", 1),
    "EP": ("A9007", "Engineering Physics", 1),
    "EPL": ("A9008", "Engineering Physics Laboratory", 1),
    "EP LAB": ("A9008", "Engineering Physics Laboratory", 1),
    "CCDT": ("A9021", "Community Centered Design Thinking", 1),
    "BEE": ("A9204", "Basic Electrical Engineering", 1),
    "BEEL": ("A9205", "Basic Electrical Engineering Laboratory", 1),
    "BEE LAB": ("A9205", "Basic Electrical Engineering Laboratory", 1),
    "EW": ("A9302", "Engineering Workshop", 1),
    "PPS": ("A9501", "Programming for Problem Solving", 1),
    "PPSL": ("A9502", "Programming for Problem Solving Laboratory", 1),
    "PPS LAB": ("A9502", "Programming for Problem Solving Laboratory", 1),
    "FDS": ("A9801", "Foundations of Data Science", 1),
    # Sem 2
    "ODEVC": ("A9002", "Ordinary Differential Equations and Vector Calculus", 2),
    "ODECV": ("A9002", "Ordinary Differential Equations and Vector Calculus", 2),
    "EC": ("A9009", "Engineering Chemistry", 2),
    "ECL": ("A9010", "Engineering Chemistry Laboratory", 2),
    "EC LAB": ("A9010", "Engineering Chemistry Laboratory", 2),
    "ESE": ("A9011", "English for Skills Enhancement", 2),
    "ECS": ("A9011", "English for Skills Enhancement", 2),
    "ESEL": ("A9012", "English Language and Communication Skills Laboratory", 2),
    "ELCSL": ("A9012", "English Language and Communication Skills Laboratory", 2),
    "PDP": ("A9022", "Product Design and Development", 2),
    "PDD": ("A9022", "Product Design and Development", 2),
    "CAEG": ("A9304", "Computer Aided Engineering Graphics", 2),
    "DE": ("A9402", "Digital Electronics", 2),
    "DS": ("A9503", "Data Structures", 2),
    "DSL": ("A9504", "Data Structures Laboratory", 2),
    "DS LAB": ("A9504", "Data Structures Laboratory", 2),
}

class SubjectMapper:
    """
    Standardizes subject codes and subject names, producing subject_mapping.csv.
    """

    @staticmethod
    def get_subject_credits(subject_code: str, semester: int) -> float:
        code_clean = str(subject_code).strip().upper()
        if (semester, code_clean) in CSM_SUBJECT_CREDITS:
            return CSM_SUBJECT_CREDITS[(semester, code_clean)]
        for (sem, sc), cr in CSM_SUBJECT_CREDITS.items():
            if sc == code_clean:
                return cr
        return 3.0

    @staticmethod
    def map_subject(raw_code: Optional[str], raw_name: Optional[str], semester: int) -> tuple[str, str, str]:
        sem_curriculum = CSM_STANDARD_CURRICULUM.get(semester, {})
        raw_c = str(raw_code).strip().upper().replace(" ", "").replace("-", "") if raw_code and pd.notna(raw_code) else ""
        raw_n = str(raw_name).strip().upper() if raw_name and pd.notna(raw_name) else ""

        # 1. Exact code match in semester curriculum
        if raw_c in sem_curriculum:
            return raw_c, sem_curriculum[raw_c], "MATCHED"

        # 2. Alias match from raw_c or raw_n (semester-matched first)
        if raw_c in SUBJECT_ALIAS_MAP:
            std_c, std_n, sem = SUBJECT_ALIAS_MAP[raw_c]
            if sem == semester or not sem_curriculum:
                return std_c, std_n, "MATCHED"
            if raw_c in sem_curriculum:
                return raw_c, sem_curriculum[raw_c], "MATCHED"
            return std_c, std_n, "MATCHED"

        if raw_n in SUBJECT_ALIAS_MAP:
            std_c, std_n, sem = SUBJECT_ALIAS_MAP[raw_n]
            if sem == semester or not sem_curriculum:
                return std_c, std_n, "MATCHED"
            if raw_n in sem_curriculum:
                return raw_n, sem_curriculum[raw_n], "MATCHED"
            return std_c, std_n, "MATCHED"

        # 3. Code substring match (e.g. A9001 in 'A9001 (MAC)')
        for std_code, std_name in sem_curriculum.items():
            if std_code in raw_c or std_code in raw_n:
                return std_code, std_name, "MATCHED"

        # 4. Fuzzy name match within the semester curriculum
        for std_code, std_name in sem_curriculum.items():
            std_n_clean = std_name.upper()
            if raw_n and (raw_n in std_n_clean or std_n_clean in raw_n or any(token in std_n_clean for token in raw_n.split() if len(token) > 2)):
                return std_code, std_name, "MATCHED"

        # Fallback: preserve original code
        fallback_code = raw_code or f"A9{semester}99"
        fallback_name = raw_name or f"Subject {raw_code}"
        return str(fallback_code).strip().upper(), str(fallback_name).strip(), "UNMATCHED"

    @staticmethod
    def generate_subject_mapping_csv(
        raw_subject_records: list[dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> Path:
        out_path = output_path or (settings.DATA_PROCESSED_DIR / "subject_mapping.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        seen = set()
        for rec in raw_subject_records:
            s_file = rec.get("source_file", "unknown")
            orig_c = str(rec.get("original_subject_code", ""))
            orig_n = str(rec.get("original_subject_name", ""))
            sem = int(rec.get("semester", 1))

            key = (s_file, orig_c, orig_n, sem)
            if key in seen:
                continue
            seen.add(key)

            std_c, std_n, status = SubjectMapper.map_subject(orig_c, orig_n, sem)
            rows.append({
                "source_file": s_file,
                "original_subject_code": orig_c,
                "original_subject_name": orig_n,
                "standard_subject_code": std_c,
                "standard_subject_name": std_n,
                "status": status
            })

        df = pd.DataFrame(rows)
        df.to_csv(out_path, index=False, encoding="utf-8")
        return out_path

class ResultAttendanceMapper:
    """
    Performs deterministic joining between Results and Attendance on
    (roll_no, semester, subject_code) and calculates mapping success rate.
    """

    @staticmethod
    def map_results_and_attendance(
        results_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        output_report_path: Optional[Path] = None
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        r_df = results_df.copy() if not results_df.empty else pd.DataFrame()
        a_df = attendance_df.copy() if not attendance_df.empty else pd.DataFrame()

        if not r_df.empty:
            r_df["join_key"] = r_df["roll_no"].astype(str) + "_" + r_df["semester"].astype(str) + "_" + r_df["subject_code"].astype(str)
        else:
            r_df["join_key"] = []

        if not a_df.empty:
            a_df["join_key"] = a_df["roll_no"].astype(str) + "_" + a_df["semester"].astype(str) + "_" + a_df["subject_code"].astype(str)
        else:
            a_df["join_key"] = []

        r_keys = set(r_df["join_key"]) if not r_df.empty else set()
        a_keys = set(a_df["join_key"]) if not a_df.empty else set()

        all_keys = r_keys.union(a_keys)
        matched_keys = r_keys.intersection(a_keys)
        r_only_keys = r_keys - a_keys
        a_only_keys = a_keys - r_keys

        total_result_records = len(r_df)
        total_attendance_records = len(a_df)
        matched_records = len(matched_keys)
        unmatched_records = len(r_only_keys) + len(a_only_keys)

        success_rate = (matched_records / total_result_records * 100.0) if total_result_records > 0 else 0.0

        report_rows = []
        for k in sorted(all_keys):
            parts = k.split("_")
            roll_no = parts[0] if len(parts) > 0 else ""
            sem = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            sub_code = parts[2] if len(parts) > 2 else ""

            has_res = k in r_keys
            has_att = k in a_keys

            status = "MATCHED" if (has_res and has_att) else ("RESULT_WITHOUT_ATTENDANCE" if has_res else "ATTENDANCE_WITHOUT_RESULT")
            report_rows.append({
                "roll_no": roll_no,
                "semester": sem,
                "subject_code": sub_code,
                "has_result": has_res,
                "has_attendance": has_att,
                "mapping_status": status
            })

        rep_df = pd.DataFrame(report_rows)
        out_path = output_report_path or (settings.DATA_REPORTS_DIR / "mapping_report.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rep_df.to_csv(out_path, index=False, encoding="utf-8")

        stats = {
            "total_result_records": total_result_records,
            "total_attendance_records": total_attendance_records,
            "matched_records": matched_records,
            "results_without_attendance": len(r_only_keys),
            "attendance_without_results": len(a_only_keys),
            "unmatched_records": unmatched_records,
            "mapping_success_rate": round(success_rate, 2),
            "report_path": str(out_path)
        }

        if not r_df.empty and not a_df.empty:
            a_dedup = a_df.drop_duplicates(subset=["join_key"])
            att_cols = [c for c in ["join_key", "attendance_percentage", "classes_attended", "classes_conducted"] if c in a_dedup.columns]
            merged = pd.merge(
                r_df,
                a_dedup[att_cols],
                on="join_key",
                how="left"
            )
        elif not r_df.empty:
            merged = r_df.copy()
            merged["attendance_percentage"] = None
        else:
            merged = a_df.copy()
            merged["marks"] = None
            merged["grade"] = None
            merged["grade_point"] = None
            merged["status"] = None

        return merged, stats
