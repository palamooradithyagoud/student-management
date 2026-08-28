# AI-Based Student Academic Risk & Performance Intelligence System (CSM)

### **Department:** Computer Science and Engineering (Artificial Intelligence & Machine Learning) — `CSM`
### **Scope:** Phase 1 — Authentication Foundation + Ingestion + Cleaning + Normalization + Integration + Validation + Quality Reporting

---

## 🏛 System Architecture Overview

The system is a specialized, single-user academic intelligence platform engineered exclusively for the **HOD of the CSM Department**.

```
HOD LOGIN (/login)
      ↓ (JWT Auth Guard)
CSM HOD DASHBOARD (/dashboard)
      ↓
INGESTION & INSPECTION (/data) ──→ Auto-detect Header Rows & Title Banners
      ↓
CLEANING & AUDIT LOGGING       ──→ data_cleaning_log.csv
      ↓
SUBJECT STANDARDIZATION        ──→ subject_mapping.csv
      ↓
RESULT ↔ ATTENDANCE MAPPING    ──→ mapping_report.csv
      ↓
MASTER DATASET SYNTHESIS       ──→ master_dataset.csv
      ↓
STUDENT SEMESTER SUMMARY       ──→ student_semester_summary.csv (with Sem 1 → Sem 2 deltas)
      ↓
DATA QUALITY REPORTING         ──→ data_quality_report.md / .json
```

---

## 🔐 Authentication Model

- **Single-User Role:** Strictly `HOD`.
- **Department:** Fixed to `CSM`.
- **Endpoints:** All endpoints require a valid JWT Bearer token signed with `HS256` and verified by `get_current_hod`.
- **Default HOD Credentials:**
  - Username: `hod.csm`
  - Password: `hod_csm_secure_2026`

---

## 📁 Generated Output Datasets & Reports

### Processed Datasets (`data/processed/`):
1. [`master_dataset.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/master_dataset.csv) — 1 row per Student + Semester + Subject.
2. [`student_semester_summary.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/student_semester_summary.csv) — Per-student semester metrics with `sgpa_change`, `attendance_change`, `backlog_change`.
3. [`students.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/students.csv) — Normalized CSM student master records.
4. [`subjects.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/subjects.csv) — Standardized curriculum subject catalog.
5. [`results.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/results.csv) — Normalized marks, grades, and pass/fail records.
6. [`attendance.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/attendance.csv) — Normalized subject-wise attendance percentages.
7. [`semester_summary.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/semester_summary.csv) — Extracted semester SGPA and backlog counts.
8. [`subject_mapping.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/processed/subject_mapping.csv) — Raw to standardized course mapping table.

### Quality & Audit Reports (`data/reports/`):
1. [`data_quality_report.md`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/reports/data_quality_report.md) — Standardized ASCII/Markdown academic data quality report.
2. [`data_quality_report.json`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/reports/data_quality_report.json) — Machine-readable quality metrics.
3. [`data_cleaning_log.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/reports/data_cleaning_log.csv) — 100% traceable log of all cleaning actions.
4. [`mapping_report.csv`](file:///c:/HACAKTHONS/COLLEGE%20PROJECT/code/data/reports/mapping_report.csv) — Result ↔ Attendance mapping report per subject.

---

## 🚀 Running the System

### 1. Backend Server
```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```
API Documentation available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Application
```bash
cd frontend
npm run dev
```
Web Interface available at: `http://localhost:3000`

### 3. Running Automated Tests
```bash
python -m pytest backend/tests -v
```
All 22 unit, validation, ingestion, and master dataset integration tests will execute.
