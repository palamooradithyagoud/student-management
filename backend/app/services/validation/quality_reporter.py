import json
from pathlib import Path
from typing import Any, Optional
from backend.app.core.config import settings

class QualityReporter:
    """
    Generates data_quality_report.json and data_quality_report.md matching
    the exact standardized format for CSM academic quality reporting.
    """

    @staticmethod
    def generate_report(
        student_val: dict[str, Any],
        results_val: dict[str, Any],
        attendance_val: dict[str, Any],
        subject_stats: dict[str, Any],
        mapping_stats: dict[str, Any],
        critical_errors: int,
        warnings: int,
        records_requiring_review: int,
        json_path: Optional[Path] = None,
        md_path: Optional[Path] = None
    ) -> dict[str, Any]:
        j_path = json_path or (settings.DATA_REPORTS_DIR / "data_quality_report.json")
        m_path = md_path or (settings.DATA_REPORTS_DIR / "data_quality_report.md")

        j_path.parent.mkdir(parents=True, exist_ok=True)
        m_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "department": settings.DEPARTMENT_CODE,
            "department_name": settings.DEPARTMENT_NAME,
            "students": {
                "sem1_students": student_val.get("sem1_total_students", 0),
                "sem2_students": student_val.get("sem2_total_students", 0),
                "matched_students": student_val.get("counts", {}).get("present_in_all", 0),
                "students_missing_from_sem2": student_val.get("counts", {}).get("missing_from_sem2_dataset", 0),
                "details": {
                    "present_in_all": student_val.get("present_in_all_datasets", []),
                    "missing_from_sem2": student_val.get("missing_from_sem2_dataset", []),
                    "missing_from_sem1": student_val.get("missing_from_sem1_dataset", []),
                    "in_results_missing_attendance": student_val.get("in_results_missing_attendance", []),
                    "in_attendance_missing_results": student_val.get("in_attendance_missing_results", [])
                }
            },
            "results": {
                "sem1_records": results_val.get("sem1_records", 0),
                "sem2_records": results_val.get("sem2_records", 0),
                "missing_marks": results_val.get("missing_marks", 0),
                "missing_grades": results_val.get("missing_grades", 0),
                "duplicate_records": results_val.get("duplicate_records", 0),
                "duplicates_list": results_val.get("duplicates_list", [])
            },
            "attendance": {
                "sem1_records": attendance_val.get("sem1_records", 0),
                "sem2_records": attendance_val.get("sem2_records", 0),
                "missing_attendance": attendance_val.get("missing_attendance", 0),
                "invalid_attendance": attendance_val.get("invalid_attendance", 0),
                "duplicate_records": attendance_val.get("duplicate_records", 0),
                "duplicates_list": attendance_val.get("duplicates_list", [])
            },
            "subjects": {
                "total_subjects": subject_stats.get("total_subjects", 0),
                "matched_subjects": subject_stats.get("matched_subjects", 0),
                "unmatched_subjects": subject_stats.get("unmatched_subjects", 0),
                "unmatched_list": subject_stats.get("unmatched_list", [])
            },
            "mapping": {
                "result_records": mapping_stats.get("total_result_records", 0),
                "attendance_records": mapping_stats.get("total_attendance_records", 0),
                "successfully_matched": mapping_stats.get("matched_records", 0),
                "unmatched": mapping_stats.get("unmatched_records", 0),
                "mapping_success_rate": f"{mapping_stats.get('mapping_success_rate', 0.0)}%"
            },
            "data_quality": {
                "critical_errors": critical_errors,
                "warnings": warnings,
                "records_requiring_review": records_requiring_review
            }
        }

        # Write JSON
        with open(j_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)

        # Write Markdown in the exact required layout
        md_content = f"""========================================
CSM ACADEMIC DATA QUALITY REPORT
========================================

STUDENTS
--------
Sem 1 students: {report_data['students']['sem1_students']}
Sem 2 students: {report_data['students']['sem2_students']}
Matched students: {report_data['students']['matched_students']}
Detained students (in Sem 1, absent from Sem 2 - institutional, NOT a data error): {report_data['students']['students_missing_from_sem2']}

RESULTS
-------
Sem 1 records: {report_data['results']['sem1_records']}
Sem 2 records: {report_data['results']['sem2_records']}
Missing marks: {report_data['results']['missing_marks']}
Missing grades: {report_data['results']['missing_grades']}
Duplicate records: {report_data['results']['duplicate_records']}

ATTENDANCE
----------
Sem 1 records: {report_data['attendance']['sem1_records']}
Sem 2 records: {report_data['attendance']['sem2_records']}
Missing attendance: {report_data['attendance']['missing_attendance']}
Invalid attendance: {report_data['attendance']['invalid_attendance']}
Duplicate records: {report_data['attendance']['duplicate_records']}

SUBJECTS
--------
Total subjects: {report_data['subjects']['total_subjects']}
Matched subjects: {report_data['subjects']['matched_subjects']}
Unmatched subjects: {report_data['subjects']['unmatched_subjects']}

MAPPING
-------
Result records: {report_data['mapping']['result_records']}
Attendance records: {report_data['mapping']['attendance_records']}
Successfully matched: {report_data['mapping']['successfully_matched']}
Unmatched: {report_data['mapping']['unmatched']}
Mapping success rate: {report_data['mapping']['mapping_success_rate']}

DATA QUALITY
------------
Critical errors: {report_data['data_quality']['critical_errors']}
Warnings: {report_data['data_quality']['warnings']}
Records requiring review: {report_data['data_quality']['records_requiring_review']}

========================================
"""
        with open(m_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return report_data
