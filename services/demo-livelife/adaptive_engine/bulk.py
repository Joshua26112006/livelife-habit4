"""Bulk answer sheets: one row per student and one column per question, as CSV or Excel.

Nothing is silently dropped: a bad row is reported with its reason, and a suspect cell is reported as a warning.
"""
import csv
import datetime
import io
import re

from openpyxl import load_workbook

ID_COLUMN = "student_id"
STUDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
MAX_BYTES = 2_000_000
MAX_STUDENTS = 200
MAX_CELL_CHARS = 2000
# Spreadsheets turn "4/10" into a date, which would silently corrupt an answer.
DATE_LIKE = re.compile(r"^\s*(\d{1,2}-[A-Za-z]{3}(-\d{2,4})?|[A-Za-z]{3}-\d{1,2}|\d{4}-\d{2}-\d{2}.*)\s*$")


class UploadError(ValueError):
    """The file as a whole cannot be used."""


def _read_csv(data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as err:
        raise UploadError("The file is not UTF-8 text. Save it as CSV UTF-8 or as .xlsx.") from err
    return [row for row in csv.reader(io.StringIO(text))]


def _read_excel(data, question_ids):
    """Reads the worksheet whose header matches this paper, so one workbook can hold both V1 and V2."""
    try:
        sheets = load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets
        wanted = set(question_ids)
        sheet = next((s for s in sheets if wanted <= {str(c).strip() for c in next(s.iter_rows(values_only=True, max_row=1), ())}), sheets[0])
    except Exception as err:
        raise UploadError("The Excel file could not be opened.") from err
    rows = []
    for values in sheet.iter_rows(values_only=True, max_row=MAX_STUDENTS + 2):
        rows.append(["" if v is None else v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else str(v) for v in values])
    return rows


def parse_upload(data, filename, question_ids):
    """Bytes -> {sheets, rejected, warnings}. Raises UploadError when the file itself is unusable."""
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > MAX_BYTES:
        raise UploadError("The file is larger than 2 MB.")
    rows = _read_excel(data, question_ids) if filename.lower().endswith((".xlsx", ".xlsm")) else _read_csv(data)
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    if not rows:
        raise UploadError("The file has no rows.")

    header = [str(c).strip() for c in rows[0]]
    if ID_COLUMN not in header:
        raise UploadError(f"The first row must include a '{ID_COLUMN}' column.")
    missing = [q for q in question_ids if q not in header]
    unknown = [c for c in header if c and c != ID_COLUMN and c not in question_ids]
    if missing or unknown:
        raise UploadError(f"Columns do not match this paper. Missing: {', '.join(missing) or 'none'}. Unexpected: {', '.join(unknown) or 'none'}.")
    if len(rows) - 1 > MAX_STUDENTS:
        raise UploadError(f"The file has more than {MAX_STUDENTS} students.")

    position = {name: i for i, name in enumerate(header)}
    sheets, rejected, warnings, seen = [], [], [], set()
    for number, row in enumerate(rows[1:], start=2):
        student = str(row[position[ID_COLUMN]]).strip() if position[ID_COLUMN] < len(row) else ""
        if not STUDENT_ID.match(student):
            rejected.append({"row": number, "reason": "Student ID is missing or has characters other than letters, digits, - or _."})
            continue
        if student in seen:
            rejected.append({"row": number, "student": student, "reason": "This student ID appears more than once."})
            continue
        seen.add(student)
        answers = {}
        for question in question_ids:
            cell = str(row[position[question]]).strip() if position[question] < len(row) else ""
            if len(cell) > MAX_CELL_CHARS:
                warnings.append({"row": number, "student": student, "question": question, "message": "Answer was too long and was cut."})
                cell = cell[:MAX_CELL_CHARS]
            if DATE_LIKE.match(cell):
                warnings.append({"row": number, "student": student, "question": question,
                                 "message": "This looks like a fraction the spreadsheet turned into a date. It was left blank for the teacher."})
                cell = ""
            answers[question] = cell
        sheets.append({"id": student, "answers": answers})
    if not sheets:
        raise UploadError("No row could be used.")
    return {"sheets": sheets, "rejected": rejected, "warnings": warnings}


def to_csv(columns, rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue()
