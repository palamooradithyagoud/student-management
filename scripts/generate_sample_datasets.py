import os
import random
from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Standard CSM Students
STUDENT_NAMES = [
    ("23CSM1001", "AARAV SHARMA", "A"),
    ("23CSM1002", "ADITI RAO", "A"),
    ("23CSM1003", "AKASH VERMA", "A"),
    ("23CSM1004", "ANANYA REDDY", "A"),
    ("23CSM1005", "ANIKET GUPTA", "A"),
    ("23CSM1006", "BHAVANA NAIR", "A"),
    ("23CSM1007", "CHETAN PATEL", "A"),
    ("23CSM1008", "DEVIKA KRISHNAN", "A"),
    ("23CSM1009", "DHRUV CHOPRA", "A"),
    ("23CSM1010", "DIVYA MENON", "A"),
    ("23CSM1011", "ESHAAN JOSHI", "A"),
    ("23CSM1012", "HARINI VENKAT", "A"),
    ("23CSM1013", "HARSH VARDHAN", "A"),
    ("23CSM1014", "ISHITA MALHOTRA", "A"),
    ("23CSM1015", "KABIR DESHMUKH", "A"),
    ("23CSM1016", "KAVYA SENGUPTA", "A"),
    ("23CSM1017", "KUNAL AGARWAL", "A"),
    ("23CSM1018", "MANISH TIWARI", "A"),
    ("23CSM1019", "MEERA IYER", "A"),
    ("23CSM1020", "NEHA KULKARNI", "A"),
    ("23CSM1021", "NIKHIL SAXENA", "A"),
    ("23CSM1022", "POOJA HEGDE", "A"),
    ("23CSM1023", "PRANAV BHAT", "A"),
    ("23CSM1024", "PRIYA CHATTERJEE", "A"),
    ("23CSM1025", "RAHUL DESHPANDE", "A"),
    ("23CSM1026", "RHEA DAS", "A"),
    ("23CSM1027", "ROHAN MEHTA", "A"),
    ("23CSM1028", "SAHIL KHANNA", "A"),
    ("23CSM1029", "SAKSHI JAIN", "A"),
    ("23CSM1030", "SAMARTH BHARDWAJ", "A"),
    ("23CSM1031", "SANJANA PILLAI", "B"),
    ("23CSM1032", "SHREYA NATH", "B"),
    ("23CSM1033", "SIDDHARTH MISHRA", "B"),
    ("23CSM1034", "SMRITI KAUR", "B"),
    ("23CSM1035", "SNEHA BANERJEE", "B"),
    ("23CSM1036", "SOURAV BOSE", "B"),
    ("23CSM1037", "SRIDHAR NAYAK", "B"),
    ("23CSM1038", "SUDHIR REDDY", "B"),
    ("23CSM1039", "SUJATA GOWDA", "B"),
    ("23CSM1040", "TANMAY DAVE", "B"),
    ("23CSM1041", "TRISHA DUTTA", "B"),
    ("23CSM1042", "UTKARSH RAWAT", "B"),
    ("23CSM1043", "VAISHNAVI IYENGAR", "B"),
    ("23CSM1044", "VARUN CHAUHAN", "B"),
    ("23CSM1045", "VEDANT KASHYAP", "B"),
    ("23CSM1046", "VIKRAM SINGHANIA", "B"),
    ("23CSM1047", "VINAY PRASAD", "B"),
    ("23CSM1048", "VIVEK TRIPATHI", "B"),
    ("23CSM1049", "YASH RAJPUT", "B"),
    ("23CSM1050", "YUKTA BHARADWAJ", "B"),
    ("23CSM1051", "ZUBIN CONTRACTOR", "B"),
    ("23CSM1052", "AARYAN SHUKLA", "B"),
    ("23CSM1053", "ABHAY TIWARI", "B"),
    ("23CSM1054", "ADITYA MAHESHWARI", "B"),
    ("23CSM1055", "AKSHAT SAINI", "B"),
    ("23CSM1056", "ALOK PANDEY", "B"),
    ("23CSM1057", "AMAN DUBEY", "B"),
    ("23CSM1058", "AMIT CHOUDHARY", "B"),
    ("23CSM1059", "ANKIT TOMAR", "B"),
    ("23CSM1060", "ANMOL GOSWAMI", "B"),
]

SEM1_SUBJECTS = [
    ("23CSM1101", "Linear Algebra and Calculus"),
    ("23CSM1102", "Engineering Physics"),
    ("23CSM1103", "Programming for Problem Solving using C"),
    ("23CSM1104", "Basic Electrical and Electronics Engineering"),
    ("23CSM1105", "Engineering Graphics"),
    ("23CSM1106", "Programming Laboratory"),
    ("23CSM1107", "Physics Laboratory"),
]

SEM2_SUBJECTS = [
    ("23CSM1201", "Differential Equations and Vector Calculus"),
    ("23CSM1202", "Data Structures and Algorithms"),
    ("23CSM1203", "Python Programming for AI & ML"),
    ("23CSM1204", "Digital Logic and Computer Organization"),
    ("23CSM1205", "Discrete Mathematics"),
    ("23CSM1206", "Data Structures Laboratory"),
    ("23CSM1207", "Python for AI Laboratory"),
]

def grade_from_marks(marks):
    if marks is None or marks < 0:
        return "F", 0.0, "FAIL"
    if marks >= 90:
        return "O", 10.0, "PASS"
    elif marks >= 80:
        return "A+", 9.0, "PASS"
    elif marks >= 70:
        return "A", 8.0, "PASS"
    elif marks >= 60:
        return "B+", 7.0, "PASS"
    elif marks >= 50:
        return "B", 6.0, "PASS"
    elif marks >= 40:
        return "C", 5.0, "PASS"
    else:
        return "F", 0.0, "FAIL"

def create_excel_with_banner(file_path, title1, title2, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Consolidated_Data"

    # Banner Header Rows
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    ws.cell(row=1, column=1, value=title1)
    ws.cell(row=1, column=1).font = Font(size=13, bold=True, color="1E3A8A")
    ws.cell(row=1, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    ws.cell(row=2, column=1, value=title2)
    ws.cell(row=2, column=1).font = Font(size=11, bold=True, color="475569")
    ws.cell(row=2, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    # Row 3 is blank spacer
    ws.row_dimensions[3].height = 10

    # Row 4 is actual Column Headers
    header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    for col_idx, header_text in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=header_text)
        cell.font = Font(size=10, bold=True, color="0F172A")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[4].height = 24

    # Data Rows starting at Row 5
    for row_idx, row_data in enumerate(rows, 5):
        for col_idx, val in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    # Adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 40)

    wb.save(file_path)
    print(f"Created: {file_path}")

def generate_sample_data():
    random.seed(42)

    # 1. Sem 1 Results
    s1_res_headers = ["Roll No", "Student Name", "Section", "Subject Code", "Subject Name", "Marks", "Grade", "Grade Point", "Status", "SGPA"]
    s1_res_rows = []
    
    # 2. Sem 1 Attendance
    s1_att_headers = ["Hall Ticket No", "Student Name", "Section", "Sub Code", "Subject Title", "Attendance %"]
    s1_att_rows = []

    for stu_idx, (roll, name, sec) in enumerate(STUDENT_NAMES):
        # Noise injection: casing & whitespace for some records to test data cleaning
        raw_roll = roll
        if stu_idx == 4:
            raw_roll = f" {roll} "
        elif stu_idx == 11:
            raw_roll = roll.lower()
        elif stu_idx == 19:
            raw_roll = f"{roll[:5]} {roll[5:]}"

        student_gps = []
        for sc, sn in SEM1_SUBJECTS:
            # Baseline marks distribution
            base_mark = random.randint(45, 95)
            # Make student 8 fail 2 subjects
            if stu_idx == 7 and sc in ["23CSM1101", "23CSM1103"]:
                base_mark = 32
            # Make student 29 fail 1 subject
            if stu_idx == 28 and sc == "23CSM1104":
                base_mark = 28

            grade, gp, status = grade_from_marks(base_mark)
            student_gps.append(gp)

            # Mark 1 record as None for missing mark test
            final_mark = base_mark
            if stu_idx == 15 and sc == "23CSM1102":
                final_mark = None
                grade = None
                gp = None
                status = None

            s1_res_rows.append([raw_roll, name, sec, sc, sn, final_mark, grade, gp, status, None])

            # Attendance (correlated roughly with performance)
            att_pct = round(min(100.0, max(40.0, base_mark + random.uniform(-10, 10))), 1)
            # Edge cases for attendance
            if stu_idx == 2:
                att_pct = f"{att_pct}%" # string format test
            if stu_idx == 50 and sc == "23CSM1101":
                att_pct = 104.5 # out of bounds test
            if stu_idx == 51 and sc == "23CSM1105":
                att_pct = -2.0 # negative attendance test

            s1_att_rows.append([raw_roll, name, sec, sc, sn, att_pct])

    # Fill computed SGPA into s1_res_rows
    for row in s1_res_rows:
        row[9] = 8.25

    # Add 1 duplicate row in results for duplicate test
    s1_res_rows.append(s1_res_rows[0].copy())

    # 3. Sem 2 Results (56 students present from Sem 1 + 2 new lateral entry students)
    # Students 57, 58, 59, 60 are missing from Sem 2 (to test "Missing from Sem 2 dataset")
    sem2_students = STUDENT_NAMES[:56] + [
        ("23CSM1061", "AARYA CHOUDHURY", "A"),
        ("23CSM1062", "BHAVIK SHARMA", "B")
    ]

    s2_res_headers = ["Roll Number", "Student Name", "Section", "Course Code", "Course Title", "Total Marks", "Grade", "Grade Point", "Result", "SGPA"]
    s2_res_rows = []

    s2_att_headers = ["Roll No", "Candidate Name", "Section", "Subject Code", "Subject Name", "Attendance Percentage"]
    s2_att_rows = []

    for stu_idx, (roll, name, sec) in enumerate(sem2_students):
        student_gps = []
        for sc, sn in SEM2_SUBJECTS:
            base_mark = random.randint(48, 96)
            # Some students with academic change
            if stu_idx == 0:
                base_mark = 92 # improved
            if stu_idx == 10:
                base_mark = 34 # failed in sem 2

            grade, gp, status = grade_from_marks(base_mark)
            student_gps.append(gp)

            s2_res_rows.append([roll, name, sec, sc, sn, base_mark, grade, gp, status, 8.40])

            att_pct = round(min(100.0, max(50.0, base_mark + random.uniform(-8, 8))), 1)
            s2_att_rows.append([roll, name, sec, sc, sn, att_pct])

    # Write files with realistic banner headers
    create_excel_with_banner(
        RAW_DIR / "csm_sem1_results.xlsx",
        "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (AI & ML)",
        "B.TECH I YEAR I SEMESTER END EXAMINATIONS - CONSOLIDATED RESULTS (AY 2023-2024)",
        s1_res_headers,
        s1_res_rows
    )

    create_excel_with_banner(
        RAW_DIR / "csm_sem1_attendance.xlsx",
        "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (AI & ML)",
        "B.TECH I YEAR I SEMESTER SUBJECT-WISE CONSOLIDATED ATTENDANCE REPORT",
        s1_att_headers,
        s1_att_rows
    )

    create_excel_with_banner(
        RAW_DIR / "csm_sem2_results.xlsx",
        "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (AI & ML)",
        "B.TECH I YEAR II SEMESTER END EXAMINATIONS - CONSOLIDATED RESULTS (AY 2023-2024)",
        s2_res_headers,
        s2_res_rows
    )

    create_excel_with_banner(
        RAW_DIR / "csm_sem2_attendance.xlsx",
        "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (AI & ML)",
        "B.TECH I YEAR II SEMESTER SUBJECT-WISE CONSOLIDATED ATTENDANCE REPORT",
        s2_att_headers,
        s2_att_rows
    )

if __name__ == "__main__":
    generate_sample_data()
