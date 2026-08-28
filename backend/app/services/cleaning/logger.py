import csv
from pathlib import Path
from typing import Optional
from backend.app.core.config import settings

class CleaningAuditLogger:
    """
    Logs all data cleaning actions, transformations, warnings, and adjustments
    to data_cleaning_log.csv to guarantee 100% traceability.
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or (settings.DATA_REPORTS_DIR / "data_cleaning_log.csv")
        self.entries: list[dict[str, str]] = []
        self._ensure_log_file()

    def _ensure_log_file(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["source_file", "record_identifier", "issue", "action_taken", "reason"])

    def log(self, source_file: str, record_identifier: str, issue: str, action_taken: str, reason: str):
        entry = {
            "source_file": source_file,
            "record_identifier": record_identifier,
            "issue": issue,
            "action_taken": action_taken,
            "reason": reason
        }
        self.entries.append(entry)
        
        with open(self.log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([source_file, record_identifier, issue, action_taken, reason])

    def get_entries(self) -> list[dict[str, str]]:
        return self.entries

    def clear(self):
        self.entries = []
        with open(self.log_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source_file", "record_identifier", "issue", "action_taken", "reason"])
